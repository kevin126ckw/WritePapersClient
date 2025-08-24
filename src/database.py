# -*- coding: utf-8 -*-
# @Time    : 2025/6/2
# @File    : database.py
# @Software: PyCharm
# @Desc    : WritePapers客户端数据库操作模块
# @Author  : Kevin Chang

"""WritePapers客户端数据库操作模块。

本模块包含客户端的数据库操作功能，包括联系人管理、聊天记录存储、元数据管理等。
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

logger = structlog.get_logger()

class Database:
    """WritePapers客户端数据库操作类。
    
    负责管理客户端的所有数据库操作，包括连接管理、数据增删改查等。
    """
    
    def __init__(self) -> None:
        """初始化数据库连接对象。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        # 全局缓存字典
        self.uid_cache: Dict[str, Any] = {}

    def connect(self, file: str) -> None:
        """建立数据库连接。
        
        Args:
            :param file: 数据库文件路径
            
        Returns:
            :return 无返回值
        """
        try:
            self.conn = sqlite3.connect(file , check_same_thread=False)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")

    def run_sql(self, command: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """执行SQL命令。
        
        Args:
            :param command: SQL命令字符串
            :param params: SQL参数元组
            
        Returns:
            :return 查询结果列表
        """
        try:
            if self.cursor is None:
                logger.error("数据库连接未建立")
                return []
            
            if params:
                self.cursor.execute(command, params)  # 参数化查询
            else:
                self.cursor.execute(command)
            
            if self.conn:
                self.conn.commit()  # 提交事务
            
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"执行 SQL 失败: {e} 欲执行的SQL语句：{command}")
            return []

    def _insert_sql(self, table: str, columns: str, values: List[Any]) -> None:
        """插入数据到指定表。
        
        Args:
            :param table: 表名
            :param columns: 列名字符串
            :param values: 值列表
            
        Returns:
            :return 无返回值
        """
        try:
            if self.cursor is None or self.conn is None:
                logger.error("数据库连接未建立")
                return
            
            # 使用 ? 占位符代替直接拼接的 values
            placeholders = ",".join(["?"] * len(values))
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(sql, tuple(values))
            self.conn.commit()
        except sqlite3.OperationalError as e:
            logger.error(f"插入数据失败: {e}")
        except sqlite3.Error as e:
            logger.error(f"插入数据失败: {e}")

    def _select_sql(self, table: str, columns: str, condition: Optional[str] = None) -> Optional[List[Tuple]]:
        """查询数据。
        
        Args:
            :param table: 表名
            :param columns: 列名字符串
            :param condition: 查询条件
            
        Returns:
            :return 查询结果列表，失败时返回None
        """
        try:
            sql = f"SELECT {columns} FROM {table}"
            if condition:
                sql += f" WHERE {condition}"
            result = self.run_sql(sql)
            return result
        except sqlite3.Error as e:
            logger.error(f"查询数据失败: {e}")
            return None
    def _update_sql(self, table: str, columns: str, values: Any, condition: str) -> None:
        """更新数据。
        
        Args:
            :param table: 表名
            :param columns: 列名
            :param values: 新值
            :param condition: 更新条件
            
        Returns:
            :return 无返回值
        """
        try:
            if self.cursor is None:
                logger.error("数据库连接未建立")
                return
            
            set_clause = f"{columns} = ?"
            self.cursor.execute(f"UPDATE {table} SET {set_clause} WHERE {condition}", (values,))
            
            if self.conn:
                self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"更新数据失败: {e}")

    def close(self) -> None:
        """关闭数据库连接。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def commit(self) -> None:
        """提交事务。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
        if self.conn:
            self.conn.commit()
    # ------------------------------------------------------------------------------------------------------------------

    def get_mem_by_uid(self, uid: Union[str, int]) -> Optional[str]:
        """根据UID获取用户昵称。
        
        Args:
            :param uid: 用户ID
            
        Returns:
            :return 用户昵称，未找到时返回None
        """
        try:
            result = self._select_sql("contact", "mem", f"id='{uid}'")
            logger.debug(f"昵称查询第一次结果：{result}")
            if not result:
                if self._select_sql("contact", "name", f"id='{uid}'"):
                    return self._select_sql("contact", "name", f"id='{uid}'")[0][0]
            return result[0][0]
        except IndexError:
            logger.error(f"未找到用户 {uid} 的昵称")
            raise ValueError(f"未找到用户 {uid} 的昵称")
        except Exception as e:
            logger.error(f"找到用户 {uid} 的昵称时发生错误{e}")
            return None
    def save_contact(self, uid: Union[str, int], username: str, name: str, mem: str) -> None:
        """保存联系人信息。
        
        Args:
            :param uid: 用户ID
            :param username: 用户名
            :param name: 昵称
            :param mem: 备注
            
        Returns:
            :return 无返回值
        """
        self._insert_sql("contact", "id, username, name, mem", [uid, username, name, mem])
        
    def save_chat_message(self, from_user: Union[str, int], to_user: Union[str, int], 
                         content: Union[str, bytes], send_time: float, message_type: str = "text") -> None:
        """保存聊天消息。
        
        Args:
            :param from_user: 发送者ID
            :param to_user: 接收者ID
            :param content: 消息内容
            :param send_time: 发送时间戳
            :param message_type: 消息类型
            
        Returns:
            :return 无返回值
        """
        self._insert_sql("chat_history", "from_user, to_user, type, content, send_time", [from_user, to_user, message_type, content, send_time])
    def get_last_chat_message(self, user_id: Union[str, int], contact_id: Union[str, int]) -> Optional[Tuple]:
        """获取最近一条聊天消息。
        
        Args:
            :param user_id: 用户ID
            :param contact_id: 联系人ID
            
        Returns:
            :return 最近一条聊天消息元组，未找到时返回None
        """
        condition = f"(from_user={user_id} AND to_user={contact_id}) OR (from_user={contact_id} AND to_user={user_id})"
        result = self._select_sql("chat_history", "*", f"{condition} ORDER BY send_time DESC LIMIT 1")
        return result[0] if result else None
    def get_metadata(self, column: str) -> Optional[Any]:
        """获取元数据。
        
        Args:
            :param column: 列名
            
        Returns:
            :return 元数据值，未找到时返回None
        """
        try:
            result = self._select_sql("meta", column)
            return result[0][0] if result else None
        except Exception as e:
            logger.error(e, exc_info=True)
    def insert_metadata(self, column: str, value: Any) -> None:
        """插入元数据。
        
        Args:
            :param column: 列名
            :param value: 值
            
        Returns:
            :return 无返回值
        """
        self._insert_sql("meta", column, [value])
    def create_tables_if_not_exists(self) -> None:
        """创建数据库表（如果不存在）。
        
        Args:
            无参数
            
        Returns:
            :return 无返回值
        """
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
    def get_contact_list(self) -> Optional[List[Tuple]]:
        """获取联系人列表。
        
        Args:
            无参数
            
        Returns:
            :return 联系人列表，未找到时返回None
        """
        contact_list = self._select_sql("contact", "mem, id, name")
        if contact_list:
            return contact_list
        else:
            return None
    def get_chat_history(self, uid: Union[str, int]) -> Optional[List[Tuple]]:
        """获取聊天记录。
        
        Args:
            :param uid: 用户ID
            
        Returns:
            :return 聊天记录列表，未找到时返回None
        """
        return self._select_sql("chat_history", "*", f"to_user={uid} or from_user={uid}")
    def check_is_friend(self, uid: Optional[Union[str, int]] = None, 
                       username: Optional[str] = None) -> Optional[bool]:
        """检查是否为好友。
        
        Args:
            :param uid: 用户ID
            :param username: 用户名
            
        Returns:
            :return 是否为好友，参数无效时返回None
        """
        if uid:
            if self._select_sql("contact", "id", f"id='{uid}'"):
                return True
            else:
                return False
        elif username:
            if self._select_sql("contact", "username", f"username='{username}'"):
                return True
            else:
                return False
        else:
            return None