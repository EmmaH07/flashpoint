from tkinter import *
import tkinter as tk
import re
import socket
import flashpoint_protocol
import hashlib
import os
import pickle
from PIL import Image, ImageTk
from PIL import ImageFile
import tkinter.ttk as ttk
import io
import base64
from queue import Queue
import subprocess

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
    valid = True
    if re.fullmatch(r'[A-Za-z0-9_!]+', username) is None or re.fullmatch(r'[A-Za-z0-9_!]+', password) is None:
        valid = False
    return valid


def slider():
    global index, text
    if index >= len(txt):
        index = -1
        txt_label.after(400, txt_label.destroy)
    else:
        text = text + txt[index]
        txt_label.config(text=text)
        index += 1
        txt_label.after(400, slider)


def get_chunks(my_socket, movie_len):
    q = Queue(0)
    ffplay = subprocess.Popen(["ffplay", "-"], stdin=subprocess.PIPE)
    play = False
    for i in range(movie_len):
        chunk_msg = flashpoint_protocol.get_proto_msg(my_socket)
        m_chunk = flashpoint_protocol.get_data(chunk_msg, 2)
        m_chunk = base64.b64decode(m_chunk)
        print(m_chunk)
        q.put(m_chunk)
        if q.qsize() > 5:
            play = True

        if play and q.qsize() > 0:
            ffplay.stdin.write(q.get())

    ffplay.stdin.close()
    ffplay.wait()


def byte2img(b_img):
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
    global poster_lst
    poster_lst = []
    client_socket.send(flashpoint_protocol.create_proto_msg('AP', flashpoint_protocol.create_proto_data()))
    lst_len = flashpoint_protocol.get_proto_msg(client_socket)
    if flashpoint_protocol.get_func(lst_len) == 'LL':
        lst_len = flashpoint_protocol.get_data(lst_len)
        for i in range(int(lst_len)):
            img_msg = flashpoint_protocol.get_proto_msg(client_socket)
            print('img message')
            print(flashpoint_protocol.get_data(img_msg, 2))
            img = base64.b64decode(flashpoint_protocol.get_data(img_msg, 2))
            img = byte2img(img)
            if img:
                poster_lst.append((flashpoint_protocol.get_data(img_msg).decode(), img))
                library_screen(client_socket, username, password)

    return poster_lst


def get_paused_movies(username, password, client_socket):
    msg = flashpoint_protocol.create_proto_msg('GM', flashpoint_protocol.create_proto_data(username.encode(),
                                                                                           password.encode()))
    client_socket.send(msg)
    ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
    print('get movie return message:')
    print(ret_msg)
    ret_lst = []
    print(flashpoint_protocol.get_func(ret_msg))
    if flashpoint_protocol.get_func(ret_msg) == 'YM':
        lst_data = flashpoint_protocol.get_bytes_data(ret_msg)
        ret_lst = pickle.loads(flashpoint_protocol.get_bytes_data(ret_msg))
        print('ret_lst: ')
        print(ret_lst)
    return ret_lst


def display_movies(client_socket, movie_lst, counter=0):
    global home_pg_frame, poster1, poster2, poster3, poster4
    poster1, poster2, poster3, poster4 = empty_poster, empty_poster, empty_poster, empty_poster
    added = 0
    while counter < len(movie_lst) and added < 4:
        poster_msg = flashpoint_protocol.create_proto_msg('GP',
                                                          flashpoint_protocol.create_proto_data(
                                                              movie_lst[counter][0].encode()))
        client_socket.send(poster_msg)
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        if flashpoint_protocol.get_func(ret_msg) == 'MP':
            if added == 0:
                poster1 = flashpoint_protocol.get_data(ret_msg).decode()
                if os.path.exists(poster1) and poster1.endswith('.png'):
                    image = Image.open(poster1)
                    img = image.resize((232, 281))
                    poster1 = ImageTk.PhotoImage(img)
                else:
                    poster1 = empty_poster

            if added == 1:
                poster2 = flashpoint_protocol.get_data(ret_msg).decode()
                if os.path.exists(poster2) and poster2.endswith('.png'):
                    image = Image.open(poster2)
                    img = image.resize((232, 281))
                    poster2 = ImageTk.PhotoImage(img)
                else:
                    poster2 = empty_poster

            if added == 2:
                poster3 = flashpoint_protocol.get_data(ret_msg).decode()
                if os.path.exists(poster3) and poster3.endswith('.png'):
                    image = Image.open(poster3)
                    img = image.resize((232, 281))
                    poster3 = ImageTk.PhotoImage(img)
                else:
                    poster3 = empty_poster

            if added == 3:
                poster4 = flashpoint_protocol.get_data(ret_msg).decode()
                if os.path.exists(poster4) and poster4.endswith('.png'):
                    image = Image.open(poster4)
                    img = image.resize((232, 281))
                    poster4 = ImageTk.PhotoImage(img)
                else:
                    poster4 = empty_poster

        counter += 1
        added += 1

    else:
        p_label1 = Label(home_pg_frame, image=poster1, background='#262626')
        p_label1.place(x=X1, y=HOME_Y)
        p_label2 = Label(home_pg_frame, image=poster2, background='#262626')
        p_label2.place(x=X2, y=HOME_Y)
        p_label3 = Label(home_pg_frame, image=poster3, background='#262626')
        p_label3.place(x=X3, y=HOME_Y)
        p_label4 = Label(home_pg_frame, image=poster4, background='#262626')
        p_label4.place(x=X4, y=HOME_Y)


def display_library(my_socket, counter=0):
    global poster_lst, title_buttons, label_lst, poster_img_refs, down_img, up_img

    title_buttons = []
    label_lst = []
    poster_img_refs = []

    for i in range(0, 8):
        y = LIB_Y1
        if i > 3:
            y = LIB_Y2

        x = [X1, X2, X3, X4][i%4]

        m_img = empty_poster

        if counter + i < len(poster_lst):
            title, m_img = poster_lst[counter + i]
            movie_button = Button(lib_frame, text=title, command=lambda t=title: start_watch(my_socket, t),
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

        p_lib_label = Label(lib_frame, image=m_img, background='#262626')
        p_lib_label.place(x=x, y=y)
        label_lst.append(p_lib_label)
        poster_img_refs.append(m_img)

    return counter


def watch_screen(client_socket, movie_name):
    bg_label = Label(watch_frame, image=clean_bg)
    bg_label.place(x=0, y=0)
    video_canvas = tk.Canvas(watch_frame, bg="black", width=640, height=360)
    video_canvas.pack(fill=tk.BOTH, expand=True)
    watch_frame.update_idletasks()
    watch_frame.pack()
    msg = flashpoint_protocol.create_proto_msg('SD', flashpoint_protocol.create_proto_data())
    client_socket.send(msg)
    ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
    print(ret_msg)
    if flashpoint_protocol.get_func(ret_msg) == 'SA':
        media_ip = flashpoint_protocol.get_data(ret_msg).decode()
        media_port = int(flashpoint_protocol.get_data(ret_msg, 2).decode())
        print('ip: ' + media_ip)
        print('port: ' + str(media_port))
        print(type(media_port))
        try:
            m_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            m_server_sock.connect((media_ip, media_port))
            print("Connected to media server.")
            msg = flashpoint_protocol.create_proto_msg('MR',
                                                       flashpoint_protocol.create_proto_data(movie_name.encode()))
            m_server_sock.send(msg)
            ret_msg = flashpoint_protocol.get_proto_msg(m_server_sock)
            if flashpoint_protocol.get_func(ret_msg) == 'ML':
                movie_len = flashpoint_protocol.get_data(ret_msg).decode()
                print(movie_len)
                print(type(movie_len))
                movie_len = int(movie_len)
                get_chunks(m_server_sock, movie_len)

        except Exception as e:
            print("[!] Failed to connect to main server:", e)
            return None


def login_submit(client_socket):
    global login_frame
    username = login_username_box.get()
    password = login_password_box.get()
    if not check_user_qualifications(username, password):
        err_txt = 'You can only use English letters, numbers, under scores(_) and exclamation marks (!)'
        err_txt_label = Label(login_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white', bg='#262626')
        err_txt_label.place(y=700, x=300)
        err_txt_label.after(3000, err_txt_label.destroy)
    else:
        password = str(hashlib.md5(str(password).encode()).hexdigest())
        login_msg = flashpoint_protocol.create_proto_msg('LI',
                                                         flashpoint_protocol.create_proto_data(username.encode(),
                                                                                               password.encode()))
        client_socket.send(login_msg)
        print(login_msg)
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        print(ret_msg)
        exists = flashpoint_protocol.get_data(ret_msg)
        print(exists)
        if isinstance(exists, bytes):
            exists = exists.decode()
        if exists == 'False':
            err_txt = "User doesn't exist"
            err_txt_label = Label(login_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white',
                                  bg='#262626')
            err_txt_label.place(y=700, x=575)
            err_txt_label.after(3000, err_txt_label.destroy)
        else:
            home_screen(client_socket, username, password)


def signup_submit(client_socket):
    global signup_frame
    username = signup_username_box.get()
    password = signup_password_box.get()
    if not check_user_qualifications(username, password):
        err_txt = 'You used incorrect characters :('
        err_txt_label = Label(signup_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white', bg='#262626')
        err_txt_label.place(y=700, x=550)
        err_txt_label.after(3000, err_txt_label.destroy)
    else:
        password = str(hashlib.md5(str(password).encode()).hexdigest())
        signup_msg = flashpoint_protocol.create_proto_msg('SU',
                                                          flashpoint_protocol.create_proto_data(username.encode(),
                                                                                                password.encode))
        client_socket.send(signup_msg)
        print(signup_msg)
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        print(ret_msg)
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
            ok_txt_label = Label(signup_frame, text=ok_txt, font=('ariel narrow', 15, 'bold'), fg='white', bg='#262626')
            ok_txt_label.place(y=300, x=1200)
            ok_txt_label.after(3000, ok_txt_label.destroy)


def down(counter, username, password, client_socket):
    global poster_lst
    print('curr counter: ' + str(counter))
    counter += 4
    if counter > len(poster_lst):
        counter = len(poster_lst)
    print('down counter' + str(counter))
    library_screen(client_socket, username, password, counter)


def up(counter, username, password, client_socket):
    global poster_lst
    print('curr counter: ' + str(counter))
    if counter == len(poster_lst):
        num = len(poster_lst) % 4
        counter -= 4
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
    print('up counter: ' + str(counter))
    library_screen(client_socket, username, password, counter)


def start_watch(client_socket, movie_name):
    print(movie_name)
    global current_frame
    if current_frame:
        current_frame.pack_forget()  # Hide current frame
    current_frame = watch_frame

    watch_frame.pack()
    watch_screen(client_socket, movie_name)


def login_screen(client_socket):
    global current_frame
    if current_frame:
        current_frame.pack_forget()  # Hide current frame
    current_frame = login_frame
    login_frame.pack()  # Show login frame
    create_login_frame(client_socket)  # Ensure UI elements are initialized properly


def signup_screen(client_socket):
    global current_frame
    if current_frame:
        current_frame.pack_forget()  # Hide current frame
    current_frame = signup_frame
    signup_frame.pack()  # Show signup frame
    create_signup_frame(client_socket)  # Ensure UI elements are initialized properly


def library_screen(client_socket, username, password, counter=0):
    global current_frame
    if current_frame:
        current_frame.pack_forget()
    current_frame = lib_frame
    lib_frame.pack()
    create_lib_pg(client_socket, username, password, counter)


def home_screen(client_socket, username, password):
    global current_frame
    if current_frame:
        current_frame.pack_forget()
    current_frame = home_pg_frame
    home_pg_frame.pack()
    create_home_pg(client_socket, username, password)


def create_login_frame(client_socket):
    global login_username_box, login_password_box, login_frame, start_bg, user_dict
    bg_label = Label(login_frame, image=start_bg)
    bg_label.place(x=0, y=0)

    # set text boxes
    login_username_box = Entry(login_frame)
    login_username_box.place(x=500, y=324)
    login_username_box.config(font=('Arial Narrow', 30))
    login_username_box.insert(0, 'Username')
    login_username_box.config(fg='#fcba03')

    login_password_box = Entry(login_frame)
    login_password_box.place(x=500, y=424)
    login_password_box.config(font=('Arial Narrow', 30))
    login_password_box.insert(0, 'Password')
    login_password_box.config(show='*')
    login_password_box.config(fg='#ba150f')

    # set submit button
    submit_button = Button(login_frame, text='Submit', command=lambda: login_submit(my_socket),
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

    change_2signup = Button(login_frame, text='Sign-Up', command=lambda: signup_screen(my_socket),
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

    change_2login = Button(login_frame, text='Login', command=lambda: login_screen(my_socket),
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
    change_2login.config(state=tk.DISABLED)

    # set signup button
    login_frame.pack()


def create_signup_frame(my_socket):
    global signup_username_box, signup_password_box, signup_frame, start_bg
    bg_label = Label(signup_frame, image=start_bg)
    bg_label.place(x=0, y=0)

    # set text boxes
    signup_username_box = Entry(signup_frame)
    signup_username_box.place(x=500, y=324)
    signup_username_box.config(font=('Arial Narrow', 30))
    signup_username_box.insert(0, 'Username')
    signup_username_box.config(fg='#fcba03')

    signup_password_box = Entry(signup_frame)
    signup_password_box.place(x=500, y=424)
    signup_password_box.config(font=('Arial Narrow', 30))
    signup_password_box.insert(0, 'Password')
    signup_password_box.config(fg='#ba150f')

    # set text
    signup_txt = 'You can only use English letters, numbers, under scores(_) and exclamation marks (!)'
    signup_txt_label = Label(signup_frame, text=signup_txt, font=('ariel narrow', 15, 'bold'), fg='white', bg='#262626')
    signup_txt_label.place(x=300, y=550)

    # set submit button
    submit_button = Button(signup_frame, text='Submit', command=lambda: signup_submit(my_socket),
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

    change_2signup = Button(signup_frame, text='Sign-Up', command=lambda: signup_screen(my_socket),
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
    change_2signup.config(state=tk.DISABLED)

    change_2login = Button(signup_frame, text='Login', command=lambda: login_screen(my_socket),
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
    signup_frame.pack()


def create_home_pg(client_socket, username, password):
    global home_pg_frame, library_bg
    bg_label = Label(home_pg_frame, image=library_bg)
    bg_label.place(x=0, y=0)
    home_txt = "Continue Watching"
    home_txt_label = Label(home_pg_frame, text=home_txt, font=('ariel narrow', 40, 'bold'), fg='white', bg='#262626')
    home_txt_label.place(y=100, x=450)
    movie_lst = get_paused_movies(username, password, client_socket)
    display_movies(client_socket, movie_lst)
    change_2lib = Button(home_pg_frame, text='Library', command=lambda: library_screen(my_socket, username, password),
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
    change_2home.config(state=tk.DISABLED)
    change_2login = Button(home_pg_frame, text='Log-out', command=lambda: login_screen(my_socket),
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
    home_pg_frame.pack()


def create_lib_pg(client_socket, username, password, counter=0):
    global lib_frame, library_bg, poster_lst
    bg_label = Label(lib_frame, image=library_bg)
    bg_label.place(x=0, y=0)
    if not poster_lst:
        poster_lst = recv_img_lst(client_socket, username, password)

    counter = display_library(client_socket, counter)

    down_button = Button(lib_frame, image=down_img, command=lambda: down(counter, username, password,
                                                                         client_socket), background='#262626')
    down_button.place(x=1300, y=366)

    up_button = Button(lib_frame, image=up_img, command=lambda: up(counter, username, password,
                                                                   client_socket), background='#262626')
    up_button.place(x=15, y=366)

    change_2lib = Button(lib_frame, text='Library', command=lambda: library_screen(my_socket, username, password),
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
    change_2lib.config(state=DISABLED)

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
    change_2login = Button(lib_frame, text='Log-out', command=lambda: login_screen(my_socket),
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
    lib_frame.pack()


win = Tk()  # creates a window instance
win.geometry('1365x768')  # set window size
win.title('Flashpoint.io')  # set title
icon = PhotoImage(file='flash_icon.png')
win.iconphoto(True, icon)  # set window icon

# set images
start_bg = PhotoImage(file='start_bg.png')
library_bg = PhotoImage(file='library_bg.png')
empty_poster = PhotoImage(file='empty_poster.png')
down_img = PhotoImage(file='down.png')
up_img = PhotoImage(file='up.png')

# set background
clean_bg = PhotoImage(file='clean_bg.png')
label1 = Label(win, image=clean_bg)
label1.place(x=0, y=0)

# set frames
login_frame = Frame(win, bg='black', height=768, width=1365)
signup_frame = Frame(win, bg='black', height=768, width=1365)
home_pg_frame = Frame(win, bg='black', height=768, width=1365)
lib_frame = Frame(win, bg='black', height=768, width=1365)
watch_frame = Frame(win, bg='black', height=768, width=1365)

# setting the login frame as default
current_frame = login_frame

# set user dictionary
user_dict = {}

# set global lists
poster_lst = []
title_buttons = []
label_lst = []
poster_img_refs = []

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
