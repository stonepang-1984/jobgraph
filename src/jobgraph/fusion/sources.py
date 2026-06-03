"""数据来源管理

管理不同数据来源的优先级和元数据
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class DataSourceType(Enum):
    """数据来源类型"""
    GOVERNMENT = "government"      # 政府数据
    API = "api"                    # API 接口
    COMPANY_WEBSITE = "company"    # 公司官网
    CRAWLER = "crawler"            # 爬虫
    USER_VERIFIED = "user_v"       # 用户验证
    USER = "user"                  # 用户贡献
    ADMIN = "admin"                # 管理员


# 数据来源优先级 (数值越高优先级越高)
SOURCE_PRIORITY = {
    DataSourceType.GOVERNMENT: 10,
    DataSourceType.API: 9,
    DataSourceType.COMPANY_WEBSITE: 8,
    DataSourceType.ADMIN: 7,
    DataSourceType.USER_VERIFIED: 6,
    DataSourceType.USER: 4,
    DataSourceType.CRAWLER: 3,
}


@dataclass
class DataSource:
    """数据来源信息"""
    source_type: DataSourceType
    source_name: str                    # 具体来源名称
    source_url: Optional[str] = None    # 来源 URL
    crawled_at: Optional[datetime] = None
    confidence: float = 1.0             # 置信度 0-1


@dataclass
class FieldValue:
    """带来源的字段值"""
    value: any
    source: DataSource
    updated_at: datetime
    
    @property
    def priority(self) -> int:
        return SOURCE_PRIORITY.get(self.source.source_type, 0)


class SourceManager:
    """数据来源管理器"""

    def __init__(self):
        self.sources: dict[str, DataSource] = {}

    def register_source(
        self,
        source_id: str,
        source_type: DataSourceType,
        source_name: str,
        source_url: Optional[str] = None,
        confidence: float = 1.0,
    ) -> DataSource:
        """注册数据来源"""
        source = DataSource(
            source_type=source_type,
            source_name=source_name,
            source_url=source_url,
            confidence=confidence,
        )
        self.sources[source_id] = source
        return source

    def get_source(self, source_id: str) -> Optional[DataSource]:
        """获取数据来源"""
        return self.sources.get(source_id)

    def get_priority(self, source_type: DataSourceType) -> int:
        """获取来源优先级"""
        return SOURCE_PRIORITY.get(source_type, 0)


# 预定义数据来源
PREDEFINED_SOURCES = {
    "tianyancha": DataSource(
        source_type=DataSourceType.API,
        source_name="天眼查",
        source_url="https://www.tianyancha.com",
        confidence=0.95,
    ),
    "qichacha": DataSource(
        source_type=DataSourceType.API,
        source_name="企查查",
        source_url="https://www.qcc.com",
        confidence=0.95,
    ),
    "government": DataSource(
        source_type=DataSourceType.GOVERNMENT,
        source_name="国家企业信用信息公示系统",
        source_url="https://www.gsxt.gov.cn",
        confidence=1.0,
    ),
    "company_website": DataSource(
        source_type=DataSourceType.COMPANY_WEBSITE,
        source_name="公司官网",
        confidence=0.9,
    ),
    "admin": DataSource(
        source_type=DataSourceType.ADMIN,
        source_name="管理员",
        confidence=1.0,
    ),
    "user": DataSource(
        source_type=DataSourceType.USER,
        source_name="用户贡献",
        confidence=0.7,
    ),
    "crawler": DataSource(
        source_type=DataSourceType.CRAWLER,
        source_name="数据爬虫",
        confidence=0.8,
    ),
}


# 全局实例
source_manager = SourceManager()
