#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : client.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
# import json
# import queue
import datetime
import socket
import sys
import threading
import time
import tkinter as tk
# import traceback
# import time
import database
# from tkinter import ttk, messagebox
# import darkdetect
# import sv_ttk
import structlog
import networking
# from plyer import notification
import paperlib as lib
from ui import GUI
from login_ui import LoginUI

uid = NotImplemented
login_ui_class = NotImplemented
login_root = NotImplemented
root = NotImplemented
gui = NotImplemented

logged_in = False

logger = structlog.get_logger()

net = networking.ClientNetwork()
net.is_debug = lambda : is_debug()
db = database.Database()


def is_debug():
    #return True
    if lib.read_xml("debug/enabled") == "true" or lib.read_xml("debug/enabled") == "True":
        return True
    else:
        return False

def _handle_chat_message(payload):
    """
    处理聊天消息
    :return None
    """
    global gui
    from_user = payload['from_user']
    send_time = payload['time']
    message_content = str(payload['message'])
    db.save_chat_message(from_user, uid, message_content, send_time)
    if gui.current_chat['id'] == int(from_user):
        gui.display_message(
            {"content":message_content, "time":time.strftime("%H:%M", time.localtime(send_time)), "type":"received", "sender":db.get_mem_by_uid(from_user)})
    logger.info(f"{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(send_time))} {db.get_mem_by_uid(from_user)}: {message_content}")
    update_contacts()

def process_message(net_module):
    """
    处理消息队列
    :return None        
    """
    global login_root, login_ui_class, logged_in

    # 离线消息
    while not net_module.offline_message_queue.empty():
        msg = net_module.offline_message_queue.get_nowait()
        if is_debug():
            logger.debug(f"离线消息：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg[3]))} {db.get_mem_by_uid(msg[1])}:{msg[0]}")
        db.save_chat_message(msg[1], msg[2], msg[0], msg[3])
        if gui.scrollable_frame is not None:
            update_contacts()
        else:
            gui.root.after(1, lambda: update_contacts())
            if is_debug():
                logger.debug("GUI未初始化，1000ms后尝试更新联系人")

    # 普通消息
    while not net_module.message_queue.empty():
        msg = net_module.message_queue.get_nowait()
        _handle_chat_message(msg['payload'])
    # 返回值
    while not net_module.return_queue.empty():
        msg = net_module.return_queue.get_nowait()
        """
        以下代码转移到networking.py的line 155了
        if msg['type'] == 'login_result':
            if msg['payload']['success']:
                logger.info("登录成功")
            else:
                logger.info("登录失败")
        """
        if msg['type'] == 'send_message_result':
            if msg['payload']['success']:
                logger.info("发送成功")
            else:
                logger.info("发送失败")
        elif msg['type'] == 'register_result':
            if msg['payload']['success']:
                logger.info("注册成功")
                lib.write_xml("account/username", msg['payload']['username'])
                lib.write_xml("account/password", msg['payload']['password'])
                lib.write_xml("account/uid", msg['payload']['uid'])
            else:
                logger.error("注册失败")
        elif msg['type'] == "login_result":
            if msg['payload']['success']:
                logger.info("登录成功")
                logged_in = True
                #login_ui_class.need_destroy = True
                login_ui_class.root.after(0, lambda: login_ui_class.login_success())
                if is_debug():
                    logger.debug("窗口销毁")
            else:
                logger.error("登录失败")
                logged_in = False
                # logger.debug("窗口销毁")


    # 未完待续

def validate_login(username, password):
    global login_ui_class
    net.send_packet("login", {"username": username, "password": password})
    return True

def load_messages(contact, display_message):
    """
    加载消息
    Params:
        :param contact: 当前选中的联系人
        :param display_message: 显示消息的函数
    Returns:
        :return: None
    """
    global uid
    if uid is None:
        logger.critical("未知的UID,请检查你是否登录了")
        uid = 0
    messages = db.select_sql("chat_history", "*", f"to_user={contact["id"]} or from_user={contact["id"]}")

    for msg in messages:
        if is_debug():
            logger.debug(f"正在加载消息：{msg}")# (1, 0, 0, 'text', 'hi', 1745813243.4815726)
        if int(msg[1]) == int(uid):
            display_message(
                {"content":msg[4], "time":time.strftime("%H:%M", time.localtime(msg[5])), "type":"sent", "sender":"我"})
        elif int(msg[2]) == int(uid):
            display_message(
                {"content":msg[4], "time":time.strftime("%H:%M", time.localtime(msg[5])), "type":"received", "sender":db.get_mem_by_uid(msg[1])})
        else:
            logger.error("未知消息")
            display_message(
                {"content": msg[4], "time": time.strftime("%H:%M", time.localtime(msg[5])), "type": "sent"})

def send_message(gui, contact):
    """
    发送消息
    Params:
        :param gui: gui类
        :param contact: 当前选中的联系人
    Returns:
        :return: None
    """
    content = gui.text_input.get("1.0", tk.END).strip()
    if not content:
        return

    current_time = datetime.datetime.now().strftime("%H:%M")

    message = {"content":content, "time":current_time, "type":"sent", "sender":"我"}

    # 添加到消息记录
    net.send_packet("send_message", {"to_user": str(contact["id"]), "message": content})
    db.save_chat_message(uid, contact["id"], content, time.time())

    # 显示消息
    gui.display_message(message)

    # 清空输入框
    gui.text_input.delete("1.0", tk.END)

    update_contacts()

def process_message_thread():
    while True:
        if not net.message_queue.empty() or not net.return_queue.empty() or not net.offline_message_queue.empty():
            process_message(net)
        else:
            time.sleep(0.1)

def login(username, password):
    net.send_packet("login", {"username": username, "password": password})

def update_contacts():
    contacts = []
    for contact in db.select_sql("contact", "mem, id"):
        last_message = db.get_last_chat_message(uid, contact[1])
        contacts.append({"name": contact[0], "id": contact[1], "avatar": "👨", "last_msg": last_message[0][4],
                         "time": time.strftime("%H:%M", time.localtime(last_message[0][5]))})
    gui.contacts = contacts
    gui.load_contacts()

def main():
    """
    测试客户端
    Returns:
        :return None
    """
    global net, db, uid, root, login_ui_class, login_root, logged_in, gui

    answer = None
    # username = "admin"
    # password = "admin"
    # uid = 0
    if is_debug():
        logger.debug("调试模式已开启")
        answer = input("是否从xml读取用户信息？(y/n)")
        if answer == "y" or answer == "":
            username = lib.read_xml("account/username", "data/")
            password = lib.read_xml("account/password", "data/")
            uid = lib.read_xml("account/uid", "data/")

        else:
            username = input("请输入用户名：")
            password = input("请输入密码：")
            uid = input("请输入用户ID：")

    else:
        username = lib.read_xml("account/username", "data/")
        password = lib.read_xml("account/password", "data/")
        uid = lib.read_xml("account/uid", "data/")

    logger.info("正在启动客户端...")
    db.connect(lib.read_xml("database/file", "data/"))
    contacts = []
    for contact in db.select_sql("contact", "mem, id"):
        last_message = db.get_last_chat_message(uid, contact[1])
        contacts.append({"name": contact[0], "id":contact[1] ,"avatar": "👨", "last_msg": f"{last_message[0][4]}" + " " * (50-len(last_message[0][4])), "time": time.strftime("%H:%M", time.localtime(last_message[0][5]))})

    main_receive_thread = threading.Thread(target=net.receive_packet, daemon=True)
    main_receive_thread.start()

    threading.Thread(target=process_message_thread, daemon=True).start()

    login_root = tk.Tk()
    login_ui_class = LoginUI(login_root)
    login_ui_class.validate_login_handler = lambda username_var, password_var: validate_login(username_var, password_var)
    if is_debug():
        if answer == "y" or answer == "":
            login_ui_class.username_entry.delete('0', tk.END)
            login_ui_class.username_entry.insert(string=username, index=0)
            login_ui_class.password_entry.delete('0', tk.END)
            login_ui_class.password_entry.insert(string=password, index=0)
    else:
        login_ui_class.username_entry.delete('0', tk.END)
        login_ui_class.username_entry.insert(string=username, index=0)
        login_ui_class.password_entry.delete('0', tk.END)
        login_ui_class.password_entry.insert(string=password, index=0)
    login_root.mainloop()


    if not logged_in:
        logger.critical("登录失败")
        return
    root = tk.Tk()
    gui = GUI(root, load_messages)
    gui.send_message_handler = lambda contact_: send_message(gui, contact_)
    gui.contacts = contacts


    # 登录
    # net.send_packet("login", {"username": username, "password": password})
    # 调试消息转发
    # net.send_packet("send_message", {"to_user": str(uid), "message": "Hello, World!"})
    # 获取离线消息
    net.send_packet("get_offline_messages", {"1": str(1)})

    gui.setup_window()
    gui.setup_styles()
    gui.create_ui()
    gui.username_label = tk.Label(gui.user_frame, text=username, font=gui.fonts['small'],
                                  bg=gui.colors['primary'], fg='white')
    gui.username_label.pack(pady=(5, 0))
    gui.setup_bindings()
    gui.load_contacts()
    # threading.Thread(target=root.mainloop, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    # global root
    try:
        if is_debug():
            result = input("请按回车键启动客户端...")
            if result == "":
                main()
            elif result == "reg":
                logger.info("正在启动客户端(test reg ver)...")
                db.connect("data/client.sqlite")

                receive_thread = threading.Thread(target=net.receive_packet, daemon=True)
                receive_thread.start()

                threading.Thread(target=process_message_thread, daemon=True).start()

                net.send_packet("register_account", {"username": input("username:"), "password": input("password:")})

                while True:
                    time.sleep(1)
        else:
            main()
    except ConnectionResetError:
        logger.warning("服务器已断开连接")
    except KeyboardInterrupt:
        logger.info("正在退出...")
        if root is not NotImplemented:
            root.destroy()
        if db.conn is not None:
            db.close()
        if net is not NotImplemented:
            net.sock.shutdown(socket.SHUT_RD)
            net.sock.close()
        sys.exit(0)
