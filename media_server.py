import json
import os
import random
import socket
import subprocess
import tempfile
from threading import Thread
import threading
import logging
import select

import flashpoint_protocol
from adv_db import AdvDB
from rsa import RsaEncryption
from aes import AesEncryption

IP = '0.0.0.0'
ADMIN_IP = '127.0.0.1'
MY_IP = '127.0.0.1'
ADMIN_PORT = 3600
QUEUE_SIZE = 10
FIRST_FUNC = 'MR'
MOVIE_START_PATH = 'movies'


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


def initialize_db(db_name, info_dir=''):
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


def get_video_duration(movie_path, chunk_duration=10):
    """
    the func checks how many 10 seconds chunks is the movie made of
    :param movie_path: the movie's file path
    :type movie_path: str
    :param chunk_duration: what is the amount of seconds each chunk is made of
    :type chunk_duration: int
    :return: the amount of 10 seconds chunks the movie contains
    """
    ret_len = 0
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            movie_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

        info = json.loads(result.stdout)
        duration = float(info['format']['duration'])

        movie_len = duration // chunk_duration
        if duration % chunk_duration > 0:
            movie_len += 1

        ret_len = int(movie_len)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"FFprobe failed on '{movie_path}': {e}")

    except json.JSONDecodeError as e:
        logging.error(f"Could not decode JSON from ffprobe output: {e}")

    except (KeyError, ValueError) as e:
        logging.error(f"Invalid duration format in ffprobe output: {e}")

    finally:
        return ret_len


def file_break(movie_path, client_socket, client_aes, admin_socket, admin_aes, port, frame=0):
    """
    breaking the movie into 10 seconds movie chunks before sending to client
    :param movie_path: the movie file path
    :type movie_path: str
    :param client_socket: the client's socket
    :param client_aes: an object that contains all the encryption info from client
    :type client_aes: AesEncryption
    :param admin_socket: the admin's socket
    :param admin_aes: an object that contains all the encryption info from admin server
    :type admin_aes: AesEncryption
    :param port: the media server's port
    :type port: int
    :param frame: the last frame the client stopped at
    :type frame: int
    :return:
    """

    stop = False

    try:
        # sending a 'movie length' message to the client
        movie_len = get_video_duration(movie_path)
        msg_data = flashpoint_protocol.create_proto_data(str(movie_len - frame).encode())
        msg = flashpoint_protocol.create_aes_msg('ML', msg_data, client_aes)
        client_socket.send(msg)
        logging.debug('Sent to client: ML')

    except Exception as e:
        logging.error(f"Failed to send ML message to : {e}")
        return

    try:
        # opening a temp directory for the chunk files
        with tempfile.TemporaryDirectory() as tmpdir:
            # FFmpeg command to split the file
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

            try:
                # running the ffmpeg command
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            except subprocess.CalledProcessError as e:
                logging.error(f"FFmpeg failed to split video: {e}")
                return

            # Sort and stream each 10-second chunk
            chunk_files = sorted(f for f in os.listdir(tmpdir) if f.endswith(".ts"))
            send = True

            for i in range(frame, movie_len):
                try:
                    rlist, _, _ = select.select([client_socket], [], [], 0.8)
                    if rlist:
                        stop_msg = flashpoint_protocol.get_aes_msg(client_socket, client_aes)
                        msg_func = flashpoint_protocol.get_func(stop_msg)
                        logging.debug(f'Got message from client: {msg_func}')

                        if msg_func == 'PM':
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
                                logging.error(f"Error sending stop message to admin: {e}")
                                return

                        # checking if I got an error message
                        elif msg_func == 'ER':
                            logging.debug('Got error message from client')
                            break

                except Exception as e:
                    logging.error(f"Error while handling stop message: {e}")
                    return

                # If the socket is still open, send the chunk
                if send:
                    try:
                        full_path = os.path.join(tmpdir, chunk_files[i])
                        with open(full_path, "rb") as f:
                            data = f.read()
                            msg = flashpoint_protocol.create_aes_msg('MC',
                                                                     flashpoint_protocol.create_proto_data(
                                                                         str(i).encode(), data),
                                                                     client_aes)
                            client_socket.send(msg)
                            logging.debug(f'Sent chunk {i} to client')

                    except (BrokenPipeError, ConnectionResetError) as e:
                        logging.error(f"Client disconnected while sending chunk {i}: {e}")
                        return

                    except Exception as e:
                        logging.error(f"Error reading/sending chunk {i}: {e}")
                        return

    except Exception as e:
        logging.error(f"Unexpected error during file break: {e}")
        return

    # if the server sent all the chunks and the client didn't stop in the middle, wait for disconnect from client
    if not stop:
        try:
            stop_msg = flashpoint_protocol.get_aes_msg(client_socket, client_aes)
            if flashpoint_protocol.get_func(stop_msg) == 'PM':
                username = flashpoint_protocol.get_data(stop_msg)
                password = flashpoint_protocol.get_data(stop_msg, 2)
                movie = flashpoint_protocol.get_data(stop_msg, 3)
                frame = flashpoint_protocol.get_data(stop_msg, 4)

                if int(frame.decode()) >= movie_len - 1:
                    frame = '-1'.encode()

                data = flashpoint_protocol.create_proto_data(username, password, movie, frame)
                msg = flashpoint_protocol.create_aes_msg('UD', data, admin_aes)

                if admin_socket:
                    try:
                        # sending UD message to admin server
                        admin_socket.send(msg)

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
                        logging.error(f"Final disconnect update failed: {e}")
                        return

        except Exception as e:
            logging.error(f"Failed to process final disconnect: {e}")
            return


def get_file(admin_sock, admin_aes, movie_name, movie_db):
    """
    A func that gets file chunks from admin, reassembles them and saves the file to the computer
    :param admin_sock: the admin server's socket
    :param admin_aes: the AES object for encryption/decryption
    :type admin_aes: AesEncryption
    :param movie_name: the movie name  of the file
    :type movie_name: str
    :param movie_db: the database that contains all movie files
    :type movie_db: AdvDB
    :return:
    """
    try:
        # waiting file length message
        len_msg = flashpoint_protocol.get_aes_msg(admin_sock, admin_aes)
        func = flashpoint_protocol.get_func(len_msg)
        logging.debug(f'Got message from client: {func}')

        # making sure that the correct message was received
        while func != 'FL':
            len_msg = flashpoint_protocol.get_aes_msg(admin_sock, admin_aes)
            func = flashpoint_protocol.get_func(len_msg)
            logging.debug(f'Got message from client: {func}')

        file_len = flashpoint_protocol.get_data(len_msg).decode()
        total_chunks = int(file_len)

        # Using a temporary directory to store the chunks and chunks.txt file
        with tempfile.TemporaryDirectory() as tmpdir:
            chunk_paths = []

            for i in range(total_chunks):
                try:
                    chunk_msg = flashpoint_protocol.get_aes_msg(admin_sock, admin_aes)
                    chunk_data = flashpoint_protocol.get_data(chunk_msg)
                    logging.debug(f'Got message from client: {func}')

                    chunk_filename = f"chunk_{i:03d}.ts"
                    chunk_path = os.path.join(tmpdir, chunk_filename)

                    with open(chunk_path, "wb") as f:
                        f.write(chunk_data)
                        f.flush()
                        os.fsync(f.fileno())

                    if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
                        logging.error(f"Failed to write chunk: {chunk_path}")
                        raise RuntimeError(f"Failed to write chunk: {chunk_path}")

                    chunk_paths.append(chunk_path)
                    print(f"Written chunk {i} to {chunk_path} (size: {os.path.getsize(chunk_path)} bytes)")
                    logging.debug(f"Written chunk {i} to {chunk_path} (size: {os.path.getsize(chunk_path)} bytes)")

                except Exception as e:
                    logging.error(f"Error while handling chunk {i}: {e}")

            # Writing chunks.txt inside the temp directory
            try:
                chunks_txt_path = os.path.join(tmpdir, "chunks.txt")
                with open(chunks_txt_path, "w", newline="\n") as f:
                    for path in chunk_paths:
                        filename = os.path.basename(path)
                        f.write(f"file '{filename}'\n")

            except Exception as e:
                logging.debug(f"Error while writing chunks.txt: {e}")

            # Creating the output path for movie file
            new_name = movie_name
            if " " in movie_name:
                new_name = new_name.replace(" ", "_")
            output_path = os.path.abspath(os.path.join("movies", f"{new_name}.mp4"))

            # FFmpeg command to reassemble the chunks to a single file
            ffmpeg_cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0",
                "-i", "chunks.txt",
                "-c", "copy", "-bsf:a", "aac_adtstoasc",
                output_path
            ]

            try:
                # running the ffmpeg command
                subprocess.run(ffmpeg_cmd, cwd=tmpdir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # adding movie file to database
                movie_db.set_val(movie_name, output_path)
                logging.debug(f"Movie saved to {output_path}")

            except subprocess.CalledProcessError as e:
                logging.error(f"FFmpeg command failed: {e}")
                raise

    except Exception as e:
        logging.error(f"Unexpected error in get_file: {e}")


def wait(admin_sock, admin_aes, movie_db):
    """
    A func that handles admin server messages
    :param admin_sock: the admin server's socket
    :param admin_aes: the AES object for encryption/decryption
    :type admin_aes: AesEncryption
    :param movie_db: the movie database
    :type movie_db: AdvDB
    :return:
    """
    try:
        cont_connection = True
        while cont_connection:
            admin_msg = flashpoint_protocol.get_aes_msg(admin_sock, admin_aes)
            func = flashpoint_protocol.get_func(admin_msg)
            logging.debug(f"Got: {func} message from admin")

            # checking if a 'Remove Movie' message was received
            if func == 'RM':
                try:
                    movie_name = flashpoint_protocol.get_data(admin_msg).decode()
                    movie_fpath = movie_db.get_val(movie_name)
                    if movie_fpath and os.path.exists(movie_fpath):
                        os.remove(movie_fpath)
                        movie_db.delete_data(movie_name)
                        logging.debug(f"Deleted file and database entry for {movie_name}")

                    else:
                        logging.warning(f"File not found for {movie_name}")

                except Exception as e:
                    logging.error(f"Error handling RM message: {e}")

            # checking if a 'File Name' message was received
            elif func == 'FN':
                try:
                    movie_name = flashpoint_protocol.get_data(admin_msg).decode()
                    get_file(admin_sock, admin_aes, movie_name, movie_db)

                except Exception as e:
                    logging.error(f"Error handling FN message: {e}")

            elif func == 'AD':
                cont_connection = False

            else:
                logging.warning(f"Unknown function received: {func}")

    except Exception as e:
        logging.error(f"error while handling 'wait' func: {e}")


def run_wait(admin_sock, admin_aes, movie_db):
    """
    A func that start a thread for communication with the admin server
    :param admin_sock: the admin server's socket
    :param admin_aes: the AES object for encryption/decryption
    :type admin_aes: AesEncryption
    :param movie_db: the database of movie file locations
    :type movie_db: AdvDB
    :return:
    """
    try:
        thread = threading.Thread(
            target=wait,
            args=(admin_sock, admin_aes, movie_db),
        )
        thread.start()
        logging.debug("Started admin handler thread.")

    except Exception as e:
        logging.error(f"Failed to start 'wait' thread: {e}")


def handle_thread(admin_sock, admin_aes, client_socket, client_address, my_port, db):
    """
    A func to handle client threads
    :param admin_sock: the admin server's socket
    :param admin_aes: the AES object for encryption/decryption
    :type admin_aes: AesEncryption
    :param client_socket: the client's socket
    :param client_address: the client's address
    :param my_port: the media server port
    :type my_port: int
    :param db: an ADV database containing the movie files paths
    :type db: AdvDB
    :return:
    """

    try:
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

        # extracting the movie name
        m_name = flashpoint_protocol.get_data(first_msg).decode()
        frame = flashpoint_protocol.get_data(first_msg, 2)

        # if the frame is empty, assume it's the first frame
        if frame == b'':
            frame = 0

        else:
            frame = int(frame.decode())

        # getting the movie path from the database
        m_fpath = db.get_val(m_name)

        # if the movie does not exist in the db
        if m_fpath == '':
            logging.error('Movie not found')
            client_socket.send(flashpoint_protocol.create_aes_msg('ER', flashpoint_protocol.create_proto_data(),
                                                                  aes_obj))

        # if the movie was found, start streaming
        else:
            file_break(m_fpath, client_socket, aes_obj, admin_sock, admin_aes, my_port, frame)

    except (BrokenPipeError, ConnectionResetError) as e:
        logging.error(f"Client connection issue: {e}")

    except UnicodeDecodeError as e:
        logging.error(f"Failed to decode string: {e}")

    except ValueError as e:
        logging.error(f"Failed to convert frame to int: {e}")

    except Exception as e:
        logging.exception(f"Unexpected error in handshake/startup process: {e}")


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
        return None


def start_encryption(client_socket):
    """
    A func to start the encryption process
    :param client_socket: the socket for communication
    :return: an AesEncryption object for the socket
    """
    try:
        # waiting for RSA public key
        key_msg = flashpoint_protocol.get_proto_msg(client_socket)

        # making sure client got the correct message
        func = flashpoint_protocol.get_func(key_msg)
        logging.debug(f'Got a message: {func}')

        while func != 'PK':
            key_msg = flashpoint_protocol.get_proto_msg(client_socket)
            func = flashpoint_protocol.get_func(key_msg)
            logging.debug(f'Got a message: {func}')

        # sending encrypted message that contains AES key
        rsa_obj = RsaEncryption()
        pub_key = flashpoint_protocol.get_data(key_msg)

        # creating an AesEncryption object
        aes_obj = AesEncryption()
        enc_key = aes_obj.get_key()

        # using RSA encryption to send AES key
        key_msg = flashpoint_protocol.create_rsa_msg('AK', flashpoint_protocol.create_proto_data(enc_key), rsa_obj,
                                                     pub_key)
        client_socket.send(key_msg)
        logging.debug("sent AK message")

        return aes_obj

    except (ConnectionResetError, BrokenPipeError) as e:
        logging.error(f"Connection error with client: {e}")

    except ValueError as e:
        logging.error(f"Value error during encryption setup: {e}")

    except Exception as e:
        logging.error(f"Unexpected error in start_encryption: {e}")


def main():
    # connecting to the admin server
    admin_sock = connect2admin()
    if not admin_sock:
        return

    # establishing encryption with admin
    admin_aes = start_encryption(admin_sock)

    # setting a database for the movie files locations
    db = initialize_db('movie', MOVIE_START_PATH)

    run_wait(admin_sock, admin_aes, db)

    # setting a port
    port = random.randint(1024, 65535)

    # sending server details to the database
    print(port)
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
            thread = Thread(target=handle_thread,
                            args=(admin_sock, admin_aes, client_socket, client_address, port, db))
            thread.start()

    except socket.error as err:
        err_str = 'received socket exception: ' + str(err)
        logging.error(err_str)

    finally:
        server_socket.close()


if __name__ == "__main__":
    logging.basicConfig(filename='media_server.log', level=logging.DEBUG)
    main()
