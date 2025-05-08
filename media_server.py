import json
import os
import random
import socket
import subprocess
import tempfile
from threading import Thread
import logging
import select

import flashpoint_protocol
from adv_db import AdvDB
from rsa import RsaEncryption
from aes import AesEncryption

IP = '0.0.0.0'
ADMIN_IP = '127.0.0.1'
MY_IP = '127.0.0.1'
PORT = 1939
ADMIN_PORT = 3600
QUEUE_SIZE = 10
LEGAL_FUNC = ['MR']
FIRST_FUNC = 'MR'
MOVIE_DICT = {'10 Things I Hate About You': 'movies/10things_trailer.mp4', 'Aladdin': 'movies/aladdin_trailer.mp4',
              'Dark Knight': 'movies/dark_knight.mp4', 'Inception': 'movies/inception.mp4',
              'Lord Of The Rings': 'movies/rings.mp4', 'Merlin': 'movies/merlin.mp4',
              'Never Ending Story': 'movies/never_ending.mp4', "Singin' In The Rain": 'movies/rain.mp4',
              'Star Wars': 'movies/star_wars.mp4', 'Superman 1978': 'movies/superman1978.mp4',
              'Superman 2025': 'movies/superman2025.mp4', 'The Batman': 'movies/the_batman.mp4',
              'The Flash': 'movies/the_flash.mp4'}


def handle_err(client_socket):
    """
    closing the client socket in case of an error
    :param client_socket: the client's socket
    :return:
    """
    client_socket.close()


def get_video_duration(movie_path, chunk_duration=10):
    """
    the func checks how many 10 seconds chunks is the movie made of
    :param movie_path: the movie's file path
    :type movie_path: str
    :param chunk_duration: what is the amount of seconds each chunk is made of
    :type chunk_duration: int
    :return: the amount of 10 seconds chunks the movie contains
    """
    result = subprocess.run([
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        movie_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    info = json.loads(result.stdout)
    duration = float(info['format']['duration'])
    movie_len = duration // chunk_duration
    if duration % chunk_duration > 0:
        movie_len += 1
    return int(movie_len)


def file_break(movie_path, client_socket, client_aes, admin_socket, admin_aes, port, frame=0):
    """
    breaking the movie into 10 seconds movie chunks before sending to client

    :param movie_path: the movie file path
    :type movie_path: str
    :param client_socket: the client's socket
    :param client_aes:
    :param admin_socket: the admin's socket
    :param admin_aes:
    :param port: the media server's port
    :type port: int
    :param frame: the last frame the client stopped at
    :type frame: int
    :return:
    """

    stop = False

    # sending a 'movie length' message to the client
    movie_len = get_video_duration(movie_path)
    msg_data = flashpoint_protocol.create_proto_data(str(movie_len - frame).encode())
    msg = flashpoint_protocol.create_aes_msg('ML', msg_data, client_aes)
    client_socket.send(msg)
    logging.debug('Sent to client: ML')

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use FFmpeg to split the video into precise 10-second segments
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
            "-segment_time", "10",
            "-segment_format", "mpegts",
            os.path.join(tmpdir, "chunk%03d.ts")
        ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Sort and stream each 10-second chunk
        chunk_files = sorted(f for f in os.listdir(tmpdir) if f.endswith(".ts"))

        send = True
        for i in range(frame, movie_len):
            # checking if a stop message was received.
            rlist, _, _ = select.select([client_socket], [], [], 0.8)  # Use select with short timeout
            if rlist:
                try:
                    stop_msg = flashpoint_protocol.get_aes_msg(client_socket, client_aes)
                    logging.debug('Got message from client: ' + flashpoint_protocol.get_func(stop_msg))

                    if flashpoint_protocol.get_func(stop_msg) == 'PM':
                        # updating the var in order to stop sending chunks to the client
                        send = False
                        username = flashpoint_protocol.get_data(stop_msg)
                        password = flashpoint_protocol.get_data(stop_msg, 2)
                        movie = flashpoint_protocol.get_data(stop_msg, 3)
                        frame = flashpoint_protocol.get_data(stop_msg, 4)

                        if int(frame.decode()) >= movie_len:
                            frame = -1

                        # asking admin server to update the database
                        data = flashpoint_protocol.create_proto_data(username, password, movie, frame)
                        msg = flashpoint_protocol.create_aes_msg('UD', data, admin_aes)

                        try:
                            if admin_socket:
                                # sending UD message to admin server
                                admin_socket.send(msg)
                                logging.debug('Sent message to admin: UD')

                                # sending a disconnect message to client
                                msg = flashpoint_protocol.create_aes_msg('DS',
                                                                         flashpoint_protocol.create_proto_data(),
                                                                         client_aes)
                                client_socket.send(msg)
                                logging.debug('Sent message to client: DS')

                                # informing the admin server that the client disconnected
                                msg = flashpoint_protocol.create_aes_msg('DC',
                                                                         flashpoint_protocol.create_proto_data(
                                                                             ADMIN_IP.encode(), str(port).encode()),
                                                                         admin_aes)
                                admin_socket.send(msg)
                                logging.debug('Sent message to admin: DC')

                                # updating the var to inform that the stop message was sent
                                stop = True

                        except (BrokenPipeError, ConnectionResetError) as e:
                            logging.error("Error sending stop message to admin: " + str(e))

                    # checking if I got an error message
                    elif flashpoint_protocol.get_func(stop_msg) == 'ER':
                        logging.debug('Got error message')
                        break

                except Exception as e:
                    logging.error("Error while handling stop message: " + str(e))
                    break

            # If the socket is still open, send the chunk
            if send:
                full_path = os.path.join(tmpdir, chunk_files[i])
                try:
                    with open(full_path, "rb") as f:
                        data = f.read()
                        msg = flashpoint_protocol.create_aes_msg('MC',
                                                                 flashpoint_protocol.create_proto_data(str(i).encode(),
                                                                                                       data),
                                                                 client_aes)
                        client_socket.send(msg)
                        logging.debug('Sent to client: MC')

                except (BrokenPipeError, ConnectionResetError) as e:
                    print(f"Client disconnected while sending chunk {i}: {e}")
                    break

            # removing all the temp files
            if os.path.exists(full_path):
                os.remove(full_path)

    # if the server sent all the chunks and the client didn't stop in the middle, wait for disconnect from client
    if not stop:
        stop_msg = flashpoint_protocol.get_aes_msg(client_socket, client_aes)

        if flashpoint_protocol.get_func(stop_msg) == 'PM':
            send = False
            username = flashpoint_protocol.get_data(stop_msg)
            password = flashpoint_protocol.get_data(stop_msg, 2)
            movie = flashpoint_protocol.get_data(stop_msg, 3)
            frame = flashpoint_protocol.get_data(stop_msg, 4)

            if int(frame.decode()) >= movie_len - 1:
                frame = '-1'.encode()
            data = flashpoint_protocol.create_proto_data(username, password, movie, frame)
            msg = flashpoint_protocol.create_aes_msg('UD', data, admin_aes)
            try:
                if admin_socket:
                    # sending UD message to admin server
                    admin_socket.send(msg)

                    # sending a disconnect message to client
                    msg = flashpoint_protocol.create_aes_msg('DS',
                                                             flashpoint_protocol.create_proto_data(), client_aes)
                    client_socket.send(msg)
                    logging.debug('Sent message to client: DS')

                    # informing the admin server that the client disconnected
                    msg = flashpoint_protocol.create_aes_msg('DC', flashpoint_protocol.create_proto_data
                    (ADMIN_IP.encode(), str(port).encode()), admin_aes)
                    admin_socket.send(msg)
                    logging.debug('Sent message to admin: DC')

                    # updating the var to inform that the stop message was sent
                    stop = True

            except (BrokenPipeError, ConnectionResetError) as e:
                print("Error sending stop message to admin: " + str(e))


def handle_thread(admin_sock, admin_aes, client_socket, client_address, my_port, db):
    """

    :param admin_sock: the admin server's socket
    :param admin_aes:
    :type admin_aes:
    :param client_socket: the client's socket
    :param client_address: the client's address
    :param my_port: the media server port
    :type my_port: int
    :param db: an ADV database containing the movie files paths
    :type db: AdvDB
    :return:
    """

    # setting RSA object and public key
    rsa_obj = RsaEncryption()
    pub_key = rsa_obj.get_pub_key()

    # sending first message
    first_msg = flashpoint_protocol.create_proto_msg('PK', flashpoint_protocol.create_proto_data(pub_key))
    client_socket.send(first_msg)

    # waiting for 'AES Key' message and making sure the command in it is the correct one for the start
    key_msg = flashpoint_protocol.get_rsa_msg(client_socket, rsa_obj)
    while flashpoint_protocol.get_func(key_msg) != 'AK':
        key_msg = flashpoint_protocol.get_rsa_msg(client_socket, rsa_obj)

    key = flashpoint_protocol.get_data(key_msg)
    aes_obj = AesEncryption(key)

    # checking that the server got the correct first func
    first_msg = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)
    logging.debug('Got a message from client: ' + flashpoint_protocol.get_func(first_msg))
    while flashpoint_protocol.get_func(first_msg) != FIRST_FUNC:
        first_msg = flashpoint_protocol.get_aes_msg(client_socket, aes_obj)
        logging.debug('Got a message from client: ' + flashpoint_protocol.get_func(first_msg))

    m_name = flashpoint_protocol.get_data(first_msg).decode()
    frame = flashpoint_protocol.get_data(first_msg, 2)

    if frame == b'':
        frame = 0

    else:
        frame = int(frame.decode())

    m_fpath = db.get_val(m_name)

    if m_fpath == '':
        logging.error('Movie not found')
        client_socket.send('ERROR'.encode())

    else:
        file_break(m_fpath, client_socket, aes_obj, admin_sock, admin_aes, my_port, frame)


def connect2admin():
    """
    the func connects to the admin server
    :return: the admin server's socket
    """
    try:
        main_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_server_sock.connect((ADMIN_IP, ADMIN_PORT))
        logging.debug("Connected to admin server.")

        return main_server_sock

    except Exception as e:
        err_str = 'Failed to connect to admin server: ' + str(e)
        logging.error(err_str)
        print(err_str)
        return None


def start_encryption(client_socket):
    # waiting for RSA public key
    key_msg = flashpoint_protocol.get_proto_msg(client_socket)
    print(key_msg)

    # making sure client got the correct message
    func = flashpoint_protocol.get_func(key_msg)
    while func != 'PK':
        key_msg = flashpoint_protocol.get_proto_msg(client_socket)
        func = flashpoint_protocol.get_func(key_msg)

    # sending encrypted message that contains AES key
    rsa_obj = RsaEncryption()
    print(flashpoint_protocol.get_data(key_msg))
    pub_key = flashpoint_protocol.get_data(key_msg)
    aes_obj = AesEncryption()
    enc_key = aes_obj.get_key()

    # using RSA encryption to send AES key
    key_msg = flashpoint_protocol.create_rsa_msg('AK', flashpoint_protocol.create_proto_data(enc_key), rsa_obj,
                                                 pub_key)
    client_socket.send(key_msg)
    print(key_msg)

    return aes_obj


def main():
    # connecting to the admin server
    admin_sock = connect2admin()
    if not admin_sock:
        return

    # establishing encryption with admin
    admin_aes = start_encryption(admin_sock)

    # setting a port
    port = random.randint(1024, 65535)

    # setting a database for the movie files locations
    db = AdvDB(True, 'movie', MOVIE_DICT)

    # sending server details to the database
    msg = flashpoint_protocol.create_aes_msg('SD', flashpoint_protocol.create_proto_data(
        MY_IP.encode(), str(port).encode()), admin_aes)
    admin_sock.send(msg)

    # connecting to a client
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, port))
        server_socket.listen(QUEUE_SIZE)
        while True:
            client_socket, client_address = server_socket.accept()
            print('connected')
            thread = Thread(target=handle_thread,
                            args=(admin_sock, admin_aes, client_socket, client_address, port, db))
            thread.start()

    except socket.error as err:
        err_str = 'received socket exception: ' + str(err)
        logging.error(err_str)
        print(err_str)

    finally:
        server_socket.close()


if __name__ == "__main__":
    logging.basicConfig(filename='media_server.log', level=logging.DEBUG)
    main()
