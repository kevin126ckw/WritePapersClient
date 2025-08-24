# WritePapers - 即时通讯客户端

WritePapers 是一个现代化的即时通讯客户端，支持文本和图片消息传输、好友管理、离线消息等功能。

## 目录结构

```
WritePapersClient/
├── docs/
├── src/
│   ├── client.py          # 客户端主程序
│   ├── ui.py              # 主界面UI
│   ├── login_ui.py        # 登录界面UI
│   ├── reg_ui.py          # 注册界面UI
│   ├── settings_ui.py     # 设置界面UI
│   ├── toast_ui.py        # Toast提示UI组件
│   ├── networking.py      # 网络通信模块
│   ├── database.py        # 数据库操作模块
│   ├── ImageViewer.py     # 图片查看器 
│   ├── paperlib.py        # 工具函数库
│   └── data/
│       ├── client.sqlite  # 数据库文件
│       └── client.xml     # 配置文件
├── tests/
├── requirements.txt       # 依赖包列表
└── README.md              # 本文件
```


## 功能特性

- 用户注册与登录
- 实时文本消息传输
- 图片消息支持（PNG、GIF格式）
- 好友管理
- 离线消息接收
- 消息历史记录
- 现代化UI界面
- 设置管理

## 安装依赖

```bash
pip install -r requirements.txt
```


## 使用方法

1. 确保服务器已启动并正确配置
2. 运行客户端：
   ```bash
   python src/client.py
   ```

## 开发说明

### 环境要求
- Python 3.10+ (推荐Python 3.13)
- Tkinter (通常随Python一起安装)
- 第三方库：structlog, pillow

### 代码规范
- 使用UTF-8编码
- 遵循PEP 8代码风格
- 函数和类都有详细文档字符串
- 变量命名使用有意义的英文名称

### 扩展建议
1. 添加更多消息类型支持（语音、视频等）
2. 增加群聊功能
3. 实现消息加密功能
4. 添加表情包支持
5. 优化UI主题和个性化设置

## 注意事项

1. 确保服务器正常运行后再启动客户端
2. 图片消息大小限制为2MB
3. 调试模式可在配置文件中启用
4. 数据库文件会自动创建和维护

## 许可证

本项目仅供学习和参考使用。