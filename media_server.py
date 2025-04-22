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
import select

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


def file_break(movie_path, client_socket, admin_socket, frame=0):
    stop = False
    movie_len = get_video_duration(movie_path)
    msg_data = flashpoint_protocol.create_proto_data(str(movie_len - frame).encode())
    msg = flashpoint_protocol.create_proto_msg('ML', msg_data)
    client_socket.send(msg)
    print(f"Sending movie length: {movie_len} seconds")
    print('frame: ')
    print(frame)

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

        send = True
        for i in range(frame, movie_len):
            rlist, _, _ = select.select([client_socket], [], [], 0.8)  # Use select with short timeout
            if rlist:
                try:
                    stop_msg = flashpoint_protocol.get_proto_msg(client_socket)
                    if flashpoint_protocol.get_func(stop_msg) == 'PM':
                        send = False
                        username = flashpoint_protocol.get_data(stop_msg)
                        password = flashpoint_protocol.get_data(stop_msg, 2)
                        movie = flashpoint_protocol.get_data(stop_msg, 3)
                        frame = flashpoint_protocol.get_data(stop_msg, 4)
                        if int(frame.decode()) > movie_len - 3:
                            frame = 0
                        data = flashpoint_protocol.create_proto_data(username, password, movie, frame)
                        msg = flashpoint_protocol.create_proto_msg('UD', data)
                        try:
                            if admin_socket:
                                print("hello admin")
                                admin_socket.send(msg)
                                print('sent to admin')
                                client_socket.send(flashpoint_protocol.create_proto_msg(
                                    'DS', flashpoint_protocol.create_proto_data()))
                                print('sent stop')
                                stop = True
                        except (BrokenPipeError, ConnectionResetError) as e:
                            print(f"[!] Error sending stop message to admin: {e}")
                except Exception as e:
                    print(f"[!] Error while handling stop message: {e}")
                    break

            # If the socket is still open, send the chunk
            if send:
                full_path = os.path.join(tmpdir, chunk_files[i])
                try:
                    with open(full_path, "rb") as f:
                        data = f.read()
                        encoded = base64.b64encode(data)
                        msg = flashpoint_protocol.create_proto_msg(
                            'MC',
                            flashpoint_protocol.create_proto_data(str(i).encode(), encoded)
                        )
                        client_socket.send(msg)  # Try sending chunk if the socket is open
                except (BrokenPipeError, ConnectionResetError) as e:
                    print(f"[!] Client disconnected while sending chunk {i}: {e}")
                    break

            if os.path.exists(full_path):
                os.remove(full_path)

    if not stop:
        stop_msg = flashpoint_protocol.get_proto_msg(client_socket)
        print('got: ')
        print(stop_msg)
        if flashpoint_protocol.get_func(stop_msg) == 'PM':
            send = False
            username = flashpoint_protocol.get_data(stop_msg)
            password = flashpoint_protocol.get_data(stop_msg, 2)
            movie = flashpoint_protocol.get_data(stop_msg, 3)
            frame = flashpoint_protocol.get_data(stop_msg, 4)
            if int(frame.decode()) > movie_len - 3:
                frame = '0'.encode()
            data = flashpoint_protocol.create_proto_data(username, password, movie, frame)
            msg = flashpoint_protocol.create_proto_msg('UD', data)
            try:
                if admin_socket:
                    print("hello admin")
                    admin_socket.send(msg)
                    print('sent to admin')
                    client_socket.send(flashpoint_protocol.create_proto_msg(
                        'DS', flashpoint_protocol.create_proto_data()))
                    print('sent stop')
                    stop = True
            except (BrokenPipeError, ConnectionResetError) as e:
                print(f"[!] Error sending stop message to admin: {e}")



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
        file_break(m_fpath, client_socket, admin_sock, frame)


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