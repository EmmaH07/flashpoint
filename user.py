class User:
    def __init__(self, name, password):
        self.__name__ = name
        self.__password__ = password
        self.__paused_movies__ = {}

    def get_username(self):
        return self.__name__

    def get_password(self):
        return self.__password__

    def update_paused_movies(self, movie_name, last_minute):
        self.__paused_movies__[movie_name] = last_minute

    def set_password(self, password):
        self.__password__= password

