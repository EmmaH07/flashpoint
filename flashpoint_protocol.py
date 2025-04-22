import struct

LEGAL_FUNCS = ['']


def get_msg_len(proto_msg):
    return int(proto_msg.split('@')[0])


def get_func(byte_msg):
    if isinstance(byte_msg, str):
        byte_msg = byte_msg.encode()
    ret_chunk = b''
    is_chunk = False
    is_func = True
    for c in byte_msg:
        c = bytes([c])
        if is_chunk:
            if c == b'|':
                is_func = False
            if is_func:
                ret_chunk += c
        if c == b'@':
            is_chunk = True
    return ret_chunk.decode()


def get_data(proto_msg, half_num=1):
    data = proto_msg.split(b'|')[1]
    if half_num < 1:
        half_num = 1
    elif half_num > 4:
        half_num = 4
    ret_data = data.split(b'^')[half_num-1]
    return ret_data


def get_bytes_second_data_half(byte_msg):
    ret_chunk = b''
    is_chunk = False
    for c in byte_msg:
        c = bytes([c])
        if is_chunk:
            ret_chunk += c
        if c == b'^':
            is_chunk = True
    return ret_chunk


def get_bytes_data(byte_msg, data_half=1):
    ret_chunk1 = b''
    ret_chunk2 = b''
    is_chunk = False
    first_half = True
    for c in byte_msg:
        c = bytes([c])
        if is_chunk:
            if c == b'^':
                first_half = False
            if first_half:
                ret_chunk1 += c
            else:
                ret_chunk2 += c
        if c == b'|':
            is_chunk = True
    ret_data = ret_chunk1
    if data_half == 2:
        ret_data = ret_chunk2
    return ret_data


def get_proto_msg(client_socket):
    packed_len = client_socket.recv(4)
    while len(packed_len) < 4:
        packed_len += client_socket.recv(4-len(packed_len))
    msg_len = struct.unpack('>I', packed_len)[0]
    msg = client_socket.recv(msg_len)
    while len(msg) < msg_len:
        msg += client_socket.recv(msg_len - len(msg))
    full_msg = packed_len + msg
    return full_msg


def get_byte_msg(client_socket):
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
    msg_str = b'@ER|^^'
    packed_length = struct.pack('>I', len(msg_str))
    msg_str = packed_length + msg_str
    return msg_str


def create_proto_msg(func, data):
    """

    :param func: the function's name
    :type func: str
    :param data: the needed data to send
    :type data: str
    :return:
    """
    msg_str = '@' + func + '|'
    msg_str = msg_str.encode()
    msg_data = data
    if isinstance(msg_data, str):
        msg_data = msg_data.encode()
    msg_str += msg_data
    packed_length = struct.pack('>I', len(msg_str))
    msg = packed_length + msg_str
    return msg


def create_proto_data(data1=b'', data2=b'', data3=b'', data4=b''):
    if isinstance(data1, str):
        data1.encode()
    if isinstance(data2, str):
        data2.encode()
    if isinstance(data3, str):
        data3.encode()
    msg = data1 + b'^' + data2 + b'^' + data3 + b'^' + data4
    return msg


def create_chunk_data(chunk_num, chunk):
    msg = chunk_num.encode() + b'^' + chunk
    return msg


print(create_proto_data('hi'.encode()))

