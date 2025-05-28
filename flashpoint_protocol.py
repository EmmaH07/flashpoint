import struct
import base64

LEGAL_FUNCS = ['LI', 'SU', 'AP', 'GM', 'DS', 'MR', 'CR', 'PM', 'LL', 'VU', 'IE', 'YM', 'PL', 'SA', 'MC', 'SD', 'UD',
               'ML', 'DC', 'AK', 'PK', 'IA', 'VA', 'RM', 'FL', 'FC', 'FN', 'FI', 'VM', 'ME', 'AD']


def get_func(proto_msg):
    """
    The func returns the 2 letter message func string.
    :param proto_msg: a message written by protocol
    :type proto_msg: bytes
    :return: the 2 letter command as a string.
    """
    if isinstance(proto_msg, str):
        proto_msg = proto_msg.encode()
    if b'@' in proto_msg:
        func = proto_msg.split(b'@')[1]
        func = func.split(b'|')[0].decode()
        if func not in LEGAL_FUNCS:
            func = 'ER'
    else:
        func = 'ER'
    return func


def get_data(proto_msg, half_num=1):
    """
    The func gets the needed data field.
    :param proto_msg: a message written by protocol
    :type proto_msg: bytes
    :param half_num: the number of the data field
    :type half_num: int
    :return: the needed data field in bytes.
    """
    data = proto_msg.split(b'|')[1]
    if half_num < 1:
        half_num = 1
    elif half_num > 4:
        half_num = 4
    if b'^' in proto_msg:
        ret_data = data.split(b'^')[half_num-1]
        ret_data = base64.b64decode(ret_data)
    else:
        ret_data = b''
    return ret_data


def get_aes_msg(client_socket, aes_obj):
    """
    the func waits for a message from the socket and receives it using the packed message length.
    :param client_socket: the socket from which the message should come.
    :param aes_obj: an object for AES encryption/decryption
    :type aes_obj: AesEncryption
    :return: the decrypted message from the socket.
    """
    packed_len = client_socket.recv(4)
    while len(packed_len) < 4:
        packed_len += client_socket.recv(4-len(packed_len))
    msg_len = struct.unpack('>I', packed_len)[0]
    msg = client_socket.recv(msg_len)
    while len(msg) < msg_len:
        msg += client_socket.recv(msg_len - len(msg))
    msg = aes_obj.decrypt_data(msg)
    if get_func(msg) not in LEGAL_FUNCS:
        msg = create_aes_msg('ER', create_proto_data(), aes_obj)
        msg = aes_obj.decrypt_data(msg)
    return msg


def create_aes_msg(func, data, aes_obj):
    """
    A func that creates an AES encrypted message by protocol
    :param func: the function's name
    :type func: str
    :param data: the needed data to send
    :type data: bytes
    :param aes_obj: an object for AES encryption/decryption
    :type aes_obj: AesEncryption
    :return: a message in bytes written by protocol and encrypted using the AES object
    """
    msg_str = '@' + func + '|'
    msg_str = msg_str.encode()
    msg_data = data
    if isinstance(msg_data, str):
        msg_data = msg_data.encode()
    if b'^' not in msg_data:
        msg_data = b'^^^'
    msg_str += msg_data
    if func not in LEGAL_FUNCS:
        msg_str = b'@ER|^^^'

    msg_str = aes_obj.encrypt_data(msg_str)
    packed_length = struct.pack('>I', len(msg_str))
    msg = packed_length + msg_str

    return msg


def create_rsa_msg(func, data, rsa_obj, pub_key=None):
    """
    A func that creates an RSA encrypted message by protocol
    :param func: the function's name
    :type func: str
    :param data: the needed data to send
    :type data: bytes
    :param rsa_obj: an object for RSA encryption/decryption
    :type rsa_obj: RsaEncryption
    :param pub_key: the public key for the RSA encryption
    :return: a message in bytes written by protocol and encrypted using the RSA object
    """
    if b'^' not in data:
        data = b'^^^'

    msg_str = b'@' + func.encode() + b'|' + data
    if func not in LEGAL_FUNCS:
        msg_str = b'@ER|^^^'

    if pub_key:
        msg_str = rsa_obj.encrypt_with_pub_key(msg_str, pub_key)

    else:
        msg_str = rsa_obj.encrypt(msg_str)

    packed_length = struct.pack('>I', len(msg_str))
    msg = packed_length + msg_str
    return msg


def get_rsa_msg(client_socket, rsa_obj):
    """
    the func waits for a message from the socket and receives it using the packed message length.
    :param client_socket: the socket from which the message should come.
    :param rsa_obj: an object for RSA encryption/decryption
    :type rsa_obj: RsaEncryption
    :return: the decrypted message from the socket.
    """
    packed_len = client_socket.recv(4)
    while len(packed_len) < 4:
        packed_len += client_socket.recv(4-len(packed_len))

    msg_len = struct.unpack('>I', packed_len)[0]
    msg = client_socket.recv(msg_len)
    while len(msg) < msg_len:
        msg += client_socket.recv(msg_len - len(msg))
    msg = rsa_obj.decrypt(msg)
    if get_func(msg) not in LEGAL_FUNCS:
        msg = create_aes_msg('ER', create_proto_data(), rsa_obj)
    return msg


def create_proto_msg(func, data):
    """
    A func that creates a message by protocol
    :param func: the function's name
    :type func: str
    :param data: the needed data to send
    :type data: bytes
    :return: a message in bytes written by protocol
    """
    if b'^' not in data:
        data = b'^^^'

    msg_str = b'@' + func.encode() + b'|' + data
    if func not in LEGAL_FUNCS:
        msg_str = b'@ER|^^^'

    packed_length = struct.pack('>I', len(msg_str))
    msg = packed_length + msg_str
    return msg


def get_proto_msg(client_socket):
    """
    the func waits for a message from the socket and receives it using the packed message length.
    :param client_socket: the socket from which the message should come.
    :return: the message from the socket.
    """
    packed_len = client_socket.recv(4)
    while len(packed_len) < 4:
        packed_len += client_socket.recv(4 - len(packed_len))

    msg_len = struct.unpack('>I', packed_len)[0]
    msg = client_socket.recv(msg_len)

    while len(msg) < msg_len:
        msg += client_socket.recv(msg_len - len(msg))

    if get_func(msg) not in LEGAL_FUNCS:
        msg = create_proto_msg('ER', create_proto_data())

    return msg


def create_proto_data(data1=b'', data2=b'', data3=b'', data4=b''):
    """
    The fun creates a byte string with the needed data by protocol
    :param data1: data field 1
    :type data1: bytes
    :param data2: data field 2
    :type data2: bytes
    :param data3: data field 3
    :type data3: bytes
    :param data4: data field 4
    :type data4: bytes
    :return: a bytes string written by protocol.
    """
    if isinstance(data1, str):
        data1.encode()
    if isinstance(data2, str):
        data2.encode()
    if isinstance(data3, str):
        data3.encode()
    msg = (base64.b64encode(data1) + b'^' + base64.b64encode(data2) + b'^' + base64.b64encode(data3) + b'^' +
           base64.b64encode(data4))
    return msg
