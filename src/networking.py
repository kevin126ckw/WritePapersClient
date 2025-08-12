#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : networking.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
import socket
import json
import queue
import paperlib as lib
import structlog
import sys

"""
    网络部分的模块
    一个标准的客户端数据包应该是json格式，具体这样的：
    {
        "type": "类型",
        "token": "TEMP_TOKEN_NEED_CHANGE", //暂时这样，以后再改成单次登录由服务端发回的一次性token,登录时token为"LOGIN"
        "payload": {
            "key":"value"
        }
    }

    服务端数据包应去除token,格式如下
    {
        "type": "类型",
        "payload": {
            "key":"value"
        }
    }
    --------------------------------------------------------------------------------------------------------------------
    以下为不同类型的数据包格式
    模板：
    {
        "type": "类型",
        "token": "TEMP_TOKEN_NEED_CHANGE",
        "payload": {
            "key":"value"
        }
    }
    客户端收到的新消息（S2C）：
    {
        "type": "new_message",
        "payload": {
            "from_user": 0,
            "message": "Hello, World!"
        }
    }
    客户端发送消息（C2S）:
    {
        "type": "send_message",
        "token": "TEMP_TOKEN_NEED_CHANGE",
        "payload":{
            "to_user": 0,
            "message": "Hello!"
        }
    }
"""


def get_logger():
    return structlog.get_logger()


logger = get_logger()
temp_xml_dir = "data/"


class ClientNetwork:
    def __init__(self):
        self.is_debug = None
        self.token = None
        self.server_host = lib.read_xml("server/ip", temp_xml_dir)
        try:
            self.server_port = int(lib.read_xml("server/port", temp_xml_dir))
        except (TypeError, ValueError):
            logger.warning("配置文件中的端口无效，正在使用默认端口3624")
            self.server_port = 3624

        self.message_queue = queue.Queue()
        self.return_queue = queue.Queue()
        self.offline_message_queue = queue.Queue()
        self.friend_token_queue = queue.Queue()
        self.welcome_back_queue = queue.Queue()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.connect((self.server_host, self.server_port))
        except ConnectionRefusedError:
            logger.critical("无法连接到服务器")
            sys.exit(1)
        if self.sock:
            logger.info("成功连接到服务器")

    def send_packet(self, message_type, payload, token=None):
        if message_type == "login":
            token = "LOGIN"
        if token is None:
            token = self.token
        packet = {
            "type": message_type,
            "token": token,
            "payload": payload
        }
        packet = json.dumps(packet)
        packet_bytes = packet.encode("utf-8")
        # 发送4字节的数据长度
        length = len(packet_bytes)
        length_bytes = length.to_bytes(4, byteorder='big')
        try:
            self.sock.sendall(length_bytes)
            # 发送实际数据
            self.sock.sendall(packet_bytes)
            if self.is_debug():
                logger.debug(f"发送数据{packet}成功")
        except ConnectionResetError:
            logger.error("服务器已断开连接")
            sys.exit(1)
        except BrokenPipeError:
            logger.error("服务器已断开连接")
            sys.exit(1)

    def receive_packet(self):
        """
        接收消息用的线程
        :return None
        """
        try:
            while True:
                """
                通过消息前4字节的数据来接收完整数据包
                """
                # 先接收4字节的数据长度
                length_bytes = self.sock.recv(4)
                if not length_bytes:
                    continue

                # 解析数据长度
                data_length = int.from_bytes(length_bytes, byteorder='big')

                # 接收实际数据
                buffer = b''
                while len(buffer) < data_length:
                    remaining = data_length - len(buffer)
                    chunk = self.sock.recv(min(1024, remaining))
                    if not chunk:
                        break
                    buffer += chunk

                if len(buffer) != data_length:
                    logger.warning(f"接收到的数据长度不匹配：预期{data_length}字节，实际接收{len(buffer)}字节")
                    continue

                try:
                    raw_msg = buffer.decode("utf-8")
                except UnicodeDecodeError as e:
                    logger.warning(f"UTF-8解码失败: {e}")
                    continue

                # 此时已获取到一个完整的数据包
                try:
                    msg = json.loads(raw_msg)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析失败: {e}, 数据内容: {raw_msg}")
                    continue
                # 调试 打印消息
                if self.is_debug():
                    logger.debug("收到消息:" + raw_msg)

                if msg["type"].endswith("result") or msg["type"].endswith("return"):
                    # 某些函数需要的返回值
                    if msg["type"] == "friend_token_result":
                        self.friend_token_queue.put(msg)
                        continue
                    self.return_queue.put(msg)
                    continue
                match msg["type"]:
                    case "new_message":
                        # 正常私聊消息
                        self.message_queue.put(msg)

                    case "server_hello":
                        # Hello
                        logger.critical("服务器给你发了个Hello!")
                    case "heartbeat":
                        if self.is_debug():
                            logger.debug("收到心跳包，正在回复")
                        self.send_packet("heartbeat", {"content": "Health check received."})
                    case "offline_messages":
                        # 离线消息
                        """for message in msg["payload"]:
                            logger.debug(f"收到离线消息: {message[1]}:{message[0]}")"""
                        for message in msg["payload"]:
                            self.offline_message_queue.put(message)
                    case "welcome_back":
                        # 上线
                        self.welcome_back_queue.put(msg)
                    case _:
                        # 未知消息
                        logger.warning(f"收到未知消息类型: {msg['type']}, full content:{msg}")
                # process_message(self)

        except BrokenPipeError:
            logger.warning("服务器已断开连接")
            sys.exit(1)
        except ConnectionResetError:
            logger.warning("服务器已断开连接")
            sys.exit(1)
        except ConnectionError:
            logger.warning("服务器已断开连接")
            sys.exit(1)


if __name__ == '__main__':
    """调试"""
    logger = structlog.get_logger()
    net = ClientNetwork()
    logger.debug(net)
