#!/usr/bin/env python3
"""初始数据导入脚本

导入 data/initial/ 目录下的初始数据到 Neo4j

用法:
    python scripts/import_initial_data.py
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


def import_companies():
    """导入公司数据"""
    from src.jobgraph.graph_manager import job_manager
    from src.jobgraph.models import Company, CompanySize, RiskLevel
    
    data_file = project_root / "data" / "initial" / "companies.json"
    
    if not data_file.exists():
        logger.warning(f"公司数据文件不存在: {data_file}")
        return 0
    
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    companies = data.get("companies", [])
    logger.info(f"导入 {len(companies)} 家公司...")
    
    # 公司规模映射
    size_map = {
        "startup": CompanySize.STARTUP,
        "small": CompanySize.SMALL,
        "medium": CompanySize.MEDIUM,
        "large": CompanySize.LARGE,
        "enterprise": CompanySize.ENTERPRISE,
        "giant": CompanySize.GIANT,
    }
    
    success_count = 0
    for company_data in companies:
        try:
            company = Company(
                id=company_data["id"],
                name=company_data["name"],
                name_en=company_data.get("name_en"),
                industry=company_data.get("industry"),
                size=size_map.get(company_data.get("size", ""), CompanySize.MEDIUM),
                headquarters=company_data.get("headquarters"),
                website=company_data.get("website"),
                description=company_data.get("description"),
                tags=company_data.get("tags", []),
                risk_level=RiskLevel.LOW,
                risk_score=0.2,
                source="initial_data",
            )
            job_manager.create_company(company)
            success_count += 1
            logger.info(f"  ✓ {company.name}")
        except Exception as e:
            logger.error(f"  ✗ {company_data.get('name')}: {e}")
    
    logger.info(f"公司导入完成: {success_count}/{len(companies)}")
    return success_count


def import_jobs():
    """导入职位数据"""
    from src.jobgraph.graph_manager import job_manager
    from src.jobgraph.models import Job, JobType
    
    data_file = project_root / "data" / "initial" / "tencent_jobs.json"
    
    if not data_file.exists():
        logger.warning(f"职位数据文件不存在: {data_file}")
        return 0
    
    with open(data_file, "r", encoding="utf-8") as f:
        jobs_data = json.load(f)
    
    logger.info(f"导入 {len(jobs_data)} 个职位...")
    
    success_count = 0
    for job_data in jobs_data:
        try:
            job = Job(
                id=job_data.get("id"),
                title=job_data.get("title", ""),
                company_id=job_data.get("company_id", "comp_tencent"),
                company_name=job_data.get("company_name", "腾讯"),
                location=job_data.get("location"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                experience_years=job_data.get("experience_years"),
                education=job_data.get("education"),
                skills=job_data.get("skills", []),
                description=job_data.get("description"),
                requirements=job_data.get("requirements"),
                is_active=job_data.get("is_active", True),
                source=job_data.get("source", "initial_data"),
            )
            job_manager.create_job(job)
            success_count += 1
        except Exception as e:
            logger.error(f"  ✗ {job_data.get('title')}: {e}")
    
    logger.info(f"职位导入完成: {success_count}/{len(jobs_data)}")
    return success_count


def check_existing_data():
    """检查是否已有数据"""
    from src.graph.neo4j_client import neo4j_client
    
    try:
        result = neo4j_client.execute_query("MATCH (c:Company) RETURN count(c) AS cnt")
        count = result[0]["cnt"] if result else 0
        return count
    except Exception:
        return 0


def main():
    logger.info("=" * 60)
    logger.info("导入初始数据")
    logger.info("=" * 60)
    
    # 检查是否已有数据
    existing_count = check_existing_data()
    if existing_count > 10:
        logger.info(f"已有 {existing_count} 家公司数据，跳过导入")
        return
    
    # 导入公司
    company_count = import_companies()
    
    # 导入职位
    job_count = import_jobs()
    
    logger.info("=" * 60)
    logger.info(f"导入完成: {company_count} 家公司, {job_count} 个职位")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
