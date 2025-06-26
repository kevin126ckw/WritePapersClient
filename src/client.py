#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : client.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
# import json
# import queue
import sys
import threading
# import tkinter as tk
# import traceback
import time
# import database
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


def _handle_chat_message(payload):
    """
    处理聊天消息
    :return None
    """
    from_user = payload['from_user']
    message_content = str(payload['message'])
    logger.info(f"{from_user}: {message_content}")

def process_message(net_module):
    time.sleep(1) # 为了避免程序退出
    """
    处理消息队列
    :return None        
    """
    # 普通消息
    while not net_module.message_queue.empty():
        msg = net_module.message_queue.get_nowait()
        _handle_chat_message(msg['payload'])
    # 未完待续

def main():
    """
    测试客户端
    Returns:
        :return None
    """
    global net

    username = "test"
    password = "password"

    logger.info("正在启动客户端...")
    receive_thread = threading.Thread(target=net.receive_packet, daemon=True)
    receive_thread.start()
    # 调试登录
    net.send_packet("login", {"username": username, "password": password})
    # 调试消息转发
    # to_user需更改为UID,待改
    net.send_packet("send_message", {"to_user": username, "message": "Hello!"})

if __name__ == "__main__":
    try:
        main()
        while True:
            process_message(net)
    except KeyboardInterrupt:
        logger.info("正在退出...")
        sys.exit(0)
