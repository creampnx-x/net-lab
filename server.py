import socket
import time
import random


def main():
    output_format("init server port:")
    # port = int(get_input())
    port = 12000

    udp_socket = init_socket(port)
    listen(udp_socket)


def init_socket(port=8080, ip='', type=socket.SOCK_DGRAM):
    output_format("开始初始化UDP服务器了...")

    s = socket.socket(socket.AF_INET, type)
    s.bind((ip, port))

    output_format("已经绑定UDP端口了, 端口为: " + str(port))
    return s


def listen(udp_socket=socket.socket()):
    output_format("开始监听端口请求...")
    create_link(udp_socket)
    accept_data(udp_socket)


def create_link(udp_socket=socket.socket()):
    waiting_seq_ack = -1
    while True:
        message, address = udp_socket.recvfrom(2048)
        seq_number = int.from_bytes(message[0: 2])
        syn = int(message[2])

        if syn == 0 and seq_number == (waiting_seq_ack + 1):
            '''and ack == waiting_seq_ack + 1'''
            print("第三次握手，握手完成...")
            break

        waiting_seq_ack = seq_number

        print("第一次握手: ...")
        udp_socket.sendto(
            b''.join([seq_number.to_bytes(2), syn.to_bytes()]), address)
        print("第二次握手：...")


def accept_data(udp_socket=socket.socket()):
    while True:
        message, address = udp_socket.recvfrom(2048)
        seq_number = int.from_bytes(message[0: 2])
        fin = int(message[3])
        print(seq_number)
        if fin == 1:
            print("第一次挥手...")
            if close_link(address, seq_number, udp_socket):
                print("断开连接")
                udp_socket.close()
                break
            else:
                print("重新等待挥手...")
                continue

        if is_unuse():
            continue

        udp_socket.sendto(
            b''.join([seq_number.to_bytes(2), int(0).to_bytes(), fin.to_bytes()]), address)

    return None


def close_link(address, seq_number, udp_socket=socket.socket()):
    # ack
    print("第二次挥手...")
    udp_socket.sendto(
        b''.join([seq_number.to_bytes(2), int(0).to_bytes(), (0).to_bytes()]), address)

    # fin
    print("第三次挥手...")
    udp_socket.sendto(
        b''.join([(seq_number + 1).to_bytes(2), int(0).to_bytes(), (1).to_bytes()]), address)

    # ack
    print("第四次挥手...")
    message, address = udp_socket.recvfrom(2048)
    ack = int.from_bytes(message[0: 2])
    print(ack, seq_number)
    if ack == seq_number + 1:
        print("第四次挥手成功...")
        return True
    return False


def get_input():
    return input()


def output_format(s):
    print(s)
    return None


def is_unuse():
    """
    是否弃用此请求来模拟丢包, 概率为 80%
    """
    return random.random() > 0.8


main()
