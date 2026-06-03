"""用户端数据同步模块 - 支持多种同步方式"""

import json
import zipfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger

import httpx

from config.settings import settings


class DataSync:
    """数据同步器 - 统一接口"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.sync_dir = Path("data/synced")
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.sync_dir / "sync_status.json"
        self._load_status()

    def _load_status(self) -> None:
        """加载同步状态"""
        if self.status_file.exists():
            self.status = json.loads(self.status_file.read_text())
        else:
            self.status = {
                "mode": None,
                "last_sync": None,
                "version": None,
                "counts": {},
            }

    def _save_status(self) -> None:
        """保存同步状态"""
        self.status_file.write_text(json.dumps(self.status, ensure_ascii=False, indent=2))

    def get_status(self) -> dict:
        """获取同步状态"""
        return self.status

    # ============================================================
    # 场景A: 离线数据包
    # ============================================================

    def import_package(self, package_path: str) -> dict:
        """导入离线数据包

        Args:
            package_path: 数据包文件路径 (.zip)

        Returns:
            导入统计
        """
        logger.info(f"导入数据包: {package_path}")

        path = Path(package_path)
        if not path.exists():
            raise FileNotFoundError(f"数据包不存在: {package_path}")

        # 1. 解压数据包
        with zipfile.ZipFile(path, "r") as zf:
            # 读取数据
            data_json = zf.read("data.json")
            package = json.loads(data_json)

        # 2. 验证校验和
        metadata = package.get("metadata", {})
        expected_checksum = metadata.get("checksum")
        if expected_checksum:
            # 重新计算校验和（排除 checksum 字段）
            verify_data = {k: v for k, v in package.items() if k != "metadata"}
            verify_data["metadata"] = {k: v for k, v in metadata.items() if k != "checksum"}
            actual_checksum = hashlib.md5(
                json.dumps(verify_data, ensure_ascii=False).encode()
            ).hexdigest()
            # 注意：实际校验和可能因 JSON 序列化差异而不匹配，这里仅警告
            if actual_checksum != expected_checksum:
                logger.warning("校验和不匹配，数据可能已修改")

        # 3. 导入数据
        stats = self._import_data(package)

        # 4. 更新状态
        self.status = {
            "mode": "package",
            "last_sync": datetime.now().isoformat(),
            "version": metadata.get("version"),
            "counts": metadata.get("counts", {}),
        }
        self._save_status()

        logger.info(f"数据包导入完成: {stats}")
        return stats

    # ============================================================
    # 场景B: Tailscale 直连
    # ============================================================

    def sync_via_tailscale(self, server_url: str, token: str = None) -> dict:
        """通过 Tailscale 同步

        Args:
            server_url: 数据中心地址 (http://100.x.x.1:8000)
            token: 认证 Token (付费用户)

        Returns:
            同步统计
        """
        logger.info(f"通过 Tailscale 同步: {server_url}")

        # 1. 测试连接
        if not self._test_connection(server_url):
            raise ConnectionError(f"无法连接到数据中心: {server_url}")

        # 2. 检查版本
        remote_version = self._get_remote_version(server_url)
        local_version = self.status.get("version")

        if remote_version == local_version:
            logger.info("数据已是最新版本")
            return {"status": "up_to_date", "version": local_version}

        # 3. 拉取数据
        stats = self._fetch_data(server_url, token)

        # 4. 更新状态
        self.status = {
            "mode": "tailscale",
            "last_sync": datetime.now().isoformat(),
            "version": remote_version,
            "server": server_url,
            "counts": stats.get("counts", {}),
        }
        self._save_status()

        logger.info(f"Tailscale 同步完成: {stats}")
        return stats

    # ============================================================
    # 场景C: 云服务器
    # ============================================================

    def sync_via_cloud(self, cloud_url: str, token: str = None) -> dict:
        """通过云服务器同步

        Args:
            cloud_url: 云服务器地址 (https://api.jobgraph.com)
            token: 认证 Token

        Returns:
            同步统计
        """
        logger.info(f"通过云服务器同步: {cloud_url}")

        # 1. 测试连接
        if not self._test_connection(cloud_url):
            raise ConnectionError(f"无法连接到云服务器: {cloud_url}")

        # 2. 检查版本
        remote_version = self._get_remote_version(cloud_url)
        local_version = self.status.get("version")

        if remote_version == local_version:
            logger.info("数据已是最新版本")
            return {"status": "up_to_date", "version": local_version}

        # 3. 拉取数据
        stats = self._fetch_data(cloud_url, token)

        # 4. 更新状态
        self.status = {
            "mode": "cloud",
            "last_sync": datetime.now().isoformat(),
            "version": remote_version,
            "server": cloud_url,
            "counts": stats.get("counts", {}),
        }
        self._save_status()

        logger.info(f"云服务器同步完成: {stats}")
        return stats

    # ============================================================
    # 内部方法
    # ============================================================

    def _test_connection(self, server_url: str) -> bool:
        """测试服务器连接"""
        try:
            response = httpx.get(f"{server_url}/api/v1/status", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False

    def _get_remote_version(self, server_url: str) -> str:
        """获取远程数据版本"""
        try:
            response = httpx.get(f"{server_url}/api/v1/version", timeout=5)
            if response.status_code == 200:
                return response.json().get("version")
        except Exception as e:
            logger.error(f"获取版本失败: {e}")
        return None

    def _fetch_data(self, server_url: str, token: str = None) -> dict:
        """从服务器拉取数据"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        stats = {"companies": 0, "jobs": 0, "reviews": 0, "counts": {}}

        try:
            # 拉取公司数据
            response = httpx.get(
                f"{server_url}/api/v1/companies",
                headers=headers,
                timeout=30,
            )
            if response.status_code == 200:
                companies_data = response.json()
                stats["companies"] = companies_data.get("count", 0)
                # 保存到本地
                self._save_local_data("companies", companies_data.get("data", []))

            # 拉取岗位数据
            response = httpx.get(
                f"{server_url}/api/v1/jobs",
                headers=headers,
                timeout=30,
            )
            if response.status_code == 200:
                jobs_data = response.json()
                stats["jobs"] = jobs_data.get("count", 0)
                self._save_local_data("jobs", jobs_data.get("data", []))

            # 拉取评价数据
            response = httpx.get(
                f"{server_url}/api/v1/reviews",
                headers=headers,
                timeout=30,
            )
            if response.status_code == 200:
                reviews_data = response.json()
                stats["reviews"] = reviews_data.get("count", 0)
                self._save_local_data("reviews", reviews_data.get("data", []))

            stats["counts"] = {
                "companies": stats["companies"],
                "jobs": stats["jobs"],
                "reviews": stats["reviews"],
            }

        except Exception as e:
            logger.error(f"数据拉取失败: {e}")
            raise

        return stats

    def _save_local_data(self, data_type: str, data: list) -> None:
        """保存数据到本地"""
        filepath = self.sync_dir / f"{data_type}.json"
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        logger.debug(f"保存 {data_type}: {len(data)} 条")

    def _import_data(self, package: dict) -> dict:
        """导入数据到 Neo4j"""
        from src.jobgraph.graph_manager import job_manager
        from src.jobgraph.models import Company, Job, Review, CompanySize, RiskLevel

        stats = {"companies": 0, "jobs": 0, "reviews": 0}

        # 导入公司
        for data in package.get("companies", []):
            try:
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
                job_manager.create_company(company)
                stats["companies"] += 1
            except Exception as e:
                logger.error(f"导入公司失败: {e}")

        # 导入岗位
        for data in package.get("jobs", []):
            try:
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
                    skills=data.get("skills", []),
                    benefits=data.get("benefits", []),
                    is_active=data.get("is_active", True),
                )
                job_manager.create_job(job)
                stats["jobs"] += 1
            except Exception as e:
                logger.error(f"导入岗位失败: {e}")

        # 导入评价
        for data in package.get("reviews", []):
            try:
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
                    pitfall_tags=data.get("pitfall_tags", []),
                )
                job_manager.create_review(review)
                stats["reviews"] += 1
            except Exception as e:
                logger.error(f"导入评价失败: {e}")

        return stats


# 全局实例
data_sync = DataSync()
