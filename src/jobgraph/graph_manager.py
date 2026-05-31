"""JobGraph manager - 求职图谱管理器

聚焦场景: 求职 - 帮你找到靠谱的工作，避开坑人的公司
"""

from typing import Optional
from loguru import logger

from src.graph.neo4j_client import neo4j_client
from src.jobgraph.models import (
    Company, Job, Review, Pitfall, SalaryData,
    UserProfile, MatchResult, RiskLevel, CompanySize, FundingStage
)


class JobGraphManager:
    """求职图谱管理器."""

    # ============================================================
    # Company CRUD
    # ============================================================

    def create_company(self, company: Company) -> None:
        """创建或更新公司节点."""
        cypher = """
        MERGE (c:Company {id: $id})
        SET c.name = $name,
            c.name_en = $name_en,
            c.industry = $industry,
            c.size = $size,
            c.founded = $founded,
            c.headquarters = $headquarters,
            c.website = $website,
            c.description = $description,
            c.funding_stage = $funding_stage,
            c.valuation = $valuation,
            c.is_listed = $is_listed,
            c.stock_code = $stock_code,
            c.employees = $employees,
            c.avg_salary = $avg_salary,
            c.avg_rating = $avg_rating,
            c.review_count = $review_count,
            c.risk_level = $risk_level,
            c.risk_score = $risk_score,
            c.risk_factors = $risk_factors,
            c.tags = $tags,
            c.source = $source,
            c.updated_at = datetime()
        """
        neo4j_client.execute_write(cypher, {
            "id": company.id,
            "name": company.name,
            "name_en": company.name_en,
            "industry": company.industry,
            "size": company.size.value if company.size else None,
            "founded": company.founded,
            "headquarters": company.headquarters,
            "website": company.website,
            "description": company.description,
            "funding_stage": company.funding_stage.value if company.funding_stage else None,
            "valuation": company.valuation,
            "is_listed": company.is_listed,
            "stock_code": company.stock_code,
            "employees": company.employees,
            "avg_salary": company.avg_salary,
            "avg_rating": company.avg_rating,
            "review_count": company.review_count,
            "risk_level": company.risk_level.value,
            "risk_score": company.risk_score,
            "risk_factors": company.risk_factors,
            "tags": company.tags,
            "source": company.source,
        })
        logger.info(f"Created/updated company: {company.name}")

    def get_company(self, company_id: str) -> Optional[dict]:
        """获取公司详情."""
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
        """搜索公司."""
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

    def get_company_risk_assessment(self, company_id: str) -> dict:
        """获取公司风险评估."""
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
                   description: p.description,
                   report_count: p.report_count
               }) AS pitfalls,
               avg(r.overall_rating) AS avg_rating,
               avg(r.work_life_rating) AS avg_work_life,
               count(DISTINCT r) AS review_count
        """
        results = neo4j_client.execute_query(cypher, {"id": company_id})
        return results[0] if results else {}

    # ============================================================
    # Job CRUD
    # ============================================================

    def create_job(self, job: Job) -> None:
        """创建岗位."""
        cypher = """
        MERGE (j:Job {id: $id})
        SET j.title = $title,
            j.company_id = $company_id,
            j.company_name = $company_name,
            j.department = $department,
            j.job_type = $job_type,
            j.location = $location,
            j.is_remote = $is_remote,
            j.salary_min = $salary_min,
            j.salary_max = $salary_max,
            j.salary_months = $salary_months,
            j.experience_years = $experience_years,
            j.education = $education,
            j.skills = $skills,
            j.description = $description,
            j.benefits = $benefits,
            j.source = $source,
            j.is_active = $is_active,
            j.updated_at = datetime()
        WITH j
        MATCH (c:Company {id: $company_id})
        MERGE (c)-[:HAS_JOB]->(j)
        """
        neo4j_client.execute_write(cypher, {
            "id": job.id,
            "title": job.title,
            "company_id": job.company_id,
            "company_name": job.company_name,
            "department": job.department,
            "job_type": job.job_type.value,
            "location": job.location,
            "is_remote": job.is_remote,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_months": job.salary_months,
            "experience_years": job.experience_years,
            "education": job.education,
            "skills": job.skills,
            "description": job.description,
            "benefits": job.benefits,
            "source": job.source,
            "is_active": job.is_active,
        })

    def search_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        salary_min: Optional[float] = None,
        limit: int = 50
    ) -> list[dict]:
        """搜索岗位."""
        conditions = ["j.is_active = true"]
        params = {"limit": limit}

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
        return neo4j_client.execute_query(cypher, params)

    def get_job_salary_range(self, job_title: str, location: str = None) -> dict:
        """获取岗位薪资范围."""
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

    # ============================================================
    # Review CRUD
    # ============================================================

    def create_review(self, review: Review) -> None:
        """创建员工评价."""
        cypher = """
        CREATE (r:Review {
            id: $id,
            company_id: $company_id,
            overall_rating: $overall_rating,
            salary_rating: $salary_rating,
            work_life_rating: $work_life_rating,
            management_rating: $management_rating,
            culture_rating: $culture_rating,
            growth_rating: $growth_rating,
            title: $title,
            pros: $pros,
            cons: $cons,
            reviewer_title: $reviewer_title,
            reviewer_tenure: $reviewer_tenure,
            is_current_employee: $is_current_employee,
            source: $source,
            posted_at: $posted_at,
            pitfall_tags: $pitfall_tags
        })
        WITH r
        MATCH (c:Company {id: $company_id})
        MERGE (c)-[:HAS_REVIEW]->(r)
        """
        neo4j_client.execute_write(cypher, {
            "id": review.id,
            "company_id": review.company_id,
            "overall_rating": review.overall_rating,
            "salary_rating": review.salary_rating,
            "work_life_rating": review.work_life_rating,
            "management_rating": review.management_rating,
            "culture_rating": review.culture_rating,
            "growth_rating": review.growth_rating,
            "title": review.title,
            "pros": review.pros,
            "cons": review.cons,
            "reviewer_title": review.reviewer_title,
            "reviewer_tenure": review.reviewer_tenure,
            "is_current_employee": review.is_current_employee,
            "source": review.source,
            "posted_at": review.posted_at,
            "pitfall_tags": review.pitfall_tags,
        })

    def get_company_reviews(self, company_id: str, limit: int = 20) -> list[dict]:
        """获取公司评价."""
        cypher = """
        MATCH (c:Company {id: $id})-[:HAS_REVIEW]->(r:Review)
        RETURN r
        ORDER BY r.posted_at DESC
        LIMIT $limit
        """
        return neo4j_client.execute_query(cypher, {"id": company_id, "limit": limit})

    # ============================================================
    # Pitfall CRUD
    # ============================================================

    def create_pitfall(self, pitfall: Pitfall) -> None:
        """创建坑点."""
        cypher = """
        MERGE (p:Pitfall {id: $id})
        SET p.company_id = $company_id,
            p.pitfall_type = $pitfall_type,
            p.severity = $severity,
            p.description = $description,
            p.evidence = $evidence,
            p.report_count = $report_count,
            p.confirmed_count = $confirmed_count,
            p.source = $source,
            p.reported_at = $reported_at,
            p.is_verified = $is_verified
        WITH p
        MATCH (c:Company {id: $company_id})
        MERGE (c)-[:HAS_PITFALL]->(p)
        """
        neo4j_client.execute_write(cypher, {
            "id": pitfall.id,
            "company_id": pitfall.company_id,
            "pitfall_type": pitfall.pitfall_type,
            "severity": pitfall.severity,
            "description": pitfall.description,
            "evidence": pitfall.evidence,
            "report_count": pitfall.report_count,
            "confirmed_count": pitfall.confirmed_count,
            "source": pitfall.source,
            "reported_at": pitfall.reported_at,
            "is_verified": pitfall.is_verified,
        })

    def get_company_pitfalls(self, company_id: str) -> list[dict]:
        """获取公司坑点."""
        cypher = """
        MATCH (c:Company {id: $id})-[:HAS_PITFALL]->(p:Pitfall)
        RETURN p
        ORDER BY p.severity DESC, p.report_count DESC
        """
        return neo4j_client.execute_query(cypher, {"id": company_id})

    # ============================================================
    # User Profile
    # ============================================================

    def create_user_profile(self, user: UserProfile) -> None:
        """创建用户档案."""
        cypher = """
        MERGE (u:UserProfile {id: $id})
        SET u.name = $name,
            u.current_title = $current_title,
            u.current_company = $current_company,
            u.experience_years = $experience_years,
            u.education = $education,
            u.location = $location,
            u.skills = $skills,
            u.desired_titles = $desired_titles,
            u.desired_locations = $desired_locations,
            u.desired_salary_min = $desired_salary_min,
            u.desired_salary_max = $desired_salary_max,
            u.prefer_remote = $prefer_remote,
            u.updated_at = datetime()
        """
        neo4j_client.execute_write(cypher, {
            "id": user.id,
            "name": user.name,
            "current_title": user.current_title,
            "current_company": user.current_company,
            "experience_years": user.experience_years,
            "education": user.education,
            "location": user.location,
            "skills": user.skills,
            "desired_titles": user.desired_titles,
            "desired_locations": user.desired_locations,
            "desired_salary_min": user.desired_salary_min,
            "desired_salary_max": user.desired_salary_max,
            "prefer_remote": user.prefer_remote,
        })

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """获取用户档案."""
        cypher = """
        MATCH (u:UserProfile {id: $id})
        RETURN u
        """
        results = neo4j_client.execute_query(cypher, {"id": user_id})
        return results[0]["u"] if results else None

    # ============================================================
    # Matching
    # ============================================================

    def find_matching_jobs(self, user_id: str, limit: int = 20) -> list[dict]:
        """为用户匹配岗位."""
        cypher = """
        MATCH (u:UserProfile {id: $user_id})
        MATCH (j:Job {is_active: true})
        OPTIONAL MATCH (c:Company)-[:HAS_JOB]->(j)
        
        WITH u, j, c,
             // 技能匹配
             size([s IN u.skills WHERE s IN j.skills]) AS matched_skills,
             size(u.skills) AS user_skill_count,
             size(j.skills) AS job_skill_count,
             
             // 薪资匹配
             CASE 
                 WHEN j.salary_max >= u.desired_salary_min AND j.salary_min <= u.desired_salary_max THEN 1.0
                 WHEN j.salary_max >= u.desired_salary_min THEN 0.5
                 ELSE 0.0
             END AS salary_match,
             
             // 地点匹配
             CASE
                 WHEN j.is_remote AND u.prefer_remote THEN 1.0
                 WHEN u.desired_locations IS NULL THEN 0.5
                 WHEN any(loc IN u.desired_locations WHERE j.location CONTAINS loc) THEN 1.0
                 ELSE 0.0
             END AS location_match
        
        WITH u, j, c, matched_skills, salary_match, location_match,
             CASE WHEN job_skill_count > 0 
                  THEN toFloat(matched_skills) / job_skill_count 
                  ELSE 0.0 
             END AS skill_score,
             CASE WHEN c.risk_level = 'low' THEN 0.9
                  WHEN c.risk_level = 'medium' THEN 0.6
                  WHEN c.risk_level = 'high' THEN 0.3
                  ELSE 0.1
             END AS risk_factor
        
        WITH u, j, c, matched_skills,
             (skill_score * 0.4 + salary_match * 0.3 + location_match * 0.2 + risk_factor * 0.1) AS total_score
        
        WHERE total_score > 0.3
        
        RETURN j.id AS job_id,
               j.title AS job_title,
               j.company_name AS company_name,
               j.salary_min AS salary_min,
               j.salary_max AS salary_max,
               j.location AS location,
               j.skills AS skills,
               c.risk_level AS company_risk,
               c.avg_rating AS company_rating,
               matched_skills,
               total_score
        ORDER BY total_score DESC
        LIMIT $limit
        """
        return neo4j_client.execute_query(cypher, {"user_id": user_id, "limit": limit})

    # ============================================================
    # Statistics
    # ============================================================

    def get_stats(self) -> dict:
        """获取图谱统计."""
        cypher = """
        OPTIONAL MATCH (c:Company) WITH count(c) AS companies
        OPTIONAL MATCH (j:Job) WITH companies, count(j) AS jobs
        OPTIONAL MATCH (r:Review) WITH companies, jobs, count(r) AS reviews
        OPTIONAL MATCH (p:Pitfall) WITH companies, jobs, reviews, count(p) AS pitfalls
        OPTIONAL MATCH (u:UserProfile) WITH companies, jobs, reviews, pitfalls, count(u) AS users
        RETURN companies, jobs, reviews, pitfalls, users
        """
        results = neo4j_client.execute_query(cypher)
        return results[0] if results else {}


# Singleton instance
job_manager = JobGraphManager()
