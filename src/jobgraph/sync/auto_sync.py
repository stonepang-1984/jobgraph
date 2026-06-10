"""自动同步模块

从数据中心（admin）自动同步数据到客户端（jobgraph）
"""

import json
import httpx
from datetime import datetime
from pathlib import Path
from loguru import logger

from src.graph.neo4j_client import neo4j_client


class AutoSync:
    """自动同步器"""

    def __init__(self, server_url: str = None, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.sync_dir = self.data_dir / "synced"
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        
        self.status_file = self.sync_dir / "sync_status.json"
        self.config_file = self.sync_dir / "sync_config.json"
        
        # 加载配置
        self.config = self._load_config()
        self.server_url = server_url or self.config.get("server_url", "")
        
        # 加载状态
        self.status = self._load_status()

    def _load_config(self) -> dict:
        """加载同步配置"""
        default_config = {
            "server_url": "",
            "auto_sync": False,
            "sync_interval": 86400,  # 每天同步一次
            "sync_on_startup": True,
            "last_sync": None,
            "last_version": None,
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception:
                pass
        
        return default_config

    def save_config(self, config: dict):
        """保存同步配置"""
        self.config = config
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _load_status(self) -> dict:
        """加载同步状态"""
        default_status = {
            "last_sync": None,
            "last_version": None,
            "sync_count": 0,
            "companies_synced": 0,
            "jobs_synced": 0,
            "reviews_synced": 0,
        }
        
        if self.status_file.exists():
            try:
                with open(self.status_file, "r", encoding="utf-8") as f:
                    status = json.load(f)
                    default_status.update(status)
            except Exception:
                pass
        
        return default_status

    def _save_status(self):
        """保存同步状态"""
        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(self.status, f, ensure_ascii=False, indent=2)

    def test_connection(self) -> bool:
        """测试数据中心连接"""
        if not self.server_url:
            logger.error("未配置服务器地址")
            return False
        
        try:
            response = httpx.get(f"{self.server_url}/api/v1/status", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False

    def get_remote_version(self) -> str | None:
        """获取远程数据版本"""
        if not self.server_url:
            return None
        
        try:
            response = httpx.get(f"{self.server_url}/api/v1/version", timeout=5)
            if response.status_code == 200:
                return response.json().get("version")
        except Exception as e:
            logger.error(f"获取版本失败: {e}")
        
        return None

    def check_and_sync(self) -> dict:
        """检查并同步数据

        Returns:
            同步结果
        """
        logger.info("=" * 60)
        logger.info("开始检查数据同步")
        logger.info("=" * 60)

        # 1. 测试连接
        if not self.test_connection():
            return {"success": False, "error": "无法连接到数据中心"}

        # 2. 获取远程版本
        remote_version = self.get_remote_version()
        local_version = self.status.get("last_version")

        logger.info(f"本地版本: {local_version}")
        logger.info(f"远程版本: {remote_version}")

        # 3. 比较版本
        if remote_version == local_version:
            logger.info("数据已是最新版本")
            return {"success": True, "status": "up_to_date", "version": local_version}

        # 4. 执行同步
        result = self.sync_all()

        # 5. 更新状态
        if result["success"]:
            self.status = {
                "last_sync": datetime.now().isoformat(),
                "last_version": remote_version,
                "sync_count": self.status.get("sync_count", 0) + 1,
                "companies_synced": result.get("companies", 0),
                "jobs_synced": result.get("jobs", 0),
                "reviews_synced": result.get("reviews", 0),
            }
            self._save_status()

        logger.info("=" * 60)
        logger.info(f"同步完成: {result}")
        logger.info("=" * 60)

        return result

    def sync_all(self) -> dict:
        """同步所有数据

        Returns:
            同步结果
        """
        result = {
            "success": True,
            "companies": 0,
            "jobs": 0,
            "reviews": 0,
        }

        try:
            # 1. 同步公司数据
            logger.info("同步公司数据...")
            companies_result = self.sync_companies()
            result["companies"] = companies_result

            # 2. 同步职位数据
            logger.info("同步职位数据...")
            jobs_result = self.sync_jobs()
            result["jobs"] = jobs_result

            # 3. 同步评价数据
            logger.info("同步评价数据...")
            reviews_result = self.sync_reviews()
            result["reviews"] = reviews_result

        except Exception as e:
            logger.error(f"同步失败: {e}")
            result["success"] = False
            result["error"] = str(e)

        return result

    def sync_companies(self) -> int:
        """同步公司数据"""
        try:
            # 获取本地最后同步时间
            since = self.status.get("last_sync")
            
            # 从数据中心获取数据
            params = {"limit": 1000}
            if since:
                params["since"] = since
            
            response = httpx.get(
                f"{self.server_url}/api/v1/companies",
                params=params,
                timeout=30,
            )
            
            if response.status_code != 200:
                logger.error(f"获取公司数据失败: {response.status_code}")
                return 0
            
            data = response.json()
            companies = data.get("data", [])
            
            # 导入到 Neo4j
            count = 0
            for company in companies:
                try:
                    self._import_company(company)
                    count += 1
                except Exception as e:
                    logger.error(f"导入公司失败: {e}")
            
            logger.info(f"同步公司完成: {count} 家")
            return count
            
        except Exception as e:
            logger.error(f"同步公司失败: {e}")
            return 0

    def sync_jobs(self) -> int:
        """同步职位数据"""
        try:
            since = self.status.get("last_sync")
            
            params = {"limit": 1000}
            if since:
                params["since"] = since
            
            response = httpx.get(
                f"{self.server_url}/api/v1/jobs",
                params=params,
                timeout=30,
            )
            
            if response.status_code != 200:
                logger.error(f"获取职位数据失败: {response.status_code}")
                return 0
            
            data = response.json()
            jobs = data.get("data", [])
            
            count = 0
            for job in jobs:
                try:
                    self._import_job(job)
                    count += 1
                except Exception as e:
                    logger.error(f"导入职位失败: {e}")
            
            logger.info(f"同步职位完成: {count} 个")
            return count
            
        except Exception as e:
            logger.error(f"同步职位失败: {e}")
            return 0

    def sync_reviews(self) -> int:
        """同步评价数据"""
        try:
            since = self.status.get("last_sync")
            
            params = {"limit": 1000}
            if since:
                params["since"] = since
            
            response = httpx.get(
                f"{self.server_url}/api/v1/reviews",
                params=params,
                timeout=30,
            )
            
            if response.status_code != 200:
                logger.error(f"获取评价数据失败: {response.status_code}")
                return 0
            
            data = response.json()
            reviews = data.get("data", [])
            
            count = 0
            for review in reviews:
                try:
                    self._import_review(review)
                    count += 1
                except Exception as e:
                    logger.error(f"导入评价失败: {e}")
            
            logger.info(f"同步评价完成: {count} 条")
            return count
            
        except Exception as e:
            logger.error(f"同步评价失败: {e}")
            return 0

    def _import_company(self, data: dict):
        """导入公司数据到 Neo4j"""
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
        neo4j_client.execute_write(cypher, data)

    def _import_job(self, data: dict):
        """导入职位数据到 Neo4j"""
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
            **data,
            "is_active": data.get("is_active", True),
        })

    def _import_review(self, data: dict):
        """导入评价数据到 Neo4j"""
        # 检查公司是否存在
        company_check = neo4j_client.execute_query(
            "MATCH (c:Company {id: $company_id}) RETURN c.id AS id",
            {"company_id": data.get("company_id")}
        )
        
        if not company_check:
            logger.warning(f"公司不存在，跳过评价: {data.get('company_id')}")
            return

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
        neo4j_client.execute_write(cypher, data)

    def get_status_info(self) -> dict:
        """获取同步状态信息"""
        return {
            "server_url": self.server_url,
            "connected": self.test_connection() if self.server_url else False,
            "last_sync": self.status.get("last_sync"),
            "last_version": self.status.get("last_version"),
            "sync_count": self.status.get("sync_count", 0),
            "companies_synced": self.status.get("companies_synced", 0),
            "jobs_synced": self.status.get("jobs_synced", 0),
            "reviews_synced": self.status.get("reviews_synced", 0),
        }


# 全局实例
auto_sync = AutoSync()
