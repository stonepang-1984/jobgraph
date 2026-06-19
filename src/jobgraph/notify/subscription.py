"""关键词订阅模块

功能：
1. 用户订阅关键词
2. 匹配新职位
3. 管理订阅列表
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from loguru import logger


class SubscriptionManager:
    """订阅管理器"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.notify_dir = self.data_dir / "notify"
        self.notify_dir.mkdir(parents=True, exist_ok=True)
        
        self.subs_file = self.notify_dir / "subscriptions.json"
        self.subscriptions = self._load_subscriptions()

    def _load_subscriptions(self) -> list:
        """加载订阅"""
        if self.subs_file.exists():
            try:
                with open(self.subs_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_subscriptions(self):
        """保存订阅"""
        with open(self.subs_file, "w", encoding="utf-8") as f:
            json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)

    def add_subscription(
        self,
        user_id: str,
        keywords: list[str],
        city: str = "",
        salary_min: float = None,
        notify_method: str = "app",
    ) -> dict:
        """添加订阅

        Args:
            user_id: 用户 ID
            keywords: 关键词列表
            city: 城市
            salary_min: 最低薪资
            notify_method: 通知方式 (app/email/wechat)

        Returns:
            订阅信息
        """
        sub = {
            "id": f"sub_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "keywords": keywords,
            "city": city,
            "salary_min": salary_min,
            "notify_method": notify_method,
            "active": True,
            "created_at": datetime.now().isoformat(),
            "last_notified": None,
        }

        self.subscriptions.append(sub)
        self._save_subscriptions()

        logger.info(f"添加订阅: {sub['id']}, 关键词: {keywords}")
        return sub

    def remove_subscription(self, sub_id: str) -> bool:
        """删除订阅

        Args:
            sub_id: 订阅 ID

        Returns:
            是否成功
        """
        original_count = len(self.subscriptions)
        self.subscriptions = [s for s in self.subscriptions if s["id"] != sub_id]

        if len(self.subscriptions) < original_count:
            self._save_subscriptions()
            logger.info(f"删除订阅: {sub_id}")
            return True

        return False

    def update_subscription(self, sub_id: str, data: dict) -> bool:
        """更新订阅

        Args:
            sub_id: 订阅 ID
            data: 更新数据

        Returns:
            是否成功
        """
        for sub in self.subscriptions:
            if sub["id"] == sub_id:
                sub.update(data)
                self._save_subscriptions()
                logger.info(f"更新订阅: {sub_id}")
                return True

        return False

    def get_user_subscriptions(self, user_id: str) -> list:
        """获取用户订阅

        Args:
            user_id: 用户 ID

        Returns:
            订阅列表
        """
        return [s for s in self.subscriptions if s["user_id"] == user_id]

    def get_active_subscriptions(self) -> list:
        """获取所有活跃订阅

        Returns:
            活跃订阅列表
        """
        return [s for s in self.subscriptions if s["active"]]

    def match_job(self, job: dict) -> list[dict]:
        """匹配职位

        Args:
            job: 职位信息

        Returns:
            匹配的订阅列表
        """
        matched = []

        for sub in self.get_active_subscriptions():
            if self._is_job_match(job, sub):
                matched.append(sub)

        return matched

    def _is_job_match(self, job: dict, subscription: dict) -> bool:
        """检查职位是否匹配订阅

        Args:
            job: 职位信息
            subscription: 订阅信息

        Returns:
            是否匹配
        """
        # 关键词匹配
        keywords = subscription.get("keywords", [])
        if keywords:
            job_text = " ".join([
                job.get("title", ""),
                " ".join(job.get("skills", [])),
                job.get("description", ""),
            ]).lower()

            if not any(kw.lower() in job_text for kw in keywords):
                return False

        # 城市匹配
        city = subscription.get("city", "")
        if city:
            job_location = (job.get("location") or "").lower()
            if city.lower() not in job_location:
                return False

        # 薪资匹配
        salary_min = subscription.get("salary_min")
        if salary_min:
            job_salary_max = job.get("salary_max") or 0
            if job_salary_max < salary_min:
                return False

        return True

    def get_stats(self) -> dict:
        """获取统计信息"""
        total = len(self.subscriptions)
        active = len([s for s in self.subscriptions if s["active"]])

        return {
            "total_subscriptions": total,
            "active_subscriptions": active,
        }


# 全局实例
subscription_manager = SubscriptionManager()
