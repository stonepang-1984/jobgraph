"""初始化 SQLite 数据库

导入初始数据到 SQLite
"""

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置存储后端为 SQLite
os.environ["STORAGE_BACKEND"] = "sqlite"

from src.jobgraph.graph_manager import job_manager
from src.jobgraph.models import Company, Job, CompanySize, RiskLevel, JobType
from loguru import logger


def import_initial_data():
    """导入初始数据"""
    logger.info("=" * 60)
    logger.info("初始化 SQLite 数据库")
    logger.info("=" * 60)
    
    # 读取初始数据
    data_dir = project_root / "data" / "initial"
    
    # 导入公司数据
    companies_file = data_dir / "companies.json"
    if companies_file.exists():
        logger.info("导入公司数据...")
        with open(companies_file, "r", encoding="utf-8") as f:
            companies_data = json.load(f)
        
        for comp in companies_data.get("companies", []):
            try:
                company = Company(
                    id=comp["id"],
                    name=comp["name"],
                    name_en=comp.get("name_en"),
                    industry=comp.get("industry"),
                    size=CompanySize(comp.get("size", "medium")),
                    founded=comp.get("founded"),
                    headquarters=comp.get("headquarters"),
                    website=comp.get("website"),
                    description=comp.get("description"),
                    tags=comp.get("tags", []),
                    risk_level=RiskLevel(comp.get("risk_level", "low")),
                    risk_score=comp.get("risk_score", 0.3),
                    avg_salary=comp.get("avg_salary", 0),
                    avg_rating=comp.get("avg_rating", 3.5),
                )
                job_manager.create_company(company)
                logger.info(f"  ✓ {company.name}")
            except Exception as e:
                logger.error(f"  ✗ {comp.get('name')}: {e}")
    
    # 导入职位数据
    jobs_file = data_dir / "tencent_jobs.json"
    if jobs_file.exists():
        logger.info("导入职位数据...")
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)
        
        for job_data in jobs_data:
            try:
                job = Job(
                    id=job_data["id"],
                    title=job_data["title"],
                    company_id=job_data.get("company_id", ""),
                    company_name=job_data.get("company_name", ""),
                    location=job_data.get("location"),
                    salary_min=job_data.get("salary_min"),
                    salary_max=job_data.get("salary_max"),
                    experience_years=job_data.get("experience_years"),
                    education=job_data.get("education"),
                    skills=job_data.get("skills", []),
                    description=job_data.get("description"),
                    requirements=job_data.get("requirements"),
                    is_active=job_data.get("is_active", True),
                )
                job_manager.create_job(job)
                logger.info(f"  ✓ {job.title}")
            except Exception as e:
                logger.error(f"  ✗ {job_data.get('title')}: {e}")
    
    # 统计
    stats = job_manager.get_stats()
    logger.info("=" * 60)
    logger.info("初始化完成！")
    logger.info(f"  公司: {stats['companies']} 家")
    logger/logger.info(f"  职位: {stats['jobs']} 个")
    logger.info(f"  评价: {stats['reviews']} 条")
    logger.info("=" * 60)


if __name__ == "__main__":
    import_initial_data()
