"""提醒通知模块

功能：
1. 新职位通知
2. 通知管理（已读/未读）
3. 通知历史
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger


class Notifier:
    """通知管理器"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.notify_dir = self.data_dir / "notify"
        self.notify_dir.mkdir(parents=True, exist_ok=True)

        self.notifs_file = self.notify_dir / "notifications.json"
        self.notifications = self._load_notifications()

    def _load_notifications(self) -> list:
        """加载通知"""
        if self.notifs_file.exists():
            try:
                with open(self.notifs_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_notifications(self):
        """保存通知"""
        with open(self.notifs_file, "w", encoding="utf-8") as f:
            json.dump(self.notifications, f, ensure_ascii=False, indent=2)

    def add_notification(
        self,
        user_id: str,
        job: dict,
        subscription_id: str = None,
    ) -> dict:
        """添加通知

        Args:
            user_id: 用户 ID
            job: 职位信息
            subscription_id: 触发通知的订阅 ID

        Returns:
            通知信息
        """
        notify = {
            "id": f"notify_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "job_id": job.get("id"),
            "job_title": job.get("title"),
            "company_name": job.get("company_name"),
            "location": job.get("location"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "skills": job.get("skills", []),
            "subscription_id": subscription_id,
            "read": False,
            "created_at": datetime.now().isoformat(),
        }

        self.notifications.append(notify)
        self._save_notifications()

        logger.info(f"添加通知: {notify['job_title']} @ {notify['company_name']}")
        return notify

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list:
        """获取用户通知

        Args:
            user_id: 用户 ID
            unread_only: 是否只返回未读
            limit: 返回数量限制

        Returns:
            通知列表
        """
        notifs = [n for n in self.notifications if n["user_id"] == user_id]

        if unread_only:
            notifs = [n for n in notifs if not n["read"]]

        # 按创建时间倒序
        notifs.sort(key=lambda x: x["created_at"], reverse=True)

        return notifs[:limit]

    def mark_read(self, notify_id: str) -> bool:
        """标记已读

        Args:
            notify_id: 通知 ID

        Returns:
            是否成功
        """
        for n in self.notifications:
            if n["id"] == notify_id:
                n["read"] = True
                self._save_notifications()
                return True

        return False

    def mark_all_read(self, user_id: str) -> int:
        """标记所有通知为已读

        Args:
            user_id: 用户 ID

        Returns:
            标记数量
        """
        count = 0
        for n in self.notifications:
            if n["user_id"] == user_id and not n["read"]:
                n["read"] = True
                count += 1

        if count > 0:
            self._save_notifications()

        return count

    def delete_notification(self, notify_id: str) -> bool:
        """删除通知

        Args:
            notify_id: 通知 ID

        Returns:
            是否成功
        """
        original_count = len(self.notifications)
        self.notifications = [n for n in self.notifications if n["id"] != notify_id]

        if len(self.notifications) < original_count:
            self._save_notifications()
            return True

        return False

    def check_new_jobs(self, jobs: list[dict], subscription_manager) -> list[dict]:
        """检查新职位并发送通知

        Args:
            jobs: 新职位列表
            subscription_manager: 订阅管理器

        Returns:
            发送的通知列表
        """
        sent_notifications = []

        for job in jobs:
            # 匹配订阅
            matched_subs = subscription_manager.match_job(job)

            for sub in matched_subs:
                user_id = sub["user_id"]

                # 检查是否已通知过（避免重复通知）
                if self._already_notified(user_id, job.get("id")):
                    continue

                # 发送通知
                notify = self.add_notification(
                    user_id=user_id,
                    job=job,
                    subscription_id=sub["id"],
                )
                sent_notifications.append(notify)

        logger.info(f"发送 {len(sent_notifications)} 条通知")
        return sent_notifications

    def _already_notified(self, user_id: str, job_id: str) -> bool:
        """检查是否已通知过"""
        for n in self.notifications:
            if n["user_id"] == user_id and n["job_id"] == job_id:
                return True
        return False

    def get_stats(self, user_id: str = None) -> dict:
        """获取统计信息"""
        if user_id:
            user_notifs = [n for n in self.notifications if n["user_id"] == user_id]
            return {
                "total": len(user_notifs),
                "unread": len([n for n in user_notifs if not n["read"]]),
            }
        else:
            return {
                "total": len(self.notifications),
                "unread": len([n for n in self.notifications if not n["read"]]),
            }


# 全局实例
notifier = Notifier()
