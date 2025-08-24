# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : networking.py
# @Software: PyCharm
# @Desc    : WritePapers客户端网络通信模块
# @Author  : Kevin Chang

"""WritePapers客户端网络通信模块。

本模块包含客户端的网络通信功能，包括数据包发送接收、消息队列管理等。
"""

import json
import queue
import socket
import sys
from typing import Any, Callable, Dict, Optional

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


def get_logger() -> structlog.BoundLogger:
    """获取结构化日志记录器。

    Returns:
        :return 结构化日志记录器实例
    """
    return structlog.get_logger()


logger = get_logger()
temp_xml_dir = "data/"


class ClientNetwork:
    """WritePapers客户端网络通信类。
    
    负责管理客户端与服务器之间的网络通信，包括连接管理、数据包收发、消息队列等。
    """
    
    def __init__(self) -> None:
        """初始化客户端网络连接。

        Returns:
            :return 无返回值
        """
        # 回调函数和配置
        self.is_debug: Optional[Callable[[], bool]] = None
        self.token: Optional[str] = None
        
        # 服务器配置
        self.server_host: str = lib.read_xml("server/ip", temp_xml_dir) or "127.0.0.1"
        try:
            port_str = lib.read_xml("server/port", temp_xml_dir)
            self.server_port: int = int(port_str) if port_str else 3624
        except (TypeError, ValueError):
            logger.warning("配置文件中的端口无效，正在使用默认端口3624")
            self.server_port = 3624

        # 消息队列
        self.message_queue: queue.Queue = queue.Queue()
        self.return_queue: queue.Queue = queue.Queue()
        self.offline_message_queue: queue.Queue = queue.Queue()
        self.friend_token_queue: queue.Queue = queue.Queue()
        self.welcome_back_queue: queue.Queue = queue.Queue()

        # 网络连接
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.connect((self.server_host, self.server_port))
            logger.info("成功连接到服务器")
        except ConnectionRefusedError:
            logger.critical("无法连接到服务器")
            sys.exit(1)

    def send_packet(self, message_type: str, payload: Dict[str, Any], token: Optional[str] = None) -> None:
        """发送数据包到服务器。
        
        Args:
            :param message_type: 消息类型
            :param payload: 消息载荷数据
            :param token: 认证令牌
            
        Returns:
            :return 无返回值
        """
        if message_type == "login":
            token = "LOGIN"
        if token is None:
            token = self.token
            
        packet_data = {
            "type": message_type,
            "token": token,
            "payload": payload
        }
        
        try:
            packet_json = json.dumps(packet_data)
            packet_bytes = packet_json.encode("utf-8")
            
            # 发送4字节的数据长度
            length = len(packet_bytes)
            length_bytes = length.to_bytes(4, byteorder='big')
            
            self.sock.sendall(length_bytes)
            # 发送实际数据
            self.sock.sendall(packet_bytes)
            
            if self.is_debug and self.is_debug():
                logger.debug(f"发送数据{packet_json}成功")
                
        except (ConnectionResetError, BrokenPipeError) as e:
            logger.error(f"服务器连接错误: {e}")
            sys.exit(1)
        except UnicodeEncodeError as e:
            logger.error(f"数据编码错误: {e}")
        except Exception as e:
            logger.error(f"发送数据包时发生未知错误: {e}")

    def receive_packet(self) -> None:
        """接收消息的线程主循环。

        Returns:
            :return 无返回值
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
                if self.is_debug and self.is_debug():
                    logger.debug("收到消息:" + raw_msg)
                
                # 处理消息
                self._handle_received_message(msg)

        except (BrokenPipeError, ConnectionResetError, ConnectionError) as e:
            logger.warning(f"服务器连接断开: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"接收消息时发生未知错误: {e}")
            sys.exit(1)
    
    def _handle_received_message(self, msg: Dict[str, Any]) -> None:
        """处理接收到的消息。
        
        Args:
            :param msg: 接收到的消息字典
            
        Returns:
            :return 无返回值
        """
        msg_type = msg.get("type", "")
        
        if msg_type.endswith("result") or msg_type.endswith("return"):
            # 某些函数需要的返回值
            if msg_type == "friend_token_result":
                self.friend_token_queue.put(msg)
                return
            self.return_queue.put(msg)
            return
            
        # 处理不同类型的消息
        message_handlers = {
            "new_message": lambda m: self.message_queue.put(m),
            "server_hello": lambda m: logger.critical("服务器给你发了个Hello!"),
            "heartbeat": self._handle_heartbeat,
            "offline_messages": self._handle_offline_messages,
            "welcome_back": lambda m: self.welcome_back_queue.put(m)
        }
        
        handler = message_handlers.get(msg_type)
        if handler:
            handler(msg)
        else:
            logger.warning(f"收到未知消息类型: {msg_type}, full content:{msg}")
    
    def _handle_heartbeat(self, msg: Dict[str, Any]) -> None:
        """处理心跳包。
        
        Args:
            :param msg: 心跳消息
            
        Returns:
            :return 无返回值
        """
        if self.is_debug and self.is_debug():
            logger.debug("收到心跳包，正在回复")
        self.send_packet("heartbeat", {"content": "Health check received."})
    
    def _handle_offline_messages(self, msg: Dict[str, Any]) -> None:
        """处理离线消息。
        
        Args:
            :param msg: 离线消息
            
        Returns:
            :return 无返回值
        """
        payload = msg.get("payload", [])
        for message in payload:
            self.offline_message_queue.put(message)


if __name__ == '__main__':
    """调试"""
    logger = structlog.get_logger()
    net = ClientNetwork()
    logger.debug(net)
