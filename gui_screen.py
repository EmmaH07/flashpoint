from tkinter import *


class GuiScreen:
    def __init__(self, win, frame, home_lst=None, poster_lst=None):
        """
        A func that creates a GuiScreen object
        :param win: the base window
        :param frame: the frame of the screen
        :param home_lst: a list of posters for the home page
        :type home_lst: list
        :param poster_lst: a list of posters for the library page
        :type poster_lst: list
        """
        self.__win = win
        self.__frame = frame
        self.__label_lst = []
        self.__button_lst = []
        self.__title_buttons = []

        if poster_lst:
            self.__poster_lst = poster_lst

        else:
            self.__poster_lst = []

        if home_lst:
            self.__home_lst = home_lst

        else:
            self.__home_lst = []

    def add_label(self, label_txt, x, y, size, color, bg_color):
        """
        A func that adds a label to the screen
        :param label_txt: the text to be shown
        :type label_txt: str
        :param x: the x coordinate
        :type x: int
        :param y: the y coordinate
        :type y: int
        :param size: the size of the text
        :type size: int
        :param color: the color of the text
        :type color: str
        :param bg_color: the background color of the label
        :type bg_color: str
        :return: the index of the label in the label list
        """
        try:
            label = Label(self.__frame, text=label_txt, font=('ariel narrow', size), fg=color, bg=bg_color)
            label.place(x=x, y=y)
            self.__label_lst.append(label)
            self.__frame.pack()
            return self.__label_lst.index(label)

        except Exception as e:
            print(f"Error adding label: {e}")
            return -1

    def add_img_label(self, img, bg_color, x, y):
        """
        A func that adds a label to the screen
        :param img: the img to be shown
        :param bg_color: the background color of the label
        :type bg_color: str
        :param x: the x coordinate
        :type x: int
        :param y: the y coordinate
        :type y: int
        :return: the image label
        """
        try:
            img_label = Label(self.__frame, image=img, background=bg_color)
            img_label.place(x=x, y=y)
            self.__frame.pack()
            return img_label

        except Exception as e:
            print(f"Error adding image label: {e}")
            return None

    def remove_label(self, i, sec=0):
        """
        A func that removes a label from screen after a specified amount of time
        :param i: the index of the label to destroy
        :type i: int
        :param sec: the amount of time before destroying the label
        :type sec: int
        :return:
        """
        try:
            self.__label_lst[i].after(sec, self.__label_lst[i].destroy)
            self.__frame.pack()

        except IndexError:
            print(f"error while handling 'remove_label': No label at index {i}")

    def add_button(self, button):
        """
        Adds a button to the button list
        :param button: the tkinter button to add
        :return:
        """
        self.__button_lst.append(button)

    def disable_all_buttons(self):
        """
        disables all buttons from the list
        :return:
        """
        try:
            for button in self.__button_lst:
                button.config(state=DISABLED)

            for button in self.__title_buttons:
                button.config(state=DISABLED)

            self.__frame.update_idletasks()
            self.__frame.pack()

        except Exception as e:
            print(f"received exception while disabling all buttons: {e}")

    def enable_all_buttons(self):
        """
        enables all buttons from the list
        :return:
        """
        try:
            for button in self.__button_lst:
                button.config(state=NORMAL)

            for button in self.__title_buttons:
                button.config(state=NORMAL)

            self.__frame.update_idletasks()
            self.__frame.pack()

        except Exception as e:
            print(f"received exception while enabling all buttons: {e}")

    def add_title_button(self, button):
        """
        The func adds a button to the button list
        :param button: a tkinter title button
        :return:
        """
        self.__title_buttons.append(button)

    def reset_button_list(self):
        """
        The func resets the button list
        :return:
        """
        self.__button_lst = []

    def destroy_title_buttons(self):
        """
        The func destroys all title buttons
        :return:
        """
        try:
            for button in self.__title_buttons:
                button.destroy()
            self.__title_buttons = []

        except Exception as e:
            print(f"received exception while destroying all title buttons: {e}")

    def disable_title_buttons(self):
        """
        A func that disables all title buttons
        :return:
        """
        try:
            for button in self.__title_buttons:
                button.config(state=DISABLED)

            self.__frame.update_idletasks()
            self.__frame.pack()

        except Exception as e:
            print(f"received exception while disabling all buttons: {e}")

    def enable_title_buttons(self):
        """
        A func that enables all title buttons
        :return:
        """
        try:
            for button in self.__title_buttons:
                button.config(state=NORMAL)

            self.__frame.update_idletasks()
            self.__frame.pack()

        except Exception as e:
            print(f"received exception while enabling all buttons: {e}")

    def add_poster(self, movie_name, poster_bytes):
        """
        Adds a poster to the library poster list
        :param movie_name: the movie's name
        :type movie_name: str
        :param poster_bytes: the poster image
        :return:
        """
        self.__poster_lst.append((movie_name, poster_bytes))

    def reset_poster_lst(self):
        """
        resets the library poster list
        :return:
        """
        self.__poster_lst = []

    def get_poster_lst(self):
        """
        fetches the library poster list
        :return: the list of library posters
        """
        return self.__poster_lst

    @staticmethod
    def disable_event():
        """
        func to enable the disable_close func
        :return:
        """
        pass

    def close_win(self):
        """
        func to enable the enable_close func
        :return:
        """
        self.__win.destroy()

    def disable_close(self):
        """
        A func that disables the ability to close the window
        :return:
        """
        self.__win.protocol("WM_DELETE_WINDOW", self.disable_event)

    def enable_close(self):
        """
        A func that enables the ability to close the window
        :return:
        """
        self.__win.protocol("WM_DELETE_WINDOW", self.close_win)

    def add_home_poster(self, movie_name, frame_num, poster_bytes):
        """
        Adds a poster to the library poster list
        :param movie_name: the movie's name
        :type movie_name: str
        :param frame_num: the number of the last frame shown
        :type frame_num: int
        :param poster_bytes: the poster image
        :return:
        """
        self.__home_lst.append((movie_name, frame_num, poster_bytes))

    def get_home_posters(self):
        """
        fetches the home page poster list
        :return: the list of home page posters
        """
        return self.__home_lst

    def reset_home_posters(self):
        """
        resets the home page poster list
        :return:
        """
        self.__home_lst = []
