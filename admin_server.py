import os.path
import socket
import threading
from threading import Thread
import flashpoint_protocol
from db_connector import DBConnection
from PIL import Image
import io
import logging
from adv_db import AdvDB
from rsa import RsaEncryption
from aes import AesEncryption

FIRST_FUNCS = ['SU', 'LI', 'SD']
IP = '0.0.0.0'
PORT = 3600
QUEUE_SIZE = 10
POSTER_DICT = {'10 Things I Hate About You': 'posters/10things_trailer.png', 'Aladdin': 'posters/aladdin_trailer.png',
               'Dark Knight': 'posters/dark_knight.png', 'Inception': 'posters/inception.png',
               'Lord Of The Rings': 'posters/rings.png', 'Merlin': 'posters/merlin.png',
               'Never Ending Story': 'posters/never_ending.png', "Singin' In The Rain": 'posters/rain.png',
               'Star Wars': 'posters/star_wars.png', 'Superman 1978': 'posters/superman1978.png',
               'Superman 2025': 'posters/superman2025.png', 'The Batman': 'posters/the_batman.png',
               'The Flash': 'posters/the_flash.png'}

# setting global lock variable
write_lock = threading.Lock()


def login(login_msg, db):
    """
    The func checks whether the user exists or not
    :param login_msg: A message written by protocol with the 'LI' command
    :type login_msg: bytes
    :param db: The MySQL database connection
    :type db: DBConnection object
    :return: True if the user exists and False if not
    """
    username = flashpoint_protocol.get_data(login_msg, 1).decode()
    password = flashpoint_protocol.get_data(login_msg, 2).decode()
    return db.user_exists(username, password)


def signup(signup_msg, db):
    """
    The func checks if a username is already in the database. If not the func adds te new user.
    :param signup_msg: A message written by protocol with the 'SU' command
    :type signup_msg: bytes
    :param db: The MySQL database connection
    :type db: DBConnection object
    :return: True if the user was added to the database, and False if not.
    """
    global write_lock
    username = flashpoint_protocol.get_data(signup_msg, 1).decode()
    password = flashpoint_protocol.get_data(signup_msg, 2).decode()
    ret_ans = db.username_exists(username)
    if not ret_ans:
        write_lock.acquire()
        db.add_user(username, password)
        logging.debug(f"added user({username, password} to database")
        write_lock.release()
    return not ret_ans


def get_movie_lst(user_id, db):
    """
    returns the user's paused movie list from client.
    :param user_id: the user's id
    :type user_id: int
    :param db: a MySQL connection
    :type db: DBConnection
    :return:
    """
    movie_lst = db.get_movie_lst(user_id)
    return movie_lst


def get_poster_lst(db):
    """
    The func returns a list of the posters file paths
    :param db: an ADV database
    :type db: AdvDB
    :return: a list of all existing poster images file paths
    """
    posters = db.get_dict()
    new_dict = {}
    for key in posters:
        if os.path.exists(posters[key]):
            new_dict[key] = posters[key]
    return new_dict


def min_clients(socket_dict):
    """
    The func finds the socket with the least amount of clients
    :param socket_dict: a dictionary that holds the sockets ip and port and how many clients each currently handles.
    :return: the ip and port of the socket that handles the min amount of clients.
    """
    first_key = next(iter(socket_dict))
    min_amount = socket_dict[first_key]
    min_key = first_key
    for key in socket_dict:
        if socket_dict[key] < min_amount:
            min_key = key
    return min_key


def image2bytes(image_fpath):
    """
    converting a png image to bytes
    :param image_fpath: the image file path
    :type image_fpath: str
    :return: the image from the file path in bytes
    """
    image_bytes = b''
    if isinstance(image_fpath, bytes):
        image_fpath.decode()
    if os.path.exists(image_fpath):
        image = Image.open(image_fpath)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        buffer.close()
    return image_bytes


def handle_thread(client_socket, client_address, poster_db, socket_db):
    global write_lock
    cont_connection = True

    # creating a MySQL database connection
    db = DBConnection()

    # setting RSA object and public key
    rsa_obj = RsaEncryption()
    pub_key = rsa_obj.get_pub_key()

    # sending first message
    first_msg = flashpoint_protocol.create_proto_msg('PK', flashpoint_protocol.create_proto_data(pub_key))
    client_socket.send(first_msg)
    logging.debug(f"{client_address}: sent PK message to client")

    # waiting for 'AES Key' message and making sure the command in it is the correct one for the start
    key_msg = flashpoint_protocol.get_rsa_msg(client_socket, rsa_obj)
    while flashpoint_protocol.get_func(key_msg) != 'AK':
        key_msg = flashpoint_protocol.get_rsa_msg(client_socket, rsa_obj)

    key = flashpoint_protocol.get_data(key_msg)
    print(key)
    aes_obj = AesEncryption(key)

    while cont_connection:
        # waiting for messages so long no error was raised

        # checking if an error was raised or if the client disconnected before waiting for a message
        ret_msg = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)
        func = flashpoint_protocol.get_func(ret_msg)
        logging.debug(f"{client_address}: got {func} message from client")

        if func == 'LI':
            # handling login request
            while not login(ret_msg, db) and flashpoint_protocol.get_func(ret_msg) == 'LI':
                msg = flashpoint_protocol.create_aes_msg('VU', flashpoint_protocol.create_proto_data(b'False'),
                                                         aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent VU to client")
                ret_msg = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)

            if flashpoint_protocol.get_func(ret_msg) != 'LI':
                msg = flashpoint_protocol.create_aes_msg('ER', flashpoint_protocol.create_proto_data(), aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent ER to client while trying to login")

            else:
                msg = flashpoint_protocol.create_aes_msg('VU', flashpoint_protocol.create_proto_data(b'True'),
                                                         aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent VU to client")

        if func == 'SU':
            # handling sign-up request
            while not signup(ret_msg, db) and flashpoint_protocol.get_func(ret_msg) == 'SU':
                msg = flashpoint_protocol.create_aes_msg('IE', flashpoint_protocol.create_proto_data(b'True'),
                                                         aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent IE to client")
                ret_msg = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)

            if flashpoint_protocol.get_func(ret_msg) != 'SU':
                msg = flashpoint_protocol.create_aes_msg('ER', flashpoint_protocol.create_proto_data(), aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent ER to client while trying to sign-up")

            else:
                msg = flashpoint_protocol.create_aes_msg('IE', flashpoint_protocol.create_proto_data(b'False'),
                                                         aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent IE to client")

        if func == 'GM':
            # handling a 'get movies' request
            user_id = db.get_user_id(flashpoint_protocol.get_data(ret_msg, 1),
                                     flashpoint_protocol.get_data(ret_msg, 2))
            if user_id:
                m_data = get_movie_lst(user_id, db)
                msg = flashpoint_protocol.create_aes_msg('LL', flashpoint_protocol.create_proto_data(
                                                                            str(len(m_data)).encode()), aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent LL to client")

                for i in range(len(m_data)):
                    img = poster_db.get_val(m_data[i][0])
                    img = image2bytes(img)
                    msg = flashpoint_protocol.create_aes_msg('YM', flashpoint_protocol.create_proto_data(
                                                                   m_data[i][0].encode(), str(m_data[i][1]).encode(),
                                                                   img), aes_obj)
                    client_socket.send(msg)
                    logging.debug(f"{client_address}: sent YM to client")

            else:
                client_socket.send(flashpoint_protocol.create_aes_msg('ER',
                                                                      flashpoint_protocol.create_proto_data(), aes_obj))
                logging.debug(f"{client_address}: sent ER to client while trying to send movie posters")

        if func == 'AP':
            # handling an 'all posters' request
            posters = get_poster_lst(poster_db)
            msg = flashpoint_protocol.create_aes_msg('LL', flashpoint_protocol.create_proto_data(
                                                                        str(len(posters)).encode()), aes_obj)
            client_socket.send(msg)
            logging.debug(f"{client_address}: sent LL to client")

            for key in posters:
                poster_bytes = image2bytes(posters[key])
                msg = flashpoint_protocol.create_aes_msg('PL', flashpoint_protocol.create_proto_data(
                                                               key.encode(), poster_bytes), aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent PL to client")

        if func == 'SD':
            # handling 'server details' command
            ip = flashpoint_protocol.get_data(ret_msg).decode()
            port = flashpoint_protocol.get_data(ret_msg, 2).decode()
            sock_details = ip + ':' + port
            socket_db.set_val(sock_details, 0)
            logging.debug(f"added {sock_details} to database")

        if func == 'CR':
            # handling a connection request
            server_dict = socket_db.get_dict()
            server_key = min_clients(server_dict)
            if server_key != '':
                ip = server_key.split(':')[0]
                port = server_key.split(':')[1]
                msg_data = flashpoint_protocol.create_proto_data(ip.encode(), port.encode())
                msg = flashpoint_protocol.create_aes_msg('SA', msg_data, aes_obj)
                client_socket.send(msg)
                logging.debug(f"{client_address}: sent SA to client")
                server_num = server_dict[server_key]
                server_num += 1
                socket_db.set_val(server_key, server_num)

        if func == 'UD':
            # handling an 'update database' request
            username = flashpoint_protocol.get_data(ret_msg).decode()
            password = flashpoint_protocol.get_data(ret_msg, 2).decode()
            movie = flashpoint_protocol.get_data(ret_msg, 3).decode()
            frame = int(flashpoint_protocol.get_data(ret_msg, 4).decode())
            write_lock.acquire()
            if frame < 0:
                db.remove_seen_movie(username, password, movie)
            else:
                db.update_last_frame(username, password, movie, frame)
            write_lock.release()

        if func == 'DC':
            # handling client disconnecting from media server and updating the needed info
            ip = flashpoint_protocol.get_data(ret_msg).decode()
            port = flashpoint_protocol.get_data(ret_msg, 2).decode()
            sock_details = ip + ':' + port
            client_num = socket_db.get_val(sock_details)

            if client_num:
                client_num -= 1
                if client_num < 0:
                    client_num = 0
            socket_db.set_val(sock_details, client_num)

        if func == 'DS':
            # client disconnected
            cont_connection = False

        if func == 'ER':
            # an error was raised
            cont_connection = False


def main():
    # creating databases to hold the poster file paths and the socket info.
    poster_db = AdvDB(True, 'poster', POSTER_DICT)
    socket_db = AdvDB(True, 'sockets')

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)

        while True:
            client_socket, client_address = server_socket.accept()
            thread = Thread(target=handle_thread,
                            args=(client_socket, client_address, poster_db, socket_db))
            thread.start()
    except socket.error as err:
        logging.error(f"received socket exception: {err}")
    finally:
        server_socket.close()


if __name__ == "__main__":
    logging.basicConfig(filename='admin_server.log', level=logging.DEBUG)
    logging.getLogger("PIL").setLevel(logging.ERROR)
    main()
