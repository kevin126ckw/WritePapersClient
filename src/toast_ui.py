# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : toast_ui.py
# @Software: PyCharm
# @Desc    : WritePapers客户端Toast提示组件模块
# @Author  : Kevin Chang

"""WritePapers客户端Toast提示组件模块。

本模块包含Toast提示框的实现，支持不同类型的提示消息显示。
"""

import _tkinter
import time
import tkinter as tk
from typing import Optional


class Toast:
    """Toast提示框类。
    
    用于显示临时提示消息，支持多种样式和位置。
    """
    
    def __init__(self, parent: Optional[tk.Tk] = None) -> None:
        """初始化Toast组件。
        
        Args:
            :param parent: 父窗口对象
            
        Returns:
            :return 无返回值
        """
        self.parent = parent
        self.toast_window = None

    def show(self, message: str, duration: int = 3000, position: str = 'bottom-right', 
             bg_color: str = '#333333', text_color: str = 'white', 
             font: tuple = ('Arial', 10), toast_type: str = 'info') -> None:
        """显示Toast通知。
        
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

        # 如果已有Toast在显示，先关闭它
        if self.toast_window:
            self.toast_window.destroy()

        # 根据类型设置颜色
        colors = {
            'info': {'bg': '#2196F3', 'fg': 'white'},
            'success': {'bg': '#4CAF50', 'fg': 'white'},
            'warning': {'bg': '#FF9800', 'fg': 'white'},
            'error': {'bg': '#F44336', 'fg': 'white'}
        }

        if toast_type in colors:
            bg_color = colors[toast_type]['bg']
            text_color = colors[toast_type]['fg']

        # 创建Toast窗口
        self.toast_window = tk.Toplevel()
        self.toast_window.withdraw()  # 先隐藏窗口

        # 设置窗口属性
        self.toast_window.overrideredirect(True)  # 移除窗口边框
        self.toast_window.configure(bg=bg_color)
        self.toast_window.attributes('-topmost', True)  # 置顶显示

        # 在Windows上设置半透明效果
        try:
            self.toast_window.attributes('-alpha', 0.9)
        except Exception as e:
            str(e) # e
            pass

        # 创建标签显示消息
        label = tk.Label(
            self.toast_window,
            text=message,
            bg=bg_color,
            fg=text_color,
            font=font,
            padx=20,
            pady=10,
            wraplength=300  # 文字换行宽度
        )
        label.pack()

        # 更新窗口以获取实际大小
        self.toast_window.update_idletasks()

        # 计算窗口位置
        window_width = self.toast_window.winfo_reqwidth()
        window_height = self.toast_window.winfo_reqheight()

        # 获取父窗口的位置和尺寸
        if self.parent:
            # 更新父窗口信息
            self.parent.update_idletasks()
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
        else:
            # 如果没有父窗口，使用屏幕尺寸
            parent_x = 0
            parent_y = 0
            parent_width = self.toast_window.winfo_screenwidth()
            parent_height = self.toast_window.winfo_screenheight()

        # 根据位置参数计算在父窗口内的坐标
        margin = 20
        positions = {
            'top-left': (parent_x + margin, parent_y + margin),
            'top-right': (parent_x + parent_width - window_width - margin, parent_y + margin),
            'bottom-left': (parent_x + margin, parent_y + parent_height - window_height - margin),
            'bottom-right': (parent_x + parent_width - window_width - margin,
                             parent_y + parent_height - window_height - margin),
            'center': (parent_x + (parent_width - window_width) // 2, parent_y + (parent_height - window_height) // 2)
        }

        x, y = positions.get(position, positions['bottom-right'])

        # 设置窗口位置并显示
        self.toast_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.toast_window.deiconify()  # 显示窗口

        """
        以下代码因为太丑了而被禁用了
        # 添加透明效果（通过设置参数）
        try:
            # 这个功能在某些系统上可能不支持
            # self.toast_window.attributes('-transparentcolor', bg_color)
            pass
        except Exception as e:
            print(e) # e
            pass
        """

        # 淡入效果
        self._fade_in()

        # 设置自动消失
        int(duration)
        exec("self.toast_window.after(duration, self._fade_out)")

        # 点击关闭功能
        if label:
            try:
                label.bind('<Button-1>', lambda event: self._fade_out())
            except _tkinter.TclError:
                pass

    def _fade_in(self):
        """淡入效果"""
        try:
            alpha = 0.0
            while alpha < 0.9:
                alpha += 0.1
                self.toast_window.attributes('-alpha', alpha)
                self.toast_window.update()
                time.sleep(0.02)
        except Exception as e:
            str(e) # e
            pass

    def _fade_out(self):
        """淡出效果并关闭"""
        if not self.toast_window:
            return

        try:
            alpha = 0.9
            while alpha > 0:
                alpha -= 0.1
                self.toast_window.attributes('-alpha', alpha)
                self.toast_window.update()
                time.sleep(0.02)
        except Exception as e:
            str(e) # e
            pass
        finally:
            if self.toast_window:
                self.toast_window.destroy()
                self.toast_window = None


# 使用示例
class ToastDemo:
    def __init__(self):
        self.message_entry = None
        self.root = tk.Tk()
        self.root.title("Toast 通知演示")
        self.root.geometry("400x300")
        self.root.configure(bg='#f0f0f0')

        # 创建Toast实例
        self.toast = Toast(self.root)

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        # 标题
        title = tk.Label(
            self.root,
            text="Toast 通知演示",
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0'
        )
        title.pack(pady=20)

        # 按钮框架
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=10)

        # 不同类型的Toast按钮
        buttons = [
            ("信息提示", lambda: self.toast.show("这是一条信息提示", toast_type='info')),
            ("成功提示", lambda: self.toast.show("操作成功完成！", toast_type='success')),
            ("警告提示", lambda: self.toast.show("请注意相关风险", toast_type='warning')),
            ("错误提示", lambda: self.toast.show("操作失败，请重试", toast_type='error')),
        ]

        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                width=12,
                height=2,
                font=('Arial', 10)
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=5)

        # 位置测试按钮
        position_frame = tk.Frame(self.root, bg='#f0f0f0')
        position_frame.pack(pady=20)

        # 位置测试按钮上的说明文字
        tk.Label(
            position_frame,
            text="位置测试 (在窗口内部显示):",
            font=('Arial', 12, 'bold'),
            bg='#f0f0f0'
        ).pack()

        positions = [
            ("左上角", lambda: self.toast.show("左上角位置", position='top-left')),
            ("右上角", lambda: self.toast.show("右上角位置", position='top-right')),
            ("左下角", lambda: self.toast.show("左下角位置", position='bottom-left')),
            ("右下角", lambda: self.toast.show("右下角位置", position='bottom-right')),
            ("居中", lambda: self.toast.show("居中位置", position='center')),
        ]

        pos_frame = tk.Frame(position_frame, bg='#f0f0f0')
        pos_frame.pack(pady=10)

        for i, (text, command) in enumerate(positions):
            btn = tk.Button(
                pos_frame,
                text=text,
                command=command,
                width=8,
                font=('Arial', 9)
            )
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=2)

        # 自定义消息输入
        input_frame = tk.Frame(self.root, bg='#f0f0f0')
        input_frame.pack(pady=20)

        tk.Label(
            input_frame,
            text="自定义消息:",
            font=('Arial', 10),
            bg='#f0f0f0'
        ).pack()

        self.message_entry = tk.Entry(input_frame, width=30, font=('Arial', 10))
        self.message_entry.pack(pady=5)
        self.message_entry.insert(0, "输入自定义消息...")

        tk.Button(
            input_frame,
            text="显示Toast",
            command=self.show_custom_toast,
            font=('Arial', 10)
        ).pack(pady=5)

    def show_custom_toast(self):
        message = self.message_entry.get().strip()
        if message and message != "输入自定义消息...":
            self.toast.show(message, duration=4000)
        else:
            self.toast.show("请输入有效消息", toast_type='warning')

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    demo = ToastDemo()
    demo.run()