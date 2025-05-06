import struct

LEGAL_FUNCS = ['LI', 'SU', 'AP','GM', 'DS', 'MR', 'CR', 'PM', 'LL', 'VU', 'IE', 'YM', 'PL', 'SA', 'MC', 'SD', 'UD',
               'ML', 'DC']


def get_func(byte_msg):
    """
    The func returns the 2 letter message func string.
    :param byte_msg: a message written by protocol
    :type byte_msg: bytes
    :return: the 2 letter command as a string.
    """
    if isinstance(byte_msg, str):
        byte_msg = byte_msg.encode()
    func = byte_msg.split(b'@')[1]
    func = func.split(b'|')[0].decode()
    if func not in LEGAL_FUNCS:
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
    ret_data = data.split(b'^')[half_num-1]
    return ret_data


def get_proto_msg(client_socket):
    """
    the func waits for a message from the socket and receives it using the packed message length.
    :param client_socket: the socket from which the message should come.
    :return: the message from the socket.
    """
    packed_len = client_socket.recv(4)
    while len(packed_len) < 4:
        packed_len += client_socket.recv(4-len(packed_len))
    msg_len = struct.unpack('>I', packed_len)[0]
    msg = client_socket.recv(msg_len)
    while len(msg) < msg_len:
        msg += client_socket.recv(msg_len - len(msg))
    full_msg = packed_len + msg
    if get_func(full_msg) not in LEGAL_FUNCS:
        full_msg = error_msg()
    return full_msg


def error_msg():
    """
    The func creates an error message.
    :return: an error message written by protocol.
    """
    msg_str = b'@ER|^^^'
    packed_length = struct.pack('>I', len(msg_str))
    msg_str = packed_length + msg_str
    return msg_str


def create_proto_msg(func, data):
    """
    A func that creates a message by protocol.
    :param func: the function's name
    :type func: str
    :param data: the needed data to send
    :type data: bytes
    :return: a message in bytes written by protocol
    """
    msg_str = '@' + func + '|'
    msg_str = msg_str.encode()
    msg_data = data
    if isinstance(msg_data, str):
        msg_data = msg_data.encode()
    if b'^' not in msg_data:
        msg_data = b'^^^'
    msg_str += msg_data
    packed_length = struct.pack('>I', len(msg_str))
    msg = packed_length + msg_str
    if func not in LEGAL_FUNCS:
        msg = error_msg()
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
    msg = data1 + b'^' + data2 + b'^' + data3 + b'^' + data4
    return msg
