"""用户数据持久化模块

保存用户数据（简历信息等）到本地文件
实现跨会话数据持久化
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger


class UserDataManager:
    """用户数据管理器"""

    def __init__(self, data_dir: str = "./data/user"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 简历文件存储目录
        self.files_dir = self.data_dir / "files"
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_file(self, user_id: str) -> Path:
        """获取用户数据文件路径"""
        return self.data_dir / f"{user_id}.json"

    def _get_user_files_dir(self, user_id: str) -> Path:
        """获取用户简历文件目录"""
        user_files = self.files_dir / user_id
        user_files.mkdir(parents=True, exist_ok=True)
        return user_files

    def save_resume_file(self, user_id: str, file_data: bytes, filename: str) -> str | None:
        """保存原始简历文件

        Args:
            user_id: 用户 ID
            file_data: 文件数据
            filename: 原始文件名

        Returns:
            保存的文件路径，失败返回 None
        """
        try:
            user_files = self._get_user_files_dir(user_id)
            file_path = user_files / filename

            with open(file_path, "wb") as f:
                f.write(file_data)

            logger.info(f"简历文件已保存: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"保存简历文件失败: {e}")
            return None

    def load_resume_file(self, user_id: str, filename: str) -> bytes | None:
        """加载原始简历文件

        Args:
            user_id: 用户 ID
            filename: 文件名

        Returns:
            文件数据，不存在返回 None
        """
        try:
            user_files = self._get_user_files_dir(user_id)
            file_path = user_files / filename

            if not file_path.exists():
                return None

            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"加载简历文件失败: {e}")
            return None

    def get_resume_file_path(self, user_id: str, filename: str) -> Path | None:
        """获取简历文件路径

        Args:
            user_id: 用户 ID
            filename: 文件名

        Returns:
            文件路径，不存在返回 None
        """
        user_files = self._get_user_files_dir(user_id)
        file_path = user_files / filename
        return file_path if file_path.exists() else None

    def delete_resume_file(self, user_id: str, filename: str) -> bool:
        """删除简历文件

        Args:
            user_id: 用户 ID
            filename: 文件名

        Returns:
            是否成功
        """
        try:
            user_files = self._get_user_files_dir(user_id)
            file_path = user_files / filename

            if file_path.exists():
                file_path.unlink()
                logger.info(f"简历文件已删除: {file_path}")
            return True
        except Exception as e:
            logger.error(f"删除简历文件失败: {e}")
            return False

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
                with open(user_file, encoding="utf-8") as f:
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

            with open(user_file, encoding="utf-8") as f:
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
                with open(user_file, encoding="utf-8") as f:
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

            with open(user_file, encoding="utf-8") as f:
                user_data = json.load(f)

            return user_data.get("user_profile")

        except Exception as e:
            logger.error(f"加载用户档案失败: {e}")
            return None

    def delete_resume_profile(self, user_id: str) -> bool:
        """删除简历信息和文件

        Args:
            user_id: 用户 ID

        Returns:
            是否成功
        """
        try:
            user_file = self._get_user_file(user_id)

            # 删除简历文件
            user_files = self._get_user_files_dir(user_id)
            if user_files.exists():
                shutil.rmtree(user_files)
                logger.info(f"简历文件目录已删除: {user_files}")

            if not user_file.exists():
                return True

            # 读取现有数据
            with open(user_file, encoding="utf-8") as f:
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
