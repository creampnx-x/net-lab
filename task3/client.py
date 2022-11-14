import sys
import socket
import random
import time


def main():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    target_port = 12000
    target_ip = '172.27.132.102'

    if len(sys.argv) >= 3:
        target_ip = sys.argv[0]
        target_port = int(sys.argv[1])
    elif len(sys.argv) == 1:
        target_ip = input("target server ip: ")
        target_port = int(input("target server port: "))

    relative_file_path = './file.txt'  # input("文件相对路径: ")
    block_min_length = int(input("最小块长度(min=0): "))
    block_max_length = int(input("最大块长度(max=512): "))

    if block_max_length < 1 or 512 < block_max_length:
        block_max_length = 512
        print("最大块长度超越限制区间, 设置为512")

    if block_min_length < 1 or 512 < block_min_length:
        block_min_length = 1
        print("最小块长度超越限制区间, 设置为1")

    if block_max_length < block_min_length:
        block_max_length = 512
        block_min_length = 1
        print("设置区间出错, 重置区间: [1, 512]")

    blocks = get_blocks(relative_file_path,
                        (block_min_length, block_max_length))


    tcp_socket.connect((target_ip, target_port))

    while True:
        '''initailization: [type(2 bytes), N(4 bytes)]'''
        print("init")
        tcp_socket.send(b''.join([(1).to_bytes(2), (len(blocks)).to_bytes(4)]))

        '''agree: [type(2 bytes)]'''
        message = tcp_socket.recv(1024)
        print("agree")
        if int.from_bytes(message[0: 2]) == 2:
            '''send data'''
            print("send_data")
            reverse_blocks = send_data(blocks, tcp_socket)
            if reverse_blocks:
                write_to_file(reverse_blocks)
                break
        else:
            continue
    
    tcp_socket.close()
    return None


def send_data(blocks=[], tcp_socket=socket.socket()):
    '''send data: [type(2 bytes), length(4 bytes), data(${length} bytes)]'''
    reverse_blocks = []
    for block in blocks:
        tcp_socket.send(
            b''.join([(3).to_bytes(2), (len(block)).to_bytes(4), str(block).encode()]))
        
        message = tcp_socket.recv(1024)
        type = int.from_bytes(message[0: 2])
        if type == 4:
            reverse_blocks = [recv_data(message), *reverse_blocks] 
    return reverse_blocks


def recv_data(message=b''):
    type = int.from_bytes(message[0: 2])
    if type != 4:
        return None

    length = int.from_bytes(message[2: 6])
    reverse_data = message[6: 6 + length].decode()
    return reverse_data


def write_to_file(reverse_blocks=[], file_path='./reverse-file.txt'):
    file = open(file_path, "w")
    file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} \n')
    for block in reverse_blocks:
        file.write(block)

    file.close()
    return None


def get_blocks(relative_file_path='./file.txt', range=(1, 512)):
    file = open(relative_file_path, "r", encoding='utf-8')
    text = file.read()
    if len(text) == 0:
        raise FileNotFoundError(relative_file_path, "not have content.")

    blocks = []
    index = 0
    split_finish = False

    while not split_finish:
        block_length = random.randint(range[0], range[1])
        if index + block_length > len(text):
            block_length = len(text) - index
            split_finish = True
        block = text[index: index + block_length]
        index += block_length
        blocks.append(block)

    file.close()
    return blocks


main()
