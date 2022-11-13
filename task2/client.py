import time
import math
import socket
import random
from threading import Timer


def main():
    '''this is the entry function of client.'''
    target_ip = '172.27.132.102'  # input("target server ip: ")
    target_port = 12000  # int(input("target server port: "))

    # init udp socket.
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 开始计时
    start_time = time.time()
    print("连接开始, 时间为: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    # 建立连接
    create_link(udp_socket, (target_ip, target_port))

    # 传送数据
    transfer_data(udp_socket, (target_ip, target_port))

    # 结束计时
    end_time = time.time()
    print("连接结束, 时间为: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    print("整体时间：", end_time - start_time, "s")
    '''end of client.'''


def create_link(udp_socket=socket.socket(), address=('127.0.0.1', 12000)):
    '''create link like tcp, send three handshakes'''

    # 初始数据结构
    syn = 1
    init_seq = 1

    print("第一次握手...")
    udp_socket.sendto(
        b''.join([init_seq.to_bytes(2), syn.to_bytes()]), address)

    print("第二次握手...")
    message, _ = udp_socket.recvfrom(2048)
    sec_seq = int.from_bytes(message[0: 2])

    # 同步标志
    syn = message[2]

    if syn != 1:
        raise ValueError("握手失败, 检查第二次握手 syn 参数")

    if sec_seq != init_seq:
        raise ValueError("握手失败, 检查第二次握手 seq 参数")

    # 第三次同步标志设为 0
    syn = 0

    print("第三次握手...")
    udp_socket.sendto(
        b''.join([(sec_seq + 1).to_bytes(2), syn.to_bytes()]), address)

    # 握手结束
    print("握手成功...")
    return True


def transfer_data(udp_socket=socket.socket(), address=('127.0.0.1', 12000)):
    '''send data with bytes arr, the structure like this: [seq(2), syn(1), fin(1)]'''

    # 结束标志
    fin = 0

    # seq 种子
    seed = int(random.random() * 100)
    seq = seed

    window = {}  # 窗口字典
    rtt_map = {}  # rtt 字典
    resend_times = {"send": 0}  # 重发次数引用指针，用于在重发线程中的数据处理
    timer_map = {-1: Timer(0, lambda: None)}  # 计时器字典，可优化

    # 发送数目为 12
    while seq < seed + 11:
        '''发送数据结构：[seq(2), syn(1), fin(1)]'''
        resend_times["send"] += 1
        udp_socket.sendto(
            b''.join([seq.to_bytes(2), int(0).to_bytes(), fin.to_bytes()]), address)

        # 记录发送时间
        rtt_map[seq] = time.time()
        seq += 1  # 下一个数据

        # 开始计时器
        timeout = Timer(0.1, resend_data, (seq, address, 0,
                        timer_map, rtt_map, resend_times, rtt_map[seq-1] + 0.1, udp_socket))
        timeout.start()

        # 记录计时器
        timer_map[seq] = timeout

    while True:
        # 接收 ack 返回
        message, address = udp_socket.recvfrom(2048)
        recv_seq = int.from_bytes(message[0: 2])

        # 计算 rtt
        rtt = time.time() - rtt_map[recv_seq]

        # 打印 信息
        print(recv_seq, address[0], ":", address[1], rtt)

        # 更新接受窗口，值为 rtt
        if window.get(recv_seq) == None:
            window[recv_seq] = rtt
            # 解除计时器
            if timer_map.get(recv_seq) != None:
                timer_map[recv_seq].cancel()
                timer_map.pop(recv_seq)

        # 窗口满了，开始挥手断开连接
        if len(window) == 12:
            while True:
                fin = 1
                print("四次挥手开始...")
                print("第一次挥手...")
                udp_socket.sendto(
                    b''.join([(seed + 50).to_bytes(2), int(0).to_bytes(), fin.to_bytes()]), address)
                print("第二次挥手...")
                message, _ = udp_socket.recvfrom(2048)
                recv_seq = int.from_bytes(message[0: 2])
                if recv_seq == seed + 50:
                    print("第三次挥手...")
                    message, _ = udp_socket.recvfrom(2048)
                    recv_seq = int.from_bytes(message[0: 2])
                    fin = int(message[3])

                    if recv_seq == seed + 51 and fin == 1:
                        udp_socket.sendto(
                            b''.join([(seed + 51).to_bytes(2), int(0).to_bytes(), (0).to_bytes()]), address)
                        print("四次挥手成功...")
                        udp_socket.close()
                        print("断开连接...")
                        break
                    else:
                        print("挥手失败, 重新挥手...")
                else:
                    print("挥手失败, 重新挥手...")
            # 输出总体信息
            output_infomation(window, resend_times["send"])
            return None


def output_infomation(window, times):
    print("共接收到的数据分组：", len(window))
    print("共发送的数据分组：", times)
    print("丢包率：", 100 * (1 - (len(window) / times)), "%")

    avgs = 0
    for value in window.values():
        avgs += value
    avgs /= len(window)

    deviation = 0
    for i in window.values():
        deviation += (i-avgs)**2
    deviation = math.sqrt(deviation/len(window))

    print("最大rtt:", max(window.values()), "最小rtt:",
          min(window.values()), "平均 rtt:", avgs, "rtt 标准差：", deviation)
    return None


def resend_data(seq, address, times, timer_map, rtt_map, resend_times, _time, udp_socket=socket.socket()):
    '''resend data in timer thread.'''

    if times == 2:
        print(seq, "已经重传两次了...")
        return None
    try:
        udp_socket.sendto(
            b''.join([seq.to_bytes(2), int(0).to_bytes(), (0).to_bytes()]), address)
        resend_times["send"] += 1

        rtt_map[seq] = _time

        timeout = Timer(0.1, resend_data,
                        (seq, address, times + 1, timer_map, rtt_map, resend_times, _time + 0.18, udp_socket))
        timer_map[seq] = timeout

        timeout.start()
    except Exception:
        return None
    return None


main()
