from tkinter import *
import tkinter as tk
import re
import socket
import flashpoint_protocol
import hashlib
import os

IP = '127.0.0.1'
PORT = 3514
HOME_X1 = 100
HOME_X2 = 411
HOME_X3 = 722
HOME_X4 = 1033
HOME_Y = 250


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


def get_paused_movies(username, password, client_socket):
    msg = flashpoint_protocol.create_proto_msg('GM', flashpoint_protocol.create_proto_data(username, password))
    client_socket.send(msg.encode())
    ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
    ret_dict = {}
    if flashpoint_protocol.get_func(ret_msg) == 'YM':
        movie_str = flashpoint_protocol.get_data(ret_msg, 1)
        frames_str = flashpoint_protocol.get_data(ret_msg, 2)
        if movie_str and frames_str:
            key_lst = movie_str.split('|')
            val_lst = frames_str.split('|')
            count = 0
            max_len = len(key_lst)
            if len(val_lst) < len(key_lst):
                max_len = len(val_lst)
            while count < max_len:
                ret_dict[key_lst[count]] = val_lst[count]
                count += 1
    return ret_dict


def display_movies(client_socket, movie_dict, counter=0):
    global home_pg_frame
    poster1, poster2, poster3, poster4 = '', '', '', ''
    added = 0
    movie_lst = [*movie_dict]
    while counter < len(movie_lst) and added < 4:
        poster_msg = flashpoint_protocol.create_proto_msg('GP',
                                                          flashpoint_protocol.create_proto_data(movie_lst[counter]))
        client_socket.send(poster_msg)
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        if flashpoint_protocol.get_func(ret_msg) == 'MP':
            if added == 0:
                poster1 = flashpoint_protocol.get_data(ret_msg)
                if os.path.exists(poster1) and poster1.endswith('.png'):
                    poster1 = PhotoImage(poster1)
                else:
                    poster1 = ''

            if added == 1:
                poster2 = flashpoint_protocol.get_data(ret_msg)
                if os.path.exists(poster2) and poster2.endswith('.png'):
                    poster2 = PhotoImage(poster2)
                else:
                    poster2 = ''

            if added == 2:
                poster3 = flashpoint_protocol.get_data(ret_msg)
                if os.path.exists(poster3) and poster3.endswith('.png'):
                    poster3 = PhotoImage(poster3)
                else:
                    poster3 = ''

            if added == 3:
                poster4 = flashpoint_protocol.get_data(ret_msg)
                if os.path.exists(poster4) and poster4.endswith('.png'):
                    poster4 = PhotoImage(poster4)
                else:
                    poster4 = ''

        counter += 1
        added += 1

    if poster1 == '' and poster2 == '' and poster3 == '' and poster4 == '':
        empty_home_pg()

    else:
        p_label1 = Label(home_pg_frame, image=poster1)
        p_label1.place(x=HOME_X1, y=HOME_Y)
        p_label2 = Label(home_pg_frame, image=poster2)
        p_label2.place(x=HOME_X2, y=HOME_Y)
        p_label3 = Label(home_pg_frame, image=poster3)
        p_label3.place(x=HOME_X3, y=HOME_Y)
        p_label4 = Label(home_pg_frame, image=poster4)
        p_label4.place(x=HOME_X4, y=HOME_Y)


def empty_home_pg():
    global home_pg_frame, empty_poster
    p_label1 = Label(home_pg_frame, image=empty_poster, background='#262626')
    p_label1.place(x=HOME_X1, y=HOME_Y)
    p_label2 = Label(home_pg_frame, image=empty_poster, background='#262626')
    p_label2.place(x=HOME_X2, y=HOME_Y)
    p_label3 = Label(home_pg_frame, image=empty_poster, background='#262626')
    p_label3.place(x=HOME_X3, y=HOME_Y)
    p_label4 = Label(home_pg_frame, image=empty_poster, background='#262626')
    p_label4.place(x=HOME_X4, y=HOME_Y)


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
                                                         flashpoint_protocol.create_proto_data(username, password))
        client_socket.send(login_msg.encode())
        print(login_msg)
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        print(ret_msg)
        exists = flashpoint_protocol.get_data(ret_msg)
        print(exists)
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
                                                          flashpoint_protocol.create_proto_data(username, password))
        client_socket.send(signup_msg.encode())
        print(signup_msg)
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        print(ret_msg)
        exists = flashpoint_protocol.get_data(ret_msg)
        print(exists)
        if exists == 'True':
            err_txt = "Username already exists, try something else..."
            err_txt_label = Label(signup_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white',
                                  bg='#262626')
            err_txt_label.place(y=700, x=470)
            err_txt_label.after(3000, err_txt_label.destroy)
        else:
            ok_txt = "Signed-up successfully! Please login to your new account"
            ok_txt_label = Label(signup_frame, text=ok_txt, font=('ariel narrow', 15, 'bold'), fg='white', bg='#262626')
            ok_txt_label.place(y=700, x=400)
            ok_txt_label.after(3000, ok_txt_label.destroy)


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


def library_screen(client_socket, username, password):
    global current_frame
    if current_frame:
        current_frame.pack_forget()
    current_frame = lib_frame
    lib_frame.pack()
    create_lib_pg(client_socket, username, password)


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
    signup_password_box.config(show='*')
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
    movie_dict = get_paused_movies(username, password, client_socket)
    display_movies(client_socket, movie_dict)
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
    home_pg_frame.pack()


def create_lib_pg(client_socket, username, password):
    global lib_frame, library_bg
    bg_label = Label(lib_frame, image=library_bg)
    bg_label.place(x=0, y=0)
    movie_dict = get_paused_movies(username, password, client_socket)
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

# set background
clean_bg = PhotoImage(file='clean_bg.png')
label1 = Label(win, image=clean_bg)
label1.place(x=0, y=0)

# set frames
login_frame = Frame(win, bg='black', height=768, width=1365)
signup_frame = Frame(win, bg='black', height=768, width=1365)
home_pg_frame = Frame(win, bg='black', height=768, width=1365)
lib_frame = Frame(win, bg='black', height=768, width=1365)

# setting the login frame as default
current_frame = login_frame

# set user dictionary
user_dict = {}

# set sliding text
txt = 'flashpoint.io'
index = 0
text = ''
txt_label = Label(win, text=txt, font=('Berlin Sans FB Demi', 150, 'bold'), fg='#c00000', bg='#262626')
txt_label.pack(padx=100, pady=300)

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
