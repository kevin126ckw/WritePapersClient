#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : client.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
# import json
# import queue
import socket
import sys
import threading
import time

# import tkinter as tk
# import traceback
# import time
import database
# from tkinter import ttk, messagebox
# import darkdetect
# import sv_ttk
import structlog
import networking
# from plyer import notification
# from paperlib import *

# from GUI import GUI


logger = structlog.get_logger()

net = networking.ClientNetwork()
db = database.Database()


def _handle_chat_message(payload):
    """
    处理聊天消息
    :return None
    """
    from_user = payload['from_user']
    send_time = payload['time']
    message_content = str(payload['message'])
    logger.info(f"{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(send_time))} {db.get_mem_by_uid(from_user)}: {message_content}")

def process_message(net_module):
    # time.sleep(1) # 为了避免程序退出
    """
    处理消息队列
    :return None        
    """

    # 离线消息
    while not net_module.offline_message_queue.empty():
        msg = net_module.offline_message_queue.get_nowait()
        logger.debug(f"离线消息：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg[3]))} {db.get_mem_by_uid(msg[1])}:{msg[0]}")
    # 普通消息
    while not net_module.message_queue.empty():
        msg = net_module.message_queue.get_nowait()
        _handle_chat_message(msg['payload'])
    # 返回值
    while not net_module.return_queue.empty():
        msg = net_module.return_queue.get_nowait()
        if msg['type'] == 'login_result':
            if msg['payload']['success']:
                logger.info("登录成功")
            else:
                logger.info("登录失败")
        elif msg['type'] == 'send_message_result':
            if msg['payload']['success']:
                logger.info("发送成功")
            else:
                logger.info("发送失败")

    # 未完待续

def main():
    """
    测试客户端
    Returns:
        :return None
    """
    global net, db

    username = "admin"
    password = "admin"
    uid = 0

    logger.info("正在启动客户端...")
    db.connect("data/client.sqlite")
    receive_thread = threading.Thread(target=net.receive_packet, daemon=True)
    receive_thread.start()

    # 登录
    net.send_packet("login", {"username": username, "password": password})
    # 调试消息转发
    net.send_packet("send_message", {"to_user": str(uid), "message": "Hello, World!"})
    # 调试离线消息
    net.send_packet("get_offline_messages", {"uid": str(uid)})


if __name__ == "__main__":
    try:
        main()
        while True:
            process_message(net)
    except ConnectionResetError:
        logger.warning("服务器已断开连接")
    except KeyboardInterrupt:
        logger.info("正在退出...")
        db.close()
        net.sock.shutdown(socket.SHUT_RD)
        net.sock.close()
        sys.exit(0)
