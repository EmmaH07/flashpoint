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


def file_break(movie_path, client_socket, frame=0):
    movie_len = get_video_duration(movie_path)
    msg_data = flashpoint_protocol.create_proto_data(str(movie_len - frame).encode())
    msg = flashpoint_protocol.create_proto_msg('ML', msg_data)
    client_socket.send(msg)
    print(f"Sending movie length: {movie_len} seconds")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use FFmpeg to split the video into precise 1-second segments
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", movie_path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-x264-params", "keyint=24:min-keyint=24",
            "-c:a", "aac",
            "-ar", "44100",
            "-ac", "2",
            "-f", "segment",
            "-segment_time", "1",
            "-segment_format", "mpegts",
            os.path.join(tmpdir, "chunk%03d.ts")
        ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Sort and stream each 1-second chunk
        chunk_files = sorted(f for f in os.listdir(tmpdir) if f.endswith(".ts"))
        print(chunk_files)

        for i, fname in enumerate(chunk_files):
            full_path = os.path.join(tmpdir, fname)
            with open(os.path.join(tmpdir, fname), "rb") as f:
                data = f.read()
                encoded = base64.b64encode(data)
                msg = flashpoint_protocol.create_proto_msg(
                    'MC',
                    flashpoint_protocol.create_proto_data(str(i).encode(), encoded)
                )
                client_socket.send(msg)
            os.remove(full_path)


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
    frame = flashpoint_protocol.get_data(first_msg, 2)
    if frame == b'':
        frame = 0
    else:
        frame = int(frame.decode())
    msg = flashpoint_protocol.create_proto_msg('MR', flashpoint_protocol.create_proto_data(m_name))
    admin_sock.send(msg)
    ret_msg = flashpoint_protocol.get_proto_msg(admin_sock)
    m_fpath = flashpoint_protocol.get_data(ret_msg).decode()
    movie_q = ''
    if m_fpath == '':
        client_socket.send('ERROR'.encode())

    else:
        file_break(m_fpath, client_socket, frame)


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
