# -*- coding: utf-8 -*-
# @Time    : 2025/8/6
# @File    : ImageViewer.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import io
from typing import Union, Optional, List
import os


class ImageViewer:
    """
    专业的图片查看器类
    支持多种图片格式，包括GIF动图
    支持缩放、旋转等功能
    可通过二进制数据或PIL图片对象调用
    """

    def __init__(self, master: Optional[tk.Tk] = None, need_menu: bool=True):
        """
        初始化图片查看器

        Args:
            master: 父窗口，如果为None则创建新的根窗口
        """
        self.need_menu = need_menu
        self.master = master if master else tk.Tk()
        self.is_root = master is None

        # 图片相关变量
        self.original_image: Optional[Image.Image] = None
        self.display_image: Optional[Image.Image] = None
        self.photo: Optional[ImageTk.PhotoImage] = None
        self.scale_factor = 1.0
        self.rotation = 0

        # GIF动画相关
        self.gif_frames: List[Image.Image] = []
        self.current_frame = 0
        self.animation_job: Optional[str] = None
        self.frame_duration = 100  # 默认帧间隔

        # 界面组件
        self.window: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.scrollbar_v: Optional[ttk.Scrollbar] = None
        self.scrollbar_h: Optional[ttk.Scrollbar] = None
        self.status_bar: Optional[tk.Label] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置用户界面"""
        # 创建窗口
        if self.is_root:
            self.window = self.master
        else:
            self.window = tk.Toplevel(self.master)

        self.window.title("WritePapers 内建图片查看器")
        self.window.geometry("800x600")
        self.window.configure(bg='#f0f0f0')

        # 创建菜单栏
        if self.need_menu:
            self._create_menu()

        # 创建工具栏
        self._create_toolbar()

        # 创建主框架
        main_frame = tk.Frame(self.window, bg='#f0f0f0')
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 创建画布和滚动条
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg='white',
            scrollregion=(0, 0, 0, 0)
        )

        self.scrollbar_v = ttk.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollbar_h = ttk.Scrollbar(
            canvas_frame,
            orient="horizontal",
            command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar_v.set,
            xscrollcommand=self.scrollbar_h.set
        )

        # 布局画布和滚动条
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar_v.pack(side="right", fill="y")
        self.scrollbar_h.pack(side="bottom", fill="x")

        # 创建状态栏
        self.status_bar = tk.Label(
            self.window,
            text="就绪",
            relief="sunken",
            anchor="w",
            bg='#f0f0f0'
        )
        self.status_bar.pack(side="bottom", fill="x")

        # 绑定事件
        self._bind_events()

    def _create_menu(self) -> None:
        """创建菜单栏"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.close)

        # 查看菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="查看", menu=view_menu)
        view_menu.add_command(label="放大", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="缩小", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="适应窗口", command=self.fit_to_window, accelerator="Ctrl+0")
        view_menu.add_command(label="原始大小", command=self.actual_size, accelerator="Ctrl+1")

    def _create_toolbar(self) -> None:
        """创建工具栏"""
        toolbar = tk.Frame(self.window, relief="raised", bd=1, bg='#e0e0e0')
        toolbar.pack(side="top", fill="x")

        if self.need_menu:
            # 打开文件按钮
            tk.Button(
                toolbar,
                text="打开",
                command=self.open_file,
                relief="flat",
                padx=10
            ).pack(side="left", padx=2, pady=2)

            tk.Frame(toolbar, width=1, bg='gray').pack(side="left", fill="y", padx=5)

        # 缩放按钮
        tk.Button(
            toolbar,
            text="放大",
            command=self.zoom_in,
            relief="flat",
            padx=10
        ).pack(side="left", padx=2, pady=2)

        tk.Button(
            toolbar,
            text="缩小",
            command=self.zoom_out,
            relief="flat",
            padx=10
        ).pack(side="left", padx=2, pady=2)

        tk.Button(
            toolbar,
            text="适应窗口",
            command=self.fit_to_window,
            relief="flat",
            padx=10
        ).pack(side="left", padx=2, pady=2)

        tk.Button(
            toolbar,
            text="原始大小",
            command=self.actual_size,
            relief="flat",
            padx=10
        ).pack(side="left", padx=2, pady=2)

        tk.Frame(toolbar, width=1, bg='gray').pack(side="left", fill="y", padx=5)

        # 旋转按钮
        tk.Button(
            toolbar,
            text="顺时针旋转",
            command=self.rotate_clockwise,
            relief="flat",
            padx=10
        ).pack(side="left", padx=2, pady=2)

        tk.Button(
            toolbar,
            text="逆时针旋转",
            command=self.rotate_counterclockwise,
            relief="flat",
            padx=10
        ).pack(side="left", padx=2, pady=2)

    def _bind_events(self) -> None:
        """绑定事件"""
        # 键盘快捷键
        self.window.bind('<Control-o>', lambda e: self.open_file())
        self.window.bind('<Control-plus>', lambda e: self.zoom_in())
        self.window.bind('<Control-equal>', lambda e: self.zoom_in())  # 支持不按Shift的+
        self.window.bind('<Control-minus>', lambda e: self.zoom_out())
        self.window.bind('<Control-0>', lambda e: self.fit_to_window())
        self.window.bind('<Control-1>', lambda e: self.actual_size())

        # 鼠标滚轮缩放
        self.canvas.bind('<Control-Button-4>', lambda e: self.zoom_in())
        self.canvas.bind('<Control-Button-5>', lambda e: self.zoom_out())
        self.canvas.bind('<Control-MouseWheel>', self._on_mousewheel)

        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def _on_mousewheel(self, event) -> None:
        """鼠标滚轮事件处理"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def open_file(self) -> None:
        """打开文件对话框选择图片"""
        file_types = [
            ("所有支持的图片", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("GIF files", "*.gif"),
            ("BMP files", "*.bmp"),
            ("TIFF files", "*.tiff"),
            ("WebP files", "*.webp"),
            ("所有文件", "*.*")
        ]

        filename = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=file_types
        )

        if filename:
            self.load_image_from_file(filename)

    def load_image_from_file(self, filepath: str) -> bool:
        """
        从文件路径加载图片

        Args:
            filepath: 图片文件路径

        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            with Image.open(filepath) as img:
                self.load_image(img.copy())
            self.status_bar.config(text=f"已加载: {os.path.basename(filepath)}")
            return True
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")
            return False

    def load_image(self, image_data: Union[bytes, Image.Image]) -> bool:
        """
        加载图片数据

        Args:
            image_data: 图片的二进制数据或PIL图片对象

        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            # 停止当前的GIF动画
            self._stop_animation()

            # 处理输入数据
            if isinstance(image_data, bytes):
                # 二进制数据
                image = Image.open(io.BytesIO(image_data))
            elif isinstance(image_data, Image.Image):
                # PIL图片对象
                image = image_data.copy()
            else:
                raise ValueError("不支持的图片数据类型")

            self.original_image = image
            self.scale_factor = 1.0
            self.rotation = 0

            # 检查是否为GIF动画
            if hasattr(image, 'is_animated') and image.is_animated:
                self._load_gif_frames()
            else:
                self.gif_frames = []
                self.current_frame = 0

            self._update_display()
            self._update_status()

            return True

        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")
            return False

    def _load_gif_frames(self) -> None:
        """加载GIF动画的所有帧"""
        self.gif_frames = []
        try:
            frame_index = 0
            while True:
                self.original_image.seek(frame_index)
                frame = self.original_image.copy()
                self.gif_frames.append(frame)
                frame_index += 1
        except EOFError:
            pass  # 已到达最后一帧

        self.current_frame = 0
        # 获取帧间隔时间
        try:
            self.frame_duration = self.original_image.info.get('duration', 100)
        except AttributeError:
            self.frame_duration = 100

    def _update_display(self) -> None:
        """更新图片显示"""
        if not self.original_image:
            return

        try:
            # 获取当前要显示的图片
            if self.gif_frames and len(self.gif_frames) > 0:
                current_img = self.gif_frames[self.current_frame]
            else:
                current_img = self.original_image

            # 应用旋转
            if self.rotation != 0:
                current_img = current_img.rotate(self.rotation, expand=True)

            # 应用缩放
            if self.scale_factor != 1.0:
                new_width = int(current_img.width * self.scale_factor)
                new_height = int(current_img.height * self.scale_factor)
                if new_width > 0 and new_height > 0:
                    current_img = current_img.resize(
                        (new_width, new_height),
                        Image.Resampling.LANCZOS
                    )

            self.display_image = current_img
            self.photo = ImageTk.PhotoImage(current_img)

            # 清除画布并显示图片
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            # 更新滚动区域
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # 如果是GIF动画，继续播放下一帧
            if self.gif_frames and len(self.gif_frames) > 1:
                self._schedule_next_frame()

        except Exception as e:
            messagebox.showerror("错误", f"无法更新显示: {str(e)}")

    def _schedule_next_frame(self) -> None:
        """安排播放下一帧GIF动画"""
        if self.animation_job:
            self.window.after_cancel(self.animation_job)

        self.animation_job = self.window.after(
            self.frame_duration,
            self._next_frame,
        )

    def _next_frame(self) -> None:
        """播放GIF动画的下一帧"""
        if self.gif_frames:
            self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
            self._update_display()

    def _stop_animation(self) -> None:
        """停止GIF动画播放"""
        if self.animation_job:
            self.window.after_cancel(self.animation_job)
            self.animation_job = None

    def zoom_in(self) -> None:
        """放大图片"""
        if self.original_image:
            self.scale_factor *= 1.2
            self._update_display()
            self._update_status()

    def zoom_out(self) -> None:
        """缩小图片"""
        if self.original_image:
            self.scale_factor /= 1.2
            if self.scale_factor < 0.1:
                self.scale_factor = 0.1
            self._update_display()
            self._update_status()

    def fit_to_window(self) -> None:
        """适应窗口大小"""
        if not self.original_image:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            self.window.after(100, self.fit_to_window)
            return

        img_width = self.original_image.width
        img_height = self.original_image.height

        # 考虑旋转后的尺寸
        if self.rotation % 180 != 0:
            img_width, img_height = img_height, img_width

        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height

        self.scale_factor = min(scale_w, scale_h) * 0.95  # 留一点边距
        self._update_display()
        self._update_status()

    def actual_size(self) -> None:
        """显示原始大小"""
        if self.original_image:
            self.scale_factor = 1.0
            self._update_display()
            self._update_status()

    def rotate_clockwise(self) -> None:
        """顺时针旋转90度"""
        if self.original_image:
            self.rotation = (self.rotation - 90) % 360
            self._update_display()
            self._update_status()

    def rotate_counterclockwise(self) -> None:
        """逆时针旋转90度"""
        if self.original_image:
            self.rotation = (self.rotation + 90) % 360
            self._update_display()
            self._update_status()

    def _update_status(self) -> None:
        """更新状态栏"""
        if self.original_image:
            width = self.original_image.width
            height = self.original_image.height
            mode = self.original_image.mode
            zoom_percent = int(self.scale_factor * 100)

            status_text = f"尺寸: {width}×{height} | 模式: {mode} | 缩放: {zoom_percent}%"

            if self.rotation != 0:
                status_text += f" | 旋转: {self.rotation}°"

            if self.gif_frames:
                status_text += f" | GIF动画: {len(self.gif_frames)}帧"

            self.status_bar.config(text=status_text)

    def show(self) -> None:
        """显示窗口"""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_set()

    def close(self) -> None:
        """关闭窗口"""
        self._stop_animation()
        if self.is_root:
            self.window.quit()
        else:
            self.window.destroy()

    def run(self) -> None:
        """运行主循环（仅当作为独立程序运行时使用）"""
        if self.is_root:
            self.window.mainloop()


def show_image(image_data: Union[bytes, Image.Image, str], parent: Optional[tk.Tk] = None) -> ImageViewer:
    """
    便捷函数：显示图片

    Args:
        image_data: 图片数据（二进制数据、PIL图片对象或文件路径）
        parent: 父窗口

    Returns:
        ImageViewer: 图片查看器实例
    """
    _viewer = ImageViewer(parent)

    if isinstance(image_data, str):
        # 文件路径
        _viewer.load_image_from_file(image_data)
    else:
        # 二进制数据或PIL图片对象
        _viewer.load_image(image_data)

    _viewer.show()
    return _viewer


# 使用示例
if __name__ == "__main__":
    # 方式1: 作为独立程序运行
    viewer = ImageViewer()
    viewer.run()

    # 方式2: 在现有应用中使用
    # root = tk.Tk()
    # root.withdraw()  # 隐藏主窗口
    #
    # # 从文件加载
    # show_image("path/to/your/image.jpg", root)
    #
    # # 从二进制数据加载
    # with open("path/to/your/image.jpg", "rb") as f:
    #     image_data = f.read()
    # show_image(image_data, root)
    #
    # # 从PIL图片对象加载
    # from PIL import Image
    # pil_image = Image.open("path/to/your/image.jpg")
    # show_image(pil_image, root)
    #
    # root.mainloop()