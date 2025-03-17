import mysql.connector
import pickle


class DBConnection:
    def __init__(self):
        self.__db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ba38IltF07!+',
            port='3306',
            database='flashpoint'
        )

    def movie_exists(self, movie_name):
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT movie_name FROM movies WHERE movie_name = %s', (movie_name,))
        movie = my_cursor.fetchone()
        my_cursor.close()
        return movie is not None

    def fetch_movie(self, movie_name):
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
        cursor.close()
        return user

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


if __name__ == '__main__':
    db = DBConnection()
    print(db.movie_exists('The Flash'))
    print(db.fetch_movie('The Flash'))
    print('movie_lst:' + str(db.get_movie_lst(1)))
