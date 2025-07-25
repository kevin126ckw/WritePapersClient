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


class Client:
    def __init__(self):
        self.uid = NotImplemented
        self.username = NotImplemented
        self.password = NotImplemented
        self.login_ui_class = NotImplemented
        self.login_root = NotImplemented
        self.register_root = NotImplemented
        self.register_class = NotImplemented
        self.root = NotImplemented
        self.gui = NotImplemented
        self.msg_uid = NotImplemented

        self.logged_in = False

        self.logger = structlog.get_logger()

        self.net = networking.ClientNetwork()
        self.net.is_debug = lambda: self.is_debug()
        self.db = database.Database()

        server_ip = lib.read_xml("server/ip")
        server_port = lib.read_xml("server/port")
        if not server_ip:
            self.logger.warning("未配置服务器地址，尝试本地服务器")
            server_ip = "127.0.0.1"
        if not server_port:
            self.logger.warning("未配置服务器端口，尝试默认端口")
            server_port = "3624"

        self.settings_config = [
            {"name": "server", "label": "服务器地址", "type": "text", "default": server_ip},
            {"name": "port", "label": "端口号", "type": "text", "default": server_port},
            {"name": "friend_token", "label": "好友口令", "type": "text", "default": "12345678"}
        ]

    @staticmethod
    def is_debug():
        # return True
        if lib.read_xml("debug/enabled") == "true" or lib.read_xml("debug/enabled") == "True":
            return True
        else:
            return False

    def _handle_chat_message(self, payload):
        """
        处理聊天消息
        :return None
        """
        from_user = payload['from_user']
        send_time = payload['time']
        message_type = payload['type']
        message_content = str(payload['message'])
        self.db.save_chat_message(from_user, self.uid, message_content, send_time, message_type)
        if self.gui.current_chat:
            if self.gui.current_chat['id'] == int(from_user):
                self.gui.display_message(
                    {"content": message_content, "time": time.strftime("%H:%M", time.localtime(send_time)),
                     "status": "received", "sender": self.db.get_mem_by_uid(from_user), "type": message_type})
        if "need_update_contact" in payload:
            self.logger.debug("need_update_contact存在")
            if not payload['need_update_contact']:
                self.logger.debug("不需要更新联系人")
                return
        if message_type == "text":
            self.logger.info(
                f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(send_time))} {self.db.get_mem_by_uid(from_user)}: {message_content}")
        else:
            self.logger.info(
                f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(send_time))} {self.db.get_mem_by_uid(from_user)}: [图片]")
        if self.is_debug():
            self.logger.debug(f"新消息payload:{payload}")
        self.update_contacts()

    def process_message(self, net_module):
        """
        处理消息队列
        :return None
        """

        # 离线消息
        while not net_module.offline_message_queue.empty():
            msg = net_module.offline_message_queue.get_nowait()
            self.logger.debug(
                f"离线消息：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg[3]))} {self.db.get_mem_by_uid(msg[1])}:{msg[0]}")
            self.db.save_chat_message(msg[1], msg[2], msg[0], msg[3])
            if self.gui.scrollable_frame is not None:
                self.update_contacts()
            else:
                self.gui.root.after(1, lambda: self.update_contacts())
                self.logger.debug("self.gui未初始化，1000ms后尝试更新联系人")

        # 普通消息
        while not net_module.message_queue.empty():
            msg = net_module.message_queue.get_nowait()
            self._handle_chat_message(msg['payload'])
        # 返回值
        while not net_module.return_queue.empty():
            msg = net_module.return_queue.get_nowait()
            """
            以下代码转移到self.networking.py的line 155了
            if msg['type'] == 'login_result':
                if msg['payload']['success']:
                    self.logger.info("登录成功")
                else:
                    self.logger.info("登录失败")
            """
            match msg['type']:
                case 'send_message_result':
                    if msg['payload']['success']:
                        self.logger.info("发送成功")
                    else:
                        self.logger.info("发送失败")
                case 'register_result':
                    if msg['payload']['success']:
                        self.logger.info("注册成功")
                        lib.write_xml("account/username", msg['payload']['username'])
                        lib.write_xml("account/password", msg['payload']['password'])
                        lib.write_xml("account/uid", msg['payload']['uid'])
                        self.logger.debug(
                            f"写入配置文件,username:{msg['payload']['username']}, password:{msg['payload']['password']}, uid:{msg['payload']['uid']}")
                        messagebox.showinfo("注册成功",
                                            f"恭喜您，注册成功！您的uid是{msg['payload']['uid']}\n请手动重新启动应用程序登录！")
                        # login(msg['payload']['username'], msg['payload']['password'])
                        # time.sleep(0.3)
                        self.register_class.root.after(3, self.register_class.root.destroy())
                    else:
                        self.logger.error("注册失败")
                        messagebox.showerror("注册失败", "注册失败，请检查用户名是否已存在")
                case "login_result":
                    if msg['payload']['success']:
                        self.logger.info("登录成功")
                        self.msg_uid = msg['payload']['uid']
                        self.logged_in = True
                        # self.login_ui_class.need_destroy = True
                        self.login_ui_class.root.after(0, lambda: self.login_ui_class.login_success())
                        self.logger.debug("窗口销毁")
                    else:
                        self.logger.error("登录失败")
                        self.logged_in = False
                        tk.messagebox.showerror("错误", "登录失败")
                        # self.logger.debug("窗口销毁")
                case "add_friend_result":
                    if msg['payload']['success']:
                        self.logger.info("添加好友成功")
                        self.db.save_contact(msg['payload']['friend_uid'], msg['payload']['friend_username'],
                                             msg['payload']['friend_name'], "")
                        messagebox.showinfo("添加好友成功", "添加好友成功")
                        self.gui.root.after(0, lambda: self.update_contacts())
                    else:
                        self.logger.error("添加好友失败")
                        messagebox.showerror("添加好友失败", "添加好友失败")

        # 未完待续

    def validate_login(self, login_username, login_password):
        self.login(login_username, login_password)
        if self.login_ui_class.remember_var.get():
            if lib.read_xml("account/username") == login_username and lib.read_xml("account/password") == login_password:
                return True
            lib.write_xml("account/username", login_username)
            lib.write_xml("account/password", login_password)
            lib.write_xml("account/uid", self.uid)
            self.logger.debug(f"写入配置文件,username:{login_username}, password:{login_password}, uid:{self.uid}")
        return True

    def load_messages(self, contact, display_message):
        """
        加载消息
        Params:
            :param contact: 当前选中的联系人
            :param display_message: 显示消息的函数
        Returns:
            :return: None
        """
        if self.uid is None:
            self.logger.critical("未知的uid,请检查你是否登录了")
            self.uid = 0
        if contact["id"] == int(self.uid):
            self.gui.show_toast("解锁成绩：给自己发消息？", position="top-right")
            messages = self.db.select_sql("chat_history", "*", f"to_user={self.uid} and from_user={self.uid}")
        else:
            messages = self.db.select_sql("chat_history", "*", f"to_user={contact['id']} or from_user={contact['id']}")

        for msg in messages:
            self.logger.debug(f"正在加载消息：{msg}")  # (1, 0, 0, 'text', 'hi', 1745813243.4815726)
            if int(msg[1]) == int(self.uid):
                display_message(
                    {"content": msg[4], "time": time.strftime("%H:%M", time.localtime(msg[5])), "status": "sent",
                     "sender": "我", 'type': msg[3]})
            elif int(msg[2]) == int(self.uid):
                display_message(
                    {"content": msg[4], "time": time.strftime("%H:%M", time.localtime(msg[5])), "status": "received",
                     "sender": self.db.get_mem_by_uid(msg[1]), 'type': msg[3]})
            else:
                self.logger.error("未知消息")
                display_message(
                    {"content": msg[4], "time": time.strftime("%H:%M", time.localtime(msg[5])), "status": "sent",
                     'type': msg[3]})

    def welcome_back(self):
        while self.net.welcome_back_queue.empty():
            pass
        welcome_back_msg = self.net.welcome_back_queue.get_nowait()
        self.gui.show_toast(welcome_back_msg['payload']['message'], position="top-right", toast_type="success")

    def send_message(self, gui_class, contact):
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

        message = {"content": content, "time": current_time, "status": "sent", "sender": "我", 'type': "text"}

        # 添加到消息记录
        self.net.send_packet("send_message", {"to_user": str(contact["id"]), "message": content, "type": "text"})
        self.db.save_chat_message(self.uid, contact["id"], content, time.time())

        # 显示消息
        gui_class.display_message(message)

        # 清空输入框
        gui_class.text_input.delete("1.0", tk.END)

        self.update_contacts()

    def send_picture(self, gui_class, contact):
        current_time = datetime.datetime.now().strftime("%H:%M")
        image_path = tkinter.filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.gif")])
        if image_path:
            if os.path.getsize(image_path) > 1024 * 1024 * 2:
                tk.messagebox.showerror("错误", "图片大小不能超过2MB")
                return
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                image_file.close()
            if not image_data:
                tk.messagebox.showerror("错误", "请选择带有内容的图片")
                return
            message = {"content": image_data, "time": current_time, "status": "sent", "sender": "我", 'type': "image"}

            def _send_picture():
                # 添加到消息记录
                self.logger.debug("正在发送图片数据")
                self.net.send_packet("send_message", {"to_user": str(contact["id"]), "type": "image",
                                                      "message": base64.b64encode(image_data).decode(
                                                          "utf-8")})  # Base64编码图片数据
                self.logger.debug("图片数据发送完成")
                self.db.save_chat_message(self.uid, contact["id"], image_data, time.time(), "image")

                # 显示消息
                gui_class.display_message(message)

                self.update_contacts()

            threading.Thread(target=_send_picture).start()

    def process_message_thread(self):
        while True:
            if not self.net.message_queue.empty() or not self.net.return_queue.empty() or not self.net.offline_message_queue.empty():
                self.process_message(self.net)
            else:
                time.sleep(0.01)

    def login(self, login_username, login_password):
        self.net.send_packet("login", {"username": login_username, "password": login_password})
        self.username = login_username
        self.password = login_password

    def update_contacts(self):
        contacts = []
        for contact in self.db.select_sql("contact", "mem, id, name"):
            last_message = self.db.get_last_chat_message(self.uid, contact[1])
            self.logger.debug(f"正在更新联系人：{contact},last_message:{last_message}")
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
        self.gui.contacts = contacts
        self.gui.load_contacts()

    def register_user_handler(self, window_class):
        self.logger.debug("注册用户")
        register_username = window_class.username_entry.get()
        register_password = window_class.password_entry.get()
        self.logger.debug(f"用户名:{register_username}, 密码:{register_password}")
        self.logger.debug(window_class.agree_terms_var.get())
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
        self.net.send_packet("register_account",
                             {"username": register_username, "password": register_password})

    def start_register(self):
        self.logger.debug("开始注册")
        self.login_ui_class.root.after(0, lambda: self.login_ui_class.root.destroy())
        self.register_root = tk.Tk()
        self.register_class = RegisterUI(self.register_root)
        self.register_class.register_user_handler = lambda: self.register_user_handler(self.register_class)
        self.register_class.create_action_buttons(self.register_class.scrollable_frame)
        self.register_class.setup_bindings()
        self.register_root.mainloop()
        self.logger.debug("注册界面创建完毕")

    def handle_add_friend(self, friend_id, verify_token):
        try:
            friend_uid = int(friend_id)
            if self.db.select_sql("contact", "id", f"id='{friend_uid}'"):
                tk.messagebox.showwarning("提示", f"{friend_id} 已经是你的好友了")
                return False
            self.net.send_packet("add_friend",
                                 {"friend_id_type": "uid", "friend_id": friend_uid, "verify_token": verify_token})
        except ValueError:
            friend_username = friend_id
            if self.db.select_sql("contact", "id", f"username='{friend_username}'"):
                tk.messagebox.showwarning("提示", f"{friend_id} 已经是你的好友了")
                return False
            self.net.send_packet("add_friend",
                                 {"friend_id_type": "username", "friend_id": friend_username, "verify_token": verify_token})
        return True

    def check_database_uid(self):
        if self.uid != self.msg_uid:
            self.uid = self.msg_uid
            if lib.read_xml("account/username") == self.username and lib.read_xml("account/password") == self.password:
                lib.write_xml("account/uid", self.uid)
            if self.db.get_metadata("uid") is None:
                self.db.insert_sql("meta", "uid", [self.uid])
            elif int(self.db.get_metadata("uid")) != int(self.msg_uid):
                tk.messagebox.showwarning("警告",
                                          f"数据库中保存的uid与当前登录的uid不一致，这可能不是你的数据库！\n数据库中的uid为{self.db.get_metadata('uid')}\n您登录的uid为{self.msg_uid}\n为保证数据库安全，即将退出程序！")
                self.exit_program()
                return

    def open_settings(self):
        """打开设置对话框的示例函数"""
        for config in self.settings_config:
            if config["name"] == "friend_token":
                # 获取好友口令
                self.net.send_packet("get_friend_token", {})
                while self.net.friend_token_queue.empty():
                    time.sleep(0.01)
                friend_token_msg = self.net.friend_token_queue.get_nowait()
                friend_token = friend_token_msg["payload"]["friend_token"]
                # 获取到好友口令之后
                self.settings_config[self.settings_config.index(config)]['default'] = friend_token
        cancel_flag: bool = False
        dialog = SettingsDialog(self.root, self.settings_config, cancel_flag)
        self.root.wait_window(dialog)  # 等待对话框关闭
        self.logger.debug("最终设置:" + str(dialog.get_settings()))
        if dialog.cancel_flag:
            self.logger.debug("取消设置")
            return
        for key, value in dialog.get_settings().items():
            self.logger.debug(f"{key}: {value}")
            match key:
                case "server":
                    lib.write_xml("server/ip", value)
                case "port":
                    lib.write_xml("server/port", value)
                case "friend_token":
                    self.net.send_packet("change_friend_token", {"new_friend_token": value})

    def main(self):
        """
        测试客户端
        Returns:
            :return None
        """
        # username = "admin"
        # password = "admin"
        # uid = 0
        self.username = lib.read_xml("account/username", "data/")
        self.password = lib.read_xml("account/password", "data/")
        self.uid = lib.read_xml("account/uid", "data/")
        if not self.username:
            self.username = ""
        if not self.password:
            self.password = ""
        if not self.uid:
            self.uid = NotImplemented
        if self.is_debug():
            self.logger.debug("调试模式已开启")
            answer = input("是否从xml读取用户信息？(y/n)")
            if answer != "y" and answer != "":
                self.username = input("请输入用户名：")
                self.password = input("请输入密码：")
                self.uid = input("请输入用户ID：")

        self.logger.info("正在启动客户端...")

        contacts = []

        main_receive_thread = threading.Thread(target=self.net.receive_packet, daemon=True)
        main_receive_thread.start()

        threading.Thread(target=self.process_message_thread, daemon=True).start()

        self.login_root = tk.Tk()
        self.login_ui_class = LoginUI(self.login_root)
        self.login_ui_class.validate_login_handler = lambda username_var, password_var: self.validate_login(
            username_var, password_var)
        self.login_ui_class.show_register = lambda: self.start_register()
        self.login_ui_class.create_register()

        self.login_ui_class.username_entry.delete('0', tk.END)
        self.login_ui_class.username_entry.insert(string=self.username, index=0)
        self.login_ui_class.password_entry.delete('0', tk.END)
        self.login_ui_class.password_entry.insert(string=self.password, index=0)

        self.login_root.mainloop()

        self.db.connect(lib.read_xml("database/file", "data/"))
        self.db.create_tables_if_not_exists()
        self.check_database_uid()

        if not self.logged_in:
            self.logger.critical("登录失败")
            return

        if not self.db.get_metadata("uid"):
            self.db.insert_sql("meta", "uid", [self.uid])

        for contact in self.db.select_sql("contact", "mem, id, name"):
            if contact:
                last_message = self.db.get_last_chat_message(self.uid, contact[1])
                if last_message:
                    if contact[0]:
                        contacts.append({"name": contact[0], "id": contact[1], "avatar": "👨",
                                         "last_msg": f"{last_message[4]}" + " " * (50 - len(last_message[4])),
                                         "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
                    else:
                        if contact[2]:
                            contacts.append({"name": contact[2], "id": contact[1], "avatar": "👨",
                                             "last_msg": f"{last_message[4]}" + " " * (50 - len(last_message[4])),
                                             "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
                        else:
                            contacts.append({"name": "未知", "id": contact[1], "avatar": "👨",
                                             "last_msg": f"{last_message[4]}" + " " * (50 - len(last_message[4])),
                                             "time": time.strftime("%H:%M", time.localtime(last_message[5]))})
        self.root = tk.Tk()
        self.gui = GUI(self.root, self.load_messages)
        self.gui.send_message_handler = lambda contact_: self.send_message(self.gui, contact_)
        self.gui.send_picture_handler = lambda contact_: self.send_picture(self.gui, contact_)
        self.gui.set_add_friend_handler(self.handle_add_friend)
        self.gui.contacts = contacts
        self.gui.show_settings = lambda: self.open_settings()

        # 登录
        # self.net.send_packet("login", {"username": self.username, "password": self.password})
        # 调试消息转发
        # self.net.send_packet("send_message", {"to_user": str(self.uid), "message": "Hello, World!"})
        # 获取离线消息
        self.net.send_packet("get_offline_messages", {"1": str(1)})

        self.gui.setup_window()
        self.gui.setup_styles()
        self.gui.create_ui()
        self.gui.username_label = tk.Label(self.gui.user_frame, text=self.username, font=self.gui.fonts['small'],
                                           bg=self.gui.colors['primary'], fg='white')
        self.gui.username_label.pack(pady=(5, 0))
        self.gui.setup_bindings()
        self.gui.load_contacts()
        # threading.Thread(target=self.root.mainloop, daemon=True).start()
        self.gui.root.after(100, self.welcome_back)
        self.root.mainloop()

    def exit_program(self, status=0):
        try:
            if self.login_root is not NotImplemented:
                self.login_root.destroy()
            if self.register_root is not NotImplemented:
                self.register_root.destroy()
            if self.root is not NotImplemented:
                self.root.destroy()
        except _tkinter.TclError:
            pass
        if self.db.conn is not None:
            self.db.close()
        if self.net is not NotImplemented:
            self.net.sock.shutdown(socket.SHUT_RD)
            self.net.sock.close()
        sys.exit(status)


if __name__ == "__main__":
    client = Client()
    # global root
    try:
        if client.is_debug():
            result = input("请按回车键启动客户端...")
            if result == "":
                client.main()
            elif result == "reg":
                client.logger.info("正在启动客户端(test reg ver)...")
                client.db.connect("data/client.sqlite")

                receive_thread = threading.Thread(target=client.net.receive_packet, daemon=True)
                receive_thread.start()

                threading.Thread(target=client.process_message_thread, daemon=True).start()

                client.net.send_packet("register_account",
                                       {"username": input("username:"), "password": input("password:")})

                while True:
                    time.sleep(1)
        else:
            client.main()
    except ConnectionResetError:
        client.logger.warning("服务器已断开连接")
    except KeyboardInterrupt:
        client.logger.info("正在退出...")
        client.exit_program()
