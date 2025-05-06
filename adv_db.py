from file_db import FileDB
import threading
import multiprocessing


class AdvDB(FileDB):
    def __init__(self, is_it_threads, file_name, dic={}):
        super().__init__(file_name, dic)
        self.is_it_threads = is_it_threads
        if self.is_it_threads:
            self.read_lock = threading.Semaphore(10)
            self.write_lock = threading.Lock()
        else:
            self.read_lock = multiprocessing.Semaphore(10)
            self.write_lock = multiprocessing.Lock()

    def set_val(self, key, new_val):
        """
        sets a new value for the key. creates a new key-value pair if the key doesn't exist.
        uses lock and semaphore for synchronization.
        :param key: the wanted key
        :param new_val: the new value
        :return: True if it worked, False if it didn't.
        """
        self.write_lock.acquire()
        for i in range(10):
            self.read_lock.acquire()
        b = super().set_val(key, new_val)
        for i in range(10):
            self.read_lock.release()
        self.write_lock.release()
        return b

    def delete_data(self, key):
        """
        deletes the key-value pair from the dictionary. uses lock and semaphore for synchronization.
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        self.write_lock.acquire()
        for i in range(10):
            self.read_lock.acquire()
        obj = super().delete_data(key)
        for i in range(10):
            self.read_lock.release()
        self.write_lock.release()
        return obj

    def get_val(self, key):
        """
        uses lock and semaphore for synchronization.
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        self.read_lock.acquire()
        obj = super().get_val(key)
        self.read_lock.release()
        return obj

    def get_dict(self):
        """
        uses lock and semaphore for synchronization.
        :return: the entire dictionary. None if the key doesn't exist.
        """
        self.read_lock.acquire()
        obj = super().get_dict()
        self.read_lock.release()
        return obj
