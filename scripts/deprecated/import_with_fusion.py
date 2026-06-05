"""数据导入脚本 - 使用数据融合引擎

支持多来源数据导入、去重、融合
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.graph.neo4j_client import neo4j_client
from src.jobgraph.fusion.engine import fusion_engine, quality_checker
from src.jobgraph.fusion.lineage import data_lineage
from src.jobgraph.models import Company, Job, Review, CompanySize, RiskLevel


def load_json(filepath: str) -> list[dict]:
    """加载 JSON 文件"""
    path = Path(filepath)
    if not path.exists():
        logger.error(f"File not found: {filepath}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def import_companies_with_fusion(companies_data: list[dict], source: str = "crawler") -> dict:
    """导入公司数据（带融合）"""
    stats = {"created": 0, "updated": 0, "merged": 0, "skipped": 0, "errors": 0}

    # 获取现有公司
    existing_companies = {}
    try:
        results = neo4j_client.execute_query("MATCH (c:Company) RETURN c")
        for r in results:
            c = r["c"]
            existing_companies[c["id"]] = c
    except Exception:
        pass

    # 质量检查
    valid_companies = []
    for data in companies_data:
        quality = quality_checker.check_company(data)
        if quality["valid"]:
            valid_companies.append(data)
        else:
            logger.warning(f"Quality check failed for {data.get('name')}: {quality['issues']}")
            stats["skipped"] += 1

    # 去重
    deduplicated = fusion_engine.deduplicate_companies(valid_companies)

    # 导入
    for data in deduplicated:
        try:
            company_id = data.get("id")
            existing = existing_companies.get(company_id)

            # 融合数据
            fused = fusion_engine.fuse_company(existing, data, source)

            # 写入数据库
            cypher = """
            MERGE (c:Company {id: $id})
            SET c.name = $name,
                c.name_en = $name_en,
                c.industry = $industry,
                c.size = $size,
                c.founded = $founded,
                c.headquarters = $headquarters,
                c.employees = $employees,
                c.avg_salary = $avg_salary,
                c.avg_rating = $avg_rating,
                c.risk_level = $risk_level,
                c.risk_score = $risk_score,
                c.tags = $tags,
                c.source = $source,
                c.updated_at = datetime()
            """
            neo4j_client.execute_write(
                cypher,
                {
                    "id": fused.get("id"),
                    "name": fused.get("name"),
                    "name_en": fused.get("name_en"),
                    "industry": fused.get("industry"),
                    "size": fused.get("size"),
                    "founded": fused.get("founded"),
                    "headquarters": fused.get("headquarters"),
                    "employees": fused.get("employees"),
                    "avg_salary": fused.get("avg_salary"),
                    "avg_rating": fused.get("avg_rating"),
                    "risk_level": fused.get("risk_level", "medium"),
                    "risk_score": fused.get("risk_score", 0.5),
                    "tags": fused.get("tags", []),
                    "source": source,
                },
            )

            # 记录血缘
            data_lineage.record_source(
                entity_id=company_id,
                entity_type="company",
                field="name",
                value=fused.get("name"),
                source=source,
            )

            if existing:
                stats["updated"] += 1
            else:
                stats["created"] += 1

        except Exception as e:
            logger.error(f"Failed to import company {data.get('name')}: {e}")
            stats["errors"] += 1

    return stats


def import_jobs_with_fusion(jobs_data: list[dict], source: str = "crawler") -> dict:
    """导入岗位数据（带融合）"""
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for data in jobs_data:
        try:
            # 质量检查
            quality = quality_checker.check_job(data)
            if not quality["valid"]:
                logger.warning(f"Quality check failed for {data.get('title')}: {quality['issues']}")
                stats["skipped"] += 1
                continue

            # 写入数据库
            cypher = """
            MERGE (j:Job {id: $id})
            SET j.title = $title,
                j.company_id = $company_id,
                j.company_name = $company_name,
                j.department = $department,
                j.location = $location,
                j.salary_min = $salary_min,
                j.salary_max = $salary_max,
                j.salary_months = $salary_months,
                j.experience_years = $experience_years,
                j.education = $education,
                j.skills = $skills,
                j.benefits = $benefits,
                j.is_active = $is_active,
                j.source = $source,
                j.updated_at = datetime()
            WITH j
            MATCH (c:Company {id: $company_id})
            MERGE (c)-[:HAS_JOB]->(j)
            """
            neo4j_client.execute_write(
                cypher,
                {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "company_id": data.get("company_id"),
                    "company_name": data.get("company_name"),
                    "department": data.get("department"),
                    "location": data.get("location"),
                    "salary_min": data.get("salary_min"),
                    "salary_max": data.get("salary_max"),
                    "salary_months": data.get("salary_months", 12),
                    "experience_years": data.get("experience_years"),
                    "education": data.get("education"),
                    "skills": data.get("skills", []),
                    "benefits": data.get("benefits", []),
                    "is_active": data.get("is_active", True),
                    "source": source,
                },
            )
            stats["created"] += 1

        except Exception as e:
            logger.error(f"Failed to import job {data.get('title')}: {e}")
            stats["errors"] += 1

    return stats


def import_reviews_with_fusion(reviews_data: list[dict], source: str = "user") -> dict:
    """导入评价数据（带融合）"""
    stats = {"created": 0, "skipped": 0, "errors": 0}

    for data in reviews_data:
        try:
            # 质量检查
            quality = quality_checker.check_review(data)
            if not quality["valid"]:
                logger.warning(f"Quality check failed for review: {quality['issues']}")
                stats["skipped"] += 1
                continue

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
                source: $source,
                status: 'approved',
                created_at: datetime()
            })
            WITH r
            MATCH (c:Company {id: $company_id})
            MERGE (c)-[:HAS_REVIEW]->(r)
            """
            neo4j_client.execute_write(
                cypher,
                {
                    "id": data.get("id"),
                    "company_id": data.get("company_id"),
                    "overall_rating": data.get("overall_rating", 0),
                    "salary_rating": data.get("salary_rating"),
                    "work_life_rating": data.get("work_life_rating"),
                    "management_rating": data.get("management_rating"),
                    "title": data.get("title"),
                    "pros": data.get("pros"),
                    "cons": data.get("cons"),
                    "reviewer_title": data.get("reviewer_title"),
                    "reviewer_tenure": data.get("reviewer_tenure"),
                    "pitfall_tags": data.get("pitfall_tags", []),
                    "source": source,
                },
            )
            stats["created"] += 1

        except Exception as e:
            logger.error(f"Failed to import review: {e}")
            stats["errors"] += 1

    return stats


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Data Import with Fusion")
    logger.info("=" * 60)

    # 加载数据
    data_dir = Path("data/crawled")

    companies_data = load_json(str(data_dir / "companies.json"))
    jobs_data = load_json(str(data_dir / "jobs.json"))
    reviews_data = load_json(str(data_dir / "reviews.json"))

    logger.info(f"Loaded: {len(companies_data)} companies, {len(jobs_data)} jobs, {len(reviews_data)} reviews")

    # 导入数据
    company_stats = import_companies_with_fusion(companies_data, source="crawler")
    logger.info(f"Companies: {company_stats}")

    job_stats = import_jobs_with_fusion(jobs_data, source="crawler")
    logger.info(f"Jobs: {job_stats}")

    review_stats = import_reviews_with_fusion(reviews_data, source="crawler")
    logger.info(f"Reviews: {review_stats}")

    # 打印统计
    from src.jobgraph.graph_manager import job_manager
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
