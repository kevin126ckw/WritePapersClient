# -*- coding: utf-8 -*-
# @Time    : 2025/7/3
# @File    : ui.py
# @Software: PyCharm
# @Desc    : WritePapers客户端用户界面模块
# @Author  : Kevin Chang

"""WritePapers客户端用户界面模块。

本模块包含客户端的图形用户界面实现，包括聊天界面、联系人列表、消息显示等功能。
"""

import _tkinter
import time
import tkinter as tk
from io import BytesIO
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Union

import ImageViewer as imageviewer
import toast_ui
from PIL import Image, ImageTk, ImageSequence

class GUI:
    """WritePapers客户端图形用户界面类。
    
    负责管理客户端的所有图形界面元素，包括聊天窗口、联系人列表、消息显示等。
    """
    
    def __init__(self, root: tk.Tk, load_messages: Callable, send_picture_handler: Callable, 
                 send_message_handler: Callable, is_debug: Callable, show_settings: Callable, 
                 contacts: List[Dict[str, Any]]) -> None:
        """初始化GUI界面。
        
        Args:
            :param root: 主窗口对象
            :param load_messages: 加载消息的回调函数
            :param send_picture_handler: 发送图片的回调函数
            :param send_message_handler: 发送消息的回调函数
            :param is_debug: 检查调试模式的回调函数
            :param show_settings: 显示设置的回调函数
            :param contacts: 联系人列表
            
        Returns:
            :return 无返回值
        """
        # 回调函数
        self.is_debug = is_debug
        self.send_picture_handler = send_picture_handler
        self.send_message_handler = send_message_handler
        self.show_settings = show_settings
        self.load_messages = load_messages
        
        # 数据
        self.contacts = contacts
        self.current_chat: Optional[Dict[str, Any]] = None
        self.messages: Dict[str, List[Dict[str, Any]]] = {}
        self.add_friend_handler: Optional[Callable] = None
        
        # UI组件
        self.root = root
        self.toast = toast_ui.Toast(self.root)
        self.user_frame: Optional[tk.Frame] = None
        self.username_label: Optional[tk.Label] = None
        self.text_input: Optional[tk.Text] = None
        self.msg_frame: Optional[tk.Frame] = None
        self.msg_canvas: Optional[tk.Canvas] = None
        self.chat_content: Optional[tk.Frame] = None
        self.chat_header: Optional[tk.Frame] = None
        self.chat_frame: Optional[tk.Frame] = None
        self.scrollable_frame: Optional[tk.Frame] = None
        self.contact_canvas: Optional[tk.Canvas] = None
        self.search_var: Optional[tk.StringVar] = None
        self.contact_frame: Optional[tk.Frame] = None
        self.nav_frame: Optional[tk.Frame] = None
        self.sidebar: Optional[tk.Frame] = None
        self.main_container: Optional[tk.Frame] = None
        
        # 样式配置
        self.fonts: Optional[Dict[str, tuple]] = None
        self.colors: Optional[Dict[str, str]] = None

        # 初始化界面

        self.setup_window()
        self.setup_styles()
        self.create_ui()

    def setup_window(self) -> None:
        """设置主窗口属性。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        self.root.title("WritePapers - 即时通讯")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        self.root.configure(bg='#f5f5f5')

        # 设置窗口图标（使用emoji作为替代）
        try:
            self.root.iconbitmap('')
        except Exception as e:
            str(e)
            pass

    def setup_styles(self) -> None:
        """设置界面样式和配色方案。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        # 现代化配色方案
        self.colors = {
            'primary': '#4f46e5',  # 主色调 - 靛蓝
            'primary_dark': '#3730a3',  # 深主色
            'secondary': '#f8fafc',  # 次要背景色
            'accent': '#06b6d4',  # 强调色 - 青色
            'success': '#10b981',  # 成功色 - 绿色
            'warning': '#f59e0b',  # 警告色 - 黄色
            'danger': '#ef4444',  # 危险色 - 红色
            'dark': '#1f2937',  # 深色文字
            'light': '#6b7280',  # 浅色文字
            'border': '#e5e7eb',  # 边框色
            'hover': '#f3f4f6',  # 悬停色
            'online': '#10b981',  # 在线状态
            'offline': '#6b7280',  # 离线状态
            'busy': '#f59e0b'  # 忙碌状态
        }

        # 自定义字体
        self.fonts = {
            'default': ('Microsoft YaHei UI', 10),
            'bold': ('Microsoft YaHei UI', 10, 'bold'),
            'large': ('Microsoft YaHei UI', 12),
            'large_bold': ('Microsoft YaHei UI', 12, 'bold'),
            'small': ('Microsoft YaHei UI', 9),
            'title': ('Microsoft YaHei UI', 14, 'bold')
        }

    def create_ui(self) -> None:
        """创建主界面布局。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        # 主容器
        self.main_container = tk.Frame(self.root, bg=self.colors['secondary'])
        self.main_container.pack(fill='both', expand=True, padx=0, pady=0)

        # 创建三列布局
        self.create_sidebar()
        self.create_contact_list()
        self.create_chat_area()

    def create_sidebar(self) -> None:
        """创建左侧边栏。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        # 左侧边栏
        self.sidebar = tk.Frame(self.main_container, bg=self.colors['primary'], width=80)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # 用户头像和信息
        self.user_frame = tk.Frame(self.sidebar, bg=self.colors['primary'])
        self.user_frame.pack(pady=20, padx=10)

        # 用户头像
        avatar_label = tk.Label(self.user_frame, text="👤", font=('Arial', 24),
                                bg=self.colors['primary'], fg='white')
        avatar_label.pack()

        # 用户名
        """
        self.username_label = tk.Label(self.user_frame, text="我", font=self.fonts['small'],
                                 bg=self.colors['primary'], fg='white')
        """
        # self.username_label.pack(pady=(5, 0))

        # 导航按钮
        nav_buttons = [
            ("💬", "聊天", self.show_chat),
            # ("👥", "联系人", self.show_contacts),
            ("⚙️", "设置", self.show_settings)
        ]

        self.nav_frame = tk.Frame(self.sidebar, bg=self.colors['primary'])
        self.nav_frame.pack(pady=30, padx=5, fill='x')

        for icon, tooltip, command in nav_buttons:
            btn = tk.Button(self.nav_frame, text=icon, font=('Arial', 20),
                            bg=self.colors['primary'], fg='white', bd=0,
                            activebackground=self.colors['primary_dark'],
                            activeforeground='white', cursor='hand2',
                            command=command, width=3, height=2)
            btn.pack(pady=5)
            self.create_tooltip(btn, tooltip)

    def create_contact_list(self) -> None:
        """创建联系人列表区域。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        # 联系人列表区域
        self.contact_frame = tk.Frame(self.main_container, bg='white', width=320)
        self.contact_frame.pack(side='left', fill='y')
        self.contact_frame.pack_propagate(False)

        # 标题栏
        title_frame = tk.Frame(self.contact_frame, bg='white', height=60)
        title_frame.pack(fill='x', padx=20, pady=(20, 0))
        title_frame.pack_propagate(False)

        # 左侧：标题
        title_label = tk.Label(title_frame, text="消息", font=self.fonts['title'],
                               bg='white', fg=self.colors['dark'])
        title_label.pack(side='left', pady=15)

        # 右侧：添加好友按钮
        add_friend_btn = tk.Button(title_frame, text="➕", font=('Arial', 16),
                                   bg=self.colors['primary'], fg='white', bd=0,
                                   activebackground=self.colors['primary_dark'],
                                   activeforeground='white', cursor='hand2',
                                   command=self.show_add_friend_dialog,
                                   width=3, height=1, relief='flat')
        add_friend_btn.pack(side='right', pady=15)
        self.create_tooltip(add_friend_btn, "添加好友")

        # 搜索框
        """
        search_frame = tk.Frame(self.contact_frame, bg='white')
        search_frame.pack(fill='x', padx=20, pady=(0, 20))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                font=self.fonts['default'], bg=self.colors['secondary'],
                                bd=0, relief='flat', fg=self.colors['dark'])
        search_entry.pack(fill='x', ipady=8, padx=2)
        search_entry.insert(0, "🔍 搜索联系人...")
        """

        # 联系人列表容器
        list_container = tk.Frame(self.contact_frame, bg='white')
        list_container.pack(fill='both', expand=True, padx=5)

        # 创建滚动条
        self.contact_canvas = tk.Canvas(list_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=self.contact_canvas.yview)
        self.scrollable_frame = tk.Frame(self.contact_canvas, bg='white')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.contact_canvas.configure(scrollregion=self.contact_canvas.bbox("all"))
        )

        self.contact_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.contact_canvas.configure(yscrollcommand=scrollbar.set)
        # 配置滚动区域
        self.contact_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_add_friend_dialog(self) -> None:
        """显示添加好友对话框。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """

        dialog = tk.Toplevel(self.root)
        dialog.title("添加好友")
        dialog.geometry("400x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中显示
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + (self.root.winfo_width() // 2) - 200,
            self.root.winfo_rooty() + (self.root.winfo_height() // 2) - 150
        ))

        # 主容器
        main_frame = tk.Frame(dialog, bg='white', padx=30, pady=30)
        main_frame.pack(fill='both', expand=True)

        # 标题
        title_label = tk.Label(main_frame, text="添加好友", font=self.fonts['title'],
                               bg='white', fg=self.colors['dark'])
        title_label.pack(pady=(0, 20))

        # 好友ID/用户名输入
        id_frame = tk.Frame(main_frame, bg='white')
        id_frame.pack(fill='x', pady=(0, 15))

        id_label = tk.Label(id_frame, text="好友ID/用户名:", font=self.fonts['default'],
                            bg='white', fg=self.colors['dark'])
        id_label.pack(anchor='w', pady=(0, 5))

        id_entry = tk.Entry(id_frame, font=self.fonts['default'], bg=self.colors['secondary'],
                            bd=0, relief='flat', fg=self.colors['dark'])
        id_entry.pack(fill='x', ipady=8, padx=2)
        id_entry.focus()

        # 验证消息输入
        msg_frame = tk.Frame(main_frame, bg='white')
        msg_frame.pack(fill='x', pady=(0, 20))

        msg_label = tk.Label(msg_frame, text="验证口令:", font=self.fonts['default'],
                             bg='white', fg=self.colors['dark'])
        msg_label.pack(anchor='w', pady=(0, 5))

        msg_text = tk.Text(msg_frame, height=4, font=self.fonts['default'],
                           bg=self.colors['secondary'], bd=0, relief='flat',
                           fg=self.colors['dark'], wrap='word')
        msg_text.pack(fill='x', padx=2)
        msg_text.insert('1.0', "")

        # 按钮区域
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill='x', pady=(20, 0))

        # 取消按钮
        cancel_btn = tk.Button(btn_frame, text="取消", font=self.fonts['default'],
                               bg=self.colors['border'], fg=self.colors['dark'], bd=0,
                               activebackground=self.colors['hover'], cursor='hand2',
                               padx=20, pady=8, command=dialog.destroy)
        cancel_btn.pack(side='right', padx=(10, 0))

        # 添加按钮
        def add_friend():
            friend_id = id_entry.get().strip()
            verify_token = msg_text.get('1.0', tk.END).strip()

            if not friend_id:
                messagebox.showerror("错误", "请输入好友ID或用户名", parent=dialog)
                return

            # 调用添加好友的回调函数
            if self.add_friend_handler:
                success = self.add_friend_handler(friend_id, verify_token)
                if success:
                    # messagebox.showinfo("成功", f"已向 {friend_id} 发送好友请求", parent=dialog)
                    dialog.destroy()
                else:
                    # messagebox.showerror("失败", "添加好友失败，请检查ID是否正确", parent=dialog)
                    pass
            else:
                # 默认行为：显示确认消息
                messagebox.showinfo("添加好友", f"正在向 {friend_id} 发送好友请求...", parent=dialog)
                dialog.destroy()

        add_btn = tk.Button(btn_frame, text="添加好友", font=self.fonts['bold'],
                            bg=self.colors['primary'], fg='white', bd=0,
                            activebackground=self.colors['primary_dark'], cursor='hand2',
                            padx=20, pady=8, command=add_friend)
        add_btn.pack(side='right')

        # 绑定回车键
        """
        def on_enter(event):
            str(event)
            add_friend()
        """
        # dialog.bind('<Return>', on_enter)

    def set_add_friend_handler(self, handler: Callable) -> None:
        """设置添加好友的处理函数。
        
        Args:
            :param handler: 添加好友的回调函数
            
        Returns:
            :return 无返回值
        """

        self.add_friend_handler = handler

    def create_chat_area(self) -> None:
        """创建聊天区域。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        # 聊天区域
        self.chat_frame = tk.Frame(self.main_container, bg='white')
        self.chat_frame.pack(side='right', fill='both', expand=True)

        # 聊天标题栏
        self.chat_header = tk.Frame(self.chat_frame, bg='white', height=70)
        self.chat_header.pack(fill='x', padx=20, pady=(20, 0))
        self.chat_header.pack_propagate(False)

        # 默认显示
        welcome_frame = tk.Frame(self.chat_frame, bg='white')
        welcome_frame.pack(fill='both', expand=True)

        welcome_label = tk.Label(welcome_frame, text="💬\n选择一个联系人开始聊天",
                                 font=self.fonts['large'], bg='white',
                                 fg=self.colors['light'], justify='center')
        welcome_label.pack(expand=True)

        self.chat_content = welcome_frame

    def create_active_chat(self, contact: Dict[str, Any]) -> None:
        """创建活动聊天界面。
        
        Args:
            :param contact: 联系人信息字典
            
        Returns:
            :return 无返回值
        """
        # 清除当前聊天内容
        if self.chat_content:
            self.chat_content.destroy()

        # 更新聊天标题
        for widget in self.chat_header.winfo_children():
            widget.destroy()

        # 联系人信息
        contact_info = tk.Frame(self.chat_header, bg='white')
        contact_info.pack(side='left', fill='y')

        avatar_label = tk.Label(contact_info, text=contact['avatar'], font=('Arial', 20), bg='white')
        avatar_label.pack(side='left', padx=(0, 15), pady=10)

        info_frame = tk.Frame(contact_info, bg='white')
        info_frame.pack(side='left', fill='y')

        name_label = tk.Label(info_frame, text=contact['name'], font=self.fonts['large_bold'],
                              bg='white', fg=self.colors['dark'])
        name_label.pack(anchor='w', pady=(15, 0))

        # 聊天操作按钮
        action_frame = tk.Frame(self.chat_header, bg='white')
        action_frame.pack(side='right', fill='y')

        actions = []
        for action in actions:
            btn = tk.Button(action_frame, text=action, font=('Arial', 16), bg='white',
                            fg=self.colors['light'], bd=0, cursor='hand2',
                            activebackground=self.colors['hover'], padx=10)
            btn.pack(side='right', padx=5, pady=20)

        # 聊天内容区域
        self.chat_content = tk.Frame(self.chat_frame, bg='white')
        self.chat_content.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # 消息显示区域
        msg_container = tk.Frame(self.chat_content, bg='white')
        msg_container.pack(fill='both', expand=True, pady=(0, 20))

        # 消息画布和滚动条
        self.msg_canvas = tk.Canvas(msg_container, bg=self.colors['secondary'], highlightthickness=0)
        msg_scrollbar = ttk.Scrollbar(msg_container, orient='vertical', command=self.msg_canvas.yview)
        self.msg_frame = tk.Frame(self.msg_canvas, bg=self.colors['secondary'])

        # 绑定 msg_frame 的配置变化事件
        def configure_msg_frame(event):
            str(event)
            self.msg_canvas.configure(scrollregion=self.msg_canvas.bbox("all"))

        self.msg_frame.bind("<Configure>", configure_msg_frame)

        # 绑定 canvas 的配置变化事件，调整 frame 宽度
        def configure_canvas(event):
            canvas_width = event.width
            self.msg_canvas.itemconfig(self.msg_canvas.find_all()[0], width=canvas_width)

        self.msg_canvas.bind('<Configure>', configure_canvas)

        # 创建 canvas 窗口
        self.msg_canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")
        self.msg_canvas.configure(yscrollcommand=msg_scrollbar.set)

        self.msg_canvas.pack(side="left", fill="both", expand=True)
        msg_scrollbar.pack(side="right", fill="y")

        # 输入区域
        input_frame = tk.Frame(self.chat_content, bg='white', height=120)
        input_frame.pack(fill='x')
        input_frame.pack_propagate(False)

        # 工具栏
        toolbar = tk.Frame(input_frame, bg='white', height=40)
        toolbar.pack(fill='x', pady=(0, 10))
        toolbar.pack_propagate(False)

        # tools = ["😊", "📎", "🖼️", "📹"]
        tools = [{"text":"🖼️","command":lambda :self.send_picture_handler(contact)}]
        if self.is_debug():
            tools.append({"text": "toastTest", "command": lambda: self.show_toast("Test")})
        for tool in tools:
            tool_text = tool['text']

            btn = tk.Button(toolbar, text=tool_text, font=('Arial', 14), bg='white',
                            fg=self.colors['light'], bd=0, cursor='hand2',
                            activebackground=self.colors['hover'], padx=8, command=tool['command'])
            btn.pack(side='left', padx=2, pady=5)

        # 文本输入和发送区域
        text_send_frame = tk.Frame(input_frame, bg='white')
        text_send_frame.pack(fill='both', expand=True)

        # 文本输入框
        self.text_input = tk.Text(text_send_frame, font=self.fonts['default'], bg=self.colors['secondary'],
                                  bd=0, relief='flat', fg=self.colors['dark'], wrap='word', height=3)
        self.text_input.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # 发送按钮
        send_btn = tk.Button(text_send_frame, text="发送", font=self.fonts['bold'],
                             bg=self.colors['primary'], fg='white', bd=0, cursor='hand2',
                             activebackground=self.colors['primary_dark'], padx=20, pady=10,
                             command=lambda: self.send_message_handler(contact))
        send_btn.pack(side='right', pady=5)

        try:
            # 加载历史消息
            self.load_messages(contact, self.display_message)
        except _tkinter.TclError:
            pass

    def load_contacts(self) -> None:
        """加载联系人列表。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        if self.scrollable_frame:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            for contact in self.contacts:
                self.create_contact_item(contact)

    def create_contact_item(self, contact: Dict[str, Any]) -> None:
        """创建联系人列表项。
        
        Args:
            :param contact: 联系人信息字典
            
        Returns:
            :return 无返回值
        """
        item_frame = tk.Frame(self.scrollable_frame, bg='white', cursor='hand2')
        item_frame.pack(fill='x', padx=15, pady=2)
        item_frame.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        # 主要内容区域
        content_frame = tk.Frame(item_frame, bg='white')
        content_frame.pack(fill='x', pady=12)
        content_frame.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        # 头像
        avatar_label = tk.Label(content_frame, text=contact['avatar'], font=('Arial', 24), bg='white')
        avatar_label.pack(side='left', padx=(0, 12))
        avatar_label.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        # 信息区域
        info_frame = tk.Frame(content_frame, bg='white')
        info_frame.pack(side='left', fill='both', expand=True)
        info_frame.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        # 第一行：姓名和时间
        top_row = tk.Frame(info_frame, bg='white')
        top_row.pack(fill='x')
        top_row.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        name_label = tk.Label(top_row, text=contact['name'], font=self.fonts['bold'],
                              bg='white', fg=self.colors['dark'])
        name_label.pack(side='left')
        name_label.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        time_label = tk.Label(top_row, text=contact['time'], font=self.fonts['small'],
                              bg='white', fg=self.colors['light'])
        time_label.pack(side='right')
        time_label.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        # 第二行：最后消息和状态
        bottom_row = tk.Frame(info_frame, bg='white')
        bottom_row.pack(fill='x', pady=(4, 0))
        bottom_row.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        msg_label = tk.Label(bottom_row, text=contact['last_msg'], font=self.fonts['default'],
                             bg='white', fg=self.colors['light'])
        msg_label.pack(side='left')
        msg_label.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        # 状态指示器
        # status_color = self.colors['online'] if contact['status'] == '在线' else \
        #               self.colors['busy'] if contact['status'] == '忙碌' else self.colors['offline']

        # status_dot = tk.Label(bottom_row, text="●", font=self.fonts['small'],
        #                      bg='white', fg=status_color)
        # status_dot.pack(side='right')
        # status_dot.bind("<Button-1>", lambda e, c=contact: self.select_contact(c))

        # 分割线
        separator = tk.Frame(item_frame, bg=self.colors['border'], height=1)
        separator.pack(fill='x', padx=10)

        # 悬停效果
        def on_enter(e):
            str(e)
            item_frame.configure(bg=self.colors['hover'])
            content_frame.configure(bg=self.colors['hover'])
            info_frame.configure(bg=self.colors['hover'])
            top_row.configure(bg=self.colors['hover'])
            bottom_row.configure(bg=self.colors['hover'])
            for child in content_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=self.colors['hover'])
            for child in info_frame.winfo_children():
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label):
                        subchild.configure(bg=self.colors['hover'])

        def on_leave(e):
            str(e)
            item_frame.configure(bg='white')
            content_frame.configure(bg='white')
            info_frame.configure(bg='white')
            top_row.configure(bg='white')
            bottom_row.configure(bg='white')
            for child in content_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg='white')
            for child in info_frame.winfo_children():
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label):
                        subchild.configure(bg='white')

        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)

    def select_contact(self, contact: Dict[str, Any]) -> None:
        """选择联系人并切换到对应聊天。
        
        Args:
            :param contact: 联系人信息字典
            
        Returns:
            :return 无返回值
        """
        self.current_chat = contact
        self.create_active_chat(contact)

    """
    def load_messages(self, contact):
        # 模拟消息数据
        if contact['name'] not in self.messages:
            self.messages[contact['name']] = [
                {"sender": contact['name'], "content": "你好！", "time": "14:20", "type": "received"},
                {"sender": "我", "content": "嗨，最近怎么样？", "time": "14:21", "type": "sent"},
                {"sender": contact['name'], "content": contact['last_msg'], "time": contact['time'], "type": "received"}
            ]

        messages = self.messages[contact['name']]

        for msg in messages:
            self.display_message(msg)
    """

    def display_message(self, message: Dict[str, Any]) -> None:
        """显示消息到聊天界面。
        
        Args:
            :param message: 消息信息字典，包含content、time、status、sender、type等字段
            
        Returns:
            :return 无返回值
        """
        msg_container = tk.Frame(self.msg_frame, bg=self.colors['secondary'])
        # msg_container = tk.Frame(self.msg_frame, bg="#030507")
        msg_container.pack(fill='x', padx=20, pady=8)
        def show_image() -> None:
            """显示图片消息的内部函数。"""
            try:
                def on_click(event) -> None:
                    """点击图片时打开图片查看器。"""
                    viewer = imageviewer.ImageViewer(self.root, False)
                    viewer.load_image(message['content'])
                    viewer.show()
                
                image = Image.open(BytesIO(message['content']))
                # 获取图像的所有帧
                frames = []
                for frame in ImageSequence.Iterator(image):
                    frames.append(ImageTk.PhotoImage(frame))
                
                if len(frames) > 1:
                    # 动图处理
                    image_label = tk.Label(msg_bubble, image=frames[0])
                    image_label.image = frames[0]  # 保持引用
                else:
                    # 静态图处理
                    image.thumbnail((300, 300))
                    tk_image = ImageTk.PhotoImage(image)
                    image_label = tk.Label(msg_bubble, image=tk_image)
                    image_label.image = tk_image  # 保持引用
                
                image_label.bind("<Button-1>", on_click)
                image_label.pack()

                # 播放动画（仅对动图）
                if len(frames) > 1:
                    def update_frame(frame_index: int) -> None:
                        """更新动画帧。"""
                        try:
                            image_label.configure(image=frames[frame_index])
                            next_frame_index = (frame_index + 1) % len(frames)
                            self.root.after(100, update_frame, next_frame_index)
                        except Exception:
                            pass  # 忽略更新错误
                    
                    update_frame(0)
            except Exception as e:
                self.show_toast(f"图片显示失败: {str(e)}", toast_type="error")
        if message['status'] == 'sent':
            # 发送的消息（右对齐）
            msg_wrapper = tk.Frame(msg_container, bg=self.colors['secondary'])
            msg_wrapper.pack(anchor='e')

            msg_bubble = tk.Frame(msg_wrapper, bg=self.colors['primary'], padx=15, pady=10)
            msg_bubble.pack(side='right', anchor='e')

            match message['type']:
                case 'text':
                    msg_label = tk.Label(msg_bubble, text=message['content'], font=self.fonts['default'],
                                         bg=self.colors['primary'], fg='white', wraplength=3000, justify='left')
                    msg_label.pack()
                case 'image':
                    show_image()

            time_label = tk.Label(msg_wrapper, text=message['time'], font=self.fonts['small'],
                                  bg=self.colors['secondary'], fg=self.colors['light'])
            time_label.pack(side='right', padx=(0, 10), pady=(5, 0), anchor='e')

        else:
            # 接收的消息（左对齐）
            msg_wrapper = tk.Frame(msg_container, bg=self.colors['secondary'])
            msg_wrapper.pack(anchor='w')

            msg_bubble = tk.Frame(msg_wrapper, bg='white', padx=15, pady=10)
            msg_bubble.pack(side='left')
            match message['type']:
                case 'text':
                    msg_label = tk.Label(msg_bubble, text=message['content'], font=self.fonts['default'],
                                         bg='white', fg=self.colors['dark'], wraplength=3000, justify='left')
                    msg_label.pack()
                case 'image':
                    show_image()

            time_label = tk.Label(msg_wrapper, text=message['time'], font=self.fonts['small'],
                                  bg=self.colors['secondary'], fg=self.colors['light'])
            time_label.pack(side='left', padx=(10, 0), pady=(5, 0))

        # 滚动到底部
        self.msg_canvas.update_idletasks()
        self.msg_canvas.yview_moveto(1.0)

    """
    def send_message(self, contact):
        content = self.text_input.get("1.0", tk.END).strip()
        if not content:
            return

        current_time = datetime.datetime.now().strftime("%H:%M")

        message = {
            "sender": "我",
            "content": content,
            "time": current_time,
            "type": "sent"
        }

        # 添加到消息记录
        if contact['name'] not in self.messages:
            self.messages[contact['name']] = []
        self.messages[contact['name']].append(message)

        # 显示消息
        self.display_message(message)

        # 清空输入框
        self.text_input.delete("1.0", tk.END)
    """

    def create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """为控件创建工具提示。
        
        Args:
            :param widget: 需要添加工具提示的控件
            :param text: 工具提示文本
            
        Returns:
            :return 无返回值
        """
        def on_enter(e):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{e.x_root + 10}+{e.y_root + 10}")
            label = tk.Label(tooltip, text=text, font=self.fonts['small'],
                             bg='black', fg='white', padx=5, pady=2)
            label.pack()
            widget.tooltip = tooltip

        def on_leave(e):
            str(e)
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def setup_bindings(self) -> None:
        """设置快捷键绑定。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        # 快捷键绑定
        self.root.bind('<Control-Return>',
                       lambda e: self.send_message_handler(self.current_chat) if self.current_chat else None)

    def show_toast(self, message: str, duration: int = 3000, position: str = 'bottom-right', 
                   bg_color: str = '#333333', text_color: str = 'white', 
                   font: tuple = ('Arial', 10), toast_type: str = 'info') -> None:
        """显示Toast提示框。
        
        Args:
            :param message: 要显示的消息
            :param duration: 显示时长(毫秒)
            :param position: 位置 ('top-left', 'top-right', 'bottom-left', 'bottom-right', 'center')
            :param bg_color: 背景颜色
            :param text_color: 文字颜色
            :param font: 字体
            :param toast_type: 类型 ('info', 'success', 'warning', 'error')
            
        Returns:
            :return 无返回值
        """
        self.toast.show(message, duration, position, bg_color, text_color, font, toast_type)

    @staticmethod
    def show_chat() -> None:
        """显示聊天界面（静态方法）。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        # messagebox.showinfo("功能", "聊天功能已激活")
        pass

    @staticmethod
    def show_contacts() -> None:
        """显示联系人管理界面（静态方法）。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        messagebox.showinfo("功能", "联系人管理功能")
