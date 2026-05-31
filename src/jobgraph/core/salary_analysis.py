"""Salary Analysis - 薪资分析 (免费功能)"""



from src.graph.neo4j_client import neo4j_client


class SalaryAnalysis:
    """薪资分析"""

    def get_salary_range(self, job_title: str, location: str | None = None) -> dict:
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

    def get_company_salary(self, company_id: str, job_title: str | None = None) -> dict:
        """获取公司薪资水平"""
        conditions = ["c.id = $company_id", "j.is_active = true"]
        params = {"company_id": company_id}

        if job_title:
            conditions.append("j.title CONTAINS $job_title")
            params["job_title"] = job_title

        where_clause = " AND ".join(conditions)

        cypher = f"""
        MATCH (c:Company)-[:HAS_JOB]->(j:Job)
        WHERE {where_clause}
        RETURN avg(j.salary_min) AS avg_salary_min,
               avg(j.salary_max) AS avg_salary_max,
               min(j.salary_min) AS min_salary,
               max(j.salary_max) AS max_salary,
               count(*) AS job_count
        """
        results = neo4j_client.execute_query(cypher, params)
        return results[0] if results else {}

    def get_industry_salary(self, industry: str) -> dict:
        """获取行业薪资水平"""
        cypher = """
        MATCH (c:Company)-[:HAS_JOB]->(j:Job)
        WHERE c.industry CONTAINS $industry AND j.is_active = true
        RETURN avg(j.salary_min) AS avg_salary_min,
               avg(j.salary_max) AS avg_salary_max,
               percentileDisc(j.salary_min, 0.50) AS median_salary_min,
               percentileDisc(j.salary_max, 0.50) AS median_salary_max,
               count(*) AS job_count,
               count(DISTINCT c.id) AS company_count
        """
        results = neo4j_client.execute_query(cypher, {"industry": industry})
        return results[0] if results else {}

    def get_location_salary(self, location: str) -> dict:
        """获取城市薪资水平"""
        cypher = """
        MATCH (j:Job)
        WHERE j.location CONTAINS $location AND j.is_active = true
        RETURN avg(j.salary_min) AS avg_salary_min,
               avg(j.salary_max) AS avg_salary_max,
               percentileDisc(j.salary_min, 0.50) AS median_salary_min,
               percentileDisc(j.salary_max, 0.50) AS median_salary_max,
               count(*) AS job_count
        """
        results = neo4j_client.execute_query(cypher, {"location": location})
        return results[0] if results else {}


# 全局实例
salary_analysis = SalaryAnalysis()
