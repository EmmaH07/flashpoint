import mysql.connector


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


if __name__ == '__main__':
    db = DBConnection()
    print(db.movie_exists('The Flash'))
    print(db.fetch_movie('The Flash'))
