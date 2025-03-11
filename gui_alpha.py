from tkinter import *
import tkinter as tk
import re
import socket
import flashpoint_protocol
import hashlib

IP = '127.0.0.1'
PORT = 3514


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
        ret_msg = flashpoint_protocol.get_proto_msg(client_socket)
        exists = flashpoint_protocol.get_data(ret_msg)
        if exists == 'False':
            err_txt = "User doesn't exist"
            err_txt_label = Label(login_frame, text=err_txt, font=('ariel narrow', 15, 'bold'), fg='white',
                                  bg='#262626')
            err_txt_label.place(y=700, x=575)
            err_txt_label.after(3000, err_txt_label.destroy)


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


def login_screen(my_socket):
    global current_frame
    if current_frame:
        current_frame.pack_forget()  # Hide current frame
    current_frame = login_frame
    login_frame.pack()  # Show login frame
    create_login_frame(my_socket)  # Ensure UI elements are initialized properly



def signup_screen(my_socket):
    global current_frame
    if current_frame:
        current_frame.pack_forget()  # Hide current frame
    current_frame = signup_frame
    signup_frame.pack()  # Show signup frame
    create_signup_frame(my_socket)  # Ensure UI elements are initialized properly


def create_login_frame(my_socket):
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


win = Tk()  # creates a window instance
win.geometry('1365x768')  # set window size
win.title('Flashpoint.io')  # set title
icon = PhotoImage(file='flash_icon.png')
win.iconphoto(True, icon)  # set window icon

# set images
start_bg = PhotoImage(file='start_bg.png')

# set background
clean_bg = PhotoImage(file='clean_bg.png')
label1 = Label(win, image=clean_bg)
label1.place(x=0, y=0)

# set frames
login_frame = Frame(win, bg='black', height=768, width=1365)
signup_frame = Frame(win, bg='black', height=768, width=1365)

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
