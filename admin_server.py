import os.path
import random
import socket
from threading import Thread
from threading import Lock
import flashpoint_protocol
from db_connector import DBConnection
import pickle
from PIL import Image
import io
import base64

FIRST_FUNCS = ['SU', 'LI', 'CS']
IP = '0.0.0.0'
PORT = 3600
QUEUE_SIZE = 10

# Setting global media servers socket list
sock_list = []

# setting lock
sock_list_lock = Lock()


def login(login_msg, db):
    username = flashpoint_protocol.get_data(login_msg, 1).decode()
    password = flashpoint_protocol.get_data(login_msg, 2).decode()
    print('username: ' + username)
    print('password: ' + password)
    return db.user_exists(username, password)


def signup(signup_msg, db):
    username = flashpoint_protocol.get_data(signup_msg, 1).decode()
    password = flashpoint_protocol.get_data(signup_msg, 2).decode()
    ret_ans = db.username_exists(username)
    if not ret_ans:
        db.add_user(username, password)
    return not ret_ans


def get_movie_lst(user_id, db):
    movie_lst = db.get_movie_lst(user_id)
    return movie_lst


def get_poster_lst(db):
    poster_lst = db.get_all_posters()
    new_lst = []
    for i in range(len(poster_lst)):
        print(poster_lst[i][1])
        if os.path.exists(poster_lst[i][1]):
            new_lst.append(poster_lst[i])
    print(new_lst)
    return new_lst


def image2bytes(image_fpath):
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


def handle_thread(client_socket, client_address):
    print('wdf')
    global sock_list
    cont_connection = True
    db = DBConnection()
    ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
    print(ret_msg)
    while flashpoint_protocol.get_func(ret_msg) not in FIRST_FUNCS:
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
    func = flashpoint_protocol.get_func(ret_msg)
    print(func)
    while cont_connection:
        if func == 'LI':
            while not login(ret_msg, db) and flashpoint_protocol.get_func(ret_msg) == 'LI':
                msg = flashpoint_protocol.create_proto_msg('VU', flashpoint_protocol.create_proto_data(b'False'))
                client_socket.send(msg)
                ret_msg = flashpoint_protocol.get_proto_msg(client_socket)

            if flashpoint_protocol.get_func(ret_msg) != 'LI':
                msg = flashpoint_protocol.error_msg()
                client_socket.send(msg)

            else:
                msg = flashpoint_protocol.create_proto_msg('VU', flashpoint_protocol.create_proto_data(b'True'))
                client_socket.send(msg)

        if func == 'SU':
            while not signup(ret_msg, db) and flashpoint_protocol.get_func(ret_msg) == 'SU':
                msg = flashpoint_protocol.create_proto_msg('IE', flashpoint_protocol.create_proto_data(b'True'))
                client_socket.send(msg)
                print(msg)
                ret_msg = flashpoint_protocol.get_proto_msg(client_socket)

            if flashpoint_protocol.get_func(ret_msg) != 'SU':
                msg = flashpoint_protocol.error_msg()
                client_socket.send(msg)

            else:
                msg = flashpoint_protocol.create_proto_msg('IE', flashpoint_protocol.create_proto_data(b'False'))
                client_socket.send(msg)

        if func == 'GM':
            ret_data = []
            user_id = db.get_user_id(flashpoint_protocol.get_data(ret_msg, 1),
                                     flashpoint_protocol.get_data(ret_msg, 2))
            if user_id:
                print('logged in')
                ret_data = get_movie_lst(user_id, db)
                ret_data = pickle.dumps(ret_data)
                msg = flashpoint_protocol.create_proto_msg('YM', flashpoint_protocol.create_proto_data(ret_data))
                client_socket.send(msg)

            else:
                client_socket.send(flashpoint_protocol.error_msg())

        if func == 'GP':
            movie_name = flashpoint_protocol.get_data(ret_msg)
            poster_fpath = db.get_poster_fpath(movie_name)
            print('poster fpath: ')
            print(poster_fpath)
            msg = flashpoint_protocol.create_proto_msg('MP', flashpoint_protocol.create_proto_data(
                poster_fpath.encode()))
            client_socket.send(msg)

        if func == 'AP':
            posters = get_poster_lst(db)
            client_socket.send(flashpoint_protocol.create_proto_msg('LL',
                                                                    flashpoint_protocol.create_proto_data(
                                                                        str(len(posters)).encode())))
            for i in range(len(posters)):
                print(posters[i][0].encode())
                poster_bytes = image2bytes(posters[i][1])
                encoded_data = base64.b64encode(poster_bytes)
                msg = flashpoint_protocol.create_proto_msg('PL',
                                                           flashpoint_protocol.create_proto_data(
                                                               posters[i][0].encode(), encoded_data))
                client_socket.send(msg)

        if func == 'CS':
            ip = flashpoint_protocol.get_data(ret_msg).decode()
            port = int(flashpoint_protocol.get_data(ret_msg, 2).decode())
            with sock_list_lock:
                sock_list.append((ip, port, 0))
                print('added: ' + str(sock_list[0]))

        if func == 'SD':
            print(sock_list[0])
            server = sock_list[0]
            msg_data = flashpoint_protocol.create_proto_data(server[0].encode(), str(server[1]).encode())
            print(msg_data)
            msg = flashpoint_protocol.create_proto_msg('SA', msg_data)
            client_socket.send(msg)

        if func == 'MR':
            m_name = flashpoint_protocol.get_data(ret_msg).decode()
            m_fpath = db.fetch_movie(m_name)
            msg = flashpoint_protocol.create_proto_msg('MW',
                                                       flashpoint_protocol.create_proto_data(m_fpath.encode()))
            client_socket.send(msg)

        print('#')
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        func = flashpoint_protocol.get_func(ret_msg)
        print(ret_msg)
        print(func)


def main():
    global sock_list
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)

        while True:
            client_socket, client_address = server_socket.accept()
            print('connected')
            thread = Thread(target=handle_thread,
                            args=(client_socket, client_address, ))
            thread.start()
    except socket.error as err:
        print('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
