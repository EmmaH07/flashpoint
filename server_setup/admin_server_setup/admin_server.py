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
POSTER_DIR = 'posters'

# keeping track of media server sockets
media_sockets = []


def get_all_file_paths(directory):
    """
    A func that fetches all movie file paths from the computer
    :param directory: the directory from which the file paths should be taken
    :return: a list of file paths from said directory
    """

    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory {directory} created.")

    file_paths = []
    for filename in os.listdir(directory):
        full_path = os.path.join(directory, filename)
        if os.path.isfile(full_path):
            file_paths.append(full_path)

    return file_paths


def initialize_db(db_name, info_dir):
    """
    A func to start a database when initializing the server
    :param db_name: the name of the file for the database
    :type db_name: str
    :param info_dir: the directory from which the files should be taken
    :type info_dir: str
    :return: an AdvDB object that contains the needed info
    """

    if info_dir != '':
        paths_lst = get_all_file_paths(info_dir)
        path_dict = {}

        for path in paths_lst:
            name = path.replace("_", " ")
            name = name.split('.')[0]
            name = name.split("\\")[1]
            path_dict[name] = path

        new_db = AdvDB(True, db_name, path_dict)

    else:
        new_db = AdvDB(True, db_name)

    return new_db


def login(login_msg, db):
    """
    The func checks whether the user exists or not
    :param login_msg: A message written by protocol with the 'LI' command
    :type login_msg: bytes
    :param db: The MySQL database connection
    :type db: DBConnection object
    :return: True if the user exists and False if not
    """
    ans = False
    try:
        username = flashpoint_protocol.get_data(login_msg, 1).decode()
        password = flashpoint_protocol.get_data(login_msg, 2).decode()
        ans = db.user_exists(username, password)

    except Exception as e:
        logging.error(f'received exception while trying to check if a user exists: {e}')

    return ans


def signup(signup_msg, db):
    """
    The func checks if a username is already in the database. If not the func adds te new user.
    :param signup_msg: A message written by protocol with the 'SU' command
    :type signup_msg: bytes
    :param db: The MySQL database connection
    :type db: DBConnection object
    :return: True if the user was added to the database, and False if not.
    """
    ret_ans = True
    try:
        username = flashpoint_protocol.get_data(signup_msg, 1).decode()
        password = flashpoint_protocol.get_data(signup_msg, 2).decode()
        ret_ans = db.username_exists(username)

        if not ret_ans:
            db.add_user(username, password)
            logging.debug(f"added user({username, password} to database")

    except Exception as e:
        logging.error(f'received exception while trying to save a user to database: {e}')

    return not ret_ans


def get_movie_lst(user_id, db):
    """
    returns the user's paused movie list from client.
    :param user_id: the user's id
    :type user_id: int
    :param db: a MySQL connection
    :type db: DBConnection
    :return: the list of the user's seen movies
    """
    movie_lst = []
    try:
        movie_lst = db.get_movie_lst(user_id)

    except Exception as e:
        logging.error(f'received exception while trying to fetch seen movies list: {e}')

    return movie_lst


def get_poster_lst(db):
    """
    The func returns a list of the posters file paths
    :param db: an ADV database
    :type db: AdvDB
    :return: a list of all existing poster images file paths
    """
    new_dict = {}
    try:
        posters = db.get_dict()
        for key in posters:
            if os.path.exists(posters[key]):
                new_dict[key] = posters[key]

    except Exception as e:
        logging.error(f'received exception while trying to fetch poster list: {e}')

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
    try:
        if isinstance(image_fpath, bytes):
            image_fpath.decode()
        if os.path.exists(image_fpath):
            image = Image.open(image_fpath)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            buffer.close()

    except Exception as e:
        logging.error(f'received exception while trying to convert image to bytes: {e}')

    return image_bytes


def save_png_bytes(image_bytes, movie_name):
    """
    Save raw PNG image bytes to a file.
    :param image_bytes: PNG image data in bytes
    :param movie_name: full path where to save the image (including filename.png)
    """
    # Make sure the directory exists (optional if you're sure it already exists)
    img_path = ''
    try:
        new_name = movie_name
        if " " in new_name:
            new_name = new_name.replace(" ", "_")
        print(new_name)
        img_path = os.path.join(POSTER_DIR, f"{new_name}.png")

        with open(img_path, 'wb') as f:
            f.write(image_bytes)
            f.flush()
            os.fsync(f.fileno())  # Ensures data is written to disk

        logging.debug(f"Image saved to {img_path}")

    except Exception as e:
        logging.error(f'received exception while trying to save image to computer: {e}')

    return img_path


def run_broadcast(func, data):
    """
    A func to start a thread for broadcasting
    :param func: the func for the protocol message
    :type func: str
    :param data: the data to transfer
    :type data: bytes
    :return:
    """
    try:
        thread = threading.Thread(
            target=broadcast,
            args=(func, data),
        )
        thread.start()
        logging.debug("Started broadcast handler thread.")

    except Exception as e:
        logging.error(f"Failed to start 'broadcast' thread: {e}")


def broadcast(func, data):
    """
    broadcasting message to all connected media servers
    :param func: the func for the protocol message
    :type func: str
    :param data: the data to transfer
    :type data: bytes
    :return:
    """
    try:
        d = flashpoint_protocol.create_proto_data(data)
        for sock in media_sockets:
            try:
                msg = flashpoint_protocol.create_aes_msg(func, d, sock[1])
                sock[0].send(msg)
                logging.debug(f"broadcast {func} message to media servers")

            except Exception as e:
                logging.debug(f"[broadcast] Error sending to socket: {e}")

    except Exception as e:
        logging.debug(f"[broadcast] General error: {e}")


def get_file(client_socket, aes_obj, movie_name, poster_db):
    """
    receiving file info from client and broadcasting it to all media servers. In addition, saving the poster to
    database.
    :param client_socket: the client's socket
    :param aes_obj: the object for aes encryption\decryption
    :type aes_obj: AesEncryption
    :param movie_name: the new movie's name
    :type movie_name: bytes
    :param poster_db: the database that contains the posters
    :type poster_db: AdvDB
    :return:
    """
    try:
        # waiting for an FI message
        img_message = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)
        logging.debug(f"got {flashpoint_protocol.get_func(img_message)} message from client")
        if flashpoint_protocol.get_func(img_message) == 'FI':
            try:
                p_path = save_png_bytes(flashpoint_protocol.get_data(img_message), movie_name.decode())
                poster_db.set_val(movie_name.decode(), p_path)
                logging.debug("set val: " + poster_db.get_val(movie_name.decode()))

            except Exception as e:
                logging.debug(f"[get_file] Error saving poster or updating DB: {e}")
                return

            try:
                # waiting for an FL message
                len_msg = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)
                logging.debug(f"got {flashpoint_protocol.get_func(len_msg)} message from client")

                if flashpoint_protocol.get_func(len_msg) == 'FL':
                    file_len = flashpoint_protocol.get_data(len_msg)
                    run_broadcast('FL', file_len)

                else:
                    file_len = 0
                    run_broadcast('ER', flashpoint_protocol.create_proto_data())

            except Exception as e:
                logging.debug(f"[get_file] Error receiving or broadcasting file length: {e}")
                return

            try:
                for i in range(int(file_len.decode())):
                    try:
                        # waiting for an FC message
                        chunk_msg = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)
                        logging.debug(f"got {flashpoint_protocol.get_func(chunk_msg)} message from client")

                        if flashpoint_protocol.get_func(chunk_msg) == 'FC':
                            chunk = flashpoint_protocol.get_data(chunk_msg)
                            run_broadcast('FC', chunk)

                        else:
                            run_broadcast('ER', flashpoint_protocol.create_proto_data())

                    except Exception as e:
                        logging.debug(f"Error handling chunk {i}: {e}")

            except Exception as e:
                logging.debug(f"Error in chunk loop: {e}")

    except Exception as e:
        logging.debug(f"General error: {e}")


def handle_thread(client_socket, client_address, poster_db, socket_db, db):
    """
    A func to handle each thread
    :param client_socket: the socket for communication
    :param client_address: the address of the socket
    :param poster_db: a database that contains info on every movie poster
    :type poster_db: AdvDB
    :param socket_db: a database that contains info on every media server
    :type socket_db: AdvDB
    :param db: a database connection to a MySql database
    :type db: DBConnection
    :return:
    """
    global media_sockets
    cont_connection = True

    try:
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
        aes_obj = AesEncryption(key)

        while cont_connection:
            try:
                # checking if an error was raised or if the client disconnected before waiting for a message
                ret_msg = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)
                func = flashpoint_protocol.get_func(ret_msg)
                logging.debug(f"{client_address}: got {func} message from client")
            except Exception as e:
                logging.error(f"{client_address}: error receiving message - {e}")
                break

            try:
                if func == 'LI':
                    # handling login request
                    if login(ret_msg, db):
                        msg = flashpoint_protocol.create_aes_msg('VU',
                                                                 flashpoint_protocol.create_proto_data(b'True'),
                                                                 aes_obj)
                    else:
                        msg = flashpoint_protocol.create_aes_msg('VU',
                                                                 flashpoint_protocol.create_proto_data(b'False'),
                                                                 aes_obj)
                    client_socket.send(msg)
                    logging.debug(f"{client_address}: sent VU to client")

                elif func == 'SU':
                    # handling sign-up request
                    if signup(ret_msg, db):
                        msg = flashpoint_protocol.create_aes_msg('IE',
                                                                 flashpoint_protocol.create_proto_data(b'False'),
                                                                 aes_obj)
                    else:
                        msg = flashpoint_protocol.create_aes_msg('IE',
                                                                 flashpoint_protocol.create_proto_data(b'True'),
                                                                 aes_obj)
                    client_socket.send(msg)
                    logging.debug(f"{client_address}: sent IE to client")

                elif func == 'IA':
                    # handling an 'Is Admin' request
                    username = flashpoint_protocol.get_data(ret_msg, 1).decode()
                    password = flashpoint_protocol.get_data(ret_msg, 2).decode()
                    is_admin = db.is_admin(username, password)
                    data = flashpoint_protocol.create_proto_data(b'True' if is_admin else b'False')
                    msg = flashpoint_protocol.create_aes_msg('VA', data, aes_obj)
                    client_socket.send(msg)

                elif func == 'GM':
                    # handling a 'get movies' request
                    user_id = db.get_user_id(flashpoint_protocol.get_data(ret_msg, 1),
                                             flashpoint_protocol.get_data(ret_msg, 2))
                    if user_id:
                        m_data = get_movie_lst(user_id, db)
                        msg = flashpoint_protocol.create_aes_msg('LL',
                                                                 flashpoint_protocol.create_proto_data(
                                                                     str(len(m_data)).encode()), aes_obj)
                        client_socket.send(msg)
                        logging.debug(f"{client_address}: sent LL to client")

                        for movie_name, frame in m_data:
                            img = poster_db.get_val(movie_name)
                            img = image2bytes(img)
                            msg = flashpoint_protocol.create_aes_msg('YM', flashpoint_protocol.create_proto_data(
                                movie_name.encode(), str(frame).encode(), img), aes_obj)
                            client_socket.send(msg)
                            logging.debug(f"{client_address}: sent YM to client")
                    else:
                        client_socket.send(flashpoint_protocol.create_aes_msg('ER',
                                                                              flashpoint_protocol.create_proto_data(),
                                                                              aes_obj))
                        logging.debug(f"{client_address}: sent ER to client while trying to send movie posters")

                elif func == 'AP':
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

                elif func == 'SD':
                    # handling 'server details' command
                    ip = flashpoint_protocol.get_data(ret_msg).decode()
                    port = flashpoint_protocol.get_data(ret_msg, 2).decode()
                    sock_details = ip + ':' + port
                    socket_db.set_val(sock_details, 0)
                    media_sockets.append((client_socket, aes_obj))
                    logging.debug(f"added {sock_details} to database")

                elif func == 'CR':
                    # handling a connection request
                    server_dict = socket_db.get_dict()
                    server_key = min_clients(server_dict)
                    if server_key:
                        ip, port = server_key.split(':')
                        msg_data = flashpoint_protocol.create_proto_data(ip.encode(), port.encode())
                        msg = flashpoint_protocol.create_aes_msg('SA', msg_data, aes_obj)
                        client_socket.send(msg)
                        logging.debug(f"{client_address}: sent SA to client")
                        socket_db.set_val(server_key, server_dict[server_key] + 1)

                elif func == 'UD':
                    # handling an 'update database' request
                    username = flashpoint_protocol.get_data(ret_msg).decode()
                    password = flashpoint_protocol.get_data(ret_msg, 2).decode()
                    movie = flashpoint_protocol.get_data(ret_msg, 3).decode()
                    frame = int(flashpoint_protocol.get_data(ret_msg, 4).decode())
                    if frame < 0:
                        db.remove_seen_movie(username, password, movie)
                    else:
                        db.update_last_frame(username, password, movie, frame)

                elif func == 'DC':
                    # handling client disconnecting from media server
                    ip = flashpoint_protocol.get_data(ret_msg).decode()
                    port = flashpoint_protocol.get_data(ret_msg, 2).decode()
                    sock_details = ip + ':' + port
                    client_num = socket_db.get_val(sock_details) or 0
                    socket_db.set_val(sock_details, max(0, client_num - 1))

                elif func == 'RM':
                    # handling a 'Remove Movie' request
                    movie_name = flashpoint_protocol.get_data(ret_msg)
                    broadcast('RM', movie_name)
                    poster_fpath = poster_db.get_val(movie_name.decode())
                    if os.path.exists(poster_fpath):
                        os.remove(poster_fpath)
                    poster_db.delete_data(movie_name.decode())
                    db.remove_movie(movie_name.decode())

                elif func == 'FN':
                    # handling a 'File Name' request
                    movie_name = flashpoint_protocol.get_data(ret_msg)
                    broadcast('FN', movie_name)
                    get_file(client_socket, aes_obj, movie_name, poster_db)

                elif func == 'ME':
                    # handling a 'Movie Exists' request
                    exists = poster_db.get_val(flashpoint_protocol.get_data(ret_msg).decode())
                    data = flashpoint_protocol.create_proto_data(b'True' if exists else b'False')
                    msg = flashpoint_protocol.create_aes_msg('VM', data, aes_obj)
                    client_socket.send(msg)

                elif func == 'DS':
                    # client disconnected
                    cont_connection = False

                elif func == 'MD':
                    ip = flashpoint_protocol.get_data(ret_msg).decode()
                    port = flashpoint_protocol.get_data(ret_msg, 2).decode()
                    sock_details = ip + ':' + port
                    socket_db.delete_data(sock_details)

                elif func == 'ER':
                    # an error was raised
                    cont_connection = False

            except Exception as inner_e:
                logging.error(f"{client_address}: error handling message '{func}' - {inner_e}")
                cont_connection = False

    except Exception as e:
        logging.error(f"{client_address}: unexpected error occurred - {e}")

    finally:
        try:
            client_socket.close()

        except Exception as e:
            logging.error(f"{client_address}: received exception: {e}")
            pass

        logging.debug(f"{client_address}: connection closed")


def main():
    # creating databases to hold the poster file paths and the socket info.
    poster_db = initialize_db('poster', POSTER_DIR)
    socket_db = AdvDB(True, 'sockets')

    # creating a MySQL database connection
    db = DBConnection()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)

        while True:
            client_socket, client_address = server_socket.accept()
            thread = Thread(target=handle_thread,
                            args=(client_socket, client_address, poster_db, socket_db, db))
            thread.start()

    except socket.error as err:
        logging.error(f"received socket exception: {err}")

    finally:
        try:
            run_broadcast('AD', flashpoint_protocol.create_proto_data())

        except Exception as e:
            logging.error(f'run into an exception while trying to disconnect from media servers: {e}')

        server_socket.close()


if __name__ == "__main__":
    logging.basicConfig(filename='admin_server.log', level=logging.DEBUG)
    logging.getLogger("PIL").setLevel(logging.ERROR)
    main()
