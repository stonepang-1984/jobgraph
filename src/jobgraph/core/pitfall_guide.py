"""Pitfall Guide - 避坑指南 (免费功能)"""

from typing import Optional
from loguru import logger

from src.graph.neo4j_client import neo4j_client


# 坑点类型定义
PITFALL_TYPES = {
    "欠薪": {"icon": "💰", "description": "拖欠工资，不按时发放", "severity": 5},
    "PUA": {"icon": "🎭", "description": "精神控制，贬低员工价值", "severity": 4},
    "996": {"icon": "⏰", "description": "强制996工作制，没有加班费", "severity": 4},
    "内卷": {"icon": "🔄", "description": "过度竞争，无效加班", "severity": 3},
    "裁员": {"icon": "📉", "description": "频繁裁员，不稳定", "severity": 4},
    "画饼": {"icon": "🎨", "description": "老板天天画饼，承诺不兑现", "severity": 3},
    "社保": {"icon": "🏥", "description": "不交或少交社保公积金", "severity": 4},
    "克扣": {"icon": "✂️", "description": "以各种理由克扣工资", "severity": 4},
}


class PitfallGuide:
    """避坑指南"""

    def get_pitfall_types(self) -> dict:
        """获取所有坑点类型"""
        return PITFALL_TYPES

    def check_company_pitfalls(self, company_id: str) -> dict:
        """检查公司坑点"""
        cypher = """
        MATCH (c:Company {id: $id})
        OPTIONAL MATCH (c)-[:HAS_PITFALL]->(p:Pitfall)
        OPTIONAL MATCH (c)-[:HAS_REVIEW]->(r:Review)
        WHERE any(tag IN r.pitfall_tags WHERE tag IS NOT NULL)
        RETURN c.risk_level AS risk_level,
               c.risk_score AS risk_score,
               c.risk_factors AS risk_factors,
               collect(DISTINCT {
                   type: p.pitfall_type,
                   severity: p.severity,
                   description: p.description,
                   report_count: p.report_count
               }) AS pitfalls,
               collect(DISTINCT r.pitfall_tags) AS review_pitfall_tags
        """
        results = neo4j_client.execute_query(cypher, {"id": company_id})

        if not results:
            return {"has_pitfalls": False}

        result = results[0]
        pitfalls = result.get("pitfalls", [])

        # 合并评价中的坑点标签
        review_tags = set()
        for tags in result.get("review_pitfall_tags", []):
            if tags:
                review_tags.update(tags)

        return {
            "has_pitfalls": len(pitfalls) > 0 or len(review_tags) > 0,
            "risk_level": result.get("risk_level"),
            "risk_score": result.get("risk_score"),
            "risk_factors": result.get("risk_factors", []),
            "pitfalls": [p for p in pitfalls if p.get("type")],
            "review_pitfall_tags": list(review_tags),
        }

    def search_high_risk_companies(self, limit: int = 20) -> list[dict]:
        """搜索高风险公司"""
        cypher = """
        MATCH (c:Company)
        WHERE c.risk_level IN ['high', 'blacklist']
        OPTIONAL MATCH (c)-[:HAS_PITFALL]->(p:Pitfall)
        RETURN c,
               count(DISTINCT p) AS pitfall_count,
               avg(p.severity) AS avg_severity
        ORDER BY c.risk_score DESC
        LIMIT $limit
        """
        return neo4j_client.execute_query(cypher, {"limit": limit})

    def get_pitfall_statistics(self) -> dict:
        """获取坑点统计"""
        cypher = """
        MATCH (p:Pitfall)
        RETURN p.pitfall_type AS type,
               count(*) AS count,
               avg(p.severity) AS avg_severity,
               sum(p.report_count) AS total_reports
        ORDER BY count DESC
        """
        return neo4j_client.execute_query(cypher)


# 全局实例
pitfall_guide = PitfallGuide()
