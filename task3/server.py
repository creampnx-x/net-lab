import socket
from threading import Thread


def main():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    bind_port = 12000 # int(input("需要服务的端口号: "))
    tcp_socket.bind(('', bind_port))
    tcp_socket.listen(100)
    while True:
        try:
            new_socket, address = tcp_socket.accept()
            print("start thread:", address)
            thread = Thread(target=deal_request, args=(new_socket, address))
            thread.start()
        except:
            print("close all.")
            tcp_socket.close()


def deal_request(tcp_socket=socket.socket(), _=('', 12000)):
    while True:
        try:
            block = tcp_socket.recv(1024)
            if len(block) == 0:
                break

            requst_type = int.from_bytes(block[0: 2])
            print("accept data.")
            if requst_type == 1:
                '''agree response.'''
                print("type: agree")
                N = int.from_bytes(block[2: 6])
                tcp_socket.send((2).to_bytes(2))
            elif requst_type == 3:
                '''reverse response.'''
                print("type: data")
                length = int.from_bytes(block[2: 6])
                data = block[6: 6 + length].decode()

                reverse_data = b''.join([
                    (4).to_bytes(2),  # type = 4
                    block[2: 6],  # length = length
                    ''.join(reversed(data)).encode()  # data = reverse(data)
                ])
                print("send reverse data.")
                tcp_socket.send(reverse_data)
        except Exception as e:
            print(e)
            break
    print("close link.")
    tcp_socket.close()
    return None

main()
