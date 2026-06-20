#!/usr/bin/env python3
"""从 Admin 导出的数据导入到 Jobgraph Neo4j

导入公司、职位、评价数据，基于 ID 去重（MERGE）

用法:
    python import_from_admin.py --file data/sync/admin_data.json
    python import_from_admin.py --file /path/to/admin_data_20260620.json
"""

import sys
import json
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.graph.neo4j_client import neo4j_client


def import_companies(companies: list[dict]) -> int:
    """导入公司数据（基于 ID 去重）"""
    success = 0
    
    for company in companies:
        try:
            cypher = """
            MERGE (c:Company {id: $id})
            SET c.name = $name,
                c.name_en = $name_en,
                c.industry = $industry,
                c.size = $size,
                c.headquarters = $headquarters,
                c.website = $website,
                c.careers_url = $careers_url,
                c.description = $description,
                c.tags = $tags,
                c.risk_level = $risk_level,
                c.risk_score = $risk_score,
                c.avg_salary = $avg_salary,
                c.avg_rating = $avg_rating,
                c.updated_at = datetime()
            """
            neo4j_client.execute_write(cypher, company)
            success += 1
        except Exception as e:
            logger.error(f"导入公司失败 {company.get('name')}: {e}")
    
    logger.info(f"公司导入: {success}/{len(companies)}")
    return success


def import_jobs(jobs: list[dict]) -> int:
    """导入职位数据（基于 ID 去重）"""
    success = 0
    
    for job in jobs:
        try:
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
                j.requirements = $requirements,
                j.is_active = $is_active,
                j.updated_at = datetime()
            WITH j
            MATCH (c:Company {id: $company_id})
            MERGE (c)-[:HAS_JOB]->(j)
            """
            neo4j_client.execute_write(cypher, {
                **job,
                "is_active": job.get("is_active", True),
            })
            success += 1
        except Exception as e:
            logger.error(f"导入职位失败 {job.get('title')}: {e}")
    
    logger.info(f"职位导入: {success}/{len(jobs)}")
    return success


def import_reviews(reviews: list[dict]) -> int:
    """导入评价数据（基于 ID 去重）"""
    success = 0
    
    for review in reviews:
        try:
            # 检查公司是否存在
            company_check = neo4j_client.execute_query(
                "MATCH (c:Company {id: $company_id}) RETURN c.id AS id",
                {"company_id": review.get("company_id")}
            )
            
            if not company_check:
                logger.warning(f"公司不存在，跳过评价: {review.get('company_id')}")
                continue
            
            cypher = """
            MERGE (r:Review {id: $id})
            SET r.company_id = $company_id,
                r.overall_rating = $overall_rating,
                r.salary_rating = $salary_rating,
                r.work_life_rating = $work_life_rating,
                r.management_rating = $management_rating,
                r.title = $title,
                r.pros = $pros,
                r.cons = $cons,
                r.reviewer_title = $reviewer_title,
                r.reviewer_tenure = $reviewer_tenure,
                r.source = $source,
                r.updated_at = datetime()
            WITH r
            MATCH (c:Company {id: $company_id})
            MERGE (c)-[:HAS_REVIEW]->(r)
            """
            neo4j_client.execute_write(cypher, review)
            success += 1
        except Exception as e:
            logger.error(f"导入评价失败 {review.get('title')}: {e}")
    
    logger.info(f"评价导入: {success}/{len(reviews)}")
    return success


def main():
    parser = argparse.ArgumentParser(description="从 Admin 导入数据到 Jobgraph")
    parser.add_argument("--file", "-f", required=True, help="Admin 导出的 JSON 文件路径")
    args = parser.parse_args()
    
    # 检查文件
    data_file = Path(args.file)
    if not data_file.exists():
        logger.error(f"文件不存在: {data_file}")
        return
    
    # 读取数据
    logger.info("=" * 60)
    logger.info(f"从 Admin 导入数据: {data_file}")
    logger.info("=" * 60)
    
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    companies = data.get("companies", [])
    jobs = data.get("jobs", [])
    reviews = data.get("reviews", [])
    
    logger.info(f"待导入: {len(companies)} 家公司, {len(jobs)} 个职位, {len(reviews)} 条评价")
    
    # 导入数据
    company_count = import_companies(companies)
    job_count = import_jobs(jobs)
    review_count = import_reviews(reviews)
    
    # 统计
    logger.info("=" * 60)
    logger.info("导入完成！")
    logger.info(f"  公司: {company_count} 家")
    logger.info(f"  职位: {job_count} 个")
    logger.info(f"  评价: {review_count} 条")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
