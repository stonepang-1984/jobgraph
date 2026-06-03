"""用户管理模块

功能:
- 设备指纹生成
- 本地用户管理
- 用户状态管理
- 贡献权限控制
"""

import hashlib
import json
import os
import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger


class UserManager:
    """用户管理器"""

    def __init__(self):
        self.config_dir = Path.home() / ".jobgraph"
        self.device_file = self.config_dir / "device.json"
        self.user_file = self.config_dir / "user.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._device_id = None
        self._user_data = None

    @property
    def device_id(self) -> str:
        """获取设备指纹"""
        if self._device_id is None:
            self._device_id = self._load_or_generate_device_id()
        return self._device_id

    @property
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        user_data = self.get_user_data()
        return user_data.get("invite_code") is not None

    @property
    def user_level(self) -> int:
        """获取用户等级"""
        user_data = self.get_user_data()
        return user_data.get("level", 1)

    @property
    def user_points(self) -> int:
        """获取用户积分"""
        user_data = self.get_user_data()
        return user_data.get("points", 0)

    def _load_or_generate_device_id(self) -> str:
        """加载或生成设备指纹"""
        if self.device_file.exists():
            try:
                data = json.loads(self.device_file.read_text())
                return data["device_id"]
            except Exception:
                pass

        # 生成新设备指纹
        device_id = self._generate_device_id()

        # 保存
        device_data = {
            "device_id": device_id,
            "created_at": datetime.now().isoformat(),
            "platform": platform.system(),
            "machine": platform.machine(),
        }
        self.device_file.write_text(json.dumps(device_data, indent=2))

        logger.info(f"Generated device ID: {device_id[:8]}...")
        return device_id

    def _generate_device_id(self) -> str:
        """生成设备指纹"""
        info_parts = [
            platform.node(),
            platform.machine(),
            str(uuid.getnode()),
            os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
            str(os.getpid()),
        ]

        device_str = "|".join(info_parts)
        return hashlib.sha256(device_str.encode()).hexdigest()[:32]

    def get_user_data(self) -> dict:
        """获取用户数据"""
        if self._user_data is None:
            self._user_data = self._load_user_data()
        return self._user_data

    def _load_user_data(self) -> dict:
        """加载用户数据"""
        default_data = {
            "device_id": self.device_id,
            "nickname": "匿名用户",
            "invite_code": None,
            "level": 1,
            "points": 0,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "contributions": {
                "reviews": 0,
                "pitfalls": 0,
                "salaries": 0,
            },
        }

        if self.user_file.exists():
            try:
                data = json.loads(self.user_file.read_text())
                # 合并默认值
                for key, value in default_data.items():
                    if key not in data:
                        data[key] = value
                return data
            except Exception:
                pass

        return default_data

    def save_user_data(self) -> None:
        """保存用户数据"""
        self.user_file.write_text(json.dumps(self._user_data, indent=2))

    def update_last_active(self) -> None:
        """更新最后活跃时间"""
        user_data = self.get_user_data()
        user_data["last_active"] = datetime.now().isoformat()
        self.save_user_data()

    def set_nickname(self, nickname: str) -> None:
        """设置昵称"""
        user_data = self.get_user_data()
        user_data["nickname"] = nickname
        self.save_user_data()

    def login_with_invite_code(self, invite_code: str) -> bool:
        """使用邀请码登录"""
        # 验证邀请码格式
        if not self._verify_invite_code(invite_code):
            return False

        user_data = self.get_user_data()
        user_data["invite_code"] = invite_code
        user_data["level"] = max(user_data.get("level", 1), 2)  # 升级到至少2级
        self.save_user_data()

        logger.info(f"User logged in with invite code: {invite_code[:8]}...")
        return True

    def login_with_device_code(self, device_code: str) -> bool:
        """使用设备码登录"""
        # 验证设备码
        if device_code != self.device_id:
            return False

        user_data = self.get_user_data()
        user_data["logged_in"] = True
        self.save_user_data()

        logger.info("User logged in with device code")
        return True

    def logout(self) -> None:
        """登出"""
        user_data = self.get_user_data()
        user_data["invite_code"] = None
        user_data["logged_in"] = False
        self.save_user_data()

    def add_points(self, points: int, reason: str = "") -> int:
        """添加积分"""
        user_data = self.get_user_data()
        user_data["points"] = user_data.get("points", 0) + points

        # 检查升级
        self._check_level_up(user_data)

        self.save_user_data()
        logger.info(f"Added {points} points: {reason}")
        return user_data["points"]

    def add_contribution(self, contribution_type: str) -> None:
        """记录贡献"""
        user_data = self.get_user_data()
        contributions = user_data.get("contributions", {})
        contributions[contribution_type] = contributions.get(contribution_type, 0) + 1
        user_data["contributions"] = contributions

        # 添加积分
        points_map = {
            "reviews": 10,
            "pitfalls": 15,
            "salaries": 5,
            "jobs": 8,
        }
        self.add_points(points_map.get(contribution_type, 5), f"贡献{contribution_type}")

        self.save_user_data()

    def _check_level_up(self, user_data: dict) -> None:
        """检查是否升级"""
        points = user_data.get("points", 0)
        current_level = user_data.get("level", 1)

        # 升级规则
        level_thresholds = {
            1: 0,
            2: 50,
            3: 150,
            4: 300,
            5: 500,
            6: 1000,
        }

        for level, threshold in sorted(level_thresholds.items(), reverse=True):
            if points >= threshold and level > current_level:
                user_data["level"] = level
                logger.info(f"User leveled up to {level}!")
                break

    def _verify_invite_code(self, invite_code: str) -> bool:
        """验证邀请码"""
        # 简单验证：格式正确即可
        # 实际应用中应该查询服务器验证
        if len(invite_code) < 8:
            return False

        # 可以添加更多验证逻辑
        return True

    def get_user_stats(self) -> dict:
        """获取用户统计"""
        user_data = self.get_user_data()
        return {
            "device_id": self.device_id[:8] + "...",
            "nickname": user_data.get("nickname", "匿名用户"),
            "level": user_data.get("level", 1),
            "points": user_data.get("points", 0),
            "is_logged_in": self.is_logged_in,
            "contributions": user_data.get("contributions", {}),
            "created_at": user_data.get("created_at"),
            "last_active": user_data.get("last_active"),
        }

    def can_contribute(self) -> bool:
        """检查是否可以贡献数据"""
        # 所有用户都可以贡献
        return True

    def get_contribution_limit(self) -> dict:
        """获取贡献限制"""
        user_data = self.get_user_data()
        level = user_data.get("level", 1)

        # 不同等级的贡献限制
        limits = {
            1: {"reviews_per_day": 5, "pitfalls_per_day": 3},
            2: {"reviews_per_day": 10, "pitfalls_per_day": 5},
            3: {"reviews_per_day": 20, "pitfalls_per_day": 10},
            4: {"reviews_per_day": 50, "pitfalls_per_day": 20},
            5: {"reviews_per_day": 100, "pitfalls_per_day": 50},
        }

        return limits.get(level, limits[1])


# 全局实例
user_manager = UserManager()
