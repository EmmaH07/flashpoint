from tkinter import *
import tkinter as tk
import re
import socket
import flashpoint_protocol
import hashlib
import os
import pickle
from PIL import Image, ImageTk

IP = '127.0.0.1'
PORT = 3514
X1 = 100
X2 = 411
X3 = 722
X4 = 1033
HOME_Y = 250
LIB_Y1 = 80
LIB_Y2 = 420


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
    ret_msg = flashpoint_protocol.get_byte_msg(client_socket)
    print('get movie return message:')
    print(ret_msg)
    ret_lst = []
    print(flashpoint_protocol.get_byte_func(ret_msg))
    if flashpoint_protocol.get_byte_func(ret_msg) == 'YM':
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
                                                          flashpoint_protocol.create_proto_data(movie_lst[counter][0]))
        client_socket.send(poster_msg.encode())
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        if flashpoint_protocol.get_func(ret_msg) == 'MP':
            if added == 0:
                poster1 = flashpoint_protocol.get_data(ret_msg)
                if os.path.exists(poster1) and poster1.endswith('.png'):
                    image = Image.open(poster1)
                    img = image.resize((232, 281))
                    poster1 = ImageTk.PhotoImage(img)
                else:
                    poster1 = empty_poster

            if added == 1:
                poster2 = flashpoint_protocol.get_data(ret_msg)
                if os.path.exists(poster2) and poster2.endswith('.png'):
                    image = Image.open(poster2)
                    img = image.resize((232, 281))
                    poster2 = ImageTk.PhotoImage(img)
                else:
                    poster2 = empty_poster

            if added == 2:
                poster3 = flashpoint_protocol.get_data(ret_msg)
                if os.path.exists(poster3) and poster3.endswith('.png'):
                    image = Image.open(poster3)
                    img = image.resize((232, 281))
                    poster3 = ImageTk.PhotoImage(img)
                else:
                    poster3 = empty_poster

            if added == 3:
                poster4 = flashpoint_protocol.get_data(ret_msg)
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


def display_library(client_socket):
    global p_lib_label1, p_lib_label2, p_lib_label3, p_lib_label4, p_lib_label5, p_lib_label6, p_lib_label7, \
        p_lib_label8, img1, img2, img3, img4, img5, img6 ,img7, img8, down_img, up_img
    msg = flashpoint_protocol.get_byte_msg(client_socket)
    func = flashpoint_protocol.get_byte_func(msg)
    while func != 'PL':
        msg = flashpoint_protocol.get_byte_msg(client_socket)
        func = flashpoint_protocol.get_byte_func(msg)
    counter = 0
    poster_lst = pickle.loads(flashpoint_protocol.get_bytes_data(msg))
    print(poster_lst)
    is_max = False
    max_counter = counter
    if counter < len(poster_lst):
        img1 = Image.open(poster_lst[counter][0])
        img1 = img1.resize((232, 281))
        img1 = ImageTk.PhotoImage(img1)
    else:
        img1 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter

    if counter + 1 < len(poster_lst):
        img2 = Image.open(poster_lst[counter + 1][0])
        img2 = img2.resize((232, 281))
        img2 = ImageTk.PhotoImage(img2)
    else:
        img2 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 1

    if counter + 2 < len(poster_lst):
        img3 = Image.open(poster_lst[counter + 2][0])
        img3 = img3.resize((232, 281))
        img3 = ImageTk.PhotoImage(img3)
    else:
        img3 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 2

    if counter + 3 < len(poster_lst):
        img4 = Image.open(poster_lst[counter + 3][0])
        img4 = img4.resize((232, 281))
        img4 = ImageTk.PhotoImage(img4)
    else:
        img4 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 3

    if counter + 4 < len(poster_lst):
        img5 = Image.open(poster_lst[counter + 4][0])
        img5 = img5.resize((232, 281))
        img5 = ImageTk.PhotoImage(img5)
    else:
        img5 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 4

    if counter + 5 < len(poster_lst):
        img6 = Image.open(poster_lst[counter + 5][0])
        img6 = img6.resize((232, 281))
        img6 = ImageTk.PhotoImage(img6)
    else:
        img6 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 5

    if counter + 6 < len(poster_lst):
        img7 = Image.open(poster_lst[counter + 6][0])
        img7 = img7.resize((232, 281))
        img7 = ImageTk.PhotoImage(img7)
    else:
        img7 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 6

    if counter + 7 < len(poster_lst):
        img8 = Image.open(poster_lst[counter + 7][0])
        img8 = img8.resize((232, 281))
        img8 = ImageTk.PhotoImage(img8)
    else:
        img8 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 7
    p_lib_label1 = Label(lib_frame, image=img1, background='#262626')
    p_lib_label2 = Label(lib_frame, image=img2, background='#262626')
    p_lib_label3 = Label(lib_frame, image=img3, background='#262626')
    p_lib_label4 = Label(lib_frame, image=img4, background='#262626')
    p_lib_label5 = Label(lib_frame, image=img5, background='#262626')
    p_lib_label6 = Label(lib_frame, image=img6, background='#262626')
    p_lib_label7 = Label(lib_frame, image=img7, background='#262626')
    p_lib_label8 = Label(lib_frame, image=img8, background='#262626')
    p_lib_label1.place(x=X1, y=LIB_Y1)
    p_lib_label2.place(x=X2, y=LIB_Y1)
    p_lib_label3.place(x=X3, y=LIB_Y1)
    p_lib_label4.place(x=X4, y=LIB_Y1)
    p_lib_label5.place(x=X1, y=LIB_Y2)
    p_lib_label6.place(x=X2, y=LIB_Y2)
    p_lib_label7.place(x=X3, y=LIB_Y2)
    p_lib_label8.place(x=X4, y=LIB_Y2)

    if max_counter > len(poster_lst):
        counter = max_counter
    else:
        counter += 4

    down_button = Button(lib_frame, image=down_img, command=lambda: down(counter, poster_lst), background='#262626')
    down_button.place(x=1300, y=366)
    up_button = Button(lib_frame, image=up_img, command=lambda: up(counter, poster_lst), background='#262626')
    up_button.place(x=15, y=366)


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
            ok_txt_label.place(y=300, x=1200)
            ok_txt_label.after(3000, ok_txt_label.destroy)


def down(counter, poster_list):
    global p_lib_label1, p_lib_label2, p_lib_label3, p_lib_label4, p_lib_label5, p_lib_label6, p_lib_label7, \
        p_lib_label8, img1, img2, img3, img4, img5, img6 ,img7, img8
    is_max = False
    max_counter = counter
    if counter < len(poster_list):
        img1 = Image.open(poster_list[counter][0])
        img1 = img1.resize((232, 281))
        img1 = ImageTk.PhotoImage(img1)
    else:
        img1 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter

    if counter + 1 < len(poster_list):
        img2 = Image.open(poster_list[counter + 1][0])
        img2 = img2.resize((232, 281))
        img2 = ImageTk.PhotoImage(img2)
    else:
        img2 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 1

    if counter + 2 < len(poster_list):
        img3 = Image.open(poster_list[counter + 2][0])
        img3 = img3.resize((232, 281))
        img3 = ImageTk.PhotoImage(img3)
    else:
        img3 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 2

    if counter + 3 < len(poster_list):
        img4 = Image.open(poster_list[counter + 3][0])
        img4 = img4.resize((232, 281))
        img4 = ImageTk.PhotoImage(img4)
    else:
        img4 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 3

    if counter + 4 < len(poster_list):
        img5 = Image.open(poster_list[counter + 4][0])
        img5 = img5.resize((232, 281))
        img5 = ImageTk.PhotoImage(img5)
    else:
        img5 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 4

    if counter + 5 < len(poster_list):
        img6 = Image.open(poster_list[counter + 5][0])
        img6 = img6.resize((232, 281))
        img6 = ImageTk.PhotoImage(img6)
    else:
        img6 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 5

    if counter + 6 < len(poster_list):
        img7 = Image.open(poster_list[counter + 6][0])
        img7 = img7.resize((232, 281))
        img7 = ImageTk.PhotoImage(img7)
    else:
        img7 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 6

    if counter + 7 < len(poster_list):
        img8 = Image.open(poster_list[counter + 7][0])
        img8 = img8.resize((232, 281))
        img8 = ImageTk.PhotoImage(img8)
    else:
        img8 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 7
    p_lib_label1 = Label(lib_frame, image=img1, background='#262626')
    p_lib_label2 = Label(lib_frame, image=img2, background='#262626')
    p_lib_label3 = Label(lib_frame, image=img3, background='#262626')
    p_lib_label4 = Label(lib_frame, image=img4, background='#262626')
    p_lib_label5 = Label(lib_frame, image=img5, background='#262626')
    p_lib_label6 = Label(lib_frame, image=img6, background='#262626')
    p_lib_label7 = Label(lib_frame, image=img7, background='#262626')
    p_lib_label8 = Label(lib_frame, image=img8, background='#262626')
    p_lib_label1.place(x=X1, y=LIB_Y1)
    p_lib_label2.place(x=X2, y=LIB_Y1)
    p_lib_label3.place(x=X3, y=LIB_Y1)
    p_lib_label4.place(x=X4, y=LIB_Y1)
    p_lib_label5.place(x=X1, y=LIB_Y2)
    p_lib_label6.place(x=X2, y=LIB_Y2)
    p_lib_label7.place(x=X3, y=LIB_Y2)
    p_lib_label8.place(x=X4, y=LIB_Y2)

    if max_counter > len(poster_list):
        counter = max_counter
    else:
        counter += 4


def up(counter, poster_list):
    global p_lib_label1, p_lib_label2, p_lib_label3, p_lib_label4, p_lib_label5, p_lib_label6, p_lib_label7, \
        p_lib_label8, img1, img2, img3, img4, img5, img6 ,img7, img8
    counter -= 4
    if counter < 0:
        counter = 0
    is_max = False
    max_counter = counter
    if counter < len(poster_list):
        img1 = Image.open(poster_list[counter][0])
        img1 = img1.resize((232, 281))
        img1 = ImageTk.PhotoImage(img1)
    else:
        img1 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter

    if counter + 1 < len(poster_list):
        img2 = Image.open(poster_list[counter + 1][0])
        img2 = img2.resize((232, 281))
        img2 = ImageTk.PhotoImage(img2)
    else:
        img2 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 1

    if counter + 2 < len(poster_list):
        img3 = Image.open(poster_list[counter + 2][0])
        img3 = img3.resize((232, 281))
        img3 = ImageTk.PhotoImage(img3)
    else:
        img3 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 2

    if counter + 3 < len(poster_list):
        img4 = Image.open(poster_list[counter + 3][0])
        img4 = img4.resize((232, 281))
        img4 = ImageTk.PhotoImage(img4)
    else:
        img4 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 3

    if counter + 4 < len(poster_list):
        img5 = Image.open(poster_list[counter + 4][0])
        img5 = img5.resize((232, 281))
        img5 = ImageTk.PhotoImage(img5)
    else:
        img5 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 4

    if counter + 5 < len(poster_list):
        img6 = Image.open(poster_list[counter + 5][0])
        img6 = img6.resize((232, 281))
        img6 = ImageTk.PhotoImage(img6)
    else:
        img6 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 5

    if counter + 6 < len(poster_list):
        img7 = Image.open(poster_list[counter + 6][0])
        img7 = img7.resize((232, 281))
        img7 = ImageTk.PhotoImage(img7)
    else:
        img7 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 6

    if counter + 7 < len(poster_list):
        img8 = Image.open(poster_list[counter + 7][0])
        img8 = img8.resize((232, 281))
        img8 = ImageTk.PhotoImage(img8)
    else:
        img8 = empty_poster
        if not is_max:
            is_max = True
            max_counter = counter + 7
    p_lib_label1 = Label(lib_frame, image=img1, background='#262626')
    p_lib_label2 = Label(lib_frame, image=img2, background='#262626')
    p_lib_label3 = Label(lib_frame, image=img3, background='#262626')
    p_lib_label4 = Label(lib_frame, image=img4, background='#262626')
    p_lib_label5 = Label(lib_frame, image=img5, background='#262626')
    p_lib_label6 = Label(lib_frame, image=img6, background='#262626')
    p_lib_label7 = Label(lib_frame, image=img7, background='#262626')
    p_lib_label8 = Label(lib_frame, image=img8, background='#262626')
    p_lib_label1.place(x=X1, y=LIB_Y1)
    p_lib_label2.place(x=X2, y=LIB_Y1)
    p_lib_label3.place(x=X3, y=LIB_Y1)
    p_lib_label4.place(x=X4, y=LIB_Y1)
    p_lib_label5.place(x=X1, y=LIB_Y2)
    p_lib_label6.place(x=X2, y=LIB_Y2)
    p_lib_label7.place(x=X3, y=LIB_Y2)
    p_lib_label8.place(x=X4, y=LIB_Y2)

    if max_counter > len(poster_list):
        counter = max_counter
    else:
        counter += 4


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
    home_pg_frame.pack()


def create_lib_pg(client_socket, username, password):
    global lib_frame, library_bg
    bg_label = Label(lib_frame, image=library_bg)
    bg_label.place(x=0, y=0)
    msg = flashpoint_protocol.create_proto_msg('AP', flashpoint_protocol.create_proto_data())
    client_socket.send(msg.encode())
    display_library(client_socket)
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
