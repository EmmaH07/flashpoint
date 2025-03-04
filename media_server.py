from queue import Queue
import socket
import math
from threading import Thread
import flashpoint_protocol
from db_connector import DBConnection
import os

IP = '0.0.0.0'
PORT = 1939
QUEUE_SIZE = 10
LEGAL_FUNC = ['MW']
FIRST_FUNC = 'MW'
BYTES_IN_CHUNK = 16384


def file_break(movie_path, client_socket):
    movie_q = Queue(0)
    movie_len = os.path.getsize(movie_path) / BYTES_IN_CHUNK
    movie_len = math.ceil(movie_len)
    msg_data = flashpoint_protocol.create_proto_data(str(movie_len))
    msg = flashpoint_protocol.create_proto_msg('ML', msg_data)
    client_socket.send(msg.encode())
    with open(movie_path, 'rb') as f:
        m_byte = f.read(BYTES_IN_CHUNK)
        i = 0
        while m_byte:
            movie_q.put(m_byte)
            chunk_data = flashpoint_protocol.create_chunk_data(str(i + 1), m_byte)
            chunk_msg = flashpoint_protocol.create_chunk_msg(chunk_data)
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


def handle_thread(client_socket, client_address, my_index):
    db = DBConnection()
    first_msg = flashpoint_protocol.get_proto_msg(client_socket)
    while flashpoint_protocol.get_func(first_msg) != FIRST_FUNC:
        first_msg = flashpoint_protocol.get_proto_msg(client_socket)
    m_name = flashpoint_protocol.get_data(first_msg)
    m_fpath = db.fetch_movie(m_name)
    movie_q = ''
    if m_fpath == '':
        client_socket.send('ERROR'.encode())

    else:
        movie_q = file_break(m_fpath, client_socket)


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
