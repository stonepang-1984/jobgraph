"""数据融合模块

功能:
- 数据来源管理
- 实体匹配算法
- 数据融合引擎
- 数据质量控制
- 数据血缘追踪
"""

from src.jobgraph.fusion.sources import DataSource, DataSourceType, SourceManager, source_manager, PREDEFINED_SOURCES
from src.jobgraph.fusion.matcher import EntityMatcher, entity_matcher
from src.jobgraph.fusion.engine import DataFusionEngine, DataQualityChecker, fusion_engine, quality_checker
from src.jobgraph.fusion.lineage import DataLineage, data_lineage

__all__ = [
    # 数据来源
    "DataSource",
    "DataSourceType",
    "SourceManager",
    "source_manager",
    "PREDEFINED_SOURCES",
    # 实体匹配
    "EntityMatcher",
    "entity_matcher",
    # 数据融合
    "DataFusionEngine",
    "DataQualityChecker",
    "fusion_engine",
    "quality_checker",
    # 数据血缘
    "DataLineage",
    "data_lineage",
]
