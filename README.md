# net-lab

## 基础

使用`python`编写的socket通信程序，项目无需安装多余依赖，原生std即可运行。

## 实现编码

### 字节编码

使用如下代码进行组织字节流：

```python
bytesStream = b''.join([int(1).to_bytes(2)])
```

值得注意的点：

1. 使用 `b''` 进行初始化`bytes`字节数组，也可使用 `bytes()`来初始化，不过更推荐前者，因为其是原始值而不是引用的对象。
2. 使用 `.join([])` 来组织字节流，在 `[]` 中按顺序放置需要添加的字节流。
3. 对于 `int` 使用`int(number).to_bytes(length)`来组织字节长度，默认为最短字节数。
4. 对于 `str` 使用`''.encode()`来组织长度，因为一个`char`即一个字节所以 `len('')` 即为`bytes` 的长度。

### 字节解码

使用如下代码进行解码：

```python
'''对于有长度的int:'''
seq_number = int.from_bytes(bytesStream[0: 2])

'''对于长度为1的int, 字节数字取值即为int:'''
fin = bytesStream[2]

'''对于str:'''
block = bytesStream[6: 6 + length].decode()
```

值得注意的点：

1. 字节流解码需和编码对应，长度应该协调
2. 字节数组切片需要注意offset与长度，防止丢值或越界

## 实现重传

### 创建计时器线程

使用如下接口，从线程中添加一个计时器：

```python
from threading import Timer

timeout = Timer(0.1, resend_data, (...args))

timeout.start()
timer_map[seq] = timeout
```

注意：`resend_data` 是个重传函数，`...args`是重传函数的参数，执行时间是0.1s（100ms），创建计时器的时机在数据发送之后，创建计时器线程后立即开始计时，同时将计时器记录在案（字典中），此时进行下一个数据包的转发。

### 取消重传

当接收到`server`返回的`ack`时，使用字典中的`timer`进行停止：

```python
timer_map[seq].cancel()
```

### 进行重传

执行重传无非就是将数据重新发送一遍，有如下实现细节：

1. 重传数据
2. 记录发送时间重算rtt
3. 重新启动一个timer线程进行第二次重传
4. 记录timer到字典中
5. 递归学习重传次数，大于两次进行报错

## 抛弃冗余

服务端可能接受多个相同 seq 的请求，避免碰撞就是使用hash表来存放收到的数据，直到 client 发送`fin`标志。

## 文件分块

### 文件读写

python极为友好的读取文件方式：

```python
file_to_send = open('file_path.txt', 'r')
content = file_to_send.read()

file_to_write = open('file_path.txt', 'w')
file_to_write.write('')
```

### 随机分块

使用：

```python
import random

block_size = random.randint(low, height)
```

获取在`[low, height]`范围内的随机分块的大小。使用size对文件content进行切分，然后进行字节编码使用tcp发送到服务端。

> 注意：切分时注意最后一块的大小。

### 分块拼接

将返回按顺序逆序存放（压到数组头上，压栈操作）。

> 注意：可以发送一个收一个，也可以发一组收一组。但必须注意客户端接收缓存，以避免接收到的数据因为没有及时处理而被抛弃。

## 防止阻塞

我的实现是使用多线程进行处理并发请求，文档中所说的 select 等都是建立在单进程单线程的轮询机制，其在执行上是流水线的异步操作。
