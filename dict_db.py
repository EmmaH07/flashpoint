class DictDB:
    def __init__(self, dic={}):
        self.__dic__ = dic

    def get_val(self, key):
        """

        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        if key in self.__dic__:
            return self.__dic__[key]
        else:
            return None

    def set_val(self, key, new_val):
        """
        sets a new value for the key. creates a new key-value pair if the key doesn't exist.
        :param key: the wanted key
        :param new_val: the new value
        :return: True if it worked, False if it didn't.
        """
        if key in self.__dic__:
            self.__dic__[key] = new_val
            return True
        else:
            try:
                new_dict = {key: new_val}
                self.__dic__.update(new_dict)
                return True
            except Exception as err:
                print(err)
                return False

    def delete_data(self, key):
        """
        deletes the key-value pair from the dictionary.
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        if key in self.__dic__:
            return self.__dic__.pop(key)
        else:
            return None

    def get_dict(self):
        return self.__dic__
