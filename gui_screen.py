import time
from tkinter import *


class GuiScreen:
    def __init__(self, win, frame, home_lst=None, poster_lst=None):
        self.__win__ = win
        self.__frame__ = frame
        self.__label_lst__ = []
        self.__button_lst__ = []
        if poster_lst:
            self.__poster_lst__ = poster_lst
        else:
            self.__poster_lst__ = []
        if home_lst:
            self.__home_lst__ = home_lst
        else:
            self.__home_lst__ = []

    def add_label(self, label_txt, x, y, size, color, bg_color):
        label = Label(self.__frame__, text=label_txt, font=('ariel narrow', size), fg=color, bg=bg_color)
        label.place(x=x, y=y)
        self.__label_lst__.append(label)
        self.__frame__.pack()
        return self.__label_lst__.index(label)

    def add_img_label(self, img, bg_color, x, y):
        img_label = Label(self.__frame__, image=img, background=bg_color)
        img_label.place(x=x, y=y)
        self.__frame__.pack()
        return img_label

    def remove_label(self, i, sec=0):
        self.__label_lst__[i].after(sec, self.__label_lst__[i].destroy)
        self.__frame__.pack()

    def add_button(self, button):
        self.__button_lst__.append(button)

    def disable_all_buttons(self):
        for button in self.__button_lst__:
            button.config(state=DISABLED)
        self.__frame__.pack()

    def enable_all_buttons(self):
        for button in self.__button_lst__:
            button.config(state=NORMAL)
        self.__frame__.pack()

    def add_poster(self, movie_name, poster_bytes):
        self.__poster_lst__.append((movie_name, poster_bytes))

    def reset_poster_lst(self):
        self.__poster_lst__ = []

    def get_poster_lst(self):
        return self.__poster_lst__

    @staticmethod
    def disable_event():
        pass

    def close_win(self):
        self.__win__.destroy()

    def disable_close(self):
        self.__win__.protocol("WM_DELETE_WINDOW", self.disable_event)

    def enable_close(self):
        self.__win__.protocol("WM_DELETE_WINDOW", self.close_win)

    def add_home_poster(self, movie_name, frame_num, poster_bytes):
        self.__home_lst__.append((movie_name, frame_num, poster_bytes))

    def get_home_posters(self):
        return self.__home_lst__

    def reset_home_posters(self):
        self.__home_lst__ = []
