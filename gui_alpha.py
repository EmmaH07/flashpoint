import base64
import hashlib
import io
import re
import socket
import subprocess
import tkinter as tk
from queue import Queue
from tkinter import *
import time
import threading

from PIL import Image, ImageTk
from PIL import ImageFile

import flashpoint_protocol

IP = '127.0.0.1'
PORT = 3600
X1 = 100
X2 = 411
X3 = 722
X4 = 1033
HOME_Y = 250
LIB_Y1 = 80
LIB_Y2 = 420
B_Y1 = 375
B_Y2 = 715
POSTER_WIDTH = 232
POSTER_HEIGHT = 281


def check_user_qualifications(username, password):
    """
    The func checks if the username and password contain only the allowed characters
    :param username: The user's username
    :type username:str
    :param password: The user's password
    :type password: str
    :return: True if the username and password follow the qualifications and False if not.
    """
    valid = True
    if (re.fullmatch(r'[A-Za-z0-9_!]+', username) is None or re.fullmatch(r'[A-Za-z0-9_!]+', password)
            is None):
        valid = False
    return valid


def slider():
    """
    The func shows a sliding text
    :return:
    """
    global index, text
    if index >= len(txt):
        index = -1
        txt_label.after(400, txt_label.destroy)
    else:
        text = text + txt[index]
        txt_label.config(text=text)
        index += 1
        txt_label.after(400, slider)


def run_get_chunks(client_socket, movie_len, movie_name, username, password, button1, button2, frame=0):
    """
    the func starts a thread that receives chunks from media server in order to not stop the tkinter loop.
    :param client_socket: the client's socket
    :param movie_len: the amount of chunks the movie is made of
    :type movie_len: int
    :param movie_name: the movie's name
    :type movie_name: str
    :param username: the user's username
    :type username:str
    :param password: the user's password in HASH
    :type password: str
    :param button1: home button
    :param button2: library button
    :param frame: the last frame the movie stopped at
    :type frame: int
    :return:
    """
    thread = threading.Thread(
        target=get_chunks,
        args=(client_socket, movie_len, movie_name, username, password, button1, button2, frame),
        daemon=True  # dies when the main program exits
    )
    thread.start()


def send_stop_message(client_socket, username, password, movie_name, button1, button2, frame):
    """
    The func sends a PM message to the media server
    :param client_socket: the client's socket
    :param username: the user's username
    :type username:str
    :param password: the user's password in HASH
    :type password: str
    :param movie_name: the movie's name
    :type movie_name: str
    :param button1: home button
    :param button2: library button
    :param frame: the last frame the movie stopped at
    :type frame: str
    :return:
    """
    global hposter_lst, empty
    data = flashpoint_protocol.create_proto_data(
        username.encode(), password.encode(), movie_name.encode(), str(frame).encode()
    )
    msg = flashpoint_protocol.create_proto_msg("PM", data)
    print(msg)
    try:
        client_socket.sendall(msg)
        hposter_lst = []
        empty = False
        time.sleep(0.5)
        print('sent stop')
        button1.config(state=tk.NORMAL)
        button2.config(state=tk.NORMAL)
    except Exception as e:
        print(f"[!] Error sending stop message: {e}")


def wait_for_disconnect(sock):
    """
    the func waits for disconnection message
    :param sock: the client's socket
    :return:
    """
    try:
        print("Waiting for 'DS' from media server...")
        ds_msg = flashpoint_protocol.get_proto_msg(sock)
        while flashpoint_protocol.get_func(ds_msg) == 'MC':
            ds_msg = flashpoint_protocol.get_proto_msg(sock)
        if flashpoint_protocol.get_func(ds_msg) == 'DS':
            print("Received 'DS' from server")
        else:
            print(f"Received unexpected message: {flashpoint_protocol.get_func(ds_msg)}")
    except Exception as e:
        print(f"Error while waiting for 'DS': {e}")


def get_chunks(client_socket, movie_len, movie_name, username, password, button1, button2, frame=0):
    """
    The func gets movie chunks from the media server and handles display using ffplay
    :param client_socket: the client's socket
    :param movie_len: the amount of chunks the movie is made of
    :type movie_len: int
    :param movie_name: the movie's name
    :type movie_name: str
    :param username: the user's username
    :type username:str
    :param password: the user's password in HASH
    :type password: str
    :param button1: home button
    :param button2: library button
    :param frame: the last frame the movie stopped at
    :type frame: int
    :return:
    """
    q = Queue(0)
    ffplay = subprocess.Popen([
        'ffplay',
        '-window_title', f'Now Playing: {movie_name}',
        '-i', 'pipe:0',
        '-autoexit'
    ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    play = False
    removed = False
    last_frame = frame

    wait_txt = "Preparing Your Movie..."
    wait_txt_label = Label(watch_frame, text=wait_txt, font=('ariel narrow', 40, 'bold'), fg='white',
                           bg='#262626')
    wait_txt_label.place(y=200, x=400)
    button1.config(state=tk.DISABLED)
    button2.config(state=tk.DISABLED)
    watch_frame.update_idletasks()
    sent = False

    try:
        for i in range(movie_len):
            chunk_msg = flashpoint_protocol.get_proto_msg(client_socket)
            print(flashpoint_protocol.get_func(chunk_msg))
            if flashpoint_protocol.get_func(chunk_msg) == 'MC':
                m_chunk = flashpoint_protocol.get_data(chunk_msg, 2)
                m_chunk = base64.b64decode(m_chunk)
                q.put(m_chunk)

                if q.qsize() > 5:
                    play = True
                    watch_frame.update_idletasks()

                if play:
                    if not removed:
                        wait_txt_label.destroy()
                        removed = True
                    ffplay.stdin.write(q.get())
                    last_frame += 1
                    print('last frame: ' + str(last_frame))

                if ffplay.poll() is not None and not sent:
                    if last_frame == movie_len:
                        last_frame = movie_len + 1
                    send_stop_message(client_socket, username, password, movie_name, button1, button2, str(last_frame))
                    sent = True
            else:
                create_err_pg()

        while not q.empty():
            if not removed:
                wait_txt_label.destroy()
                removed = True
            ffplay.stdin.write(q.get())
            last_frame += 1
            print('last frame: ' + str(last_frame))

        ffplay.stdin.close()

        if ffplay.poll() is not None and not sent:
            if last_frame == movie_len:
                last_frame = movie_len + 1
                print('last frame: ' + str(last_frame))
            send_stop_message(client_socket, username, password, movie_name, button1, button2, str(last_frame))
            sent = True

    except (BrokenPipeError, ValueError):
        print("Chunk receiving interrupted")

    finally:
        if not sent:
            if last_frame == movie_len:
                last_frame = movie_len + 1
                print('last frame: ' + str(last_frame))
            send_stop_message(client_socket, username, password, movie_name, button1, button2, str(last_frame))

        # Wait fully for 'DS' before closing
        wait_thread = threading.Thread(target=wait_for_disconnect, args=(client_socket,))
        wait_thread.start()
        wait_thread.join()

        try:
            client_socket.shutdown(socket.SHUT_WR)

        except Exception as e:
            print(e)

        client_socket.close()

        ffplay.stdin.close()
        ffplay.wait()


def byte2img(b_img):
    """
    transforms bytes to a tkinter photo-image
    :param b_img: the image in bytes
    :return: a photo-image object
    """
    img = None
    try:
        buffer = io.BytesIO(b_img)
        img = Image.open(buffer)
        img = img.resize((POSTER_WIDTH, POSTER_HEIGHT))
        img = ImageTk.PhotoImage(img)
        buffer.close()
    except OSError as ex:
        print(ex)
    return img


def recv_img_lst(client_socket, username, password):
    """
    the func receives all the library posters
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :return: the full poster list
    """
    global poster_lst
    poster_lst = []

    # sending an 'All Posters' request
    client_socket.send(flashpoint_protocol.create_proto_msg('AP', flashpoint_protocol.create_proto_data()))

    # waiting for 'List Length' message
    lst_len = flashpoint_protocol.get_proto_msg(client_socket)
    if flashpoint_protocol.get_func(lst_len) == 'LL':
        lst_len = flashpoint_protocol.get_data(lst_len)
        lib_frame.update_idletasks()
        for i in range(int(lst_len)):
            # displaying loading text
            wait_txt = "Loading..."
            wait_txt_label = Label(lib_frame, text=wait_txt, font=('ariel narrow', 40, 'bold'), fg='white',
                                   bg='#262626')
            wait_txt_label.place(y=355, x=550)
            lib_frame.update_idletasks()

            # waiting for image message
            img_msg = flashpoint_protocol.get_proto_msg(client_socket)
            if flashpoint_protocol.get_func(img_msg) == 'PL':
                # converting image to bytes
                img = base64.b64decode(flashpoint_protocol.get_data(img_msg, 2))
                img = byte2img(img)

                if img:
                    poster_lst.append((flashpoint_protocol.get_data(img_msg).decode(), img))
                    if i >= 7:
                        lib_frame.forget()
                        display_library(client_socket, username, password)
                        lib_frame.pack()
                wait_txt_label.destroy()
                lib_frame.update_idletasks()
                library_screen(client_socket, username, password)
            else:
                # in case of an error message, displaying error screen
                create_err_pg()
    else:
        # in case of an error message, displaying error screen
        create_err_pg()

    return poster_lst


def get_paused_movies(username, password, client_socket):
    """
    the func receives all the library posters
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param client_socket: the client's socket
    :return: alist of the client's paused movies
    """
    global hposter_lst, empty
    hposter_lst = []
    # sending a 'Get Movies' request
    msg = flashpoint_protocol.create_proto_msg('GM', flashpoint_protocol.create_proto_data(username.encode(),
                                                                                           password.encode()))
    client_socket.send(msg)

    # waiting for a 'List Length' message
    ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
    if flashpoint_protocol.get_func(ret_msg) == 'LL':
        lst_len = int(flashpoint_protocol.get_data(ret_msg).decode())
        if lst_len == 0:
            empty = True

        for i in range(lst_len):
            # displaying loading text
            wait_txt = "Loading..."
            wait_txt_label = Label(home_pg_frame, text=wait_txt, font=('ariel narrow', 40, 'bold'), fg='white',
                                   bg='#262626')
            wait_txt_label.place(y=600, x=550)
            home_pg_frame.update_idletasks()

            # waiting for 'Your Movie' message
            m_msg = flashpoint_protocol.get_proto_msg(client_socket)
            if flashpoint_protocol.get_func(m_msg) == 'YM':
                m_name = flashpoint_protocol.get_data(m_msg)
                m_frame = flashpoint_protocol.get_data(m_msg, 2)

                # turning bytes to a photo-image
                m_poster = base64.b64decode(flashpoint_protocol.get_data(m_msg, 3))
                m_poster = byte2img(m_poster)

                home_pg_frame.forget()
                hposter_lst.append((m_name, m_frame, m_poster))
                display_movies(client_socket, username, password)
                home_pg_frame.pack()
                home_pg_frame.update_idletasks()
                wait_txt_label.destroy()
                home_pg_frame.update_idletasks()
            else:
                # in case of an error message, displaying error screen
                create_err_pg()

        home_screen(client_socket, username, password)

    else:
        # in case of an error message, displaying error screen
        create_err_pg()

    return hposter_lst


def display_movies(client_socket, username, password, counter=0):
    """
    The func displays the client's paused movies
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param counter: the index of the last displayed movie
    :type counter: int
    :return: the updated counter
    """
    global hposter_lst, title_buttons, label_lst, poster_img_refs

    # resetting global variables
    title_buttons = []
    label_lst = []
    poster_img_refs = []

    for i in range(0, 4):
        x = [X1, X2, X3, X4][i % 4]

        # setting empty poster image as default
        m_img = empty_poster

        if counter + i < len(hposter_lst):
            title, frame, m_img = hposter_lst[counter + i]
            frame = int(frame.decode())
            # creating a button for each movie
            movie_button = Button(home_pg_frame, text=title, command=lambda t=title.decode(): start_watch
                                  (client_socket, t, username, password, frame),
                                  activebackground="black",
                                  activeforeground="white",
                                  anchor="center",
                                  bd=3,
                                  bg="black",
                                  cursor="hand2",
                                  disabledforeground="gray",
                                  fg="white",
                                  font=("Arial Narrow", 11))
            movie_button.place(x=x, y=HOME_Y + POSTER_HEIGHT + 5)
            title_buttons.append(movie_button)

        # displaying the movie posters
        p_lib_label = Label(home_pg_frame, image=m_img, background='#262626')
        p_lib_label.place(x=x, y=HOME_Y)
        label_lst.append(p_lib_label)
        poster_img_refs.append(m_img)

    return counter


def display_library(client_socket, username, password, counter=0):
    """
    the func displays the library posters
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param counter: the index of the last displayed movie
    :type counter: int
    :return: the updated counter
    """
    global poster_lst, title_buttons, label_lst, poster_img_refs

    # resetting global variables
    title_buttons = []
    label_lst = []
    poster_img_refs = []

    for i in range(0, 8):
        y = LIB_Y1
        if i > 3:
            y = LIB_Y2

        x = [X1, X2, X3, X4][i % 4]

        # setting empty poster image as default
        m_img = empty_poster

        if counter + i < len(poster_lst):
            title, m_img = poster_lst[counter + i]
            # creating a button for each movie
            movie_button = Button(lib_frame, text=title,
                                  command=lambda t=title: start_watch(client_socket, t, username, password),
                                  activebackground="black",
                                  activeforeground="white",
                                  anchor="center",
                                  bd=3,
                                  bg="black",
                                  cursor="hand2",
                                  disabledforeground="gray",
                                  fg="white",
                                  font=("Arial Narrow", 11))
            movie_button.place(x=x, y=y + POSTER_HEIGHT + 5)
            title_buttons.append(movie_button)

        # displaying the movie posters
        p_lib_label = Label(lib_frame, image=m_img, background='#262626')
        p_lib_label.place(x=x, y=y)
        label_lst.append(p_lib_label)
        poster_img_refs.append(m_img)

    return counter


def watch_screen(client_socket, movie_name, username, password, frame=0):
    """
    creating a screen for watching the movie
    :param client_socket: the client's socket
    :param movie_name:
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param frame: the last frame the movie stopped at
    :type frame: int
    :return:
    """

    # setting the background
    bg_label = Label(watch_frame, image=clean_bg)
    bg_label.place(x=0, y=0)

    # setting a button to return to library
    change_2lib = Button(watch_frame, image=lib_img,
                         command=lambda: library_screen(client_socket, username, password),
                         activebackground="#7d0101",
                         activeforeground="#fcba03",
                         anchor="center",
                         bd=3,
                         bg="#c00000",
                         cursor="hand2",
                         disabledforeground="#fcba03",
                         fg="#fcba03",
                         font=("Arial Narrow", 30))
    change_2lib.place(x=715, y=300)

    # setting a button to return to home page
    change_2home = Button(watch_frame, image=home_img,
                          command=lambda: home_screen(client_socket, username, password),
                          activebackground="#fcba03",
                          activeforeground="#fcba03",
                          anchor="center",
                          bd=3,
                          bg="#fcba03",
                          cursor="hand2",
                          disabledforeground="#fcba03",
                          fg="#fcba03",
                          font=("Arial Narrow", 30))
    change_2home.place(x=450, y=300)

    watch_frame.update_idletasks()
    watch_frame.pack()

    # sending a 'Connection Request' message
    msg = flashpoint_protocol.create_proto_msg('CR', flashpoint_protocol.create_proto_data())
    client_socket.send(msg)

    # waiting for a 'Server Details' message
    ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
    if flashpoint_protocol.get_func(ret_msg) == 'SA':
        media_ip = flashpoint_protocol.get_data(ret_msg).decode()
        media_port = int(flashpoint_protocol.get_data(ret_msg, 2).decode())

        # connecting to media server
        try:
            m_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            m_server_sock.connect((media_ip, media_port))
            print("Connected to media server.")

            # sending a 'Movie Request' message
            msg = flashpoint_protocol.create_proto_msg('MR',
                                                       flashpoint_protocol.create_proto_data(movie_name.encode(),
                                                                                             str(frame).encode()))
            m_server_sock.send(msg)

            # waiting for a 'Movie Length' message
            ret_msg = flashpoint_protocol.get_proto_msg(m_server_sock)
            if flashpoint_protocol.get_func(ret_msg) == 'ML':
                movie_len = flashpoint_protocol.get_data(ret_msg).decode()
                movie_len = int(movie_len)
                run_get_chunks(m_server_sock, movie_len, movie_name, username, password, change_2home, change_2lib,
                               frame)

            else:
                # in case of an error message, displaying error screen
                create_err_pg()

        except Exception as e:
            print("Failed to connect to main server:", e)

    else:
        # in case of an error message, displaying error screen
        create_err_pg()


def login_submit(client_socket):
    """
    submitting data from the text boxes to the server
    :param client_socket: the client's socket
    :return:
    """
    global login_frame
    username = login_username_box.get()
    password = login_password_box.get()

    # checking if client used only the allowed characters
    if not check_user_qualifications(username, password):
        err_txt = 'You can only use English letters, numbers, under scores(_) and exclamation marks (!)'
        err_txt_label = Label(login_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white', bg='#262626')
        err_txt_label.place(y=700, x=300)
        err_txt_label.after(3000, err_txt_label.destroy)

    # checking if user exists in the database
    else:
        # hashing the password
        password = str(hashlib.md5(str(password).encode()).hexdigest())

        # sending a 'Login' message
        login_msg = flashpoint_protocol.create_proto_msg('LI',
                                                         flashpoint_protocol.create_proto_data(username.encode(),
                                                                                               password.encode()))
        client_socket.send(login_msg)

        # waiting for a 'Validate User' message
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        if flashpoint_protocol.get_func(ret_msg) == 'VU':
            exists = flashpoint_protocol.get_data(ret_msg)
            exists = exists.decode()
            if exists == 'False':
                err_txt = "User doesn't exist"
                err_txt_label = Label(login_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white',
                                      bg='#262626')
                err_txt_label.place(y=700, x=575)
                err_txt_label.after(3000, err_txt_label.destroy)
            else:
                home_screen(client_socket, username, password)
        else:
            # in case of an error message, displaying error screen
            create_err_pg()


def signup_submit(client_socket):
    """
    submitting data from the text boxes to the server
    :param client_socket: the client's socket
    :return:
    """
    global signup_frame
    username = signup_username_box.get()
    password = signup_password_box.get()

    # checking if client used only the allowed characters
    if not check_user_qualifications(username, password):
        err_txt = 'You used incorrect characters :('
        err_txt_label = Label(signup_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white', bg='#262626')
        err_txt_label.place(y=700, x=550)
        err_txt_label.after(3000, err_txt_label.destroy)

    # checking if user exists in the database
    else:
        # hashing the password
        password = str(hashlib.md5(str(password).encode()).hexdigest())

        # sending a 'Sign-Up' message
        signup_msg = flashpoint_protocol.create_proto_msg('SU',
                                                          flashpoint_protocol.create_proto_data(username.encode(),
                                                                                                password.encode()))
        client_socket.send(signup_msg)

        # waiting for an 'Is Exist' message
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)

        if flashpoint_protocol.get_func(ret_msg) == 'IE':
            exists = flashpoint_protocol.get_data(ret_msg)
            print(exists)
            if isinstance(exists, bytes):
                exists = exists.decode()
            if exists == 'True':
                err_txt = "Username already exists, try something else..."
                err_txt_label = Label(signup_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white',
                                      bg='#262626')
                err_txt_label.place(y=700, x=470)
                err_txt_label.after(3000, err_txt_label.destroy)

            else:
                ok_txt = "Signed-up successfully! Please login to your new account"
                ok_txt_label = Label(signup_frame, text=ok_txt, font=('ariel narrow', 15, 'bold'), fg='white',
                                     bg='#262626')
                ok_txt_label.place(y=250, x=400)
                ok_txt_label.after(3000, ok_txt_label.destroy)

        else:
            # in case of an error message, displaying error screen
            create_err_pg()


def down(counter, username, password, client_socket):
    """
    updating the counter after client pressed 'down' button
    :param counter: the last poster shown
    :type counter: int
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param client_socket: the client's socket
    :return:
    """
    global poster_lst

    counter += 4
    if counter + 4 > len(poster_lst):
        counter -= 4

    library_screen(client_socket, username, password, counter)


def up(counter, username, password, client_socket):
    """
    updating the counter after client pressed 'up' button
    :param counter: the last poster shown
    :type counter: int
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param client_socket: the client's socket
    :return:
    """
    global poster_lst

    if counter == len(poster_lst):
        num = len(poster_lst) % 4
        counter -= num

        if num == 1:
            counter -= 1

        elif num == 2:
            counter -= 2

        else:
            counter -= 3

    elif counter - 4 < 0:
        counter = 0

    else:
        counter -= 4

    library_screen(client_socket, username, password, counter)


def next_submit(client_socket, username, password, counter=0):
    """
    updating the counter after client pressed 'next' button
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param counter: the last poster shown
    :type counter: int
    :return:
    """
    global hposter_lst

    counter += 4
    if counter > len(hposter_lst):
        counter -= 4

    home_screen(client_socket, username, password, counter)


def prev(client_socket, username, password, counter=0):
    """
    updating the counter after client pressed 'prev' button
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param counter: the last poster shown
    :type counter: int
    :return:
    """
    global hposter_lst

    if counter >= len(hposter_lst):
        num = len(hposter_lst) % 4
        counter -= num

    elif counter - 4 < 0:
        counter = 0

    else:
        counter -= 4

    home_screen(client_socket, username, password, counter)


def start_watch(client_socket, movie_name, username, password, frame=0):
    """
    switching to watch frame
    :param client_socket: the client's socket
    :param movie_name: the movie's name
    :type movie_name: str
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param frame: the last seen frame
    :type frame: int
    :return:
    """

    global current_frame
    if current_frame:
        current_frame.pack_forget()  # Hide current frame
    current_frame = watch_frame

    watch_frame.pack()
    watch_screen(client_socket, movie_name, username, password, frame)


def login_screen(client_socket):
    """
    switching to log in frame
    :param client_socket: the client's socket
    :return:
    """
    global current_frame, login_frame, hposter_lst
    if current_frame:
        current_frame.pack_forget()  # Hide current frame
    current_frame = login_frame
    login_frame.pack()

    # reset global variable
    hposter_lst = []

    create_login_frame(client_socket)


def signup_screen(client_socket):
    """
    switching to sign-up frame
    :param client_socket: the client's socket
    :return:
    """
    global current_frame, signup_frame
    if current_frame:
        current_frame.pack_forget()  # Hide current frame
    current_frame = signup_frame
    signup_frame.pack()
    create_signup_frame(client_socket)


def library_screen(client_socket, username, password, counter=0):
    """
    switching to library frame
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param counter: the counter of the last shown poster
    :type counter: int
    :return:
    """
    global current_frame, lib_frame
    if current_frame:
        current_frame.pack_forget()  # hide current frame
    current_frame = lib_frame
    lib_frame.pack()
    create_lib_pg(client_socket, username, password, counter)


def home_screen(client_socket, username, password, counter=0):
    """
    switching to home page frame
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param counter: the counter of the last shown poster
    :type counter: int
    :return:
    """
    global current_frame, home_pg_frame
    if current_frame:
        current_frame.pack_forget()  # hide current frame
    current_frame = home_pg_frame
    home_pg_frame.pack()
    create_home_pg(client_socket, username, password, counter)


def err_screen(client_socket):
    """
    switching to error frame
    :param client_socket: the client's socket
    :return:
    """
    global current_frame, err_frame
    if current_frame:
        current_frame.pack_forget()  # hide current frame
    current_frame = err_frame
    err_frame.pack()
    create_err_pg()


def create_login_frame(client_socket):
    """
    creating Login frame widgets
    :param client_socket: the client's socket
    :return:
    """
    global login_username_box, login_password_box, login_frame, start_bg, user_dict

    # setting the background
    bg_label = Label(login_frame, image=start_bg)
    bg_label.place(x=0, y=0)

    # setting username text box
    login_username_box = Entry(login_frame)
    login_username_box.place(x=500, y=324)
    login_username_box.config(font=('Arial Narrow', 30))
    login_username_box.insert(0, 'Username')
    login_username_box.config(fg='#fcba03')

    # setting password text box
    login_password_box = Entry(login_frame)
    login_password_box.place(x=500, y=424)
    login_password_box.config(font=('Arial Narrow', 30))
    login_password_box.insert(0, 'Password')
    login_password_box.config(show='*')
    login_password_box.config(fg='#ba150f')

    # setting submit button
    submit_button = Button(login_frame, text='Submit', command=lambda: login_submit(client_socket),
                           activebackground="#bf8e04",
                           activeforeground="white",
                           anchor="center",
                           bd=3,
                           bg="#fcba03",
                           cursor="hand2",
                           disabledforeground="gray",
                           fg="white",
                           font=("Arial Narrow", 18),
                           width=11)
    submit_button.place(x=600, y=600)

    # setting 'change to signup screen' button
    change_2signup = Button(login_frame, text='Sign-Up', command=lambda: signup_screen(client_socket),
                            activebackground="#7d0101",
                            activeforeground="#fcba03",
                            anchor="center",
                            bd=3,
                            bg="#c00000",
                            cursor="hand2",
                            disabledforeground="#fcba03",
                            fg="#fcba03",
                            font=("Arial Narrow", 18),
                            width=11)
    change_2signup.place(x=10, y=10)

    # setting 'change to log-in screen' button
    change_2login = Button(login_frame, text='Login', command=lambda: login_screen(client_socket),
                           activebackground="#7d0101",
                           activeforeground="#fcba03",
                           anchor="center",
                           bd=3,
                           bg="#7d0101",
                           cursor="hand2",
                           disabledforeground="#fcba03",
                           fg="#fcba03",
                           font=("Arial Narrow", 18),
                           width=11)
    change_2login.place(x=155, y=10)
    change_2login.config(state=tk.DISABLED)  # disabling button

    # displaying the frame
    login_frame.pack()


def create_signup_frame(client_socket):
    """
    creating signup frame widgets
    :param client_socket: the client's socket
    :return:
    """
    global signup_username_box, signup_password_box, signup_frame, start_bg

    # setting the background
    bg_label = Label(signup_frame, image=start_bg)
    bg_label.place(x=0, y=0)

    # setting username text box
    signup_username_box = Entry(signup_frame)
    signup_username_box.place(x=500, y=324)
    signup_username_box.config(font=('Arial Narrow', 30))
    signup_username_box.insert(0, 'Username')
    signup_username_box.config(fg='#fcba03')

    # setting password text box
    signup_password_box = Entry(signup_frame)
    signup_password_box.place(x=500, y=424)
    signup_password_box.config(font=('Arial Narrow', 30))
    signup_password_box.insert(0, 'Password')
    signup_password_box.config(fg='#ba150f')

    # setting text
    signup_txt = 'You can only use English letters, numbers, under scores(_) and exclamation marks (!)'
    signup_txt_label = Label(signup_frame, text=signup_txt, font=('ariel narrow', 15, 'bold'), fg='white', bg='#262626')
    signup_txt_label.place(x=300, y=550)

    # setting submit button
    submit_button = Button(signup_frame, text='Submit', command=lambda: signup_submit(client_socket),
                           activebackground="#bf8e04",
                           activeforeground="white",
                           anchor="center",
                           bd=3,
                           bg="#fcba03",
                           cursor="hand2",
                           disabledforeground="gray",
                           fg="white",
                           font=("Arial Narrow", 18),
                           width=11)
    submit_button.place(x=600, y=600)

    # setting 'change to signup screen' button
    change_2signup = Button(signup_frame, text='Sign-Up', command=lambda: signup_screen(client_socket),
                            activebackground="#7d0101",
                            activeforeground="#fcba03",
                            anchor="center",
                            bd=3,
                            bg="#7d0101",
                            cursor="hand2",
                            disabledforeground="#fcba03",
                            fg="#fcba03",
                            font=("Arial Narrow", 18),
                            width=11)
    change_2signup.place(x=10, y=10)
    change_2signup.config(state=tk.DISABLED)  # disabling button

    # setting 'change to log-in screen' button
    change_2login = Button(signup_frame, text='Login', command=lambda: login_screen(client_socket),
                           activebackground="#7d0101",
                           activeforeground="#fcba03",
                           anchor="center",
                           bd=3,
                           bg="#c00000",
                           cursor="hand2",
                           disabledforeground="#fcba03",
                           fg="#fcba03",
                           font=("Arial Narrow", 18),
                           width=11)
    change_2login.place(x=155, y=10)

    # displaying the frame
    signup_frame.pack()


def create_home_pg(client_socket, username, password, counter=0):
    """
    creating home page frame widgets
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param counter: the index of the last displayed poster
    :type counter: int
    :return:
    """
    global home_pg_frame, library_bg, hposter_lst, empty

    # setting the background
    bg_label = Label(home_pg_frame, image=library_bg)
    bg_label.place(x=0, y=0)

    # setting text
    home_txt = "Continue Watching"
    home_txt_label = Label(home_pg_frame, text=home_txt, font=('ariel narrow', 40, 'bold'), fg='white', bg='#262626')
    home_txt_label.place(y=100, x=450)

    # setting 'change to library screen' button
    change_2lib = Button(home_pg_frame, text='Library', command=lambda: library_screen(client_socket,
                                                                                       username, password),
                         activebackground="#7d0101",
                         activeforeground="#fcba03",
                         anchor="center",
                         bd=3,
                         bg="#c00000",
                         cursor="hand2",
                         disabledforeground="#fcba03",
                         fg="#fcba03",
                         font=("Arial Narrow", 18),
                         width=11)
    change_2lib.place(x=1200, y=10)

    # setting 'change to home screen' button
    change_2home = Button(home_pg_frame, text='Home', command=lambda: home_screen(client_socket, username, password),
                          activebackground="#7d0101",
                          activeforeground="#fcba03",
                          anchor="center",
                          bd=3,
                          bg="#7d0101",
                          cursor="hand2",
                          disabledforeground="#fcba03",
                          fg="#fcba03",
                          font=("Arial Narrow", 18),
                          width=11)
    change_2home.place(x=1060, y=10)
    change_2home.config(state=tk.DISABLED)  # disabling button

    # setting 'change to log-in screen' button
    change_2login = Button(home_pg_frame, text='Log-out', command=lambda: login_screen(client_socket),
                           activebackground="#7d0101",
                           activeforeground="#fcba03",
                           anchor="center",
                           bd=3,
                           bg="#c00000",
                           cursor="hand2",
                           disabledforeground="#fcba03",
                           fg="#fcba03",
                           font=("Arial Narrow", 18),
                           width=11)
    change_2login.place(x=920, y=10)

    # checking if client already received the list of seen movies
    if not hposter_lst and not empty:
        # setting empty posters while loading
        for i in range(0, 4):
            x = [X1, X2, X3, X4][i % 4]
            p_lib_label = Label(lib_frame, image=empty_poster, background='#262626')
            p_lib_label.place(x=x, y=HOME_Y)
        home_pg_frame.update_idletasks()

        # getting the list of seen movies
        hposter_lst = get_paused_movies(username, password, client_socket)

    # displaying the movie posters and updating the counter
    counter = display_movies(client_socket, username, password, counter)

    # setting 'next' button
    next_button = Button(home_pg_frame, image=next_img, command=lambda: next_submit(client_socket, username, password,
                                                                                    counter), bg='#262626')
    next_button.place(x=715, y=650)

    # setting 'prev' button
    prev_button = Button(home_pg_frame, image=prev_img, command=lambda: prev(client_socket, username, password,
                                                                             counter), bg='#262626')
    prev_button.place(x=600, y=650)

    # displaying frame
    home_pg_frame.pack()


def create_lib_pg(client_socket, username, password, counter=0):
    """
    creating library frame widgets
    :param client_socket: the client's socket
    :param username: the user's username
    :type username: str
    :param password: the user's password in HASH
    :type password: str
    :param counter: the index of the last displayed poster
    :type counter: int
    :return:
    """
    global lib_frame, library_bg, poster_lst

    # setting the background
    bg_label = Label(lib_frame, image=library_bg)
    bg_label.place(x=0, y=0)

    # setting 'change to library screen' button
    change_2lib = Button(lib_frame, text='Library', command=lambda: library_screen(client_socket, username, password),
                         activebackground="#7d0101",
                         activeforeground="#fcba03",
                         anchor="center",
                         bd=3,
                         bg="#7d0101",
                         cursor="hand2",
                         disabledforeground="#fcba03",
                         fg="#fcba03",
                         font=("Arial Narrow", 18),
                         width=11)
    change_2lib.place(x=1200, y=10)
    change_2lib.config(state=DISABLED)  # disabling button

    # setting 'change to home screen' button
    change_2home = Button(lib_frame, text='Home', command=lambda: home_screen(client_socket, username, password),
                          activebackground="#7d0101",
                          activeforeground="#fcba03",
                          anchor="center",
                          bd=3,
                          bg="#c00000",
                          cursor="hand2",
                          disabledforeground="#fcba03",
                          fg="#fcba03",
                          font=("Arial Narrow", 18),
                          width=11)
    change_2home.place(x=1060, y=10)

    # setting 'change to log-in screen' button
    change_2login = Button(lib_frame, text='Log-out', command=lambda: login_screen(client_socket),
                           activebackground="#7d0101",
                           activeforeground="#fcba03",
                           anchor="center",
                           bd=3,
                           bg="#c00000",
                           cursor="hand2",
                           disabledforeground="#fcba03",
                           fg="#fcba03",
                           font=("Arial Narrow", 18),
                           width=11)
    change_2login.place(x=920, y=10)

    # checking if the client already has a list of all the library movie posters
    if not poster_lst:
        # setting empty posters while loading
        for i in range(0, 8):
            y = LIB_Y1
            if i > 3:
                y = LIB_Y2
            x = [X1, X2, X3, X4][i % 4]
            p_lib_label = Label(lib_frame, image=empty_poster, background='#262626')
            p_lib_label.place(x=x, y=y)
        lib_frame.update_idletasks()

        # getting the list of all library movies
        poster_lst = recv_img_lst(client_socket, username, password)

    # displaying the movie posters and updating the counter
    counter = display_library(client_socket, username, password, counter)

    # setting 'down' button
    down_button = Button(lib_frame, image=down_img, command=lambda: down(counter, username, password,
                                                                         client_socket), background='#262626')
    down_button.place(x=1300, y=366)

    # setting 'up' button
    up_button = Button(lib_frame, image=up_img, command=lambda: up(counter, username, password,
                                                                   client_socket), background='#262626')
    up_button.place(x=15, y=366)

    # displaying frame
    lib_frame.pack()


def create_err_pg():
    """
    creating error frame widgets
    :return:
    """
    global err_frame, err_bg
    # setting the background
    bg_label = Label(err_frame, image=err_bg)
    bg_label.place(x=0, y=0)

    # displaying frame
    err_frame.pack()


# setting the window
win = Tk()  # creates a window instance
win.geometry('1365x768')  # set window size
win.title('Flashpoint.io')  # set title
icon = PhotoImage(file='gui_images/flash_icon.png')  # set window icon
win.iconphoto(True, icon)

# set widget images
empty_poster = PhotoImage(file='gui_images/empty_poster.png')
down_img = PhotoImage(file='gui_images/down.png')
up_img = PhotoImage(file='gui_images/up.png')
next_img = PhotoImage(file='gui_images/next.png')
prev_img = PhotoImage(file='gui_images/prev.png')
lib_img = PhotoImage(file='gui_images/lib.png')
home_img = PhotoImage(file='gui_images/home.png')

# set background images
start_bg = PhotoImage(file='gui_images/start_bg.png')
library_bg = PhotoImage(file='gui_images/library_bg.png')
clean_bg = PhotoImage(file='gui_images/clean_bg.png')
err_bg = PhotoImage(file='gui_images/err_pg.png')

# set default background
label1 = Label(win, image=clean_bg)
label1.place(x=0, y=0)

# set frames
login_frame = Frame(win, bg='black', height=768, width=1365)
signup_frame = Frame(win, bg='black', height=768, width=1365)
home_pg_frame = Frame(win, bg='black', height=768, width=1365)
lib_frame = Frame(win, bg='black', height=768, width=1365)
watch_frame = Frame(win, bg='black', height=768, width=1365)
err_frame = Frame(win, bg='black', height=768, width=1365)

# setting the login frame as default
current_frame = login_frame

# set user dictionary
user_dict = {}

# set global variables
poster_lst = []
hposter_lst = []
title_buttons = []
label_lst = []
poster_img_refs = []
empty = False

# set text boxes
login_username_box = Entry(login_frame)
login_password_box = Entry(login_frame)
signup_username_box = Entry(signup_frame)
signup_password_box = Entry(signup_frame)

# set sliding text
txt = 'flashpoint.io'
index = 0
text = ''
txt_label = Label(win, text=txt, font=('Berlin Sans FB Demi', 150, 'bold'), fg='#c00000', bg='#262626')
txt_label.pack(padx=100, pady=300)

# setting the buffer and image settings
ImageFile.LOAD_TRUNCATED_IMAGES = True

my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    my_socket.connect((IP, PORT))
    slider()
    create_login_frame(my_socket)
    win.mainloop()  # place window on computer screen and listen to events

except socket.error as err:
    print('received socket error ' + str(err))

finally:
    my_socket.close()
