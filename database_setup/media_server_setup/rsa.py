from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


class RsaEncryption:
    def __init__(self):
        self.__key__ = RSA.generate(2048)

    def get_pub_key(self):
        return self.__key__.publickey().export_key()

    def encrypt(self, data):
        cipher = PKCS1_OAEP.new(self.__key__.publickey())
        encrypted_data = cipher.encrypt(data)
        return encrypted_data

    def decrypt(self, encrypted_data):
        """
        Decrypt data using this instance's private key.
        """
        cipher = PKCS1_OAEP.new(self.__key__)
        decrypted_data = cipher.decrypt(encrypted_data)
        return decrypted_data

    @staticmethod
    def encrypt_with_pub_key(data, pub_key):
        imp_pub_key = RSA.import_key(pub_key)
        cipher = PKCS1_OAEP.new(imp_pub_key)
        encrypted_data = cipher.encrypt(data)
        return encrypted_data


if __name__ == '__main__':
    msg = b'hello world!'
    rsa_obj = RsaEncryption()
    print('encoded: ')
    enc_msg = rsa_obj.encrypt(msg)
    print(enc_msg)
    print('decoded: ')
    print(rsa_obj.decrypt(enc_msg))
    print('key: ')
    print(rsa_obj.get_pub_key())
    print('encrypted with key: ')
    print(rsa_obj.encrypt_with_pub_key(msg, rsa_obj.get_pub_key()))
