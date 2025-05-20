import mysql.connector
import pymysql
import hashlib


class DBConnection:
    def __init__(self):
        print('hi')
        try:
            self.__db = pymysql.connect(
                host='127.0.0.1',
                user='root',
                password='FBaDb250739#',
                database='flashpoint',
            )
            print('connected')
        except Exception as e:
            print(f"General Exception: {e}")

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

    @staticmethod
    def get_movie_lst(user_id):
        try:
            conn = pymysql.connect(
                host='127.0.0.1',
                user='root',
                password='FBaDb250739#',
                database='flashpoint',
            )
            cursor = conn.cursor()
            cursor.execute('SELECT movie_name, last_frame FROM seen_movies WHERE userID = %s', (user_id,))
            user = cursor.fetchall()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            print(f"[!] Error fetching movie list: {e}")
            return []

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

    def get_all_posters(self):
        cursor = self.__db.cursor()
        cursor.execute('SELECT movie_name, poster_fpath FROM movies')
        posters = cursor.fetchall()

        return posters

    def update_last_frame(self, username, password, movie_name, frame):
        user_id = self.get_user_id(username, password)
        cursor = self.__db.cursor()

        if user_id:
            # Check if the movie is already in the seen_movies table
            sql = 'SELECT last_frame FROM seen_movies WHERE userID = %s AND movie_name = %s'
            cursor.execute(sql, (user_id, movie_name))
            result = cursor.fetchone()  # Get the actual result

            if result:
                # Update the existing record
                sql = 'UPDATE seen_movies SET last_frame = %s WHERE userID = %s AND movie_name = %s'
                cursor.execute(sql, (frame, user_id, movie_name))
                print('yay')
            else:
                # Insert a new record
                sql = 'INSERT INTO seen_movies (userID, movie_name, last_frame) VALUES (%s, %s, %s)'
                cursor.execute(sql, (user_id, movie_name, frame))
                print('or nor')

            self.__db.commit()
        else:
            print('something went wrong')
        cursor.close()

    def remove_seen_movie(self, username, password, movie_name):
        user_id = self.get_user_id(username, password)
        cursor = self.__db.cursor()

        # Check if the movie is already in the seen_movies table
        sql = 'SELECT last_frame FROM seen_movies WHERE userID = %s AND movie_name = %s'
        cursor.execute(sql, (user_id, movie_name))
        result = cursor.fetchone()  # Get the actual result
        if result:
            # remove the movie
            sql = 'DELETE FROM seen_movies WHERE userID = %s AND movie_name = %s'
            cursor.execute(sql, (user_id, movie_name))
            self.__db.commit()
        cursor.close()

    def is_admin(self, username, password):
        cursor = self.__db.cursor()
        sql = 'SELECT admin FROM users WHERE username = %s AND user_password = %s'
        cursor.execute(sql, (username, password))
        is_admin = cursor.fetchone()[0]
        res = False
        if is_admin == 1:
            res = True
        return res

    def remove_movie(self, movie_name):
        cursor = self.__db.cursor()
        sql = 'DELETE FROM seen_movies WHERE movie_name = %s'
        cursor.execute(sql, args=(movie_name, ))
        self.__db.commit()
        cursor.close()


if __name__ == '__main__':
    db = DBConnection()
    print(db.movie_exists('The Flash'))
    print(db.fetch_movie('The Flash'))
    print('movie_lst:' + str(db.get_movie_lst(1)))
    print(db.get_poster_fpath('Superman 2025'))
    print('poster list: ')
    print(db.get_all_posters())
    print(db.is_admin('Username', str(hashlib.md5('Password'.encode()).hexdigest())))
