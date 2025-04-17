import mysql.connector
import pymysql


class DBConnection:
    def __init__(self):
        print('hi')
        try:
            self.__db = pymysql.connect(
                host='127.0.0.1',
                user='root',
                password='password',
                database='flashpoint_database',
            )
            print('connected')
        except Exception as e:
            print(f"General Exception: {e}")

    def movie_exists(self, movie_name):
        print('1')
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT movie_name FROM movies WHERE movie_name = %s', (movie_name,))
        movie = my_cursor.fetchone()
        my_cursor.close()
        return movie is not None

    def fetch_movie(self, movie_name):
        print('2')
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT * FROM movies WHERE movie_name = %s', (movie_name,))
        movie = my_cursor.fetchone()
        my_cursor.close()
        return movie[1] if movie else None

    def username_exists(self, name):
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT username FROM users WHERE username = %s', (name,))
        user = my_cursor.fetchone()
        my_cursor.close()
        return user is not None

    def user_exists(self, username, password_in_hash):
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT user_password FROM users WHERE username = %s', (username,))
        user = my_cursor.fetchone()
        my_cursor.close()
        return user is not None and user[0] == password_in_hash

    def add_user(self, username, password):
        cursor = self.__db.cursor()
        try:
            sql = "INSERT INTO users (username, user_password) VALUES (%s, %s)"
            cursor.execute(sql, (username, password))
            self.__db.commit()
            return True  # Success
        except mysql.connector.IntegrityError:
            print("Error: Username already exists.")
            return False  # Failure
        finally:
            cursor.close()

    def get_movie_lst(self, user_id):
        cursor = self.__db.cursor()
        cursor.execute('SELECT movie_name, last_frame FROM seen_movies WHERE userID = %s',
                       (user_id,))
        user = cursor.fetchall()
        print(user)
        cursor.close()
        return user

    def get_poster_fpath(self, movie_name):
        cursor = self.__db.cursor()
        cursor.execute('SELECT poster_fpath FROM movies WHERE movie_name = %s',
                       (movie_name,))
        user = cursor.fetchone()
        cursor.close()
        return user[0]

    def get_user_id(self, username, password):
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT userID FROM users WHERE username = %s and user_password = %s',
                          (username, password))
        user = my_cursor.fetchone()
        my_cursor.close()
        return user[0]

    def update_movie_lst(self, username, password, movie_to_add, last_frame):
        cursor = self.__db.cursor()
        cursor.execute('SELECT (movies, frames) FROM users WHERE username = %s AND user_password = %s',
                       (username, password))
        user = cursor.fetchone()
        movie_str = ''
        frames_str = ''
        if user[0] is not None and user[1] is not None:
            movie_str = user[0]
            frames_str = user[1]

        if movie_to_add != '' and last_frame != '' and movie_str != '':
            movie_str += '|' + movie_to_add
            frames_str += '|' + last_frame

        elif movie_str == '' and movie_to_add != '' and last_frame != '':
            movie_str += movie_to_add
            frames_str += last_frame

        try:
            sql = "INSERT INTO users (movies, frames) VALUES (%s, %s) WHERE username = %s AND user_password = %s'"
            cursor.execute(sql, (movie_str, frames_str, username, password))
            self.__db.commit()
            return True  # Success
        except mysql.connector.IntegrityError:
            print("Error: Username already exists.")
            return False  # Failure
        finally:
            cursor.close()

    def get_all_posters(self):
        cursor = self.__db.cursor()
        cursor.execute('SELECT movie_name, poster_fpath FROM movies')
        posters = cursor.fetchall()

        return posters


if __name__ == '__main__':
    db = DBConnection()
    if not db:
        print('failed')
    else:
        print(db.movie_exists('The Flash'))
        print(db.fetch_movie('The Flash'))
        print('movie_lst:' + str(db.get_movie_lst(1)))
        print(db.get_poster_fpath('Superman 2025'))
        print('poster list: ')
        print(db.get_all_posters())
