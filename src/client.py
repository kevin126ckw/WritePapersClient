#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : client.py
# @Software: PyCharm
# @Desc    : WritePapers客户端主程序
# @Author  : Kevin Chang

"""WritePapers客户端主程序模块。

本模块包含客户端的核心功能，包括用户登录、消息处理、联系人管理等。
"""

import _tkinter
import base64
import datetime
import os
import socket
import sys
import threading
import time
import tkinter as tk
import tkinter.filedialog
from tkinter import messagebox
from typing import Any, Dict, List, Optional, Union

import database
import networking
import paperlib as lib
import structlog
from login_ui import LoginUI
from reg_ui import RegisterUI
from settings_ui import SettingsDialog
from ui import GUI


class Client:
    """WritePapers客户端主类。
    
    负责管理客户端的所有功能，包括网络连接、用户界面、数据库操作等。
    """
    
    def __init__(self) -> None:
        """初始化WritePapers客户端。
        
        初始化客户端的所有核心组件，包括：
        - 用户认证相关属性
        - 用户界面组件
        - 网络通信模块
        - 数据库连接
        - 服务器配置信息

        Returns:
            :return None
            
        Raises:
            无异常抛出
        """
        # ==================== 用户认证相关属性 ====================
        self.uid: Optional[Union[str, int]] = None  # 用户唯一标识符
        self.username: Optional[str] = None  # 用户名
        self.password: Optional[str] = None  # 用户密码
        self.msg_uid: Optional[Union[str, int]] = None  # 消息系统中的用户ID
        self.logged_in: bool = False  # 用户登录状态标志
        
        # ==================== 用户界面相关属性 ====================
        self.login_ui_class: Optional[LoginUI] = None  # 登录界面类实例
        self.login_root: Optional[tk.Tk] = None  # 登录窗口根对象
        self.register_root: Optional[tk.Tk] = None  # 注册窗口根对象
        self.register_class: Optional[RegisterUI] = None  # 注册界面类实例
        self.root: Optional[tk.Tk] = None  # 主窗口根对象
        self.gui: Optional[GUI] = None  # 主界面类实例
        
        # ==================== 核心功能组件 ====================
        self.logger = structlog.get_logger()  # 结构化日志记录器
        self.net = networking.ClientNetwork()  # 网络通信模块
        self.net.is_debug = lambda: self.is_debug()  # 设置网络模块的调试模式检查函数
        self.db = database.Database()  # 数据库操作模块
        
        # ==================== 服务器配置初始化 ====================
        # 从配置文件读取服务器连接信息
        server_ip = lib.read_xml("server/ip")
        server_port = lib.read_xml("server/port")
        
        # 设置默认服务器配置（如果配置文件中没有相关信息）
        if not server_ip:
            self.logger.warning("未配置服务器地址，使用默认本地服务器地址")
            server_ip = "127.0.0.1"
        if not server_port:
            self.logger.warning("未配置服务器端口，使用默认端口号")
            server_port = "3624"
        
        # 初始化设置配置项列表，用于设置对话框显示
        self.settings_config: List[Dict[str, str]] = [
            {"name": "server", "label": "服务器地址", "type": "text", "default": server_ip},
            {"name": "port", "label": "端口号", "type": "text", "default": server_port},
            {"name": "friend_token", "label": "好友口令", "type": "text", "default": "12345678"}
        ]

    @staticmethod
    def is_debug() -> bool:
        """检查是否启用调试模式。
        
        从配置文件中读取调试模式设置，用于控制程序的调试输出和行为。

        Returns:
            bool: 如果启用调试模式返回True，否则返回False
            
        Note:
            调试模式配置存储在XML配置文件的debug/enabled节点中
        """
        debug_enabled = lib.read_xml("debug/enabled")
        # 检查配置值是否为真值字符串
        return debug_enabled in ("true", "True")

    def _handle_chat_message(self, from_user: Union[str, int], send_time: float, 
                           message_type: str, message_content: Union[str, bytes], 
                           need_update_contact: bool = True) -> None:
        """处理接收到的聊天消息。
        
        该方法负责处理从服务器接收到的聊天消息，包括：
        1. 将消息保存到本地数据库
        2. 如果当前聊天窗口对应发送者，则实时显示消息
        3. 记录消息到日志系统
        4. 更新联系人列表（可选）
        
        Args:
            from_user (Union[str, int]): 消息发送者的用户ID
            send_time (float): 消息发送的时间戳（Unix时间戳）
            message_type (str): 消息类型，支持"text"（文本）和"image"（图片）
            message_content (Union[str, bytes]): 消息内容，文本消息为字符串，图片消息为字节数据
            need_update_contact (bool, optional): 是否需要更新联系人列表，默认为True
            
        Returns:
            :return None
            
        Note:
            - 图片消息内容为base64编码的字节数据
            - 消息会自动保存到本地SQLite数据库中
        """
        # 步骤1: 保存消息到本地数据库
        self.db.save_chat_message(from_user, self.uid, message_content, send_time, message_type)
        
        # 步骤2: 如果当前聊天窗口对应消息发送者，则实时显示消息
        if self.gui.current_chat and self.gui.current_chat['id'] == int(from_user):
            # 获取发送者显示名称
            sender_name = self.db.get_mem_by_uid(from_user)
            formatted_time = time.strftime("%H:%M", time.localtime(send_time))
            
            if message_type == "text":
                # 处理文本消息
                message_data = {
                    "content": message_content, 
                    "time": formatted_time,
                    "status": "received", 
                    "sender": sender_name, 
                    "type": message_type
                }
                self.gui.display_message(message_data)
            elif message_type == "image":
                # 处理图片消息（需要解码base64数据）
                message_data = {
                    "content": base64.b64decode(message_content), 
                    "time": formatted_time,
                    "status": "received", 
                    "sender": sender_name, 
                    "type": message_type
                }
                self.gui.display_message(message_data)
        # 步骤3: 记录消息到日志系统
        sender_name = self.db.get_mem_by_uid(from_user)
        formatted_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(send_time))
        
        if message_type == "text":
            # 记录文本消息到日志
            self.logger.info(f"{formatted_datetime} {sender_name}: {message_content}")
        elif message_type == "image":
            # 记录图片消息到日志
            self.logger.info(f"{formatted_datetime} {sender_name}: [图片]")
        
        # 步骤4: 根据需要更新联系人列表
        if need_update_contact:
            self.update_contacts()

    def process_message(self, net_module: networking.ClientNetwork) -> None:
        """处理网络模块中的各种消息队列。
        
        该方法负责处理网络模块中的三种消息队列：
        1. 离线消息队列 - 处理用户离线期间收到的消息
        2. 实时消息队列 - 处理实时接收的聊天消息
        3. 返回值队列 - 处理服务器的各种响应结果
        
        Args:
            net_module (networking.ClientNetwork): 网络通信模块实例
            
        Returns:
            :return None
            
        Note:
            该方法通常在独立线程中循环调用，用于实时处理各种网络消息
        """

        # ==================== 处理离线消息队列 ====================
        while not net_module.offline_message_queue.empty():
            offline_msg = net_module.offline_message_queue.get_nowait()
            # 离线消息格式: [content, from_user, to_user, timestamp, message_type]
            content, from_user, to_user, timestamp, msg_type = offline_msg
            
            if msg_type == "text":
                # 处理离线文本消息
                self.db.save_chat_message(from_user, to_user, content, timestamp)
                sender_name = self.db.get_mem_by_uid(from_user)
                formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                self.logger.debug(f"离线消息：{formatted_time} {sender_name}: {content}")
                
            elif msg_type == "image":
                # 处理离线图片消息（需要解码base64数据）
                image_data = base64.b64decode(content)
                self.db.save_chat_message(from_user, to_user, image_data, timestamp, "image")
                sender_name = self.db.get_mem_by_uid(from_user)
                formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                self.logger.debug(f"离线消息：{formatted_time} {sender_name}: [图片]")
            
            # 更新联系人列表（需要检查GUI是否已初始化）
            if self.gui and self.gui.scrollable_frame is not None:
                self.update_contacts()
            else:
                # GUI未完全初始化，延迟更新联系人列表
                if self.gui and self.gui.root:
                    self.gui.root.after(1, lambda: self.update_contacts())
                    self.logger.debug("GUI未完全初始化，延迟更新联系人列表")

        # ==================== 处理实时消息队列 ====================
        while not net_module.message_queue.empty():
            real_time_msg = net_module.message_queue.get_nowait()
            # 提取消息载荷数据
            payload = real_time_msg['payload']
            self._handle_chat_message(
                payload['from_user'], 
                payload['send_time'], 
                payload['message_type'], 
                payload['message_content']
            )
            
        # ==================== 处理服务器返回值队列 ====================
        while not net_module.return_queue.empty():
            return_msg = net_module.return_queue.get_nowait()
            self._handle_server_response(return_msg)

    def validate_login(self, login_username: str, login_password: str) -> bool:
        """验证用户登录信息并处理记住密码功能。
        
        该方法执行以下操作：
        1. 发送登录请求到服务器
        2. 如果用户选择记住密码，则保存登录信息到配置文件
        3. 返回验证结果
        
        Args:
            login_username (str): 用户输入的登录用户名
            login_password (str): 用户输入的登录密码
            
        Returns:
            bool: 始终返回True（实际验证结果通过异步消息处理）
            
        Note:
            实际的登录验证结果会通过process_message方法中的login_result处理
        """
        # 发送登录请求到服务器
        self.login(login_username, login_password)
        
        # 处理"记住密码"功能
        if self.login_ui_class and self.login_ui_class.remember_var.get():
            stored_username = lib.read_xml("account/username")
            stored_password = lib.read_xml("account/password")
            
            # 如果当前输入的用户名密码与存储的不同，则更新配置文件
            if stored_username != login_username or stored_password != login_password:
                lib.write_xml("account/username", login_username)
                lib.write_xml("account/password", login_password)
                lib.write_xml("account/uid", str(self.uid) if self.uid is not None else "")
                self.logger.debug(
                    f"更新保存的登录信息 - 用户名:{login_username}, 密码:{'*' * len(login_password)}, UID:{self.uid}")
        
        return True

    def load_messages(self, contact: Dict[str, Any], display_message: callable) -> None:
        """加载指定联系人的聊天历史记录。
        
        该方法从本地数据库中读取与指定联系人的聊天记录，并通过回调函数显示在界面上。
        支持文本消息和图片消息的加载显示。
        
        Args:
            contact (Dict[str, Any]): 当前选中的联系人信息字典，包含id、name等字段
            display_message (callable): 用于显示消息的回调函数，接收消息字典作为参数
            
        Returns:
            :return None
            
        Note:
            - 如果联系人ID与当前用户ID相同，会显示特殊提示
            - 消息按时间顺序加载显示
        """
        # 检查用户ID是否有效
        if self.uid is None:
            self.logger.critical("用户ID未知，请检查是否已正确登录")
            self.uid = 0
            
        # 根据联系人ID获取聊天历史记录
        contact_id = contact["id"]
        if contact_id == int(self.uid):
            # 特殊情况：用户查看与自己的聊天记录
            self.gui.show_toast("彩蛋解锁：给自己发消息？", position="top-right")
            messages = self.db.get_chat_history(self.uid)
        else:
            # 正常情况：查看与其他联系人的聊天记录
            messages = self.db.get_chat_history(contact_id)

        # 遍历消息历史记录并显示
        for msg in messages:
            # 消息格式: (id, from_user, to_user, message_type, content, timestamp)
            msg_id, from_user, to_user, msg_type, content, timestamp = msg
            
            # 调试日志：根据消息长度决定是否完整显示
            if len(str(msg)) < 250:
                self.logger.debug(f"加载历史消息: {msg}")
            else:
                self.logger.debug(f"加载历史消息 (内容过长，仅显示长度): {len(str(msg))} 字符")
            
            # 格式化消息时间
            formatted_time = time.strftime("%H:%M", time.localtime(timestamp))
            
            # 根据发送者和接收者确定消息显示方式
            if int(from_user) == int(self.uid):
                # 当前用户发送的消息
                message_data = {
                    "content": content, 
                    "time": formatted_time, 
                    "status": "sent",
                    "sender": "我", 
                    "type": msg_type
                }
                display_message(message_data)
                
            elif int(to_user) == int(self.uid):
                # 当前用户接收的消息
                sender_name = self.db.get_mem_by_uid(from_user)
                message_data = {
                    "content": content, 
                    "time": formatted_time, 
                    "status": "received",
                    "sender": sender_name, 
                    "type": msg_type
                }
                display_message(message_data)
                
            else:
                # 异常情况：消息不属于当前用户
                self.logger.error(f"发现异常消息记录，消息ID: {msg_id}")
                message_data = {
                    "content": content, 
                    "time": formatted_time, 
                    "status": "sent",
                    "type": msg_type
                }
                display_message(message_data)

    def _handle_server_response(self, return_msg: Dict[str, Any]) -> None:
        """处理服务器返回的响应消息。
        
        根据不同的响应类型，执行相应的处理逻辑，包括消息发送结果、
        用户注册结果、登录结果、添加好友结果等。
        
        Args:
            return_msg (Dict[str, Any]): 服务器返回的响应消息字典
            
        Returns:
            :return None
        """
        response_type = return_msg.get('type')
        payload = return_msg.get('payload', {})
        
        match response_type:
            case 'send_message_result':
                self._handle_send_message_result(payload)
            case 'register_result':
                self._handle_register_result(payload)
            case 'login_result':
                self._handle_login_result(payload)
            case 'add_friend_result':
                self._handle_add_friend_result(payload)
            case _:
                self.logger.warning(f"未知的服务器响应类型: {response_type}")
    
    def _handle_send_message_result(self, payload: Dict[str, Any]) -> None:
        """处理消息发送结果。"""
        if payload.get('success'):
            self.logger.info("消息发送成功")
        else:
            self.logger.error("消息发送失败")
    
    def _handle_register_result(self, payload: Dict[str, Any]) -> None:
        """处理用户注册结果。"""
        if payload.get('success'):
            self.logger.info("用户注册成功")
            # 保存注册成功的用户信息到配置文件
            lib.write_xml("account/username", payload['username'])
            lib.write_xml("account/password", payload['password'])
            lib.write_xml("account/uid", payload['uid'])
            self.logger.debug(
                f"保存用户信息到配置文件 - 用户名:{payload['username']}, 密码:{payload['password']}, UID:{payload['uid']}")
            
            # 显示注册成功提示
            messagebox.showinfo("注册成功",
                                f"恭喜您，注册成功！\n您的用户ID是: {payload['uid']}\n请重新启动应用程序进行登录！")
            
            # 延迟关闭注册窗口
            if self.register_class and self.register_class.root:
                self.register_class.root.after(3000, self.register_class.root.destroy)
        else:
            self.logger.error("用户注册失败")
            messagebox.showerror("注册失败", "注册失败，请检查用户名是否已被使用")
    
    def _handle_login_result(self, payload: Dict[str, Any]) -> None:
        """处理用户登录结果。"""
        if payload.get('success'):
            self.logger.info("用户登录成功")
            # 保存登录成功后的用户信息
            self.msg_uid = payload['uid']
            self.net.token = payload['token']
            self.logged_in = True
            
            # 通知登录界面登录成功，准备关闭登录窗口
            if self.login_ui_class and self.login_ui_class.root:
                self.login_ui_class.root.after(0, lambda: self.login_ui_class.login_success())
            self.logger.debug("登录成功，准备关闭登录窗口")
        else:
            self.logger.error("用户登录失败")
            self.logged_in = False
            tk.messagebox.showerror("登录失败", "用户名或密码错误，请重试")
    
    def _handle_add_friend_result(self, payload: Dict[str, Any]) -> None:
        """处理添加好友结果。"""
        if payload.get('success'):
            self.logger.info("添加好友成功")
            # 将新好友信息保存到本地数据库
            self.db.save_contact(
                payload['friend_uid'], 
                payload['friend_username'],
                payload['friend_name'], 
                ""  # 备注信息暂时为空
            )
            messagebox.showinfo("添加好友成功", f"成功添加好友: {payload['friend_name']}")
            # 更新联系人列表显示
            if self.gui and self.gui.root:
                self.gui.root.after(0, lambda: self.update_contacts())
        else:
            self.logger.error("添加好友失败")
            messagebox.showerror("添加好友失败", "添加好友失败，请检查好友ID或验证口令")

    def welcome_back(self) -> None:
        """处理欢迎回来消息。

        Returns:
            :return None
        """
        while self.net.welcome_back_queue.empty():
            pass
        welcome_back_msg = self.net.welcome_back_queue.get_nowait()
        if self.gui:
            self.gui.show_toast(welcome_back_msg['payload']['message'], position="top-right", toast_type="success")

    def send_message(self, gui_class: GUI, contact: Dict[str, Any]) -> None:
        """发送文本消息。
        
        Args:
            :param gui_class: GUI类实例
            :param contact: 当前选中的联系人信息字典
            
        Returns:
            :return None
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

    def send_picture(self, gui_class: GUI, contact: Dict[str, Any]) -> None:
        """发送图片消息。
        
        Args:
            :param gui_class: GUI类实例
            :param contact: 当前选中的联系人信息字典
            
        Returns:
            :return None
        """
        current_time = datetime.datetime.now().strftime("%H:%M")
        image_path = tkinter.filedialog.askopenfilename(filetypes=[("PNG Files", "*.png"), ("GIF Files", "*.gif")])
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
                self.gui.show_toast("正在发送图片数据，请稍候...")
                self.net.send_packet("send_message", {"to_user": str(contact["id"]), "type": "image",
                                                      "message": base64.b64encode(image_data).decode(
                                                          "utf-8")})  # Base64编码图片数据
                self.logger.debug("图片数据发送完成")
                self.gui.show_toast("图片发送成功")
                self.db.save_chat_message(self.uid, contact["id"], image_data, time.time(), "image")

                # 显示消息
                gui_class.display_message(message)

                self.update_contacts()

            threading.Thread(target=_send_picture).start()

    def process_message_thread(self) -> None:
        """消息处理线程主循环。
        
        持续监听网络模块的各种消息队列，当有消息时调用process_message方法处理。
        该方法运行在独立的后台线程中，确保消息处理不会阻塞主界面。

        Returns:
            :return None
            
        Note:
            该方法会无限循环运行，直到程序退出
        """
        while True:
            if (not self.net.message_queue.empty() or 
                not self.net.return_queue.empty() or 
                not self.net.offline_message_queue.empty()):
                self.process_message(self.net)
            else:
                time.sleep(0.01)

    def login(self, login_username: str, login_password: str) -> None:
        """向服务器发送用户登录请求。
        
        将用户输入的用户名和密码发送到服务器进行验证，
        同时保存用户名和密码到客户端实例中。
        
        Args:
            login_username (str): 用户输入的登录用户名
            login_password (str): 用户输入的登录密码
            
        Returns:
            :return None
            
        Note:
            登录结果会通过异步消息处理机制返回
        """
        # 发送登录数据包到服务器
        self.net.send_packet("login", {"username": login_username, "password": login_password})
        
        # 保存用户凭据到客户端实例
        self.username = login_username
        self.password = login_password

    def update_contacts(self) -> None:
        """更新联系人列表。
        
        从数据库获取联系人信息和最后一条消息，格式化后更新到GUI界面。

        Returns:
            :return None
        """
        contacts = []
        contact_list = self.db.get_contact_list()
        
        for contact in contact_list:
            contact_info = self._build_contact_info(contact)
            if contact_info:
                contacts.append(contact_info)
        
        # 更新GUI中的联系人列表
        self.gui.contacts = contacts
        self.gui.load_contacts()
    
    def _build_contact_info(self, contact: tuple) -> Optional[Dict[str, Any]]:
        """构建单个联系人的信息字典。
        
        Args:
            contact (tuple): 联系人数据元组，格式为(nickname, uid, username, ...)
            
        Returns:
            Optional[Dict[str, Any]]: 格式化的联系人信息字典，如果无法构建则返回None
        """
        try:
            # 安全地解包联系人数据
            if len(contact) < 3:
                self.logger.warning(f"联系人数据格式不完整: {contact}")
                return None
                
            nickname, contact_id, username = contact[0], contact[1], contact[2]
            
            # 验证联系人ID的有效性
            if not contact_id or not str(contact_id).isdigit():
                self.logger.warning(f"无效的联系人ID: {contact_id}")
                return None
            
            # 获取与该联系人的最后一条消息
            last_message = self.db.get_last_chat_message(self.uid, contact_id)
            if not last_message:
                self.logger.debug(f"联系人 {contact_id} 没有聊天记录")
                return None
                
            self.logger.debug(f"更新联系人信息: {contact}, 最后消息: {last_message}")
            
            # 确定显示名称
            display_name = self._get_contact_display_name(nickname, username)
            
            # 格式化最后一条消息
            last_msg_text, formatted_time = self._format_last_message(last_message)
            
            return {
                "name": display_name,
                "id": contact_id,
                "avatar": "👨",
                "last_msg": last_msg_text,
                "time": formatted_time
            }
            
        except Exception as e:
            self.logger.error(f"构建联系人信息时发生错误: {e}, 联系人数据: {contact}")
            return None

    @staticmethod
    def _get_contact_display_name(nickname: str, username: str) -> str:
        """获取联系人的显示名称。
        
        Args:
            nickname (str): 联系人昵称
            username (str): 联系人用户名
            
        Returns:
            str: 用于显示的联系人名称
        """
        if nickname:
            return nickname
        elif username:
            return username
        else:
            return "未知用户"
    
    def _format_last_message(self, last_message: tuple) -> tuple[str, str]:
        """格式化最后一条消息的显示内容和时间。
        
        Args:
            last_message (tuple): 最后一条消息的数据元组
            
        Returns:
            tuple[str, str]: (消息显示文本, 格式化时间)
        """
        try:
            # 验证消息数据的完整性
            if len(last_message) < 6:
                self.logger.warning(f"消息数据格式不完整: {last_message}")
                return "[数据错误]", "--:--"
            
            msg_type, content, timestamp = last_message[3], last_message[4], last_message[5]
            
            # 安全地格式化时间戳
            try:
                if isinstance(timestamp, (int, float)) and timestamp > 0:
                    formatted_time = time.strftime("%H:%M", time.localtime(timestamp))
                else:
                    formatted_time = "--:--"
            except (ValueError, OSError) as e:
                self.logger.warning(f"时间戳格式化失败: {timestamp}, 错误: {e}")
                formatted_time = "--:--"
            
            # 根据消息类型返回相应的显示文本
            if msg_type == "text":
                # 限制文本消息的显示长度
                display_content = str(content)[:50] + "..." if len(str(content)) > 50 else str(content)
                return display_content, formatted_time
            elif msg_type == "image":
                return "[图片]", formatted_time
            else:
                return "[未知消息类型]", formatted_time
                
        except Exception as e:
            self.logger.error(f"格式化消息时发生错误: {e}, 消息数据: {last_message}")
            return "[格式化错误]", "--:--"
    
    def _load_user_config(self) -> None:
        """从配置文件加载用户信息。
        
        安全地从XML配置文件中读取用户的登录信息，
        如果读取失败则使用默认值。
        """
        try:
            self.username = lib.read_xml("account/username", "data/") or ""
            self.password = lib.read_xml("account/password", "data/") or ""
            self.uid = lib.read_xml("account/uid", "data/") or None
            
            self.logger.debug(f"成功加载用户配置 - 用户名: {self.username}, UID: {self.uid}")
            
        except Exception as e:
            self.logger.error(f"加载用户配置时发生错误: {e}")
            # 使用默认值
            self.username = ""
            self.password = ""
            self.uid = None
        
    def _handle_debug_mode_input(self) -> None:
        """处理调试模式下的用户输入。"""
        self.logger.debug("调试模式已开启")
        use_config_file = input("是否从XML配置文件读取用户信息？(y/n): ")
        if use_config_file.lower() not in ("y", "yes", ""):
            self.username = input("请输入用户名: ")
            self.password = input("请输入密码: ")
            self.uid = input("请输入用户ID: ")
    
    def _start_network_threads(self) -> None:
        """启动网络通信相关的后台线程。
        
        创建并启动网络数据接收线程和消息处理线程，
        确保网络通信能够正常工作。
        
        Raises:
            Exception: 如果线程启动失败
        """
        try:
            # 启动网络数据接收线程
            self.receive_thread = threading.Thread(target=self.net.receive_packet, daemon=True)
            self.receive_thread.start()
            self.logger.debug("网络接收线程已启动")
            
            # 启动消息处理线程
            self.message_thread = threading.Thread(target=self.process_message_thread, daemon=True)
            self.message_thread.start()
            self.logger.debug("消息处理线程已启动")
            
        except Exception as e:
            self.logger.error(f"启动网络线程时发生错误: {e}")
            raise Exception(f"网络线程启动失败: {e}")
    
    def _show_login_interface(self) -> bool:
        """显示登录界面并等待用户登录。
        
        Returns:
            bool: 登录是否成功
        """
        login_window = tk.Tk()
        login_interface = LoginUI(login_window)
        
        # 设置登录界面的回调函数
        login_interface.validate_login_handler = lambda username, password: self.validate_login(username, password)
        login_interface.show_register = lambda: self.start_register()
        login_interface.create_register()
        
        # 预填充保存的用户信息
        if self.username:
            login_interface.username_entry.delete('0', tk.END)
            login_interface.username_entry.insert(0, self.username)
        if self.password:
            login_interface.password_entry.delete('0', tk.END)
            login_interface.password_entry.insert(0, self.password)
        
        # 保存引用并启动界面
        self.login_root = login_window
        self.login_ui_class = login_interface
        
        login_window.mainloop()
        return self.logged_in
    
    def _initialize_main_interface(self) -> None:
        """初始化主界面和相关组件。
        
        执行数据库连接、表创建、用户数据验证等初始化操作，
        然后创建主界面GUI。
        
        Raises:
            Exception: 如果初始化过程中发生关键错误
        """
        try:
            # 连接数据库
            database_file = lib.read_xml("database/file", "data/") or "data/client.sqlite"
            self.logger.info(f"正在连接数据库: {database_file}")
            
            self.db.connect(database_file)
            self.db.create_tables_if_not_exists()
            self.logger.debug("数据库连接和表创建完成")
            
            # 检查数据库UID一致性
            self.check_database_uid()
            
            # 初始化用户元数据
            if not self.db.get_metadata("uid"):
                self.db.insert_metadata("uid", str(self.uid) if self.uid else "")
                self.logger.debug("用户元数据初始化完成")
            
            # 构建联系人列表并创建主界面
            contacts = self._build_initial_contacts_list()
            self._create_main_gui(contacts)
            
        except Exception as e:
            self.logger.error(f"初始化主界面时发生错误: {e}")
            tk.messagebox.showerror("初始化错误", f"程序初始化失败: {str(e)}")
            raise
    
    def _build_initial_contacts_list(self) -> List[Dict[str, Any]]:
        """构建初始的联系人列表。
        
        从数据库中获取所有联系人信息，并构建用于界面显示的联系人列表。
        
        Returns:
            List[Dict[str, Any]]: 格式化的联系人列表
        """
        contacts = []
        try:
            contact_list = self.db.get_contact_list()
            self.logger.debug(f"从数据库获取到 {len(contact_list)} 个联系人")
            
            for contact in contact_list:
                contact_info = self._build_contact_info(contact)
                if contact_info:
                    contacts.append(contact_info)
                    
            self.logger.info(f"成功构建 {len(contacts)} 个有效联系人")
            
        except Exception as e:
            self.logger.error(f"构建联系人列表时发生错误: {e}")
            # 返回空列表，让程序继续运行
            
        return contacts
    
    def _create_main_gui(self, contact_list: List[Dict[str, Any]]) -> None:
        """创建主界面GUI。
        
        Args:
            contact_list (List[Dict[str, Any]]): 联系人列表
        """
        main_window = tk.Tk()
        main_interface = GUI(
            main_window,
            self.load_messages,
            lambda selected_contact: self.send_picture(self.gui, selected_contact),
            lambda selected_contact: self.send_message(self.gui, selected_contact),
            self.is_debug,
            self.open_settings,
            contact_list
        )
        main_interface.set_add_friend_handler(self.handle_add_friend)
        
        # 保存引用
        self.root = main_window
        self.gui = main_interface
        
        # 获取离线消息
        self.net.send_packet("get_offline_messages", {"request_id": "1"})
        
        # 创建并设置用户名显示标签
        username_label = tk.Label(
            main_interface.user_frame, 
            text=self.username, 
            font=main_interface.fonts['small'],
            bg=main_interface.colors['primary'], 
            fg='white'
        )
        username_label.pack(pady=(5, 0))
        main_interface.username_label = username_label
        
        # 完成界面初始化
        main_interface.setup_bindings()
        main_interface.load_contacts()
        
        # 延迟显示欢迎消息并启动主循环
        main_window.after(100, self.welcome_back)
        main_window.mainloop()

    def register_user_handler(self) -> None:
        """处理用户注册请求。

        Returns:
            :return None
        """
        self.logger.debug("注册用户")
        register_username = self.register_class.username_entry.get()
        register_password = self.register_class.password_entry.get()
        self.logger.debug(f"用户名:{register_username}, 密码:{register_password}")
        self.logger.debug(self.register_class.agree_terms_var.get())
        # 注册用户
        if not self.register_class.validate_all_fields():
            return

        if not self.register_class.agree_terms_var.get():
            messagebox.showerror("错误", "请先同意用户协议和隐私政策")
            return

        # 模拟注册过程
        # messagebox.showinfo("注册成功", "恭喜您，注册成功！\n系统将为您自动登录...")

        # 这里可以添加实际的注册逻辑
        # self.register_class.root.destroy()
        self.net.send_packet("register_account",
                             {"username": register_username, "password": register_password})

    def start_register(self) -> None:
        """启动用户注册界面。

        Returns:
            :return None
        """
        self.logger.debug("开始注册")
        self.login_ui_class.root.after(0, lambda: self.login_ui_class.root.destroy())
        self.register_root = tk.Tk()
        self.register_class = RegisterUI(self.register_root)
        self.register_class.register_user_handler = lambda: self.register_user_handler()
        self.register_class.create_action_buttons(self.register_class.scrollable_frame)
        self.register_class.setup_bindings()
        self.register_root.mainloop()
        self.logger.debug("注册界面创建完毕")

    def handle_add_friend(self, friend_id: Union[str, int], verify_token: str) -> bool:
        """处理添加好友请求。
        
        Args:
            :param friend_id: 好友ID（可以是UID或用户名）
            :param verify_token: 验证令牌
            
        Returns:
            :return 是否成功处理添加好友请求
        """
        try:
            friend_uid = int(friend_id)
            if self.db.check_is_friend(friend_uid):
                tk.messagebox.showwarning("提示", f"{friend_id} 已经是你的好友了")
                return False
            self.net.send_packet("add_friend",
                                 {"friend_id_type": "uid", "friend_id": friend_uid, "verify_token": verify_token})
        except ValueError:
            friend_username = friend_id
            if self.db.check_is_friend():
                tk.messagebox.showwarning("提示", f"{friend_id} 已经是你的好友了")
                return False
            self.net.send_packet("add_friend",
                                 {"friend_id_type": "username", "friend_id": friend_username, "verify_token": verify_token})
        return True

    def check_database_uid(self) -> None:
        """检查数据库中的UID与当前登录UID是否一致。

        Returns:
            :return None
        """
        if self.uid != self.msg_uid:
            self.uid = self.msg_uid
            if lib.read_xml("account/username") == self.username and lib.read_xml("account/password") == self.password:
                lib.write_xml("account/uid", self.uid)
            stored_uid = self.db.get_metadata("uid")
            if stored_uid is None:
                self.db.insert_metadata("uid", str(self.uid) if self.uid is not None else "")
            elif stored_uid and self.msg_uid and int(stored_uid) != int(self.msg_uid):
                tk.messagebox.showwarning("警告",
                                          f"数据库中保存的uid与当前登录的uid不一致，这可能不是你的数据库！\n数据库中的uid为{self.db.get_metadata('uid')}\n您登录的uid为{self.msg_uid}\n为保证数据库安全，即将退出程序！")
                self.exit_program()
                return

    def open_settings(self) -> None:
        """打开设置对话框。

        Returns:
            :return None
        """
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

    def main(self) -> None:
        """客户端主程序入口。
        
        执行客户端的完整启动流程，包括：
        1. 加载用户配置信息
        2. 启动网络通信线程
        3. 显示登录界面
        4. 登录成功后初始化主界面
        5. 加载联系人和聊天记录

        Returns:
            :return None
            
        Note:
            这是客户端的主要入口点，包含完整的应用程序生命周期管理
        """
        r"""
                                    _ooOoo_
                                   o8888888o
                                   88" . "88
                                   (| -_- |)
                                    O\ = /O
                                ____/`---'\____
                              .   ' \\| |// `.
                               / \\||| : |||// \
                             / _||||| -:- |||||- \
                               | | \\\ - /// | |
                             | \_| ''\---/'' | |
                              \ .-\__ `-` ___/-. /
                           ___`. .' /--.--\ `. . __
                        ."" '< `.___\_<|>_/___.' >'"".
                       | | : `- \`.;`\ _ /`;.`/ - ` : | |
                         \ \ `-. \_ __\ /__ _/ .-` / /
                 ======`-.____`-.___\_____/___.-`____.-'======
                                    `=---='

                 .............................................
                          佛祖保佑             永无BUG
                  佛曰:
                          写字楼里写字间，写字间里程序员；
                          程序人员写程序，又拿程序换酒钱。
                          酒醒只在网上坐，酒醉还来网下眠；
                          酒醉酒醒日复日，网上网下年复年。
                          但愿老死电脑间，不愿鞠躬老板前；
                          奔驰宝马贵者趣，公交自行程序员。
                          别人笑我忒疯癫，我笑自己命太贱；
                          不见满街漂亮妹，哪个归得程序员？
                    """
        # ==================== 第一步：加载用户配置信息 ====================
        self._load_user_config()
        
        # 调试模式下允许手动输入用户信息
        if self.is_debug():
            self._handle_debug_mode_input()

        # ==================== 第二步：启动网络通信线程 ====================
        self.logger.info("正在启动WritePapers客户端...")
        self._start_network_threads()
        
        # ==================== 第三步：显示登录界面 ====================
        if not self._show_login_interface():
            self.logger.critical("登录失败，程序退出")
            return
        
        # ==================== 第四步：初始化主界面和数据库 ====================
        self._initialize_main_interface()

    def exit_program(self, status: int = 0) -> None:
        """退出程序并清理资源。
        
        Args:
            :param status: 退出状态码
            
        Returns:
            :return None
        """
        try:
            if self.login_root is not None:
                self.login_root.destroy()
            if self.register_root is not None:
                self.register_root.destroy()
            if self.root is not None:
                self.root.destroy()
        except _tkinter.TclError:
            pass
        if self.db.conn is not None:
            self.db.close()
        if self.net is not None and hasattr(self.net, 'sock') and self.net.sock:
            try:
                self.net.sock.shutdown(socket.SHUT_RD)
                self.net.sock.close()
            except (OSError, AttributeError):
                pass
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
