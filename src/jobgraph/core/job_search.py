"""Job Search - 岗位搜索 (免费功能)"""

from typing import Optional
from loguru import logger

from src.graph.neo4j_client import neo4j_client


# 免费版限制
FREE_SEARCH_LIMIT = 50
FREE_DAILY_LIMIT = 100


class JobSearch:
    """岗位搜索"""

    def __init__(self):
        self.daily_count = 0

    def search(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        salary_min: Optional[float] = None,
        limit: int = FREE_SEARCH_LIMIT,
    ) -> list[dict]:
        """搜索岗位

        Args:
            query: 搜索关键词
            location: 工作地点
            salary_min: 最低薪资
            limit: 返回数量限制

        Returns:
            岗位列表
        """
        # 检查每日限制
        if self.daily_count >= FREE_DAILY_LIMIT:
            logger.warning("Daily search limit reached")
            return []

        # 限制返回数量
        actual_limit = min(limit, FREE_SEARCH_LIMIT)

        # 构建查询
        conditions = ["j.is_active = true"]
        params = {"limit": actual_limit}

        if query:
            conditions.append("(j.title CONTAINS $query OR j.company_name CONTAINS $query)")
            params["query"] = query
        if location:
            conditions.append("j.location CONTAINS $location")
            params["location"] = location
        if salary_min:
            conditions.append("j.salary_max >= $salary_min")
            params["salary_min"] = salary_min

        where_clause = " AND ".join(conditions)

        cypher = f"""
        MATCH (j:Job)
        OPTIONAL MATCH (c:Company)-[:HAS_JOB]->(j)
        WHERE {where_clause}
        RETURN j, c.name AS company_name, c.risk_level AS company_risk
        ORDER BY j.posted_at DESC
        LIMIT $limit
        """

        results = neo4j_client.execute_query(cypher, params)
        self.daily_count += 1

        return results

    def get_job_salary_range(self, job_title: str, location: str = None) -> dict:
        """获取岗位薪资范围"""
        conditions = ["j.title CONTAINS $title", "j.is_active = true"]
        params = {"title": job_title}

        if location:
            conditions.append("j.location CONTAINS $location")
            params["location"] = location

        where_clause = " AND ".join(conditions)

        cypher = f"""
        MATCH (j:Job)
        WHERE {where_clause}
        WITH j.salary_min AS salary_min, j.salary_max AS salary_max
        WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL
        RETURN percentileDisc(salary_min, 0.25) AS p25_min,
               percentileDisc(salary_min, 0.50) AS p50_min,
               percentileDisc(salary_min, 0.75) AS p75_min,
               percentileDisc(salary_max, 0.25) AS p25_max,
               percentileDisc(salary_max, 0.50) AS p50_max,
               percentileDisc(salary_max, 0.75) AS p75_max,
               avg((salary_min + salary_max) / 2) AS mean,
               count(*) AS sample_count
        """
        results = neo4j_client.execute_query(cypher, params)
        return results[0] if results else {}

    def get_search_stats(self) -> dict:
        """获取搜索统计"""
        return {
            "daily_count": self.daily_count,
            "daily_limit": FREE_DAILY_LIMIT,
            "search_limit": FREE_SEARCH_LIMIT,
            "remaining": max(0, FREE_DAILY_LIMIT - self.daily_count),
        }


# 全局实例
job_search = JobSearch()
