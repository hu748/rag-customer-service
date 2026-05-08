import os
import json
from typing import Sequence
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict


def get_history(session_id):
    return FileChatMessageHistory(session_id, "./chat_history")

class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id, storage_path):
        self.session_id = session_id
        self.storage_path = storage_path
        self.file_path = os.path.join(storage_path, session_id)

        # ✅ 修复：正确创建文件夹
        os.makedirs(self.storage_path, exist_ok=True)

    # ✅ 修复：必须是单条 message（解决 tuple 报错）
    def add_message(self, message:  Sequence[BaseMessage]) -> None:
        # 读取现有历史
        all_messages = list(self.messages)
        # 添加单条
        all_messages.append(message)

        # 保存
        new_messages = [message_to_dict(m) for m in all_messages]
        with open(self.file_path, 'w', encoding='utf-8') as f:

            json.dump(new_messages, f, ensure_ascii=False)

    @property
    def messages(self) -> list[BaseMessage]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)