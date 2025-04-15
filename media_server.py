import random
from queue import Queue
import socket
import math
from threading import Thread
import flashpoint_protocol
import base64
import os

IP = '0.0.0.0'
ADMIN_IP = '127.0.0.1'
PORT = 1939
ADMIN_PORT = 3600
QUEUE_SIZE = 10
LEGAL_FUNC = ['MR']
FIRST_FUNC = 'MR'
BYTES_IN_CHUNK = 16384


def file_break(movie_path, client_socket):
    movie_q = Queue(0)
    movie_len = os.path.getsize(movie_path) / BYTES_IN_CHUNK
    movie_len = math.ceil(movie_len)
    msg_data = flashpoint_protocol.create_proto_data(str(movie_len).encode())
    msg = flashpoint_protocol.create_proto_msg('ML', msg_data)
    client_socket.send(msg)
    print(msg)
    with open(movie_path, 'rb') as f:
        m_byte = f.read(BYTES_IN_CHUNK)
        i = 0
        while m_byte:
            movie_q.put(m_byte)
            encoded_chunk = base64.b64encode(m_byte)
            chunk_data = flashpoint_protocol.create_proto_data(str(i + 1).encode(), encoded_chunk)
            chunk_msg = flashpoint_protocol.create_proto_msg('MC', chunk_data)
            client_socket.send(chunk_msg)
            i += 1
            m_byte = f.read(BYTES_IN_CHUNK)
    return movie_q


def send_chunk(movie_q, client_socket):
    len_msg = flashpoint_protocol.create_proto_msg('ML', flashpoint_protocol.create_proto_data(str(movie_q.qsize())))
    client_socket.send(len_msg.encode())
    for i in range(movie_q.qsize()):
        chunk_msg = flashpoint_protocol.create_proto_msg('MC', str(i + 1)) + '^'
        chunk_msg = chunk_msg.encode() + movie_q.get()
        client_socket.send(chunk_msg)


def handle_thread(admin_sock, client_socket, client_address, my_port):
    first_msg = flashpoint_protocol.get_proto_msg(client_socket)
    while flashpoint_protocol.get_func(first_msg) != FIRST_FUNC:
        first_msg = flashpoint_protocol.get_proto_msg(client_socket)
    m_name = flashpoint_protocol.get_data(first_msg)
    msg = flashpoint_protocol.create_proto_msg('MR', flashpoint_protocol.create_proto_data(m_name))
    admin_sock.send(msg)
    ret_msg = flashpoint_protocol.get_proto_msg(admin_sock)
    m_fpath = flashpoint_protocol.get_data(ret_msg).decode()
    movie_q = ''
    if m_fpath == '':
        client_socket.send('ERROR'.encode())

    else:
        movie_q = file_break(m_fpath, client_socket)


def connect2admin():
    try:
        main_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_server_sock.connect((ADMIN_IP, ADMIN_PORT))
        print("Connected to admin server.")

        # You can return the socket if you want to keep communicating with the main server
        return main_server_sock

    except Exception as e:
        print("Failed to connect to main server:", e)
        return None


def main():
    admin_sock = connect2admin()
    if not admin_sock:
        return
    port = random.randint(1024, 65535)
    port = 2085
    msg = flashpoint_protocol.create_proto_msg('CS', flashpoint_protocol.create_proto_data(ADMIN_IP.encode(),
                                                                                           str(port).encode()))
    admin_sock.send(msg)
    print('sent')
    print(msg)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, port))
        server_socket.listen(QUEUE_SIZE)
        sock_list = []
        while True:
            client_socket, client_address = server_socket.accept()
            print('connected')
            sock_list.append(client_socket)
            thread = Thread(target=handle_thread,
                            args=(admin_sock, client_socket, client_address, port))
            thread.start()
    except socket.error as err:
        print('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
