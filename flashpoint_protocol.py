LEGAL_FUNCS = ['']


def get_func(proto_msg):
    return proto_msg.split('@')[0]


def get_msg_len(proto_msg):
    len_str = proto_msg.split('@')[1]
    len_str = len_str.split('|')[0]
    return int(len_str)


def get_data(proto_msg, half_num=1):
    return proto_msg.split('|')[1].split('^')[half_num - 1]


def get_chunk(chunk_msg):
    ret_chunk = b''
    is_chunk = False
    for c in chunk_msg:
        c = bytes([c])
        if is_chunk:
            ret_chunk += c
        if c == b'^':
            is_chunk = True
    return ret_chunk


def get_proto_msg(client_socket):
    full_msg = client_socket.recv(3).decode()
    msg_len = ''
    curr_char = client_socket.recv(1).decode()
    while curr_char != '|':
        msg_len += curr_char
        curr_char = client_socket.recv(1).decode()

    full_msg += msg_len
    full_msg += curr_char
    for i in range(int(msg_len)):
        full_msg += client_socket.recv(1).decode()
    return full_msg


def get_chunk_msg(client_socket):
    full_msg = client_socket.recv(3)
    msg_len = b''
    curr_char = client_socket.recv(1)
    while curr_char != b'|':
        msg_len += curr_char
        curr_char = client_socket.recv(1)

    full_msg += msg_len
    full_msg += curr_char
    for i in range(int(msg_len)):
        full_msg += client_socket.recv(1)
    return full_msg


def error_msg():
    return 'ER@0|^'


def create_proto_msg(func, data):
    """

    :param func: the function's name
    :type func: str
    :param data: the needed data to send
    :type data: str
    :return:
    """
    msg = func + '@' + str(len(data)) + '|' + data
    return msg


def create_proto_data(data1='', data2=''):
    msg = data1 + '^' + data2
    return msg


def create_chunk_data(chunk_num, chunk):
    msg = chunk_num.encode() + b'^' + chunk
    return msg


def create_chunk_msg(data):
    msg = b'MC@' + str(len(data)).encode() + b'|' + data
    return msg
