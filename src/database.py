#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : self.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
import sqlite3

import structlog

logger = structlog.get_logger()

class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        # 全局缓存字典
        self.uid_cache = {}

    def connect(self, file):
        """
        建立数据库连接
        Args:
            :param file: 文件路径
        """
        try:
            self.conn = sqlite3.connect(file , check_same_thread=False)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}",exec_info=True)

    def run_sql(self, command, params=None):
        """
        执行 SQL 命令
        Args:
            :param command: SQL命令
            :param params: 参数
        """
        try:
            if params:
                self.cursor.execute(command, params)  # 参数化查询
            else:
                self.cursor.execute(command)
            self.conn.commit()  # 提交事务
        except sqlite3.Error as e:
            logger.error(f"执行 SQL 失败: {e} 欲执行的SQL语句：{command}")
        return self.cursor.fetchall()

    def insert_sql(self, table, columns, values):
        """
        插入数据
        Args:
            :param table: 表
            :param columns: 列
            :param values: 值
        """
        try:
            # 使用 ? 占位符代替直接拼接的 values
            placeholders = ",".join(["?"] * len(values))
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(sql, tuple(values))
            self.conn.commit()
        except sqlite3.OperationalError as e:
            logger.error(f"插入数据失败: {e}")
        except sqlite3.Error as e:
            logger.error(f"插入数据失败: {e}",exec_info=True)

    def select_sql(self, table, columns, condition=None):
        """
        查询数据
        Args:
            :param table: 表
            :param columns: 列
            :param condition: 条件
        """
        try:
            sql = f"SELECT {columns} FROM {table}"
            if condition:
                sql += f" WHERE {condition}"
            result = self.run_sql(sql)
            return result
        except sqlite3.Error as e:
            logger.error(f"查询数据失败: {e}",exec_info=True)
            return None
    def update_sql(self, table, columns, values, condition):
        """
        Args:
            :param table: 表
            :param columns: 列
            :param values: 值
            :param condition: 条件
        """
        try:
            set_clause = f"{columns} = ?"
            self.cursor.execute(f"UPDATE {table} SET {set_clause} WHERE {condition}", (values,))
        except sqlite3.Error as e:
            logger.error(f"更新数据失败: {e}",exec_info=True)

    def close(self):
        """
        关闭数据库连接
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def commit(self):
        """
        提交事务
        """
        if self.conn:
            self.conn.commit()
    # ------------------------------------------------------------------------------------------------------------------

    def get_mem_by_uid(self, uid):
        """
        根据 uid 获取 昵称
        Args:
            :param uid: 用户id
        Returns:
            :return str:昵称
        """
        try:
            result = self.select_sql("contact", "mem", f"id='{uid}'")
            logger.debug(f"昵称查询第一次结果：{result}")
            if not result:
                if self.select_sql("contact", "name", f"id='{uid}'"):
                    return self.select_sql("contact", "name", f"id='{uid}'")[0][0]
            return result[0][0]
        except IndexError:
            logger.error(f"未找到用户 {uid} 的昵称",exc_info=True)
            return None
        except Exception as e:
            logger.error(f"找到用户 {uid} 的昵称时发生错误{e}",exec_info=True)
            return None
    def save_contact(self, uid, username, name, mem):
        """
        保存联系人信息
        Args:
            :param uid: 用户id
            :param username: 用户名
            :param name: 昵称
            :param mem: 备注
        """
        self.insert_sql("contact", "id, username, name, mem", [uid, username, name, mem])
        
    def save_chat_message(self, from_user, to_user, content, send_time, message_type="text"):
        """
        保存聊天消息
        Args:
            :param from_user: 发送者id
            :param to_user: 接收者id
            :param content: 消息内容
            :param send_time: 发送时间
            :param message_type: 消息类型
        """
        self.insert_sql("chat_history", "from_user, to_user, type, content, send_time", [from_user, to_user, message_type, content, send_time])
    def get_last_chat_message(self, user_id, contact_id):
        """
        获取最近一条聊天消息
        Args:
            :param user_id: 用户id
            :param contact_id: 联系人id
        Returns:
            :return list: 最近一条聊天消息
        """
        condition = f"(from_user={user_id} AND to_user={contact_id}) OR (from_user={contact_id} AND to_user={user_id})"
        return self.select_sql("chat_history", "*", f"{condition} ORDER BY send_time DESC LIMIT 1")
    def get_metadata(self, column):
        """
        获取元数据
        Args:
            :param column: 列名
        Returns:
            :return: 元数据
        """
        try:
            result = self.select_sql("meta", column)
            return result[0][0] if result else None
        except Exception as e:
            logger.error(e, exc_info=True)
    def run_sql_file(self, sql_file):
        with open(sql_file, encoding='utf-8', mode='r') as f:
            # 读取整个sql文件，以分号切割。[:-1]删除最后一个元素，也就是空字符串
            sql_list = f.read().split(';')[:-1]
            for x in sql_list:
                # 判断包含空行的
                if '\n' in x:
                    # 替换空行为1个空格
                    x = x.replace('\n', ' ')

                # 判断多个空格时
                if '    ' in x:
                    # 替换为空
                    x = x.replace('    ', '')

                # sql语句添加分号结尾
                sql_item = x + ';'
                self.run_sql(sql_item)
    def create_tables_if_not_exists(self):
        sql_item1 = """
        create table if not exists chat_history
(
    "index"   integer
        constraint chat_history_pk
            primary key autoincrement,
    from_user INTEGER,
    to_user   INTEGER,
    type      TEXT,
    content   ANY TEXT,
    send_time integer
);
        """
        sql_item2 = """
        create unique index if not exists chat_history_index
    on chat_history ("index");
        """
        sql_item3 = """
        create table if not exists contact
(
    id       integer
        constraint contact_pk
            primary key autoincrement,
    username TEXT,
    name     text,
    mem      text
);

        """
        sql_item4 = """
        create table if not exists meta
(
    uid integer
)
    strict;
        """
        self.run_sql(sql_item1)
        self.run_sql(sql_item2)
        self.run_sql(sql_item3)
        self.run_sql(sql_item4)