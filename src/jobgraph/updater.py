"""数据更新管理器

功能:
1. 跟踪数据版本
2. 增量更新
3. 定时更新
4. 更新日志
"""

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.graph.neo4j_client import neo4j_client


class DataUpdateManager:
    """数据更新管理器"""

    def __init__(self):
        self.update_dir = Path("data/updates")
        self.update_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.update_dir / "update_log.json"
        self._load_log()

    def _load_log(self) -> None:
        """加载更新日志"""
        if self.log_file.exists():
            self.log_data = json.loads(self.log_file.read_text())
        else:
            self.log_data = {
                "last_update": None,
                "updates": [],
                "data_versions": {},
            }

    def _save_log(self) -> None:
        """保存更新日志"""
        self.log_file.write_text(json.dumps(self.log_data, indent=2, ensure_ascii=False))

    def get_last_update(self, data_type: str = "all") -> str | None:
        """获取最后更新时间"""
        if data_type == "all":
            return self.log_data.get("last_update")
        return self.log_data.get("data_versions", {}).get(data_type, {}).get("last_update")

    def check_update_needed(self, data_type: str, interval_hours: int = 24) -> bool:
        """检查是否需要更新"""
        last_update = self.get_last_update(data_type)
        if not last_update:
            return True

        last_time = datetime.fromisoformat(last_update)
        elapsed = (datetime.now() - last_time).total_seconds() / 3600
        return elapsed >= interval_hours

    def record_update(self, data_type: str, count: int, details: dict = None) -> None:
        """记录更新"""
        now = datetime.now().isoformat()

        # 更新总时间
        self.log_data["last_update"] = now

        # 更新数据版本
        if data_type not in self.log_data["data_versions"]:
            self.log_data["data_versions"][data_type] = {}

        self.log_data["data_versions"][data_type]["last_update"] = now
        self.log_data["data_versions"][data_type]["count"] = count

        # 添加更新记录
        self.log_data["updates"].append(
            {
                "type": data_type,
                "timestamp": now,
                "count": count,
                "details": details or {},
            }
        )

        # 只保留最近 100 条记录
        self.log_data["updates"] = self.log_data["updates"][-100:]

        self._save_log()
        logger.info(f"Recorded update: {data_type}, count={count}")

    def get_update_history(self, limit: int = 10) -> list[dict]:
        """获取更新历史"""
        return self.log_data.get("updates", [])[-limit:]

    def get_statistics(self) -> dict:
        """获取更新统计"""
        versions = self.log_data.get("data_versions", {})
        return {
            "last_update": self.log_data.get("last_update"),
            "data_types": list(versions.keys()),
            "total_updates": len(self.log_data.get("updates", [])),
            "versions": versions,
        }


class IncrementalUpdater:
    """增量更新器"""

    def __init__(self):
        self.update_manager = DataUpdateManager()

    def update_companies(self, companies: list[dict]) -> dict:
        """增量更新公司数据"""

        stats = {"created": 0, "updated": 0, "unchanged": 0}

        for data in companies:
            try:
                # 检查是否存在
                existing = neo4j_client.execute_query("MATCH (c:Company {id: $id}) RETURN c", {"id": data["id"]})

                if existing:
                    # 检查是否有变化
                    if self._has_changes(existing[0]["c"], data):
                        self._update_company(data)
                        stats["updated"] += 1
                    else:
                        stats["unchanged"] += 1
                else:
                    self._create_company(data)
                    stats["created"] += 1

            except Exception as e:
                logger.error(f"Failed to update company {data.get('name')}: {e}")

        # 记录更新
        self.update_manager.record_update("companies", sum(stats.values()), stats)
        return stats

    def update_jobs(self, jobs: list[dict]) -> dict:
        """增量更新岗位数据"""

        stats = {"created": 0, "updated": 0, "unchanged": 0, "deactivated": 0}

        # 获取现有岗位
        existing_jobs = {
            r["id"]: r for r in neo4j_client.execute_query("MATCH (j:Job) RETURN j.id AS id, j.is_active AS is_active")
        }

        new_job_ids = {j["id"] for j in jobs}

        for data in jobs:
            try:
                if data["id"] in existing_jobs:
                    # 更新现有岗位
                    self._update_job(data)
                    stats["updated"] += 1
                else:
                    # 创建新岗位
                    self._create_job(data)
                    stats["created"] += 1
            except Exception as e:
                logger.error(f"Failed to update job {data.get('title')}: {e}")

        # 停用不再存在的岗位
        for job_id, job_data in existing_jobs.items():
            if job_id not in new_job_ids and job_data.get("is_active"):
                self._deactivate_job(job_id)
                stats["deactivated"] += 1

        # 记录更新
        self.update_manager.record_update("jobs", sum(stats.values()), stats)
        return stats

    def _has_changes(self, existing: dict, new_data: dict) -> bool:
        """检查数据是否有变化"""
        compare_fields = ["name", "industry", "headquarters", "avg_salary", "avg_rating"]
        for field in compare_fields:
            if existing.get(field) != new_data.get(field):
                return True
        return False

    def _create_company(self, data: dict) -> None:
        """创建公司"""
        from src.jobgraph.models import Company, CompanySize, RiskLevel

        size_map = {
            "startup": CompanySize.STARTUP,
            "small": CompanySize.SMALL,
            "medium": CompanySize.MEDIUM,
            "large": CompanySize.LARGE,
            "enterprise": CompanySize.ENTERPRISE,
            "giant": CompanySize.GIANT,
        }
        risk_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "blacklist": RiskLevel.BLACKLIST,
        }

        company = Company(
            id=data["id"],
            name=data["name"],
            name_en=data.get("name_en"),
            industry=data.get("industry"),
            size=size_map.get(data.get("size", "").lower(), CompanySize.MEDIUM),
            founded=data.get("founded"),
            headquarters=data.get("headquarters"),
            employees=data.get("employees"),
            avg_salary=data.get("avg_salary"),
            avg_rating=data.get("avg_rating"),
            risk_level=risk_map.get(data.get("risk_level", "medium").lower(), RiskLevel.MEDIUM),
            risk_score=data.get("risk_score", 0.5),
            tags=data.get("tags", []),
        )

        cypher = """
        CREATE (c:Company {
            id: $id, name: $name, name_en: $name_en,
            industry: $industry, size: $size, founded: $founded,
            headquarters: $headquarters, employees: $employees,
            avg_salary: $avg_salary, avg_rating: $avg_rating,
            risk_level: $risk_level, risk_score: $risk_score,
            tags: $tags, created_at: datetime(), updated_at: datetime()
        })
        """
        neo4j_client.execute_write(
            cypher,
            {
                "id": company.id,
                "name": company.name,
                "name_en": company.name_en,
                "industry": company.industry,
                "size": company.size.value if company.size else None,
                "founded": company.founded,
                "headquarters": company.headquarters,
                "employees": company.employees,
                "avg_salary": company.avg_salary,
                "avg_rating": company.avg_rating,
                "risk_level": company.risk_level.value,
                "risk_score": company.risk_score,
                "tags": company.tags,
            },
        )

    def _update_company(self, data: dict) -> None:
        """更新公司"""
        cypher = """
        MATCH (c:Company {id: $id})
        SET c.name = $name, c.name_en = $name_en,
            c.industry = $industry, c.headquarters = $headquarters,
            c.avg_salary = $avg_salary, c.avg_rating = $avg_rating,
            c.risk_level = $risk_level, c.risk_score = $risk_score,
            c.tags = $tags, c.updated_at = datetime()
        """
        neo4j_client.execute_write(cypher, data)

    def _create_job(self, data: dict) -> None:
        """创建岗位"""
        cypher = """
        CREATE (j:Job {
            id: $id, title: $title, company_id: $company_id,
            company_name: $company_name, department: $department,
            location: $location, salary_min: $salary_min,
            salary_max: $salary_max, salary_months: $salary_months,
            experience_years: $experience_years, education: $education,
            skills: $skills, benefits: $benefits, is_active: true,
            created_at: datetime(), updated_at: datetime()
        })
        WITH j
        MATCH (c:Company {id: $company_id})
        MERGE (c)-[:HAS_JOB]->(j)
        """
        neo4j_client.execute_write(cypher, data)

    def _update_job(self, data: dict) -> None:
        """更新岗位"""
        cypher = """
        MATCH (j:Job {id: $id})
        SET j.title = $title, j.salary_min = $salary_min,
            j.salary_max = $salary_max, j.skills = $skills,
            j.is_active = true, j.updated_at = datetime()
        """
        neo4j_client.execute_write(cypher, data)

    def _deactivate_job(self, job_id: str) -> None:
        """停用岗位"""
        cypher = """
        MATCH (j:Job {id: $id})
        SET j.is_active = false, j.updated_at = datetime()
        """
        neo4j_client.execute_write(cypher, {"id": job_id})


# 全局实例
update_manager = DataUpdateManager()
incremental_updater = IncrementalUpdater()
