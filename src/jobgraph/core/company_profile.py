"""Company Profile - 公司画像 (免费功能)"""

from src.graph.neo4j_client import neo4j_client


class CompanyProfile:
    """公司画像"""

    def get_company(self, company_id: str) -> dict | None:
        """获取公司详情"""
        cypher = """
        MATCH (c:Company {id: $id})
        OPTIONAL MATCH (c)-[:HAS_JOB]->(j:Job)
        OPTIONAL MATCH (c)-[:HAS_REVIEW]->(r:Review)
        OPTIONAL MATCH (c)-[:HAS_PITFALL]->(p:Pitfall)
        RETURN c,
               count(DISTINCT j) AS job_count,
               count(DISTINCT r) AS review_count,
               count(DISTINCT p) AS pitfall_count,
               avg(r.overall_rating) AS avg_rating
        """
        results = neo4j_client.execute_query(cypher, {"id": company_id})
        return results[0] if results else None

    def search_companies(self, query: str, limit: int = 20) -> list[dict]:
        """搜索公司"""
        cypher = """
        MATCH (c:Company)
        WHERE c.name CONTAINS $query
           OR c.name_en CONTAINS $query
           OR any(tag IN c.tags WHERE tag CONTAINS $query)
        RETURN c
        ORDER BY c.avg_rating DESC
        LIMIT $limit
        """
        return neo4j_client.execute_query(cypher, {"query": query, "limit": limit})

    def get_company_reviews(self, company_id: str, limit: int = 10) -> list[dict]:
        """获取公司评价 (免费版限制10条)"""
        cypher = """
        MATCH (c:Company {id: $id})-[:HAS_REVIEW]->(r:Review)
        RETURN r
        ORDER BY r.posted_at DESC
        LIMIT $limit
        """
        return neo4j_client.execute_query(cypher, {"id": company_id, "limit": limit})

    def get_company_pitfalls(self, company_id: str) -> list[dict]:
        """获取公司坑点"""
        cypher = """
        MATCH (c:Company {id: $id})-[:HAS_PITFALL]->(p:Pitfall)
        RETURN p
        ORDER BY p.severity DESC, p.report_count DESC
        """
        return neo4j_client.execute_query(cypher, {"id": company_id})

    def get_risk_assessment(self, company_id: str) -> dict:
        """获取公司风险评估"""
        cypher = """
        MATCH (c:Company {id: $id})
        OPTIONAL MATCH (c)-[:HAS_PITFALL]->(p:Pitfall)
        OPTIONAL MATCH (c)-[:HAS_REVIEW]->(r:Review)
        RETURN c.risk_level AS risk_level,
               c.risk_score AS risk_score,
               c.risk_factors AS risk_factors,
               collect(DISTINCT {
                   type: p.pitfall_type,
                   severity: p.severity,
                   description: p.description
               }) AS pitfalls,
               avg(r.overall_rating) AS avg_rating,
               count(DISTINCT r) AS review_count
        """
        results = neo4j_client.execute_query(cypher, {"id": company_id})
        return results[0] if results else {}


# 全局实例
company_profile = CompanyProfile()
