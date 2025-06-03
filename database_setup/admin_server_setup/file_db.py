from dict_db import DictDB
import os
import pickle


FILE_PATH = 'db.pkl'


class FileDB(DictDB):
    def __init__(self, file_name, dic={}):
        super().__init__(dic)
        if '.' in file_name:
            file_name = file_name.split('.')[0]
        self.__file_name = file_name + '.pkl'
        if not os.path.exists(file_name):
            self.file_dump()

    def file_dump(self):
        try:
            with open(self.__file_name, 'wb') as f:
                pickle.dump(self.__dic__, f)

        except Exception as err:
            print('Got an exception in FileDB - file_dump: ' + str(err))

    def file_load(self):
        try:
            with open(self.__file_name, 'rb') as file:
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
        try:
            self.file_load()
            result = super().set_val(key, new_val)
            self.file_dump()
            return result

        except Exception as e:
            print(f'Error setting key {key}: {e}')
            return False

    def delete_data(self, key):
        """
        deletes the key-value pair from the dictionary. dumps the updated dictionary to a file.
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        try:
            self.file_load()
            val = super().delete_data(key)
            self.file_dump()
            return val

        except Exception as e:
            print(f'Error deleting key {key}: {e}')
            return None

    def get_val(self, key):
        """
        fetches the needed value by key
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        try:
            self.file_load()
            val = super().get_val(key)
            self.file_dump()
            return val

        except Exception as e:
            print(f'Error getting value for key {key}: {e}')
            return None

    def get_dict(self):
        """
        retrieves the dictionary from file
        :return: the entire dictionary. None if an error accrued
        """
        try:
            self.file_load()
            val = super().get_dict()
            self.file_dump()
            return val

        except Exception as e:
            print(f'Error retrieving dictionary: {e}')
            return None


if __name__ == "__main__":
    f_obj = FileDB('test')
    f_obj.set_val('hi', 'shalom')
