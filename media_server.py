import random
from queue import Queue
import socket
import math
from threading import Thread
import flashpoint_protocol
import base64
import os
import subprocess
import json
import tempfile

IP = '0.0.0.0'
ADMIN_IP = '127.0.0.1'
PORT = 1939
ADMIN_PORT = 3600
QUEUE_SIZE = 10
LEGAL_FUNC = ['MR']
FIRST_FUNC = 'MR'
BYTES_IN_CHUNK = 16384


def get_video_duration(movie_path):
    result = subprocess.run([
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        movie_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    info = json.loads(result.stdout)
    duration = float(info['format']['duration'])
    return int(duration)


def file_break(movie_path, client_socket):
    movie_len = get_video_duration(movie_path)
    msg_data = flashpoint_protocol.create_proto_data(str(movie_len).encode())
    msg = flashpoint_protocol.create_proto_msg('ML', msg_data)
    client_socket.send(msg)
    print(f"Sending movie length: {movie_len} seconds")

    for i in range(movie_len):
        # Create a temporary file to store each 1-second chunk
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_name = tmp_file.name

        # Use FFmpeg to extract a 1-second chunk starting at `i` seconds
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", movie_path,
            "-ss", str(i),  # Start at second `i`
            "-t", "1",  # 1 second duration
            "-c:v", "libx264",
            "-c:a", "aac",
            "-f", "mpegts",  # Ensure this is used for streaming
            "-y",
            tmp_name
        ]
        # Run ffmpeg to extract the 1-second chunk
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Read the temporary chunk file and encode it
        with open(tmp_name, "rb") as f:
            data = f.read()  # Read the content of the chunk
            encoded = base64.b64encode(data)  # Base64 encode the chunk

            # Create and send the protocol message with the chunk
            msg = flashpoint_protocol.create_proto_msg('MC', flashpoint_protocol.create_proto_data(
                str(i).encode(), encoded))
            client_socket.send(msg)

        # Clean up by deleting the temporary file after sending the chunk
        os.remove(tmp_name)


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