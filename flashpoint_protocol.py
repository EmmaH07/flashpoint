LEGAL_FUNCS = ['']


def get_msg_len(proto_msg):
    return int(proto_msg.split('@')[0])


def get_func(proto_msg):
    func_str = proto_msg.split('@')[1]
    func_str = func_str.split('|')[0]
    return func_str


def get_data(proto_msg, half_num=1):
    if half_num < 1 or half_num > 2:
        half_num = 1
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
    curr_char = client_socket.recv(1).decode()
    msg_len = ''
    while curr_char != '@':
        msg_len += curr_char
        curr_char = client_socket.recv(1).decode()

    full_msg = msg_len
    full_msg += curr_char
    for i in range(int(msg_len)):
        full_msg += client_socket.recv(1).decode()
    return full_msg


def get_chunk_msg(client_socket):
    curr_char = client_socket.recv(1)
    msg_len = b''
    while curr_char != b'@':
        msg_len += curr_char
        curr_char = client_socket.recv(1)

    full_msg = msg_len
    full_msg += curr_char
    for i in range(int(msg_len)):
        full_msg += client_socket.recv(1)
    return full_msg


def error_msg():
    ret_str = 'ER|^'
    return str(len(ret_str)) + '@' + ret_str


def create_proto_msg(func, data):
    """

    :param func: the function's name
    :type func: str
    :param data: the needed data to send
    :type data: str
    :return:
    """
    msg_str = func + '|' + data
    msg = str(len(msg_str)) + '@' + msg_str
    return msg


def create_proto_data(data1='', data2=''):
    msg = data1 + '^' + data2
    return msg


def create_chunk_data(chunk_num, chunk):
    msg = chunk_num.encode() + b'^' + chunk
    return msg


def create_chunk_msg(data):
    msg_bytes = b'MC|' + data
    msg = str(len(msg_bytes)).encode() + b'@' + msg_bytes
    return msg
