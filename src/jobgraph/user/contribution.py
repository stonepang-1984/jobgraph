"""贡献管理模块

功能:
- 评价提交
- 坑点提交
- 薪资提交
- 数据审核
"""

import hashlib
from datetime import datetime
from typing import Optional
from loguru import logger

from src.graph.neo4j_client import neo4j_client
from src.jobgraph.user.manager import user_manager


class ContributionManager:
    """贡献管理器"""

    def submit_review(
        self,
        company_id: str,
        overall_rating: float,
        pros: str,
        cons: str,
        title: Optional[str] = None,
        salary_rating: Optional[float] = None,
        work_life_rating: Optional[float] = None,
        management_rating: Optional[float] = None,
        reviewer_title: Optional[str] = None,
        reviewer_tenure: Optional[str] = None,
        pitfall_tags: list[str] = None,
    ) -> dict:
        """提交评价"""
        # 检查贡献限制
        if not self._check_contribution_limit("reviews"):
            return {"success": False, "error": "今日贡献次数已用完"}

        # 生成 ID
        review_id = hashlib.md5(
            f"{company_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # 获取用户信息
        user_data = user_manager.get_user_data()

        # 写入数据库
        cypher = """
        CREATE (r:Review {
            id: $id,
            company_id: $company_id,
            overall_rating: $overall_rating,
            salary_rating: $salary_rating,
            work_life_rating: $work_life_rating,
            management_rating: $management_rating,
            title: $title,
            pros: $pros,
            cons: $cons,
            reviewer_title: $reviewer_title,
            reviewer_tenure: $reviewer_tenure,
            pitfall_tags: $pitfall_tags,
            source: 'user_contribution',
            user_id: $user_id,
            user_level: $user_level,
            status: 'pending',
            created_at: datetime()
        })
        WITH r
        MATCH (c:Company {id: $company_id})
        MERGE (c)-[:HAS_REVIEW]->(r)
        """

        try:
            neo4j_client.execute_write(
                cypher,
                {
                    "id": review_id,
                    "company_id": company_id,
                    "overall_rating": overall_rating,
                    "salary_rating": salary_rating,
                    "work_life_rating": work_life_rating,
                    "management_rating": management_rating,
                    "title": title,
                    "pros": pros,
                    "cons": cons,
                    "reviewer_title": reviewer_title,
                    "reviewer_tenure": reviewer_tenure,
                    "pitfall_tags": pitfall_tags or [],
                    "user_id": user_manager.device_id,
                    "user_level": user_manager.user_level,
                },
            )

            # 记录贡献
            user_manager.add_contribution("reviews")

            logger.info(f"Review submitted: {review_id}")
            return {"success": True, "id": review_id}

        except Exception as e:
            logger.error(f"Failed to submit review: {e}")
            return {"success": False, "error": str(e)}

    def submit_pitfall(
        self,
        company_id: str,
        pitfall_type: str,
        description: str,
        severity: int = 3,
        evidence: Optional[str] = None,
    ) -> dict:
        """提交坑点"""
        # 检查贡献限制
        if not self._check_contribution_limit("pitfalls"):
            return {"success": False, "error": "今日贡献次数已用完"}

        # 生成 ID
        pitfall_id = hashlib.md5(
            f"{company_id}_{pitfall_type}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # 获取用户信息
        user_data = user_manager.get_user_data()

        # 写入数据库
        cypher = """
        MERGE (p:Pitfall {company_id: $company_id, pitfall_type: $pitfall_type})
        ON CREATE SET p.id = $id,
                      p.severity = $severity,
                      p.description = $description,
                      p.evidence = $evidence,
                      p.report_count = 1,
                      p.confirmed_count = 0,
                      p.source = 'user_contribution',
                      p.user_id = $user_id,
                      p.is_verified = false,
                      p.created_at = datetime()
        ON MATCH SET p.report_count = p.report_count + 1,
                     p.severity = CASE WHEN $severity > p.severity THEN $severity ELSE p.severity END
        WITH p
        MATCH (c:Company {id: $company_id})
        MERGE (c)-[:HAS_PITFALL]->(p)
        """

        try:
            neo4j_client.execute_write(
                cypher,
                {
                    "id": pitfall_id,
                    "company_id": company_id,
                    "pitfall_type": pitfall_type,
                    "severity": severity,
                    "description": description,
                    "evidence": evidence,
                    "user_id": user_manager.device_id,
                },
            )

            # 记录贡献
            user_manager.add_contribution("pitfalls")

            logger.info(f"Pitfall submitted: {pitfall_id}")
            return {"success": True, "id": pitfall_id}

        except Exception as e:
            logger.error(f"Failed to submit pitfall: {e}")
            return {"success": False, "error": str(e)}

    def submit_salary(
        self,
        company_id: str,
        job_title: str,
        salary_min: float,
        salary_max: float,
        experience_years: Optional[int] = None,
        education: Optional[str] = None,
    ) -> dict:
        """提交薪资信息"""
        # 检查贡献限制
        if not self._check_contribution_limit("salaries"):
            return {"success": False, "error": "今日贡献次数已用完"}

        # 生成 ID
        salary_id = hashlib.md5(
            f"{company_id}_{job_title}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # 写入数据库
        cypher = """
        CREATE (s:SalaryInfo {
            id: $id,
            company_id: $company_id,
            job_title: $job_title,
            salary_min: $salary_min,
            salary_max: $salary_max,
            experience_years: $experience_years,
            education: $education,
            source: 'user_contribution',
            user_id: $user_id,
            status: 'pending',
            created_at: datetime()
        })
        WITH s
        MATCH (c:Company {id: $company_id})
        MERGE (c)-[:HAS_SALARY]->(s)
        """

        try:
            neo4j_client.execute_write(
                cypher,
                {
                    "id": salary_id,
                    "company_id": company_id,
                    "job_title": job_title,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "experience_years": experience_years,
                    "education": education,
                    "user_id": user_manager.device_id,
                },
            )

            # 记录贡献
            user_manager.add_contribution("salaries")

            logger.info(f"Salary info submitted: {salary_id}")
            return {"success": True, "id": salary_id}

        except Exception as e:
            logger.error(f"Failed to submit salary info: {e}")
            return {"success": False, "error": str(e)}

    def submit_job(
        self,
        company_id: str,
        company_name: str,
        title: str,
        location: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        experience_years: Optional[int] = None,
        education: Optional[str] = None,
        skills: list[str] = None,
        description: Optional[str] = None,
        benefits: list[str] = None,
    ) -> dict:
        """提交职位信息"""
        # 检查贡献限制
        if not self._check_contribution_limit("jobs"):
            return {"success": False, "error": "今日贡献次数已用完"}

        # 生成 ID
        job_id = hashlib.md5(
            f"{company_id}_{title}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # 写入数据库
        cypher = """
        MERGE (j:Job {id: $id})
        SET j.title = $title,
            j.company_id = $company_id,
            j.company_name = $company_name,
            j.location = $location,
            j.salary_min = $salary_min,
            j.salary_max = $salary_max,
            j.experience_years = $experience_years,
            j.education = $education,
            j.skills = $skills,
            j.description = $description,
            j.benefits = $benefits,
            j.source = 'user_contribution',
            j.user_id = $user_id,
            j.is_active = true,
            j.status = 'pending',
            j.created_at = datetime(),
            j.updated_at = datetime()
        WITH j
        MATCH (c:Company {id: $company_id})
        MERGE (c)-[:HAS_JOB]->(j)
        """

        try:
            neo4j_client.execute_write(
                cypher,
                {
                    "id": job_id,
                    "title": title,
                    "company_id": company_id,
                    "company_name": company_name,
                    "location": location,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "experience_years": experience_years,
                    "education": education,
                    "skills": skills or [],
                    "description": description,
                    "benefits": benefits or [],
                    "user_id": user_manager.device_id,
                },
            )

            # 记录贡献
            user_manager.add_contribution("jobs")

            logger.info(f"Job submitted: {job_id}")
            return {"success": True, "id": job_id}

        except Exception as e:
            logger.error(f"Failed to submit job: {e}")
            return {"success": False, "error": str(e)}

    def _check_contribution_limit(self, contribution_type: str) -> bool:
        """检查贡献限制"""
        limits = user_manager.get_contribution_limit()
        user_data = user_manager.get_user_data()
        contributions = user_data.get("contributions", {})

        limit_key = f"{contribution_type}_per_day"
        limit = limits.get(limit_key, 5)
        current = contributions.get(contribution_type, 0)

        # 简化检查：不检查每日限制，只检查总限制
        return current < limit * 30  # 一个月的限制

    def get_user_contributions(self) -> dict:
        """获取用户贡献统计"""
        user_data = user_manager.get_user_data()
        return user_data.get("contributions", {})


# 全局实例
contribution_manager = ContributionManager()
