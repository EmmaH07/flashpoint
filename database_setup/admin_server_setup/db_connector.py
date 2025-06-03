import pymysql
import hashlib
from dbutils.pooled_db import PooledDB


class DBConnection:
    def __init__(self):
        """
        A func that builds a DBConnection object with a connection pool
        """
        try:
            self.__pool = PooledDB(
                creator=pymysql,
                maxconnections=10,
                mincached=2,
                maxcached=5,
                blocking=True,
                host='127.0.0.1',
                user='root',
                password='FBaDb250739#',
                database='flashpoint',
            )
        except Exception as e:
            print(f"General Exception while creating pool: {e}")

    def get_conn(self):
        """
        A helper function to get a pooled DB connection
        """
        return self.__pool.connection()

    def username_exists(self, name):
        """
        A func that checks if the given username exists in the database
        :param name: the user's username
        :type name: str
        :return: True if the username exists, False if not
        """
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT username FROM users WHERE username = %s', (name,))
                user = cursor.fetchone()

                return user is not None

            except Exception as db_err:
                print(f"error while handling 'username_exists': {db_err}")
                return False

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            print(f"Unexpected error while handling 'username_exists': {e}")
            return False

    def user_exists(self, username, password_in_hash):
        """
        A func that checks if a user with the given username and password exists in the database
        :param username: the user's username
        :type username: str
        :param password_in_hash: the user's password in HASH
        :type password_in_hash: str
        :return: True if the user exists, False if not
        """
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT user_password FROM users WHERE username = %s', (username,))
                user = cursor.fetchone()
                return user is not None and user[0] == password_in_hash

            except Exception as db_err:
                print(f"error while handling 'user_exists': {db_err}")
                return False

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            print(f"Unexpected error while handling 'user_exists': {e}")
            return False

    def add_user(self, username, password):
        """
        A func that adds a new user to the database
        :param username: the user's username
        :type username: str
        :param password: the user's password in HASH
        :type password: str
        :return: True if the user was added, False if not
        """
        ret_ans = False
        conn = None
        cursor = None
        try:
            conn = self.get_conn()  # get connection from pool
            cursor = conn.cursor()
            sql = "INSERT INTO users (username, user_password) VALUES (%s, %s)"
            cursor.execute(sql, (username, password))
            conn.commit()
            ret_ans = True

        except Exception as e:
            print(f"error while trying to add a user: {e}")

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()  # return connection to the pool

        return ret_ans

    @staticmethod
    def get_movie_lst(user_id):
        """
        A func that gets the user's seen movies
        :param user_id: the user's ID
        :type user_id: int
        :return: a list that contains the user's seen movies
        """
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
            print(f"Error fetching movie list: {e}")
            return []

    def get_user_id(self, username, password):
        """
        A func the fetches the user's ID
        :param username: the user's username
        :type username: str
        :param password: the user's password in HASH
        :type password: str
        :return: the user's ID. None if the user doesn't exist.
        """
        conn = None
        cursor = None
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT userID FROM users WHERE username = %s AND user_password = %s',
                (username, password)
            )
            user = cursor.fetchone()

            if user is None:
                raise ValueError("User not found or incorrect credentials.")

            return user[0]

        except Exception as e:
            print(f"Error while handling 'get_user_id': {e}")
            return None

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def update_last_frame(self, username, password, movie_name, frame):
        """
        A func that updates the last seen frame of the movie
        :param username: the user's username
        :type username: str
        :param password: the user's password in HASH
        :type password: str
        :param movie_name: the movie's name
        :type movie_name: str
        :param frame: the last seen frame
        :type frame: int
        :return:
        """
        conn = None
        cursor = None
        try:
            user_id = self.get_user_id(username, password)
            if not user_id:
                print('Invalid username or password.')
                return

            conn = self.get_conn()
            cursor = conn.cursor()

            try:
                # Check if the movie is already in the seen_movies table
                sql = 'SELECT last_frame FROM seen_movies WHERE userID = %s AND movie_name = %s'
                cursor.execute(sql, (user_id, movie_name))
                result = cursor.fetchone()

                if result:
                    # Update the existing record
                    sql = 'UPDATE seen_movies SET last_frame = %s WHERE userID = %s AND movie_name = %s'
                    cursor.execute(sql, (frame, user_id, movie_name))

                else:
                    # Insert a new record
                    sql = 'INSERT INTO seen_movies (userID, movie_name, last_frame) VALUES (%s, %s, %s)'
                    cursor.execute(sql, (user_id, movie_name, frame))

                conn.commit()

            except Exception as db_err:
                print(f"error while handling 'update_last_frame': {db_err}")

        except Exception as e:
            print(f"Unexpected error while handling 'update_last_frame': {e}")

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def remove_seen_movie(self, username, password, movie_name):
        """
        A func that removes a movie from the user's seen movies list
        :param username: the user's username
        :type username: str
        :param password: the user's password in HASH
        :type password: str
        :param movie_name: the movie's name
        :type movie_name: str
        :return:
        """
        conn = None
        cursor = None
        try:
            user_id = self.get_user_id(username, password)
            if not user_id:
                print("Invalid credentials.")
                return

            conn = self.get_conn()
            cursor = conn.cursor()
            try:
                # Check if the movie is already in the seen_movies table
                sql = 'SELECT last_frame FROM seen_movies WHERE userID = %s AND movie_name = %s'
                cursor.execute(sql, (user_id, movie_name))
                result = cursor.fetchone()

                if result:
                    sql = 'DELETE FROM seen_movies WHERE userID = %s AND movie_name = %s'
                    cursor.execute(sql, (user_id, movie_name))
                    conn.commit()

            except Exception as db_err:
                print(f"error while handling 'remove_seen_movie': {db_err}")

        except Exception as e:
            print(f"Unexpected error while handling 'remove_seen_movie': {e}")

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def is_admin(self, username, password):
        """
        A func that checks if the user has admin qualifications
        :param username: the user's username
        :type username: str
        :param password: the user's password in HASH
        :type password: str
        :return: True if the user is admin, False if not
        """
        conn = None
        cursor = None
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            try:
                sql = 'SELECT admin FROM users WHERE username = %s AND user_password = %s'
                cursor.execute(sql, (username, password))
                is_admin = cursor.fetchone()
                if is_admin is None:
                    return False
                return is_admin[0] == 1

            except Exception as db_err:
                print(f"error while handling 'is_admin': {db_err}")
                return False

        except Exception as e:
            print(f"Unexpected error while handling 'is_admin': {e}")
            return False

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def remove_movie(self, movie_name):
        """
        A func that deletes a movie from the database
        :param movie_name: the movie's name
        :type movie_name: str
        :return:
        """
        conn = None
        cursor = None
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            try:
                sql = 'DELETE FROM seen_movies WHERE movie_name = %s'
                cursor.execute(sql, (movie_name,))
                conn.commit()

            except Exception as db_err:
                print(f"error while handling 'remove_movie': {db_err}")

        except Exception as e:
            print(f"Unexpected error while handling 'remove_movie': {e}")

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


if __name__ == '__main__':
    db = DBConnection()
    print(db.is_admin('Username', str(hashlib.md5('Password'.encode()).hexdigest())))
