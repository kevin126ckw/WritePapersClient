#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : self.py
# @Software: PyCharm
# @Desc    :
# @Author  : Kevin Chang
import sqlite3,traceback
import time
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
            logger.error(f"Error connecting to database: {e}")
            logger.traceback(traceback.format_exc())

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
        except sqlite3.Error as e:
            logger.error(f"插入数据失败: {e}")
            logger.traceback(traceback.format_exc())

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
            logger.error(f"查询数据失败: {e}")
            logger.traceback(traceback.format_exc())
            return None

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
            return result[0][0]
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return None
    def save_contact(self, uid, username, name, mem):
        self.insert_sql("contact", "id, username, name, mem", [uid, username, name, mem])
        
        