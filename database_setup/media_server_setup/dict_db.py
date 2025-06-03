class DictDB:
    def __init__(self, dic={}):
        """
        A func that creates a DictDB object
        :param dic:
        """
        self.__dic = dic

    def get_val(self, key):
        """

        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        if key in self.__dic:
            return self.__dic[key]

        else:
            return None

    def set_val(self, key, new_val):
        """
        sets a new value for the key. creates a new key-value pair if the key doesn't exist.
        :param key: the wanted key
        :param new_val: the new value
        :return: True if it worked, False if it didn't.
        """
        if key in self.__dic:
            try:
                self.__dic[key] = new_val
                return True

            except Exception as err:
                print(f'Error setting key {key}: {err}')
                return False

        else:
            try:
                new_dict = {key: new_val}
                self.__dic.update(new_dict)
                return True

            except Exception as err:
                print(f'Error setting key {key}: {err}')
                return False

    def delete_data(self, key):
        """
        deletes the key-value pair from the dictionary.
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        if key in self.__dic:
            return self.__dic.pop(key)

        else:
            return None

    def get_dict(self):
        """
        A func that gets the dictionary
        :return: the database's dictionary
        """
        return self.__dic
