from file_db import FileDB
import threading
import multiprocessing


class AdvDB(FileDB):
    def __init__(self, is_it_threads, file_name, dic={}):
        """
        a func that builds an ADVdb object
        :param is_it_threads: a bool that signals whether there is a need of thread locks or multiprocess locks
        :type is_it_threads: bool
        :param file_name: the database file name
        :type file_name: str
        :param dic: the dictionary to insert into the database file
        :type dic: dict
        """
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

        try:
            return super().set_val(key, new_val)

        except Exception as e:
            print(f"Error setting value for key '{key}': {e}")
            return False

        finally:
            for i in range(10):
                self.read_lock.release()
            self.write_lock.release()

    def delete_data(self, key):
        """
        deletes the key-value pair from the dictionary. uses lock and semaphore for synchronization.
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        self.write_lock.acquire()
        for i in range(10):
            self.read_lock.acquire()

        try:
            return super().delete_data(key)

        except Exception as e:
            print(f"Error deleting key '{key}': {e}")
            return None

        finally:
            for i in range(10):
                self.read_lock.release()
            self.write_lock.release()

    def get_val(self, key):
        """
        uses lock and semaphore for synchronization.
        :param key: the wanted key
        :return: the value of said key. None if the key doesn't exist.
        """
        self.read_lock.acquire()

        try:
            return super().get_val(key)

        except Exception as e:
            print(f"Error getting value for key '{key}': {e}")
            return None

        finally:
            self.read_lock.release()

    def get_dict(self):
        """
        uses lock and semaphore for synchronization.
        :return: the entire dictionary. None if an error accrued
        """
        self.read_lock.acquire()
        try:
            return super().get_dict()

        except Exception as e:
            print(f"Error retrieving dictionary: {e}")
            return None

        finally:
            self.read_lock.release()
