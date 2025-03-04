from queue import Queue
import socket
import flashpoint_protocol
import subprocess

IP = '127.0.0.1'
PORT = 1939


def get_chunks(my_socket, movie_len):
    movie_len = int(movie_len)
    q = Queue(0)
    ffplay = subprocess.Popen(["ffplay", "-"], stdin=subprocess.PIPE)
    play = False
    for i in range(movie_len):
        chunk_msg = flashpoint_protocol.get_chunk_msg(my_socket)
        m_chunk = flashpoint_protocol.get_chunk(chunk_msg)
        print(m_chunk)
        q.put(m_chunk)
        if q.qsize() > 5:
            play = True

        if play and q.qsize() > 0:
            ffplay.stdin.write(q.get())

    ffplay.stdin.close()
    ffplay.wait()


def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.connect((IP, PORT))
        first_msg = flashpoint_protocol.create_proto_msg('MW', flashpoint_protocol.create_proto_data('The Flash'))
        my_socket.send(first_msg.encode())
        len_msg = flashpoint_protocol.get_proto_msg(my_socket)
        movie_len = flashpoint_protocol.get_data(len_msg)
        get_chunks(my_socket, movie_len)

    except socket.error as err:
        print('received socket error ' + str(err))

    finally:
        my_socket.close()


if __name__ == "__main__":
    main()
