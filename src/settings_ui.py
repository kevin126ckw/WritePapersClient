import tkinter as tk
from tkinter import ttk
from structlog import get_logger
logger = get_logger()

class SettingsDialog(tk.Toplevel):
    """设置对话框类，继承自Toplevel窗口"""

    def __init__(self, parent, settings_items, cancel_flag):
        """
        初始化设置对话框
        :param parent: 父窗口
        :param settings_items: 设置项列表，格式示例：
            [{"name": "username", "label": "用户名", "type": "text", "default": "guest"},
             {"name": "dark_mode", "label": "深色模式", "type": "checkbox", "default": True}]
        """
        super().__init__(parent)
        self.title("系统设置")  # 窗口标题
        self.geometry("400x300")  # 初始窗口尺寸
        self.resizable(True, True)  # 允许调整窗口大小
        self.settings_items = settings_items  # 存储设置项配置
        self.cancel_flag = cancel_flag
        self.values = {}  # 存储当前设置值
        self.widgets = {}  # 存储界面控件引用

        # 创建主框架
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # 动态创建设置项控件
        self.create_settings_widgets(main_frame)

        # 创建按钮区域
        self.create_buttons(main_frame)


    def create_settings_widgets(self, parent_frame):
        """根据配置动态创建设置项控件"""
        for item in self.settings_items:
            # 创建每行设置项的框架
            frame = ttk.Frame(parent_frame)
            frame.pack(fill="x", padx=5, pady=5)

            # 创建标签
            label = ttk.Label(frame, text=item["label"] + ":", width=15, anchor="w")
            label.pack(side="left", padx=(0, 10))

            # 根据类型创建不同控件
            if item["type"] == "text":
                entry_var = tk.StringVar(value=item.get("default", ""))
                entry = ttk.Entry(frame, textvariable=entry_var, width=25)
                entry.pack(side="left", fill="x", expand=True)
                self.widgets[item["name"]] = entry_var  # 存储引用
                self.values[item["name"]] = item.get("default", "")  # 初始化值

            elif item["type"] == "checkbox":
                check_var = tk.BooleanVar(value=item.get("default", False))
                check = ttk.Checkbutton(frame, variable=check_var, text="")
                check.pack(side="left")
                self.widgets[item["name"]] = check_var
                self.values[item["name"]] = item.get("default", False)

    def create_buttons(self, parent_frame):
        """创建确认/取消按钮"""
        btn_frame = ttk.Frame(parent_frame)
        btn_frame.pack(fill="x", pady=10)

        # 确认按钮
        btn_ok = ttk.Button(btn_frame, text="确定", width=10, command=self.on_ok)
        btn_ok.pack(side="right", padx=(5, 0))

        # 取消按钮
        btn_cancel = ttk.Button(btn_frame, text="取消", width=10, command=self.on_cancel)
        btn_cancel.pack(side="right")

    def on_ok(self):
        """确定按钮点击事件处理"""
        # 从控件获取当前值
        for name, var in self.widgets.items():
            self.values[name] = var.get()

        # 在实际应用中这里可以添加保存设置的操作
        logger.debug("当前设置值:" + str(self.values))
        self.destroy()  # 关闭对话框

    def on_cancel(self):
        """取消按钮点击事件处理"""
        self.cancel_flag = True
        self.destroy()

    def get_settings(self):
        """获取当前设置值的字典"""
        return self.values.copy()

# 示例用法
if __name__ == "__main__":
    root = tk.Tk()
    root.title("主窗口")

    # 定义设置项配置（可扩展）
    settings_config = [
        {"name": "server", "label": "服务器地址", "type": "text", "default": "127.0.0.1"},
        {"name": "port", "label": "端口号", "type": "text", "default": "8080"},
        {"name": "auto_update", "label": "自动更新", "type": "checkbox", "default": True},
        {"name": "notifications", "label": "启用通知", "type": "checkbox", "default": False},
        {"name": "language", "label": "语言", "type": "text", "default": "English"}
    ]

    def open_settings():
        """打开设置对话框的示例函数"""
        dialog = SettingsDialog(root, settings_config, cancel_flag=False)
        root.wait_window(dialog)  # 等待对话框关闭
        logger.debug("最终设置:", dialog.get_settings())

    # 添加打开设置按钮
    btn_open = ttk.Button(root, text="打开设置", command=open_settings)
    btn_open.pack(pady=50)

    root.mainloop()
