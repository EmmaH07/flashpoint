from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64


class AesEncryption:
    def __init__(self, key=None):
        if key is None:
            self.__key__ = get_random_bytes(32)
        elif len(key) in (16, 24, 32):
            self.__key__ = key
        else:
            raise ValueError('Invalid key')

    def get_key(self):
        return self.__key__

    def encrypt_data(self, data):
        cipher = AES.new(self.__key__, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        parts = [
            base64.b64encode(cipher.nonce),
            base64.b64encode(tag),
            base64.b64encode(ciphertext)
        ]
        ret_data = b'~'.join(parts)
        return ret_data

    def decrypt_data(self, enc_data):
        b64_nonce, b64_tag, b64_ciphertext = enc_data.split(b"~")
        nonce = base64.b64decode(b64_nonce)
        tag = base64.b64decode(b64_tag)
        ciphertext = base64.b64decode(b64_ciphertext)
        cipher = AES.new(self.__key__, AES.MODE_EAX, nonce=nonce)
        ret_data = cipher.decrypt_and_verify(ciphertext, tag)
        return ret_data


if __name__ == '__main__':
    msg = b'hello world!'
    aes_obj = AesEncryption()
    print('encoded: ')
    enc_msg = aes_obj.encrypt_data(msg)
    print(enc_msg)
    print('decoded: ')
    print(aes_obj.decrypt_data(enc_msg))
    print('key:')
    print(aes_obj.get_key())

