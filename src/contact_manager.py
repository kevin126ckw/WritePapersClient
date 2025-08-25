# -*- coding: utf-8 -*-
# @Time    : 2025/8/12
# @File    : contact_manager.py
# @Software: PyCharm
# @Desc    : WritePapers客户端联系人管理模块
# @Author  : Kevin Chang

"""WritePapers客户端联系人管理模块。

本模块包含联系人管理的相关功能，包括联系人列表管理、好友添加删除等。
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any


class ContactManager:
    """联系人管理器类。
    
    负责管理客户端的联系人相关操作。
    """
    
    def __init__(self) -> None:
        """初始化联系人管理器。

        Returns:
            :return 无返回值
        """
        self.contacts: List[Dict[str, Any]] = []
    
    def add_contact(self, contact: Dict[str, Any]) -> bool:
        """添加联系人。
        
        Args:
            :param contact: 联系人信息字典
            
        Returns:
            :return 是否添加成功
        """
        if contact not in self.contacts:
            self.contacts.append(contact)
            return True
        return False
    
    def remove_contact(self, contact_id: str) -> bool:
        """删除联系人。
        
        Args:
            :param contact_id: 联系人ID
            
        Returns:
            :return 是否删除成功
        """
        for contact in self.contacts:
            if contact.get('id') == contact_id:
                self.contacts.remove(contact)
                return True
        return False
    
    def get_contact_list(self) -> List[Dict[str, Any]]:
        """获取联系人列表。

        Returns:
            :return 联系人列表
        """
        return self.contacts.copy()
    
    def find_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """查找联系人。
        
        Args:
            :param contact_id: 联系人ID
            
        Returns:
            :return 联系人信息，未找到时返回None
        """
        for contact in self.contacts:
            if contact.get('id') == contact_id:
                return contact
        return None
