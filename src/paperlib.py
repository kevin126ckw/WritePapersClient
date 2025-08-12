# -*- coding: utf-8 -*-
# @Time    : 2025/5/1
# @File    : paperlib.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
from xml.etree import ElementTree
import os


def read_xml(keyword, path="data/"):
    """
    从指定侧的XML文件中读取对应关键字的值

    通过解析项目data目录下的client.xml文件，使用XPath查找指定关键字的文本内容。
    若XML结构不符合预期或关键字不存在，将抛出可追踪的异常。

    Args:
        :param keyword: 要查找的XML元素名称，对应xml文件中的标签名
        :param path: client.xml的相对路径
    Returns:
        :return str: 匹配到的XML元素文本内容

    Raises:
        ValueError: 当指定的关键字在XML中不存在或XML格式不符合预期时抛出

    """
    try:
        # 构建XML文件绝对路径：参数指定的目录 + client.xml
        xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{path}client.xml')

        # 解析XML文档并获取根节点
        tree = ElementTree.parse(xml_path)
        root = tree.getroot()

        # 使用XPath语法递归搜索指定关键字节点
        return root.find(f".//{keyword}").text
    except AttributeError as e:
        # 转换底层解析异常为更有业务意义的错误类型，保留原始异常堆栈信息
        raise ValueError(f"Keyword '{keyword}' not found in XML or invalid format.") from e

def write_xml(keyword, value, path="data/"):
    """
    将指定关键字的值写入XML文件

    通过解析项目data目录下的client.xml文件，使用XPath定位指定关键字节点并更新其文本内容。
    若关键字不存在或XML格式异常，将抛出可追踪的异常。

    Args:
        :param keyword: 要修改的XML元素名称（标签名）
        :param value: 要写入的新值
        :param path: client.xml的相对路径（默认' data/'）

    Raises:
        :raise ValueError: 当关键字在XML中不存在时抛出
        :raise FileNotFoundError: 当XML文件不存在时抛出
    """
    try:
        # 构建XML文件绝对路径
        xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{path}client.xml')

        # 检查文件是否存在
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"XML file not found at {xml_path}")

        # 解析XML文档
        tree = ElementTree.parse(xml_path)
        root = tree.getroot()

        # 查找目标节点
        target = root.find(f".//{keyword}")
        if target is None:
            raise ValueError(f"Keyword '{keyword}' not found in XML")

        # 更新节点文本内容
        target.text = str(value)

        # 写回文件（保留XML声明和编码格式）
        tree.write(
            xml_path,
            encoding="utf-8",
            xml_declaration=True
        )

    except ElementTree.ParseError as e:
        raise ValueError(f"Invalid XML format: {str(e)}") from e

