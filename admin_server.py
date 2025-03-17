import socket
from threading import Thread
import flashpoint_protocol
from db_connector import DBConnection
import os

FIRST_FUNCS = ['SU', 'LI']
IP = '0.0.0.0'
PORT = 3514
QUEUE_SIZE = 10


def login(login_msg, db):
    username = flashpoint_protocol.get_data(login_msg, 1)
    password = flashpoint_protocol.get_data(login_msg, 2)
    return db.user_exists(username, password)


def signup(signup_msg, db):
    username = flashpoint_protocol.get_data(signup_msg, 1)
    password = flashpoint_protocol.get_data(signup_msg, 2)
    ret_ans = db.username_exists(username)
    if not ret_ans:
        db.add_user(username, password)
    return not ret_ans


def handle_thread(client_socket, client_address, my_index):
    cont_connection = True
    db = DBConnection()
    first_msg = flashpoint_protocol.get_proto_msg(client_socket)
    print(first_msg)
    while flashpoint_protocol.get_func(first_msg) not in FIRST_FUNCS:
        first_msg = flashpoint_protocol.get_proto_msg(client_socket)
    func = flashpoint_protocol.get_func(first_msg)
    print(func)
    while cont_connection:
        if func == 'LI':
            while not login(first_msg, db) and flashpoint_protocol.get_func(first_msg) == 'LI':
                msg = flashpoint_protocol.create_proto_msg('VU', flashpoint_protocol.create_proto_data('False'))
                client_socket.send(msg.encode())
                first_msg = flashpoint_protocol.get_proto_msg(client_socket)

            if flashpoint_protocol.get_func(first_msg) != 'LI':
                msg = flashpoint_protocol.error_msg()
                client_socket.send(msg.encode())

            else:
                msg = flashpoint_protocol.create_proto_msg('VU', flashpoint_protocol.create_proto_data('True'))
                client_socket.send(msg.encode())

        if func == 'SU':
            while not signup(first_msg, db) and flashpoint_protocol.get_func(first_msg) == 'SU':
                msg = flashpoint_protocol.create_proto_msg('IE', flashpoint_protocol.create_proto_data('True'))
                client_socket.send(msg.encode())
                print(msg)
                first_msg = flashpoint_protocol.get_proto_msg(client_socket)

            if flashpoint_protocol.get_func(first_msg) != 'SU':
                msg = flashpoint_protocol.error_msg()
                client_socket.send(msg.encode())

            else:
                msg = flashpoint_protocol.create_proto_msg('IE', flashpoint_protocol.create_proto_data('False'))
                client_socket.send(msg.encode())

        if func == 'GM':
            ret_data = ''
            username = flashpoint_protocol.get_data(first_msg, 1)
            password = flashpoint_protocol.get_data(first_msg, 2)
            if login(first_msg, db):
                print('logged in')
                movie_str = db.get_movie_lst(username, password)
                print(movie_str)
                frame_str = db.get_frame_lst(username, password)
                print(frame_str)
                msg = flashpoint_protocol.create_proto_msg('YM',
                                                           flashpoint_protocol.create_proto_data(movie_str,frame_str))
                print(msg)
                client_socket.send(msg.encode())

        print('#')
        first_msg = flashpoint_protocol.get_proto_msg(client_socket)
        func = flashpoint_protocol.get_func(first_msg)
        print(first_msg)
        print(func)


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        sock_list = []
        while True:
            client_socket, client_address = server_socket.accept()
            print('connected')
            sock_list.append(client_socket)
            thread = Thread(target=handle_thread,
                            args=(client_socket, client_address, len(sock_list) - 1))
            thread.start()
    except socket.error as err:
        print('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
