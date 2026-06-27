"""存储抽象层

提供统一的存储接口，支持 SQLite 和 Neo4j 两种后端
"""

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    def execute_query(self, cypher: str, params: dict = None) -> list[dict]:
        """执行查询"""
        pass

    @abstractmethod
    def execute_write(self, cypher: str, params: dict = None):
        """执行写入"""
        pass

    @abstractmethod
    def close(self):
        """关闭连接"""
        pass


def get_storage_backend() -> StorageBackend:
    """根据配置获取存储后端"""
    import os
    
    backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
    
    if backend == "neo4j":
        from src.graph.neo4j_client import Neo4jClient
        return Neo4jClient()
    else:
        from src.graph.sqlite_client import SQLiteClient
        return SQLiteClient()


# 全局实例
storage = get_storage_backend()
