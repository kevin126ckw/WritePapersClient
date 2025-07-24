#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : client.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
# import json
# import queue
import _tkinter
import datetime
import socket
import sys
import threading
import time
import base64
import tkinter as tk
import tkinter.filedialog
import os
from tkinter import messagebox

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
from reg_ui import RegisterUI
from settings_ui import SettingsDialog

uid = NotImplemented
username = NotImplemented
password = NotImplemented
login_ui_class = NotImplemented
login_root = NotImplemented
register_root = NotImplemented
register_class = NotImplemented
root = NotImplemented
gui = NotImplemented
msg_uid = NotImplemented

logged_in = False

logger = structlog.get_logger()

net = networking.ClientNetwork()
net.is_debug = lambda : is_debug()
db = database.Database()

server_ip = lib.read_xml("server/ip")
server_port = lib.read_xml("server/port")
if not server_ip:
    logger.warning("未配置服务器地址，尝试本地服务器")
    server_ip = "127.0.0.1"
if not server_port:
    logger.warning("未配置服务器端口，尝试默认端口")
    server_port = "3624"

settings_config = [
    {"name": "server", "label": "服务器地址", "type": "text", "default": server_ip},
    {"name": "port", "label": "端口号", "type": "text", "default": server_port},
    {"name": "friend_token", "label": "好友口令", "type": "text", "default": "12345678"}
    ]

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
    message_type = payload['type']
    message_content = str(payload['message'])
    db.save_chat_message(from_user, uid, message_content, send_time, message_type)
    if gui.current_chat:
        if gui.current_chat['id'] == int(from_user):
            gui.display_message(
                {"content":message_content, "time":time.strftime("%H:%M", time.localtime(send_time)), "status":"received", "sender":db.get_mem_by_uid(from_user), "type": message_type})
    if "need_update_contact" in payload:
        logger.debug("need_update_contact存在")
        if not payload['need_update_contact']:
            logger.debug("不需要更新联系人")
            return
    if message_type == "text":
        logger.info(f"{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(send_time))} {db.get_mem_by_uid(from_user)}: {message_content}")
    else:
        logger.info(f"{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(send_time))} {db.get_mem_by_uid(from_user)}: [图片]")
    if is_debug():
        logger.debug(f"新消息payload:{payload}")
    update_contacts()

def process_message(net_module):
    """
    处理消息队列
    :return None        
    """
    global login_root, login_ui_class, logged_in, register_class, uid, username, password, msg_uid

    # 离线消息
    while not net_module.offline_message_queue.empty():
        msg = net_module.offline_message_queue.get_nowait()
        logger.debug(f"离线消息：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg[3]))} {db.get_mem_by_uid(msg[1])}:{msg[0]}")
        db.save_chat_message(msg[1], msg[2], msg[0], msg[3])
        if gui.scrollable_frame is not None:
            update_contacts()
        else:
            gui.root.after(1, lambda: update_contacts())
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
        match msg['type']:
            case 'send_message_result':
                if msg['payload']['success']:
                    logger.info("发送成功")
                else:
                    logger.info("发送失败")
            case 'register_result':
                if msg['payload']['success']:
                    logger.info("注册成功")
                    lib.write_xml("account/username", msg['payload']['username'])
                    lib.write_xml("account/password", msg['payload']['password'])
                    lib.write_xml("account/uid", msg['payload']['uid'])
                    logger.debug(f"写入配置文件,username:{msg['payload']['username']}, password:{msg['payload']['password']}, uid:{msg['payload']['uid']}")
                    messagebox.showinfo("注册成功", f"恭喜您，注册成功！您的UID是{msg['payload']['uid']}\n请手动重新启动应用程序登录！")
                    # login(msg['payload']['username'], msg['payload']['password'])
                    # time.sleep(0.3)
                    register_class.root.after(3, register_class.root.destroy())
                else:
                    logger.error("注册失败")
                    messagebox.showerror("注册失败", "注册失败，请检查用户名是否已存在")
            case "login_result":
                if msg['payload']['success']:
                    logger.info("登录成功")
                    msg_uid = msg['payload']['uid']
                    logged_in = True
                    #login_ui_class.need_destroy = True
                    login_ui_class.root.after(0, lambda: login_ui_class.login_success())
                    logger.debug("窗口销毁")
                else:
                    logger.error("登录失败")
                    logged_in = False
                    tk.messagebox.showerror("错误", "登录失败")
                    # logger.debug("窗口销毁")
            case "add_friend_result":
                if msg['payload']['success']:
                    logger.info("添加好友成功")
                    db.save_contact(msg['payload']['friend_uid'],msg['payload']['friend_username'],msg['payload']['friend_name'], "")
                    messagebox.showinfo("添加好友成功", "添加好友成功")
                    gui.root.after(0, lambda: update_contacts())
                else:
                    logger.error("添加好友失败")
                    messagebox.showerror("添加好友失败", "添加好友失败")


    # 未完待续

def validate_login(login_username, login_password):
    global login_ui_class
    login(login_username, login_password)
    if login_ui_class.remember_var.get():
        if lib.read_xml("account/username") == login_username and lib.read_xml("account/password") == login_password:
            return True
        lib.write_xml("account/username", login_username)
        lib.write_xml("account/password", login_password)
        lib.write_xml("account/uid", uid)
        logger.debug(f"写入配置文件,username:{login_username}, password:{login_password}, uid:{uid}")
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
        logger.debug(f"正在加载消息：{msg}")# (1, 0, 0, 'text', 'hi', 1745813243.4815726)
        if int(msg[1]) == int(uid):
            display_message(
                {"content":msg[4], "time":time.strftime("%H:%M", time.localtime(msg[5])), "status":"sent", "sender":"我", 'type': msg[3]})
        elif int(msg[2]) == int(uid):
            display_message(
                {"content":msg[4], "time":time.strftime("%H:%M", time.localtime(msg[5])), "status":"received", "sender":db.get_mem_by_uid(msg[1]), 'type': msg[3]})
        else:
            logger.error("未知消息")
            display_message(
                {"content": msg[4], "time": time.strftime("%H:%M", time.localtime(msg[5])), "status": "sent", 'type': msg[3]})

def send_message(gui_class, contact):
    """
    发送消息
    Params:
        :param gui_class: gui类
        :param contact: 当前选中的联系人
    Returns:
        :return: None
    """
    content = gui_class.text_input.get("1.0", tk.END).strip()
    if not content:
        return

    current_time = datetime.datetime.now().strftime("%H:%M")

    message = {"content":content, "time":current_time, "status":"sent", "sender":"我", 'type': "text"}

    # 添加到消息记录
    net.send_packet("send_message", {"to_user": str(contact["id"]), "message": content, "type": "text"})
    db.save_chat_message(uid, contact["id"], content, time.time())

    # 显示消息
    gui_class.display_message(message)

    # 清空输入框
    gui_class.text_input.delete("1.0", tk.END)

    update_contacts()
def send_picture(gui_class, contact):
    current_time = datetime.datetime.now().strftime("%H:%M")
    image_path = tkinter.filedialog.askopenfilename()
    if image_path:
        if os.path.getsize(image_path) > 1024 * 1024 * 2:
            tk.messagebox.showerror("错误", "图片大小不能超过2MB")
            return
        with open(image_path,'rb') as image_file:
            image_data = image_file.read()
            image_file.close()
        if not image_data:
            tk.messagebox.showerror("错误", "请选择带有内容的图片")
            return
        message = {"content": image_data, "time": current_time, "status": "sent", "sender": "我", 'type': "image"}
        def _send_picture():
            # 添加到消息记录
            print("正在发送图片数据")
            net.send_packet("send_message", {"to_user": str(contact["id"]), "type": "image", "message": base64.b64encode(image_data).decode("utf-8")}) # image_data不加str会TypeError: Object of type bytes is not JSON serializable
            print("图片数据发送完成")
            db.save_chat_message(uid, contact["id"], image_data, time.time(), "image")

            # 显示消息
            gui_class.display_message(message)

            update_contacts()
        threading.Thread(target=_send_picture).start()
def process_message_thread():
    while True:
        if not net.message_queue.empty() or not net.return_queue.empty() or not net.offline_message_queue.empty():
            process_message(net)
        else:
            time.sleep(0.01)

def login(login_username, login_password):
    global username, password
    net.send_packet("login", {"username": login_username, "password": login_password})
    username = login_username
    password = login_password

def update_contacts():
    contacts = []
    for contact in db.select_sql("contact", "mem, id, name"):
        last_message = db.get_last_chat_message(uid, contact[1])
        logger.debug(f"正在更新联系人：{contact},last_message:{last_message}")
        if contact[0]:
            if last_message[3] == "text":
                contacts.append({"name": contact[0], "id": contact[1], "avatar": "👨", "last_msg": last_message[4],
                                 "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
            elif last_message[3] == "image":
                contacts.append({"name": contact[0], "id": contact[1], "avatar": "👨", "last_msg": "[图片]",
                                 "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
        else:
            if contact[2]:
                if last_message[3] == "text":
                    contacts.append({"name": contact[2], "id": contact[1], "avatar": "👨", "last_msg": last_message[4],
                                     "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
                elif last_message[3] == "image":
                    contacts.append(
                        {"name": contact[2], "id": contact[1], "avatar": "👨", "last_msg": "[图片]",
                         "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
            else:
                if last_message[3] == "text":
                    contacts.append({"name": "未知", "id": contact[1], "avatar": "👨", "last_msg": last_message[4],
                                     "time": time.localtime(last_message[5])
                    })
                elif last_message[3] == "image":
                    contacts.append(
                        {"name": "未知", "id": contact[1], "avatar": "👨", "last_msg": "[图片]",
                         "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
    gui.contacts = contacts
    gui.load_contacts()

def register_user_handler(window_class):
    logger.debug("注册用户")
    register_username = window_class.username_entry.get()
    register_password = window_class.password_entry.get()
    logger.debug(f"用户名:{register_username}, 密码:{password}")
    logger.debug(window_class.agree_terms_var.get())
    # 注册用户
    if not window_class.validate_all_fields():
        return

    if not window_class.agree_terms_var.get():
        messagebox.showerror("错误", "请先同意用户协议和隐私政策")
        return


    # 模拟注册过程
    # messagebox.showinfo("注册成功", "恭喜您，注册成功！\n系统将为您自动登录...")

    # 这里可以添加实际的注册逻辑
    # window_class.root.destroy()
    net.send_packet("register_account", {"username": register_username, "password": register_password})
def start_register():
    global register_root,register_class, login_ui_class
    logger.debug("开始注册")
    login_ui_class.root.after(0, lambda: login_ui_class.root.destroy())
    register_root = tk.Tk()
    register_class = RegisterUI(register_root)
    register_class.register_user_handler = lambda : register_user_handler(register_class)
    register_class.create_action_buttons(register_class.scrollable_frame)
    register_class.setup_bindings()
    register_root.mainloop()
    logger.debug("注册界面创建完毕")
def handle_add_friend(friend_id, verify_token):
    try:
        friend_uid = int(friend_id)
        if db.select_sql("contact", "id", f"id='{friend_uid}'"):
            tk.messagebox.showwarning("提示", f"{friend_id} 已经是你的好友了")
            return False
        net.send_packet("add_friend", {"friend_id_type": "uid", "friend_id": friend_uid, "verify_token": verify_token})
    except ValueError:
        friend_username = friend_id
        if db.select_sql("contact", "id", f"username='{friend_username}'"):
            tk.messagebox.showwarning("提示", f"{friend_id} 已经是你的好友了")
            return False
        net.send_packet("add_friend", {"friend_id_type": "username", "friend_id": friend_username, "verify_token": verify_token})
    return True
def check_database_uid():
    global msg_uid, uid
    if uid != msg_uid:
        uid = msg_uid
        if lib.read_xml("account/username") == username and lib.read_xml("account/password") == password:
            lib.write_xml("account/uid", uid)
        if db.get_metadata("uid") is None:
            db.insert_sql("meta", "uid", [uid])
        elif int(db.get_metadata("uid")) != int(msg_uid):
            tk.messagebox.showwarning("警告",
                                      f"数据库中保存的UID与当前登录的UID不一致，这可能不是你的数据库！\n数据库中的UID为{db.get_metadata('uid')}\n您登录的UID为{msg_uid}\n即将退出程序！")
            exit_program()
            return
def open_settings():
    """打开设置对话框的示例函数"""
    for config in settings_config:
        if config["name"] == "friend_token":
            # 获取好友口令
            net.send_packet("get_friend_token", {})
            while net.friend_token_queue.empty():
                time.sleep(0.01)
            friend_token_msg = net.friend_token_queue.get_nowait()
            friend_token = friend_token_msg["payload"]["friend_token"]
            # 获取到好友口令之后
            settings_config[settings_config.index(config)]['default'] = friend_token
    cancel_flag : bool = False
    dialog = SettingsDialog(root, settings_config, cancel_flag)
    root.wait_window(dialog)  # 等待对话框关闭
    logger.debug("最终设置:" + str(dialog.get_settings()))
    if dialog.cancel_flag:
        logger.debug("取消设置")
        return
    for key, value in dialog.get_settings().items():
        logger.debug(f"{key}: {value}")
        match key:
            case "server":
                lib.write_xml("server/ip", value)
            case "port":
                lib.write_xml("server/port", value)
            case "friend_token":
                net.send_packet("change_friend_token", {"new_friend_token": value})
def main():
    """
    测试客户端
    Returns:
        :return None
    """
    global net, db, uid, root, login_ui_class, login_root, logged_in, gui, username, password

    # username = "admin"
    # password = "admin"
    # uid = 0
    username = lib.read_xml("account/username", "data/")
    password = lib.read_xml("account/password", "data/")
    uid = lib.read_xml("account/uid", "data/")
    if not username:
        username = ""
    if not password:
        password = ""
    if not uid:
        uid = NotImplemented
    if is_debug():
        logger.debug("调试模式已开启")
        answer = input("是否从xml读取用户信息？(y/n)")
        if answer != "y" and answer != "":
            username = input("请输入用户名：")
            password = input("请输入密码：")
            uid = input("请输入用户ID：")


    logger.info("正在启动客户端...")

    contacts = []

    main_receive_thread = threading.Thread(target=net.receive_packet, daemon=True)
    main_receive_thread.start()

    threading.Thread(target=process_message_thread, daemon=True).start()

    login_root = tk.Tk()
    login_ui_class = LoginUI(login_root)
    login_ui_class.validate_login_handler = lambda username_var, password_var: validate_login(username_var, password_var)
    login_ui_class.show_register = lambda : start_register()
    login_ui_class.create_register()

    login_ui_class.username_entry.delete('0', tk.END)
    login_ui_class.username_entry.insert(string=username, index=0)
    login_ui_class.password_entry.delete('0', tk.END)
    login_ui_class.password_entry.insert(string=password, index=0)

    login_root.mainloop()

    db.connect(lib.read_xml("database/file", "data/"))
    db.create_tables_if_not_exists()
    check_database_uid()

    if not logged_in:
        logger.critical("登录失败")
        return

    if not db.get_metadata("uid"):
        db.insert_sql("meta", "uid" ,[uid])

    for contact in db.select_sql("contact", "mem, id, name"):
        if contact:
            last_message = db.get_last_chat_message(uid, contact[1])
            if last_message:
                if contact[0]:
                    contacts.append({"name": contact[0], "id":contact[1] ,"avatar": "👨", "last_msg": f"{last_message[4]}" + " " * (50-len(last_message[4])), "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
                else:
                    if contact[2]:
                        contacts.append({"name": contact[2], "id": contact[1],"avatar": "👨", "last_msg": f"{last_message[4]}" + " " * (50-len(last_message[4])), "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
                    else:
                        contacts.append({"name": "未知", "id": contact[1],"avatar": "👨", "last_msg": f"{last_message[4]}" + " " * (50-len(last_message[4])), "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
    root = tk.Tk()
    gui = GUI(root, load_messages)
    gui.send_message_handler = lambda contact_: send_message(gui, contact_)
    gui.send_picture_handler = lambda contact_: send_picture(gui, contact_)
    gui.set_add_friend_handler(handle_add_friend)
    gui.contacts = contacts
    gui.show_settings = lambda : open_settings()


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

def exit_program(status=0):
    try:
        if login_root is not NotImplemented:
            login_root.destroy()
        if register_root is not NotImplemented:
            register_root.destroy()
        if root is not NotImplemented:
            root.destroy()
    except _tkinter.TclError:
        pass
    if db.conn is not None:
        db.close()
    if net is not NotImplemented:
        net.sock.shutdown(socket.SHUT_RD)
        net.sock.close()
    sys.exit(status)


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
        exit_program()
