"""数据血缘追踪

记录数据的来源、变更历史
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger

from src.graph.neo4j_client import neo4j_client


class DataLineage:
    """数据血缘管理"""

    def __init__(self):
        self.lineage_dir = Path("data/lineage")
        self.lineage_dir.mkdir(parents=True, exist_ok=True)

    def record_source(
        self,
        entity_id: str,
        entity_type: str,
        field: str,
        value: any,
        source: str,
        confidence: float = 1.0,
    ) -> None:
        """记录数据来源

        Args:
            entity_id: 实体 ID
            entity_type: 实体类型 (company/job/review)
            field: 字段名
            value: 字段值
            source: 数据来源
            confidence: 置信度
        """
        try:
            cypher = """
            MERGE (l:DataLineage {
                entity_id: $entity_id,
                entity_type: $entity_type,
                field: $field
            })
            SET l.value = $value,
                l.source = $source,
                l.confidence = $confidence,
                l.updated_at = datetime()
            WITH l
            MATCH (e {id: $entity_id})
            MERGE (e)-[:HAS_LINEAGE]->(l)
            """
            neo4j_client.execute_write(
                cypher,
                {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "field": field,
                    "value": str(value),
                    "source": source,
                    "confidence": confidence,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to record lineage: {e}")

    def record_change(
        self,
        entity_id: str,
        entity_type: str,
        field: str,
        old_value: any,
        new_value: any,
        source: str,
        reason: str = "",
    ) -> None:
        """记录数据变更

        Args:
            entity_id: 实体 ID
            entity_type: 实体类型
            field: 字段名
            old_value: 旧值
            new_value: 新值
            source: 数据来源
            reason: 变更原因
        """
        try:
            cypher = """
            CREATE (c:DataChange {
                entity_id: $entity_id,
                entity_type: $entity_type,
                field: $field,
                old_value: $old_value,
                new_value: $new_value,
                source: $source,
                reason: $reason,
                changed_at: datetime()
            })
            """
            neo4j_client.execute_write(
                cypher,
                {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "field": field,
                    "old_value": str(old_value),
                    "new_value": str(new_value),
                    "source": source,
                    "reason": reason,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to record change: {e}")

    def get_lineage(self, entity_id: str, field: Optional[str] = None) -> list[dict]:
        """获取数据血缘

        Args:
            entity_id: 实体 ID
            field: 字段名 (可选)

        Returns:
            血缘记录列表
        """
        try:
            if field:
                cypher = """
                MATCH (l:DataLineage {entity_id: $entity_id, field: $field})
                RETURN l
                ORDER BY l.updated_at DESC
                """
                return neo4j_client.execute_query(
                    cypher, {"entity_id": entity_id, "field": field}
                )
            else:
                cypher = """
                MATCH (l:DataLineage {entity_id: $entity_id})
                RETURN l
                ORDER BY l.field, l.updated_at DESC
                """
                return neo4j_client.execute_query(cypher, {"entity_id": entity_id})
        except Exception as e:
            logger.warning(f"Failed to get lineage: {e}")
            return []

    def get_changes(self, entity_id: str, limit: int = 50) -> list[dict]:
        """获取数据变更历史

        Args:
            entity_id: 实体 ID
            limit: 返回数量限制

        Returns:
            变更记录列表
        """
        try:
            cypher = """
            MATCH (c:DataChange {entity_id: $entity_id})
            RETURN c
            ORDER BY c.changed_at DESC
            LIMIT $limit
            """
            return neo4j_client.execute_query(
                cypher, {"entity_id": entity_id, "limit": limit}
            )
        except Exception as e:
            logger.warning(f"Failed to get changes: {e}")
            return []

    def get_field_history(self, entity_id: str, field: str) -> list[dict]:
        """获取字段的历史值

        Args:
            entity_id: 实体 ID
            field: 字段名

        Returns:
            字段历史值列表
        """
        try:
            cypher = """
            MATCH (l:DataLineage {entity_id: $entity_id, field: $field})
            RETURN l.value AS value,
                   l.source AS source,
                   l.confidence AS confidence,
                   l.updated_at AS updated_at
            ORDER BY l.updated_at DESC
            """
            return neo4j_client.execute_query(
                cypher, {"entity_id": entity_id, "field": field}
            )
        except Exception as e:
            logger.warning(f"Failed to get field history: {e}")
            return []

    def export_lineage(self, entity_id: str) -> dict:
        """导出数据血缘

        Returns:
            血缘数据字典
        """
        lineage = self.get_lineage(entity_id)
        changes = self.get_changes(entity_id)

        return {
            "entity_id": entity_id,
            "exported_at": datetime.now().isoformat(),
            "lineage": lineage,
            "changes": changes,
        }


# 全局实例
data_lineage = DataLineage()
