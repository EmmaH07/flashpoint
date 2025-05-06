from dict_db import DictDB
import os
import pickle


FILE_PATH = 'db.pkl'


class FileDB(DictDB):
    def __init__(self, file_name, dic={}):
        super().__init__(dic)
        if '.' in file_name:
            file_name = file_name.split('.')[0]
        self.__file_name__ = file_name + '.pkl'
        if not os.path.exists(file_name):
            self.file_dump()

    def file_dump(self):
        try:
            with open(self.__file_name__, 'wb') as f:
                pickle.dump(self.__dic__, f)

        except Exception as err:
            print('Got an exception in FileDB - file_dump: ' + str(err))

    def file_load(self):
        try:
            with open(self.__file_name__, 'rb') as file:
                self.__dic__ = pickle.load(file)

        except Exception as err:
            print('Got an exception in FileDB - file_load: ' + str(err))

    def set_val(self, key, new_val):
        """
        sets a new value for the key. creates a new key-value pair if the key doesn't exist.
        dumps the updated dictionary to a file.
        :param key: the wanted key
        :param new_val: the new value
        :return: True if it worked, False if it didn't.
        """
        self.file_load()
        b = super().set_val(key, new_val)
        self.file_dump()
        return b

    def delete_data(self, key):
        """
        deletes the key-value pair from the dictionary. dumps the updated dictionary to a file.
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        self.file_load()
        val = super().delete_data(key)
        self.file_dump()
        return val

    def get_val(self, key):
        """
        fetches the needed value by key
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        self.file_load()
        val = super().get_val(key)
        self.file_dump()
        return val

    def get_dict(self):
        self.file_load()
        var = super().get_dict()
        self.file_dump()
        return var


if __name__ == "__main__":
    f_obj = FileDB()
    f_obj.set_val('hi', 'shalom')

