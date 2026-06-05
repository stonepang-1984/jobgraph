#!/usr/bin/env python3
"""数据导入脚本 - 将爬取的数据导入到 Neo4j"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.jobgraph.graph_manager import job_manager
from src.jobgraph.models import Company, Job, Review, Pitfall, CompanySize, RiskLevel, JobType


def load_json(filepath: str) -> list[dict]:
    """加载 JSON 文件"""
    path = Path(filepath)
    if not path.exists():
        logger.error(f"File not found: {filepath}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def import_companies(companies_data: list[dict]) -> int:
    """导入公司数据"""
    count = 0
    for data in companies_data:
        try:
            # 解析公司规模
            size_map = {
                "startup": CompanySize.STARTUP,
                "small": CompanySize.SMALL,
                "medium": CompanySize.MEDIUM,
                "large": CompanySize.LARGE,
                "enterprise": CompanySize.ENTERPRISE,
                "giant": CompanySize.GIANT,
            }
            size = size_map.get(data.get("size", "").lower(), CompanySize.MEDIUM)

            # 解析风险等级
            risk_map = {
                "low": RiskLevel.LOW,
                "medium": RiskLevel.MEDIUM,
                "high": RiskLevel.HIGH,
                "blacklist": RiskLevel.BLACKLIST,
            }
            risk_level = risk_map.get(data.get("risk_level", "medium").lower(), RiskLevel.MEDIUM)

            # 解析标签
            tags = data.get("tags", "")
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]

            company = Company(
                id=data["id"],
                name=data["name"],
                name_en=data.get("name_en"),
                industry=data.get("industry"),
                size=size,
                founded=data.get("founded"),
                headquarters=data.get("headquarters"),
                employees=data.get("employees"),
                avg_salary=data.get("avg_salary"),
                avg_rating=data.get("avg_rating"),
                risk_level=risk_level,
                risk_score=data.get("risk_score", 0.5),
                risk_factors=data.get("risk_factors", []),
                tags=tags,
            )
            job_manager.create_company(company)
            count += 1
        except Exception as e:
            logger.error(f"Failed to import company {data.get('name')}: {e}")

    return count


def import_jobs(jobs_data: list[dict]) -> int:
    """导入岗位数据"""
    count = 0
    for data in jobs_data:
        try:
            # 解析技能
            skills = data.get("skills", "")
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split(",") if s.strip()]

            # 解析福利
            benefits = data.get("benefits", "")
            if isinstance(benefits, str):
                benefits = [b.strip() for b in benefits.split(",") if b.strip()]

            job = Job(
                id=data["id"],
                title=data["title"],
                company_id=data["company_id"],
                company_name=data["company_name"],
                department=data.get("department"),
                location=data.get("location"),
                salary_min=data.get("salary_min"),
                salary_max=data.get("salary_max"),
                salary_months=data.get("salary_months", 12),
                experience_years=data.get("experience_years"),
                education=data.get("education"),
                skills=skills,
                benefits=benefits,
                is_active=data.get("is_active", True),
            )
            job_manager.create_job(job)
            count += 1
        except Exception as e:
            logger.error(f"Failed to import job {data.get('title')}: {e}")

    return count


def import_reviews(reviews_data: list[dict]) -> int:
    """导入评价数据"""
    count = 0
    for data in reviews_data:
        try:
            # 解析坑点标签
            pitfall_tags = data.get("pitfall_tags", "")
            if isinstance(pitfall_tags, str):
                pitfall_tags = [t.strip() for t in pitfall_tags.split(",") if t.strip()]

            review = Review(
                id=data["id"],
                company_id=data["company_id"],
                overall_rating=data.get("overall_rating", 0),
                salary_rating=data.get("salary_rating"),
                work_life_rating=data.get("work_life_rating"),
                management_rating=data.get("management_rating"),
                title=data.get("title"),
                pros=data.get("pros"),
                cons=data.get("cons"),
                reviewer_title=data.get("reviewer_title"),
                reviewer_tenure=data.get("reviewer_tenure"),
                is_current_employee=data.get("is_current_employee", True),
                pitfall_tags=pitfall_tags,
            )
            job_manager.create_review(review)
            count += 1
        except Exception as e:
            logger.error(f"Failed to import review: {e}")

    return count


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Importing Data to Neo4j")
    logger.info("=" * 60)

    # 加载数据
    data_dir = Path("data/crawled")

    companies_data = load_json(str(data_dir / "companies.json"))
    jobs_data = load_json(str(data_dir / "jobs.json"))
    reviews_data = load_json(str(data_dir / "reviews.json"))

    logger.info(f"Loaded: {len(companies_data)} companies, {len(jobs_data)} jobs, {len(reviews_data)} reviews")

    # 导入数据
    companies_count = import_companies(companies_data)
    logger.info(f"Imported {companies_count} companies")

    jobs_count = import_jobs(jobs_data)
    logger.info(f"Imported {jobs_count} jobs")

    reviews_count = import_reviews(reviews_data)
    logger.info(f"Imported {reviews_count} reviews")

    # 打印统计
    stats = job_manager.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Companies: {stats.get('companies', 0)}")
    logger.info(f"Jobs: {stats.get('jobs', 0)}")
    logger.info(f"Reviews: {stats.get('reviews', 0)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
