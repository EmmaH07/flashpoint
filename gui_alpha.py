from tkinter import *

user_dict = {}


def slider():
    global index, text
    if index >= len(txt):
        index = -1
        txt_label.after(400, txt_label.destroy)
        create_login_frame()
    else:
        text = text + txt[index]
        txt_label.config(text=text)
        index += 1
        txt_label.after(400, slider)


def submit():
    username = username_box.get()
    password = password_box.get()
    user_dict[username] = password


def create_login_frame():
    global username_box, password_box, login_frame, start_bg
    login_frame.pack()
    bg_label = Label(login_frame, image=start_bg)
    bg_label.place(x=0, y=0)

    # set text boxes
    username_box = Entry(login_frame)
    username_box.place(x=500, y=324)
    username_box.config(font=('Arial Narrow', 30))
    username_box.insert(0, 'Username')
    username_box.config(fg='#fcba03')

    password_box = Entry(login_frame)
    password_box.place(x=500, y=424)
    password_box.config(font=('Arial Narrow', 30))
    password_box.insert(0, 'Password')
    password_box.config(show='*')
    password_box.config(fg='#ba150f')

    # set submit button
    submit_button = Button(login_frame, text='Submit', command=submit,
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
    login_frame.pack()


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

# set text boxes
username_box = Entry(login_frame)
password_box = Entry(login_frame)

# set sliding text
txt = 'flashpoint.io'
index = 0
text = ''
txt_label = Label(win, text=txt, font=('Berlin Sans FB Demi', 150, 'bold'), fg='#c00000', bg='#262626')
txt_label.pack(padx=100, pady=300)
slider()

win.mainloop()  # place window on computer screen and listen to events
print(user_dict)
user_dict = {}
