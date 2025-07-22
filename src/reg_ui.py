import tkinter as tk
from tkinter import ttk, messagebox, filedialog
"""
import re
from PIL import Image, ImageTk
import os
"""


class RegisterUI:
    def __init__(self, window_root):
        self.agree_terms_checkbox = None
        self.confirm_password_entry = None
        self.password_entry = None
        self.username_entry = None
        self.scrollable_frame = None
        self.register_user_handler = None
        self.colors = None
        self.fonts = None
        self.avatar_label = None
        self.avatar_preview_frame = None
        self.avatar_path = None
        self.username_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.gender_var = tk.StringVar(value="保密")
        self.agree_terms_var = tk.BooleanVar()
        self.root = window_root
        self.setup_window()
        self.setup_styles()
        self.create_ui()

        # self.setup_bindings()

    def setup_window(self):
        self.root.title("WritePapers - 用户注册")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#f5f5f5')

        # 居中显示窗口
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"1000x700+{x}+{y}")

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
            'title': ('Microsoft YaHei UI', 24, 'bold'),
            'subtitle': ('Microsoft YaHei UI', 14),
            'large': ('Microsoft YaHei UI', 12),
            'default': ('Microsoft YaHei UI', 10),
            'bold': ('Microsoft YaHei UI', 10, 'bold'),
            'small': ('Microsoft YaHei UI', 9),
            'button': ('Microsoft YaHei UI', 11, 'bold')
        }


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

        # 欢迎标题
        welcome_label = tk.Label(deco_frame, text="欢迎加入", font=self.fonts['title'],
                                 bg=self.colors['primary'], fg='white')
        welcome_label.pack(pady=(50, 10))

        # 应用名称
        app_name_label = tk.Label(deco_frame, text="WritePapers", font=self.fonts['title'],
                                  bg=self.colors['primary'], fg='white')
        app_name_label.pack(pady=(0, 20))

        # 描述文字
        desc_label = tk.Label(deco_frame, text="连接你我，沟通无界\n开启全新的即时通讯体验",
                              font=self.fonts['subtitle'], bg=self.colors['primary'],
                              fg='white', justify='center')
        desc_label.pack(pady=(0, 30))

        # 装饰图标
        icon_frame = tk.Frame(deco_frame, bg=self.colors['primary'])
        icon_frame.pack(pady=20)

        icons = ["💬", "👥", "🌐", "🔒"]
        for i, icon in enumerate(icons):
            icon_label = tk.Label(icon_frame, text=icon, font=('Arial', 24),
                                  bg=self.colors['primary'], fg='white')
            icon_label.pack(pady=10)

        """
        # 已有账户提示
        login_frame = tk.Frame(deco_frame, bg=self.colors['primary'])
        login_frame.pack(side='bottom', pady=30)

        login_text = tk.Label(login_frame, text="已有账户？", font=self.fonts['default'],
                              bg=self.colors['primary'], fg='white')
        login_text.pack(side='left')

        login_btn = tk.Button(login_frame, text="立即登录", font=self.fonts['bold'],
                              bg=self.colors['primary'], fg='white', bd=0,
                              activebackground=self.colors['primary_dark'],
                              cursor='hand2', command=self.show_login)
        login_btn.pack(side='left', padx=(10, 0))
        """


    def create_right_panel(self, parent):
        # 右侧注册表单
        right_frame = tk.Frame(parent, bg='white', width=600)
        right_frame.pack(side='right', fill='both', expand=True)
        right_frame.pack_propagate(False)

        # 表单容器
        form_container = tk.Frame(right_frame, bg='white')
        form_container.pack(expand=True, fill='both', padx=60, pady=40)

        # 创建滚动区域
        canvas = tk.Canvas(form_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_container, orient='vertical', command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg='white')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 表单标题
        title_label = tk.Label(self.scrollable_frame, text="创建账户", font=self.fonts['title'],
                               bg='white', fg=self.colors['dark'])
        title_label.pack(pady=(0, 10))

        subtitle_label = tk.Label(self.scrollable_frame, text="请填写以下信息完成注册",
                                  font=self.fonts['subtitle'], bg='white', fg=self.colors['light'])
        subtitle_label.pack(pady=(0, 30))

        # 头像上传区域
        # self.create_avatar_section(scrollable_frame)

        # 表单字段
        self.create_form_fields(self.scrollable_frame)

        # 协议同意
        self.create_agreement_section(self.scrollable_frame)

        # 注册按钮
        # self.create_action_buttons(scrollable_frame)

        # 配置滚动
        canvas.pack(side="left", fill="both", expand=True)
        # scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮绑定
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

    def create_avatar_section(self, parent):
        # 头像上传区域
        avatar_frame = tk.Frame(parent, bg='white')
        avatar_frame.pack(pady=(0, 25))

        avatar_label = tk.Label(avatar_frame, text="设置头像", font=self.fonts['large'],
                                bg='white', fg=self.colors['dark'])
        avatar_label.pack()

        # 头像预览区域
        self.avatar_preview_frame = tk.Frame(avatar_frame, bg=self.colors['secondary'],
                                             width=100, height=100)
        self.avatar_preview_frame.pack(pady=(10, 0))
        self.avatar_preview_frame.pack_propagate(False)

        # 默认头像
        self.avatar_label = tk.Label(self.avatar_preview_frame, text="👤", font=('Arial', 48),
                                     bg=self.colors['secondary'], fg=self.colors['light'])
        self.avatar_label.pack(expand=True)

        # 上传按钮
        upload_btn = tk.Button(avatar_frame, text="上传头像", font=self.fonts['default'],
                               bg=self.colors['secondary'], fg=self.colors['dark'],
                               bd=0, cursor='hand2', activebackground=self.colors['hover'],
                               command=self.upload_avatar, padx=20, pady=5)
        upload_btn.pack(pady=(10, 0))

    def create_form_fields(self, parent):
        # 表单字段配置
        """
        fields = [
            ("用户名", self.username_var, "请输入用户名"),
#            ("邮箱", self.email_var, "请输入邮箱地址"),
            ("密码", self.password_var, "请输入密码", True),
            ("确认密码", self.confirm_password_var, "请再次输入密码", True)
#            ("手机号", self.phone_var, "请输入手机号码")
        ]

        for field_info in fields:
            field_name = field_info[0]
            field_var = field_info[1]
            placeholder = field_info[2]
            is_password = len(field_info) > 3 and field_info[3]

            self.create_input_field(parent, field_name, field_var, placeholder, is_password)
        """
        # 性别选择
        # self.create_gender_field(parent)
        str(parent.info)
        self.username_entry = self.create_input_field(self.scrollable_frame, "用户名", self.username_var, "请输入用户名")
        self.password_entry = self.create_input_field(self.scrollable_frame, "密码", self.password_var, "请输入密码", True)
        self.confirm_password_entry = self.create_input_field(self.scrollable_frame, "确认密码", self.confirm_password_var, "请再次输入密码", True)

    def create_input_field(self, parent, label_text, variable, placeholder, is_password=False):
        # 字段容器
        field_frame = tk.Frame(parent, bg='white')
        field_frame.pack(fill='x', pady=(0, 20))

        # 标签
        label = tk.Label(field_frame, text=label_text, font=self.fonts['default'],
                         bg='white', fg=self.colors['dark'])
        label.pack(anchor='w', pady=(0, 5))

        # 输入框容器
        input_container = tk.Frame(field_frame, bg=self.colors['input_bg'],
                                   relief='solid', bd=1, highlightthickness=1,
                                   highlightcolor=self.colors['primary'])
        input_container.pack(fill='x', ipady=12)

        # 输入框
        if is_password:
            entry = tk.Entry(input_container, textvariable=variable, font=self.fonts['default'],
                             bg=self.colors['input_bg'], fg=self.colors['dark'], bd=0,
                             relief='flat', show='*')
        else:
            entry = tk.Entry(input_container, textvariable=variable, font=self.fonts['default'],
                             bg=self.colors['input_bg'], fg=self.colors['dark'], bd=0,
                             relief='flat')
        entry.pack(fill='x', padx=15)

        # 占位符效果
        self.setup_placeholder(entry, placeholder)

        # 验证状态指示器
        status_label = tk.Label(field_frame, text="", font=self.fonts['small'],
                                bg='white', fg=self.colors['danger'])
        status_label.pack(anchor='w', pady=(2, 0))

        # 实时验证
        variable.trace('w', lambda *args: self.validate_field(label_text, variable, status_label))

        return entry

    def create_gender_field(self, parent):
        # 性别选择
        gender_frame = tk.Frame(parent, bg='white')
        gender_frame.pack(fill='x', pady=(0, 20))

        gender_label = tk.Label(gender_frame, text="性别", font=self.fonts['default'],
                                bg='white', fg=self.colors['dark'])
        gender_label.pack(anchor='w', pady=(0, 5))

        # 性别选项
        gender_options_frame = tk.Frame(gender_frame, bg='white')
        gender_options_frame.pack(anchor='w', pady=(5, 0))

        genders = [("男", "male"), ("女", "female"), ("保密", "secret")]
        for text, value in genders:
            rb = tk.Radiobutton(gender_options_frame, text=text, variable=self.gender_var,
                                value=value, font=self.fonts['default'], bg='white',
                                fg=self.colors['dark'], selectcolor=self.colors['primary'],
                                activebackground='white', activeforeground=self.colors['primary'])
            rb.pack(side='left', padx=(0, 20))

    def create_agreement_section(self, parent):
        # 协议同意区域
        agreement_frame = tk.Frame(parent, bg='white')
        agreement_frame.pack(fill='x', pady=(10, 20))

        def change_checkbox_value():
            self.agree_terms_var.set(not self.agree_terms_var.get())

        # 复选框
        self.agree_terms_checkbox = tk.Checkbutton(agreement_frame, variable=self.agree_terms_var,
                                  bg='white', activebackground='white',
                                  selectcolor='white', onvalue=True, offvalue=False, command=change_checkbox_value)
        self.agree_terms_checkbox.pack(side='left')

        # 协议文本
        agreement_text_frame = tk.Frame(agreement_frame, bg='white')
        agreement_text_frame.pack(side='left', fill='x', expand=True, padx=(5, 0))

        agreement_label = tk.Label(agreement_text_frame, text="我已阅读并同意",
                                   font=self.fonts['default'], bg='white', fg=self.colors['dark'])
        agreement_label.pack(side='left')

        terms_btn = tk.Button(agreement_text_frame, text="《用户协议》",
                              font=self.fonts['default'], bg='white', fg=self.colors['primary'],
                              bd=0, cursor='hand2', activebackground='white',
                              command=self.show_terms)
        terms_btn.pack(side='left')

        and_label = tk.Label(agreement_text_frame, text="和", font=self.fonts['default'],
                             bg='white', fg=self.colors['dark'])
        and_label.pack(side='left')

        privacy_btn = tk.Button(agreement_text_frame, text="《隐私政策》",
                                font=self.fonts['default'], bg='white', fg=self.colors['primary'],
                                bd=0, cursor='hand2', activebackground='white',
                                command=self.show_privacy)
        privacy_btn.pack(side='left')

    def create_action_buttons(self, parent):
        # 按钮区域
        button_frame = tk.Frame(parent, bg='white')
        button_frame.pack(fill='x', pady=(20, 0))

        # 注册按钮
        register_btn = tk.Button(button_frame, text="立即注册", font=self.fonts['button'],
                                 bg=self.colors['primary'], fg='white', bd=0, cursor='hand2',
                                 activebackground=self.colors['primary_dark'],
                                 command=self.register_user_handler, pady=12)
        register_btn.pack(fill='x', pady=(0, 15))

        """
        # 社交登录分割线
        divider_frame = tk.Frame(button_frame, bg='white')
        divider_frame.pack(fill='x', pady=(10, 15))

        divider_line1 = tk.Frame(divider_frame, bg=self.colors['border'], height=1)
        divider_line1.pack(side='left', fill='x', expand=True)

        divider_text = tk.Label(divider_frame, text="或", font=self.fonts['default'],
                                bg='white', fg=self.colors['light'])
        divider_text.pack(side='left', padx=15)

        divider_line2 = tk.Frame(divider_frame, bg=self.colors['border'], height=1)
        divider_line2.pack(side='right', fill='x', expand=True)

        # 社交登录按钮
        social_frame = tk.Frame(button_frame, bg='white')
        social_frame.pack(fill='x')

        social_buttons = [
            ("微信登录", "💬", self.colors['success']),
            ("QQ登录", "🐧", self.colors['accent']),
            ("微博登录", "📱", self.colors['danger'])
        ]

        for text, icon, color in social_buttons:
            btn = tk.Button(social_frame, text=f"{icon} {text}", font=self.fonts['default'],
                            bg='white', fg=color, bd=1, relief='solid', cursor='hand2',
                            activebackground=self.colors['hover'], pady=8)
            btn.pack(fill='x', pady=2)
        """

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
    def validate_field(field_name, variable, status_label):
        # 字段验证
        value = variable.get()
        str(value)
        str(field_name)
        r"""
        if field_name == "用户名":
            if len(value) < 3:
                status_label.config(text="用户名至少3个字符", fg=self.colors['danger'])
                return False
            elif not re.match("^[a-zA-Z0-9_\u4e00-\u9fa5]+$", value):
                status_label.config(text="用户名只能包含字母、数字、下划线和中文", fg=self.colors['danger'])
                return False
            else:
                status_label.config(text="✓ 用户名可用", fg=self.colors['success'])
                return True

        elif field_name == "邮箱":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                status_label.config(text="请输入有效的邮箱地址", fg=self.colors['danger'])
                return False
            else:
                status_label.config(text="✓ 邮箱格式正确", fg=self.colors['success'])
                return True

        elif field_name == "密码":
            if len(value) < 6:
                status_label.config(text="密码至少6个字符", fg=self.colors['danger'])
                return False
            elif not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
                status_label.config(text="密码必须包含字母和数字", fg=self.colors['danger'])
                return False
            else:
                status_label.config(text="✓ 密码强度良好", fg=self.colors['success'])
                return True

        elif field_name == "确认密码":
            if value != self.password_var.get():
                status_label.config(text="两次输入的密码不一致", fg=self.colors['danger'])
                return False
            else:
                status_label.config(text="✓ 密码确认一致", fg=self.colors['success'])
                return True

        elif field_name == "手机号":
            phone_pattern = r'^1[3-9]\d{9}$'
            if not re.match(phone_pattern, value):
                status_label.config(text="请输入有效的手机号码", fg=self.colors['danger'])
                return False
            else:
                status_label.config(text="✓ 手机号格式正确", fg=self.colors['success'])
                return True
        """
        status_label.config(text="")
        print("验证字段：", field_name, "值：", value)
        return True

    def upload_avatar(self):
        # 上传头像
        file_path = filedialog.askopenfilename(
            title="选择头像",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )

        if file_path:
            try:
                # 这里只是模拟，实际应用中需要PIL库来处理图片
                self.avatar_path = file_path
                self.avatar_label.config(text="📷", fg=self.colors['success'])
                messagebox.showinfo("成功", "头像上传成功！")
            except Exception as e:
                messagebox.showerror("错误", f"头像上传失败: {str(e)}")



    def validate_all_fields(self):
        # 验证所有字段
        fields = [
            ("用户名", self.username_entry.get()),
            # ("邮箱", self.email_var.get()),
            ("密码", self.password_entry.get()),
            ("确认密码", self.confirm_password_entry.get())
            # ("手机号", self.phone_var.get())
        ]

        for field_name, value in fields:
            if not value or value.startswith("请输入"):
                messagebox.showerror("错误", f"请填写{field_name}")
                return False

        return True

    def setup_bindings(self):
        # 快捷键绑定
        self.root.bind('<Return>', lambda e: self.register_user_handler())
        self.root.bind('<Escape>', lambda e: self.root.destroy())

    @staticmethod
    def show_login():
        messagebox.showinfo("登录", "跳转到登录页面")

    @staticmethod
    def show_terms():
        messagebox.showinfo("用户协议", "这里显示用户协议内容")

    @staticmethod
    def show_privacy():
        messagebox.showinfo("隐私政策", "这里显示隐私政策内容")


# 运行应用
if __name__ == "__main__":
    root = tk.Tk()
    app = RegisterUI(root)
    def register_user_handler():
        print("注册用户")
    app.register_user_handler = lambda : register_user_handler()
    root.mainloop()