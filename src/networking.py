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

        self.server_host = lib.read_xml("server/ip", temp_xml_dir)
        try:
            self.server_port = int(lib.read_xml("server/port", temp_xml_dir))
        except (TypeError, ValueError):
            logger.warning("配置文件中的端口无效，正在使用默认端口3624")
            self.server_port = 3624

        self.message_queue = queue.Queue()
        self.return_queue = queue.Queue()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_host, self.server_port))
        if self.sock:
            logger.debug("成功连接到服务器")

    def send_packet(self, message_type, payload, token="TEMP_TOKEN_NEED_CHANGE"):
        if message_type == "login":
            token = "LOGIN"
        packet = {
            "type": message_type,
            "token": token,
            "payload": payload
        }
        packet = json.dumps(packet) + "\n"
        self.sock.sendall(packet.encode("utf-8"))

    def receive_packet(self):
        """
        接收消息用的线程
        :return None
        """
        while True:
            """
            通过\n作为结尾为条件来接收完整数据包
            """
            buffer = ""
            packet = self.sock.recv(1024).decode("utf-8")
            if not packet:
                continue
            buffer += packet
            while '\n' in buffer:
                raw_msg, buffer = buffer.split('\n', 1)
                if not raw_msg.strip():
                    continue
                #此时已获取到一个完整的数据包
                try:
                    msg = json.loads(raw_msg)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析失败: {e}, 数据内容: {raw_msg}")
                    continue
                # 调试 打印消息
                logger.debug("收到消息:" + raw_msg)
                if msg["type"] == "new_message":
                    # 正常私聊消息
                    self.message_queue.put(msg)
                elif msg["type"].endswith("result") or msg["type"].endswith("return"):
                    # 某些函数需要的返回值
                    self.return_queue.put(msg)
                elif msg["type"] == "server_hello":
                    # Hello
                    logger.critical("服务器给你发了个Hello!")
                elif msg["type"] == "heartbeat":
                    logger.debug("收到心跳包，正在回复")
                    self.send_packet("heartbeat", {"content": "Health check received."})
                else:
                    # 未知消息
                    logger.warning(f"收到未知消息类型: {msg['type']}, full content:{msg}")


if __name__ == '__main__':
    """调试"""
    logger = structlog.get_logger()
    net = ClientNetwork()
    logger.debug(net)
