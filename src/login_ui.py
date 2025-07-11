import tkinter as tk
from tkinter import messagebox
# from tkinter import ttk
import re
# import hashlib
import time


class LoginUI:
    def __init__(self, self_root):
        self.bottom_frame = None
        self.show_register = None
        self.login_status_label = None
        self.login_btn = None
        self.colors = None
        self.login_blocked_until = None
        self.fonts = None
        self.username_var = None
        self.password_var = None
        self.remember_var = None
        self.login_attempts = None
        self.max_attempts = None
        self.password_entry = None
        self.username_entry = None
        self.need_destroy = False
        self.validate_login_handler = None
        self.root = self_root
        self.setup_window()
        self.setup_styles()
        self.setup_variables()
        self.create_ui()
        self.setup_bindings()

    def setup_window(self):
        self.root.title("WritePapers - 用户登录")
        self.root.geometry("1320x780")
        self.root.resizable(True, True)
        self.root.configure(bg='#f5f5f5')

        # 居中显示窗口
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"1320x780+{x}+{y}")

    def setup_styles(self):
        # 与IM界面保持一致的配色方案
        self.colors = {
            'primary': '#4f46e5',  # 主色调 - 靛蓝
            'primary_dark': '#3730a3',  # 深主色
            'primary_light': '#6366f1',  # 浅主色
            'secondary': '#f8fafc',  # 次要背景色
            'accent': '#06b6d4',  # 强调色 - 青色
            'success': '#10b981',  # 成功色 - 绿色
            'warning': '#f59e0b',  # 警告色 - 黄色
            'danger': '#ef4444',  # 危险色 - 红色
            'dark': '#1f2937',  # 深色文字
            'light': '#6b7280',  # 浅色文字
            'border': '#e5e7eb',  # 边框色
            'hover': '#f3f4f6',  # 悬停色
            'input_bg': '#ffffff',  # 输入框背景
            'gradient_start': '#667eea',  # 渐变起始色
            'gradient_end': '#764ba2'  # 渐变结束色
        }

        # 字体配置
        self.fonts = {
            'title': ('Microsoft YaHei UI', 28, 'bold'),
            'subtitle': ('Microsoft YaHei UI', 16),
            'large': ('Microsoft YaHei UI', 14),
            'default': ('Microsoft YaHei UI', 11),
            'bold': ('Microsoft YaHei UI', 11, 'bold'),
            'small': ('Microsoft YaHei UI', 9),
            'button': ('Microsoft YaHei UI', 12, 'bold')
        }

    def setup_variables(self):
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar()
        self.login_attempts = 0
        self.max_attempts = 5
        self.login_blocked_until = 0

    def create_ui(self):
        # 主容器
        main_frame = tk.Frame(self.root, bg='#f5f5f5')
        main_frame.pack(fill='both', expand=True)

        # 创建左右两栏布局
        self.create_left_panel(main_frame)
        self.create_right_panel(main_frame)

    def create_left_panel(self, parent):
        # 左侧装饰面板
        left_frame = tk.Frame(parent, bg=self.colors['primary'], width=400)
        left_frame.pack(side='left', fill='y')
        left_frame.pack_propagate(False)

        # 装饰内容
        deco_frame = tk.Frame(left_frame, bg=self.colors['primary'])
        deco_frame.pack(expand=True, fill='both', padx=50, pady=50)

        # 品牌Logo区域
        logo_frame = tk.Frame(deco_frame, bg=self.colors['primary'])
        logo_frame.pack(pady=(30, 20))

        # 应用Logo
        logo_label = tk.Label(logo_frame, text="💬", font=('Arial', 48),
                              bg=self.colors['primary'], fg='white')
        logo_label.pack()

        # 应用名称
        app_name_label = tk.Label(logo_frame, text="WritePapers", font=self.fonts['title'],
                                  bg=self.colors['primary'], fg='white')
        app_name_label.pack(pady=(10, 0))

        # 欢迎标语
        welcome_label = tk.Label(deco_frame, text="欢迎回来！", font=self.fonts['subtitle'],
                                 bg=self.colors['primary'], fg='white')
        welcome_label.pack(pady=(30, 10))

        # 描述文字
        desc_label = tk.Label(deco_frame, text="登录您的账户\n继续畅快沟通",
                              font=self.fonts['large'], bg=self.colors['primary'],
                              fg='white', justify='center')
        desc_label.pack(pady=(0, 40))

        # 功能特色展示
        features_frame = tk.Frame(deco_frame, bg=self.colors['primary'])
        features_frame.pack(pady=20)

        features = [
            ("🔐", "安全加密"),
            ("⚡", "极速体验"),
            ("🌐", "多端同步"),
            ("👥", "群聊协作")
        ]

        for icon, text in features:
            feature_item = tk.Frame(features_frame, bg=self.colors['primary'])
            feature_item.pack(pady=8)

            icon_label = tk.Label(feature_item, text=icon, font=('Arial', 20),
                                  bg=self.colors['primary'], fg='white')
            icon_label.pack(side='left', padx=(0, 15))

            text_label = tk.Label(feature_item, text=text, font=self.fonts['default'],
                                  bg=self.colors['primary'], fg='white')
            text_label.pack(side='left')

        # 底部提示
        self.bottom_frame = tk.Frame(deco_frame, bg=self.colors['primary'])
        self.bottom_frame.pack(side='bottom', pady=20)

        new_user_label = tk.Label(self.bottom_frame, text="还没有账户？", font=self.fonts['default'],
                                  bg=self.colors['primary'], fg='white')
        new_user_label.pack(side='left')
    def create_register(self):
        register_btn = tk.Button(self.bottom_frame, text="立即注册", font=self.fonts['bold'],
                                 bg=self.colors['primary'], fg='white', bd=0,
                                 activebackground=self.colors['primary_dark'],
                                 cursor='hand2', command=self.show_register,
                                 relief='flat')
        register_btn.pack(side='left', padx=(10, 0))

    def create_right_panel(self, parent):
        # 右侧登录表单
        right_frame = tk.Frame(parent, bg='white', width=500)
        right_frame.pack(side='right', fill='both', expand=True)
        right_frame.pack_propagate(False)

        # 表单容器
        form_container = tk.Frame(right_frame, bg='white')
        form_container.pack(expand=True, fill='both', padx=60, pady=60)

        # 登录标题
        title_label = tk.Label(form_container, text="登录账户", font=self.fonts['title'],
                               bg='white', fg=self.colors['dark'])
        title_label.pack(pady=(0, 10))

        subtitle_label = tk.Label(form_container, text="请输入您的登录信息",
                                  font=self.fonts['subtitle'], bg='white', fg=self.colors['light'])
        subtitle_label.pack(pady=(0, 40))

        # 登录表单
        self.create_login_form(form_container)

        # 登录选项
        self.create_login_options(form_container)

        # 登录按钮
        self.create_login_button(form_container)

        # 分割线
        # self.create_divider(form_container)

        # 社交登录
        # self.create_social_login(form_container)

        # 其他链接
        self.create_footer_links(form_container)

    def create_login_form(self, parent):
        # 表单区域
        form_frame = tk.Frame(parent, bg='white')
        form_frame.pack(fill='x', pady=(0, 30))

        # 用户名输入
        self.username_entry = self.create_input_field(form_frame, "用户名/邮箱", self.username_var,
                                "请输入用户名", icon="👤")

        # 密码输入
        self.password_entry = self.create_input_field(form_frame, "密码", self.password_var,
                                "请输入密码", icon="🔒", is_password=True)

    def create_input_field(self, parent, label_text, variable, placeholder, icon=None, is_password=False):
        # 字段容器
        field_frame = tk.Frame(parent, bg='white')
        field_frame.pack(fill='x', pady=(0, 25))

        # 标签
        label = tk.Label(field_frame, text=label_text, font=self.fonts['default'],
                         bg='white', fg=self.colors['dark'])
        label.pack(anchor='w', pady=(0, 8))

        # 输入框容器
        input_container = tk.Frame(field_frame, bg=self.colors['input_bg'],
                                   relief='solid', bd=1)
        input_container.pack(fill='x', ipady=15)

        # 图标
        if icon:
            icon_label = tk.Label(input_container, text=icon, font=('Arial', 16),
                                  bg=self.colors['input_bg'], fg=self.colors['light'])
            icon_label.pack(side='left', padx=(15, 5))

        # 输入框
        if is_password:
            entry = tk.Entry(input_container, textvariable=variable, font=self.fonts['default'],
                             bg=self.colors['input_bg'], fg=self.colors['dark'], bd=0,
                             relief='flat', show='*')
        else:
            entry = tk.Entry(input_container, textvariable=variable, font=self.fonts['default'],
                             bg=self.colors['input_bg'], fg=self.colors['dark'], bd=0,
                             relief='flat')
        entry.pack(side='left', fill='x', expand=True, padx=(5, 15))

        # 占位符效果
        self.setup_placeholder(entry, placeholder)

        # 焦点效果
        def on_focus_in(event):
            str(event)
            input_container.configure(highlightbackground=self.colors['primary'],
                                      highlightcolor=self.colors['primary'],
                                      highlightthickness=2)

        def on_focus_out(event):
            str(event)
            input_container.configure(highlightthickness=0)

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

        # 密码显示切换
        if is_password:
            show_btn = tk.Button(input_container, text="👁", font=('Arial', 12),
                                 bg=self.colors['input_bg'], fg=self.colors['light'],
                                 bd=0, cursor='hand2', activebackground=self.colors['input_bg'],
                                 command=lambda: self.toggle_password_visibility(entry, show_btn))
            show_btn.pack(side='right', padx=(0, 15))
        return entry

    def create_login_options(self, parent):
        # 登录选项
        options_frame = tk.Frame(parent, bg='white')
        options_frame.pack(fill='x', pady=(0, 30))

        # 记住我
        remember_frame = tk.Frame(options_frame, bg='white')
        remember_frame.pack(side='left')

        remember_check = tk.Checkbutton(remember_frame, variable=self.remember_var,
                                        bg='white', activebackground='white',
                                        selectcolor=self.colors['primary'],
                                        font=self.fonts['default'], text="记住我",
                                        fg=self.colors['dark'])
        remember_check.pack(side='left')

        # 忘记密码
        """
        forgot_btn = tk.Button(options_frame, text="忘记密码？", font=self.fonts['default'],
                               bg='white', fg=self.colors['primary'], bd=0, cursor='hand2',
                               activebackground='white', activeforeground=self.colors['primary_dark'],
                               command=self.show_forgot_password)
        forgot_btn.pack(side='right')
        """

    def create_login_button(self, parent):
        # 登录按钮容器
        button_frame = tk.Frame(parent, bg='white')
        button_frame.pack(fill='x', pady=(0, 30))

        # 登录按钮
        self.login_btn = tk.Button(button_frame, text="登录", font=self.fonts['button'],
                                   bg=self.colors['primary'], fg='white', bd=0, cursor='hand2',
                                   activebackground=self.colors['primary_dark'],
                                   command=self.login_user, pady=15)
        self.login_btn.pack(fill='x')

        # 登录状态提示
        self.login_status_label = tk.Label(button_frame, text="", font=self.fonts['small'],
                                           bg='white', fg=self.colors['danger'])
        self.login_status_label.pack(pady=(10, 0))

    def create_divider(self, parent):
        # 分割线
        divider_frame = tk.Frame(parent, bg='white')
        divider_frame.pack(fill='x', pady=(20, 30))

        divider_line1 = tk.Frame(divider_frame, bg=self.colors['border'], height=1)
        divider_line1.pack(side='left', fill='x', expand=True)

        divider_text = tk.Label(divider_frame, text="或", font=self.fonts['default'],
                                bg='white', fg=self.colors['light'])
        divider_text.pack(side='left', padx=20)

        divider_line2 = tk.Frame(divider_frame, bg=self.colors['border'], height=1)
        divider_line2.pack(side='right', fill='x', expand=True)

    def create_social_login(self, parent):
        # 社交登录
        social_frame = tk.Frame(parent, bg='white')
        social_frame.pack(fill='x', pady=(0, 30))

        social_title = tk.Label(social_frame, text="快速登录", font=self.fonts['default'],
                                bg='white', fg=self.colors['dark'])
        social_title.pack(pady=(0, 15))

        # 社交登录按钮
        social_buttons_frame = tk.Frame(social_frame, bg='white')
        social_buttons_frame.pack()

        social_buttons = [
            ("微信", "💬", self.colors['success']),
            ("QQ", "🐧", self.colors['accent']),
            ("微博", "📱", self.colors['danger'])
        ]

        for i, (name, icon, color) in enumerate(social_buttons):
            btn = tk.Button(social_buttons_frame, text=icon, font=('Arial', 24),
                            bg='white', fg=color, bd=1, relief='solid', cursor='hand2',
                            activebackground=self.colors['hover'], width=4, height=2,
                            command=lambda n=name: self.social_login(n))
            btn.pack(side='left', padx=10)

            # 添加工具提示
            self.create_tooltip(btn, f"{name}登录")

    def create_footer_links(self, parent):
        # 底部链接
        footer_frame = tk.Frame(parent, bg='white')
        footer_frame.pack(fill='x', pady=(20, 0))

        links = [
            ("帮助中心", self.show_help),
            ("隐私政策", self.show_privacy),
            ("用户协议", self.show_terms)
        ]

        for i, (text, command) in enumerate(links):
            if i > 0:
                separator = tk.Label(footer_frame, text="·", font=self.fonts['default'],
                                     bg='white', fg=self.colors['light'])
                separator.pack(side='left', padx=5)

            link_btn = tk.Button(footer_frame, text=text, font=self.fonts['small'],
                                 bg='white', fg=self.colors['light'], bd=0, cursor='hand2',
                                 activebackground='white', activeforeground=self.colors['primary'],
                                 command=command)
            link_btn.pack(side='left')

        # 版本信息
        version_label = tk.Label(footer_frame, text="v1.0.0", font=self.fonts['small'],
                                 bg='white', fg=self.colors['light'])
        version_label.pack(side='right')

    def setup_placeholder(self, entry, placeholder):
        # 占位符效果
        entry.insert(0, placeholder)
        entry.config(fg=self.colors['light'])

        def on_focus_in(event):
            str(event)
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg=self.colors['dark'])

        def on_focus_out(event):
            str(event)
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=self.colors['light'])

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    @staticmethod
    def toggle_password_visibility(entry, button):
        # 切换密码可见性
        if entry.cget('show') == '*':
            entry.config(show='')
            button.config(text='🙈')
        else:
            entry.config(show='*')
            button.config(text='👁')

    def create_tooltip(self, widget, text):
        # 工具提示
        def on_enter(e):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{e.x_root + 10}+{e.y_root + 10}")
            tooltip.configure(bg='black')
            label = tk.Label(tooltip, text=text, font=self.fonts['small'],
                             bg='black', fg='white', padx=8, pady=4)
            label.pack()
            widget.tooltip = tooltip

        def on_leave(e):
            str(e)
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def login_user(self):
        # 检查登录限制
        if time.time() < self.login_blocked_until:
            remaining_time = int(self.login_blocked_until - time.time())
            self.login_status_label.config(text=f"登录失败次数过多，请等待 {remaining_time} 秒后重试")
            return

        # 获取输入值
        username = self.username_var.get()
        password = self.password_var.get()

        # 基本验证
        if not username or username.startswith("请输入"):
            self.login_status_label.config(text="请输入用户名或邮箱")
            return

        if not password or password.startswith("请输入"):
            self.login_status_label.config(text="请输入密码")
            return

        """
        # 模拟登录验证
        if self.validate_login_handler(username, password):
            self.login_status_label.config(text="登录成功，正在跳转...", fg=self.colors['success'])
            self.login_btn.config(text="登录中...", state='disabled')

            # 模拟登录延迟
            # self.root.after(1500, self.login_success)
        else:
            self.login_attempts += 1
            if self.login_attempts >= self.max_attempts:
                self.login_blocked_until = time.time() + 300  # 5分钟锁定
                self.login_status_label.config(text="登录失败次数过多，账户已锁定5分钟")
                self.login_btn.config(state='disabled')
                self.root.after(300000, self.unlock_login)  # 5分钟后解锁
            else:
                remaining_attempts = self.max_attempts - self.login_attempts
                self.login_status_label.config(text=f"用户名或密码错误，还有 {remaining_attempts} 次尝试机会")
        """

        self.validate_login_handler(username, password)
        """
        time.sleep(0.3)
        if self.need_destroy:
            self.root.after(0,self.login_success())
        else:
            print("登录失败")
        """
        # self.root.after(0,self.login_success())


    @staticmethod
    def validate_login(username, password):
        # 模拟登录验证（实际应用中应该连接到后端服务）
        valid_users = {
            "admin": "123456",
            "user@example.com": "password",
            "test": "test123"
        }

        return username in valid_users and valid_users[username] == password

    def login_success(self):
        # 登录成功
        # messagebox.showinfo("登录成功", "欢迎回来！正在为您启动应用...")
        self.root.quit()
        self.root.destroy()

    def unlock_login(self):
        # 解锁登录
        self.login_attempts = 0
        self.login_blocked_until = 0
        self.login_btn.config(state='normal')
        self.login_status_label.config(text="")

    @staticmethod
    def social_login(platform):
        # 社交登录
        messagebox.showinfo("社交登录", f"正在使用{platform}登录...")

    def setup_bindings(self):
        # 快捷键绑定
        self.root.bind('<Return>', lambda e: self.login_user())
        self.root.bind('<Escape>', lambda e: self.root.destroy())


    def show_forgot_password(self):
        # 忘记密码对话框
        forgot_window = tk.Toplevel(self.root)
        forgot_window.title("找回密码")
        forgot_window.geometry("400x300")
        forgot_window.resizable(False, False)
        forgot_window.configure(bg='white')

        # 居中显示
        forgot_window.update_idletasks()
        x = (forgot_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (forgot_window.winfo_screenheight() // 2) - (300 // 2)
        forgot_window.geometry(f"400x300+{x}+{y}")

        # 内容
        content_frame = tk.Frame(forgot_window, bg='white')
        content_frame.pack(expand=True, fill='both', padx=40, pady=40)

        title_label = tk.Label(content_frame, text="找回密码", font=self.fonts['large'],
                               bg='white', fg=self.colors['dark'])
        title_label.pack(pady=(0, 20))

        desc_label = tk.Label(content_frame, text="请输入您的邮箱地址\n我们将发送重置链接到您的邮箱",
                              font=self.fonts['default'], bg='white', fg=self.colors['light'],
                              justify='center')
        desc_label.pack(pady=(0, 30))

        # 邮箱输入
        email_var = tk.StringVar()
        email_entry = tk.Entry(content_frame, textvariable=email_var, font=self.fonts['default'],
                               bg=self.colors['secondary'], bd=0, relief='flat')
        email_entry.pack(fill='x', ipady=10, pady=(0, 30))
        email_entry.insert(0, "请输入邮箱地址")
        self.setup_placeholder(email_entry, "请输入邮箱地址")

        # 发送按钮
        send_btn = tk.Button(content_frame, text="发送重置链接", font=self.fonts['button'],
                             bg=self.colors['primary'], fg='white', bd=0, cursor='hand2',
                             activebackground=self.colors['primary_dark'], pady=10,
                             command=lambda: self.send_reset_email(email_var.get(), forgot_window))
        send_btn.pack(fill='x')

    @staticmethod
    def send_reset_email(email, window):
        # 发送重置邮件
        if not email or email.startswith("请输入"):
            messagebox.showerror("错误", "请输入邮箱地址")
            return

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messagebox.showerror("错误", "请输入有效的邮箱地址")
            return

        messagebox.showinfo("成功", f"重置链接已发送到 {email}\n请查收邮件并按照说明操作")
        window.destroy()

    def destroy_window(self):
        self.root.destroy()

    @staticmethod
    def show_help():
        messagebox.showinfo("帮助中心", "这里是帮助中心内容")

    @staticmethod
    def show_privacy():
        messagebox.showinfo("隐私政策", "这里是隐私政策内容")

    @staticmethod
    def show_terms():
        messagebox.showinfo("用户协议", "这里是用户协议内容")


# 运行应用
if __name__ == "__main__":
    def show_register():
        messagebox.showinfo("功能", "注册功能已激活")
    root = tk.Tk()
    app = LoginUI(root)
    app.show_register = lambda : show_register()
    root.mainloop()