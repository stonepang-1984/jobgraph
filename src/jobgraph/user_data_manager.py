"""用户数据持久化模块

保存用户数据（简历信息等）到本地文件
实现跨会话数据持久化
"""

import json
from pathlib import Path
from datetime import datetime
from loguru import logger


class UserDataManager:
    """用户数据管理器"""

    def __init__(self, data_dir: str = "./data/user"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_file(self, user_id: str) -> Path:
        """获取用户数据文件路径"""
        return self.data_dir / f"{user_id}.json"

    def save_resume_profile(self, user_id: str, profile: dict) -> bool:
        """保存简历信息

        Args:
            user_id: 用户 ID
            profile: 简历信息

        Returns:
            是否成功
        """
        try:
            user_file = self._get_user_file(user_id)

            # 读取现有数据
            user_data = {}
            if user_file.exists():
                with open(user_file, "r", encoding="utf-8") as f:
                    user_data = json.load(f)

            # 更新简历信息
            user_data["resume_profile"] = profile
            user_data["resume_updated_at"] = datetime.now().isoformat()

            # 保存数据
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)

            logger.info(f"简历信息已保存: {user_file}")
            return True

        except Exception as e:
            logger.error(f"保存简历信息失败: {e}")
            return False

    def load_resume_profile(self, user_id: str) -> dict | None:
        """加载简历信息

        Args:
            user_id: 用户 ID

        Returns:
            简历信息，不存在返回 None
        """
        try:
            user_file = self._get_user_file(user_id)

            if not user_file.exists():
                return None

            with open(user_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)

            return user_data.get("resume_profile")

        except Exception as e:
            logger.error(f"加载简历信息失败: {e}")
            return None

    def save_user_profile(self, user_id: str, profile: dict) -> bool:
        """保存用户档案

        Args:
            user_id: 用户 ID
            profile: 用户档案

        Returns:
            是否成功
        """
        try:
            user_file = self._get_user_file(user_id)

            # 读取现有数据
            user_data = {}
            if user_file.exists():
                with open(user_file, "r", encoding="utf-8") as f:
                    user_data = json.load(f)

            # 更新用户档案
            user_data["user_profile"] = profile
            user_data["profile_updated_at"] = datetime.now().isoformat()

            # 保存数据
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)

            logger.info(f"用户档案已保存: {user_file}")
            return True

        except Exception as e:
            logger.error(f"保存用户档案失败: {e}")
            return False

    def load_user_profile(self, user_id: str) -> dict | None:
        """加载用户档案

        Args:
            user_id: 用户 ID

        Returns:
            用户档案，不存在返回 None
        """
        try:
            user_file = self._get_user_file(user_id)

            if not user_file.exists():
                return None

            with open(user_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)

            return user_data.get("user_profile")

        except Exception as e:
            logger.error(f"加载用户档案失败: {e}")
            return None

    def delete_resume_profile(self, user_id: str) -> bool:
        """删除简历信息

        Args:
            user_id: 用户 ID

        Returns:
            是否成功
        """
        try:
            user_file = self._get_user_file(user_id)

            if not user_file.exists():
                return True

            # 读取现有数据
            with open(user_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)

            # 删除简历信息
            if "resume_profile" in user_data:
                del user_data["resume_profile"]
            if "resume_updated_at" in user_data:
                del user_data["resume_updated_at"]

            # 保存数据
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)

            logger.info(f"简历信息已删除: {user_file}")
            return True

        except Exception as e:
            logger.error(f"删除简历信息失败: {e}")
            return False


# 全局实例
user_data_manager = UserDataManager()
