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
        my_cursor.execute('SELECT movie_name FROM movies')
        movies = my_cursor.fetchall()
        ret_ans = False
        for movie in movies:
            if movie_name == movie[0]:
                ret_ans = True
        return ret_ans

    def fetch_movie(self, movie_name):
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT * FROM movies')
        movies = my_cursor.fetchall()
        ret_ans = ''
        for movie in movies:
            if movie_name == movie[0]:
                ret_ans = movie[1]
        return ret_ans

    def username_exists(self, name):
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT username FROM users')
        users = my_cursor.fetchall()
        ret_ans = False
        for user in users:
            if name == user[0]:
                ret_ans = True
        return ret_ans

    def user_exists(self, username, password_in_hash):
        my_cursor = self.__db.cursor()
        my_cursor.execute('SELECT username FROM users')
        users = my_cursor.fetchall()
        ret_ans = False
        for user in users:
            if username == user[0]:
                if password_in_hash == user[1]:
                    ret_ans = True
        return ret_ans

    def add_user(self, username, password):
        cursor = self.__db.cursor()

        sql = "INSERT INTO users (name, password) VALUES (%s, %s, %s)"
        values = (username, password)

        cursor.execute(sql, values)
        self.__db.commit()


if __name__ == '__main__':
    db = DBConnection()
    print(db.movie_exists('The Flash'))
    print(db.fetch_movie('The Flash'))
