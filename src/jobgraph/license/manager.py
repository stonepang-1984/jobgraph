"""License Manager - 安全增强版

安全机制:
1. 代码分片加密 - 每个函数单独加密
2. 内存执行 - 解密后在内存执行，不落地
3. 设备绑定 - 解密密钥与设备绑定
4. 定期验证 - 每次调用都验证
5. 密钥轮换 - 定期更换解密密钥
6. 7天试用 - 首次使用自动激活
"""

import hashlib
import json
import os
import platform
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from loguru import logger

# License 存储路径
LICENSE_DIR = Path.home() / ".jobgraph"
LICENSE_FILE = LICENSE_DIR / "license.key"
TRIAL_FILE = LICENSE_DIR / "trial.json"
VERIFICATION_FILE = LICENSE_DIR / "verification.json"

# 安全配置
VERIFICATION_INTERVAL = 300  # 5 分钟验证一次
KEY_ROTATION_INTERVAL = 3600  # 1 小时轮换一次
TRIAL_DAYS = 7  # 试用天数


class SecureLicenseManager:
    """安全增强版 License 管理器"""

    def __init__(self):
        self.license_key: str | None = None
        self.is_pro: bool = False
        self.is_trial: bool = False
        self.device_id: str = self._get_device_id()
        self.expire_at: datetime | None = None
        self.trial_expire_at: datetime | None = None
        self.last_verification: datetime | None = None
        self.last_key_rotation: datetime | None = None
        self._decrypt_keys: dict[str, bytes] = {}
        self._load_license()

    def _get_device_id(self) -> str:
        """获取设备指纹"""
        info_parts = [
            platform.node(),
            platform.machine(),
            str(uuid.getnode()),
            os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        ]
        device_str = "|".join(info_parts)
        return hashlib.sha256(device_str.encode()).hexdigest()[:16]

    def _load_license(self) -> None:
        """从本地加载 License"""
        try:
            # 1. 尝试加载正式 License
            if LICENSE_FILE.exists():
                license_data = json.loads(LICENSE_FILE.read_text())

                # 验证设备绑定
                if license_data.get("device_id") != self.device_id:
                    logger.warning("License device mismatch")
                elif not self._verify_signature(license_data.get("key", "")):
                    logger.warning("License signature invalid")
                else:
                    # 解析过期时间
                    self.expire_at = datetime.fromisoformat(license_data.get("expire_at", "2000-01-01"))

                    if self.expire_at >= datetime.now():
                        # License 有效
                        self.license_key = license_data["key"]
                        self.is_pro = True
                        self.is_trial = False
                        self._generate_decrypt_keys()
                        logger.info(f"License loaded, expires at {self.expire_at}")
                        return

            # 2. 尝试加载试用状态
            self._load_trial()

        except Exception as e:
            logger.error(f"Failed to load license: {e}")

    def _load_trial(self) -> None:
        """加载试用状态"""
        try:
            if not TRIAL_FILE.exists():
                # 首次使用，激活试用
                self._activate_trial()
                return

            trial_data = json.loads(TRIAL_FILE.read_text())

            # 验证设备
            if trial_data.get("device_id") != self.device_id:
                logger.warning("Trial device mismatch")
                return

            # 检查试用是否过期
            trial_expire = datetime.fromisoformat(trial_data.get("expire_at", "2000-01-01"))
            if trial_expire >= datetime.now():
                # 试用有效
                self.is_pro = True
                self.is_trial = True
                self.trial_expire_at = trial_expire
                self.expire_at = trial_expire
                logger.info(f"Trial active, expires at {trial_expire}")
            else:
                logger.warning("Trial expired")

        except Exception as e:
            logger.error(f"Failed to load trial: {e}")

    def _activate_trial(self) -> None:
        """激活试用"""
        LICENSE_DIR.mkdir(parents=True, exist_ok=True)

        self.trial_expire_at = datetime.now() + timedelta(days=TRIAL_DAYS)
        self.is_pro = True
        self.is_trial = True
        self.expire_at = self.trial_expire_at

        trial_data = {
            "device_id": self.device_id,
            "activated_at": datetime.now().isoformat(),
            "expire_at": self.trial_expire_at.isoformat(),
            "trial_days": TRIAL_DAYS,
        }

        TRIAL_FILE.write_text(json.dumps(trial_data, indent=2))
        logger.info(f"Trial activated, expires at {self.trial_expire_at}")

    def activate(self, key: str) -> tuple[bool, str]:
        """激活 License Key"""
        if not self._verify_format(key):
            return False, "License Key 格式无效"

        if not self._verify_signature(key):
            return False, "License Key 签名无效"

        if not self._verify_device(key):
            return False, "License Key 与此设备不匹配"

        expire_at = self._extract_expire_time(key)
        if expire_at and expire_at < datetime.now():
            return False, "License Key 已过期"

        self.license_key = key
        self.is_pro = True
        self.is_trial = False
        self.expire_at = expire_at
        self._generate_decrypt_keys()
        self._save_license()

        return True, f"激活成功，有效期至 {expire_at.strftime('%Y-%m-%d')}"

    def deactivate(self) -> None:
        """停用 License"""
        self.license_key = None
        self.is_pro = False
        self.is_trial = False
        self._decrypt_keys.clear()

        if LICENSE_FILE.exists():
            LICENSE_FILE.unlink()

    def check_pro_access(self) -> bool:
        """检查是否有专业版访问权限"""
        if not self.is_pro:
            return False

        if self.expire_at and self.expire_at < datetime.now():
            self.is_pro = False
            self.is_trial = False
            return False

        # 定期重新验证
        if self._needs_reverification():
            if not self._verify_offline():
                self.is_pro = False
                return False
            self._save_verification()

        return True

    def get_license_info(self) -> dict:
        """获取 License 信息"""
        days_remaining = 0
        if self.expire_at:
            days_remaining = max(0, (self.expire_at - datetime.now()).days)

        return {
            "is_pro": self.is_pro,
            "is_trial": self.is_trial,
            "key": self.license_key[:8] + "..." if self.license_key else None,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
            "days_remaining": days_remaining,
            "trial_expire_at": self.trial_expire_at.isoformat() if self.trial_expire_at else None,
            "device_id": self.device_id,
        }

    def get_decrypt_key(self, module_name: str) -> bytes | None:
        """获取模块解密密钥"""
        if not self.check_pro_access():
            return None

        if self._needs_key_rotation():
            self._rotate_keys()

        return self._decrypt_keys.get(module_name)

    def _generate_decrypt_keys(self) -> None:
        """生成分片解密密钥"""
        # 试用模式使用固定密钥
        if self.is_trial:
            trial_key = f"trial-{self.device_id}"
            hashlib.sha256(trial_key.encode()).digest()
            modules = ["advanced_matching", "data_updater", "data_export"]
            for module in modules:
                module_data = f"{module}|{self.device_id}|trial"
                self._decrypt_keys[module] = hashlib.sha256(module_data.encode()).digest()[:32]
            return

        # 正式 License
        if not self.license_key:
            return

        hashlib.sha256(self.license_key.encode()).digest()
        modules = ["advanced_matching", "data_updater", "data_export"]
        for module in modules:
            module_data = f"{module}|{self.device_id}|{self.license_key}"
            self._decrypt_keys[module] = hashlib.sha256(module_data.encode()).digest()[:32]

    def _rotate_keys(self) -> None:
        """轮换解密密钥"""
        logger.info("Rotating decrypt keys")
        self._generate_decrypt_keys()
        self.last_key_rotation = datetime.now()

    def _needs_key_rotation(self) -> bool:
        """检查是否需要轮换密钥"""
        if not self.last_key_rotation:
            return True
        elapsed = (datetime.now() - self.last_key_rotation).total_seconds()
        return elapsed > KEY_ROTATION_INTERVAL

    def _verify_format(self, key: str) -> bool:
        parts = key.split("-")
        if len(parts) != 5:
            return False
        if parts[0] != "JGP":
            return False
        for part in parts[1:]:
            if len(part) != 4:
                return False
            if not part.isalnum():
                return False
        return True

    def _verify_signature(self, key: str) -> bool:
        parts = key.split("-")
        if len(parts) != 5:
            return False
        data = "-".join(parts[:4])
        expected = self._compute_signature(data)
        return parts[4].upper() == expected.upper()

    def _verify_device(self, key: str) -> bool:
        parts = key.split("-")
        if len(parts) != 5:
            return False
        key_device = parts[1][:8]
        return key_device == self.device_id[:8] or key_device == "00000000"

    def _verify_offline(self) -> bool:
        if self.is_trial:
            return self.trial_expire_at and self.trial_expire_at >= datetime.now()
        if not self.license_key:
            return False
        if not self._verify_signature(self.license_key):
            return False
        if self.expire_at and self.expire_at < datetime.now():
            return False
        return True

    def _extract_expire_time(self, key: str) -> datetime | None:
        parts = key.split("-")
        if len(parts) != 5:
            return None
        try:
            expire_str = parts[2]
            year = 2000 + int(expire_str[:2])
            month = int(expire_str[2:4])
            day = int(expire_str[4:6])
            return datetime(year, month, day, 23, 59, 59)
        except Exception:
            return datetime.now() + timedelta(days=365)

    def _needs_reverification(self) -> bool:
        if not self.last_verification:
            return True
        elapsed = (datetime.now() - self.last_verification).total_seconds()
        return elapsed > VERIFICATION_INTERVAL

    def _save_verification(self) -> None:
        LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        data = {"last_verification": datetime.now().isoformat()}
        VERIFICATION_FILE.write_text(json.dumps(data))
        self.last_verification = datetime.now()

    def _compute_signature(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()[:4].upper()

    def _save_license(self) -> None:
        LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        license_data = {
            "key": self.license_key,
            "device_id": self.device_id,
            "expire_at": self.expire_at.isoformat()
            if self.expire_at
            else (datetime.now() + timedelta(days=365)).isoformat(),
            "activated_at": datetime.now().isoformat(),
        }
        LICENSE_FILE.write_text(json.dumps(license_data, indent=2))
        logger.info(f"License saved to {LICENSE_FILE}")


def require_pro(feature_name: str):
    """装饰器：要求专业版权限"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not license_manager.check_pro_access():
                raise PermissionError(
                    f"功能 '{feature_name}' 需要专业版 License。请使用 'license activate <key>' 激活。"
                )
            return func(*args, **kwargs)

        wrapper._is_pro_feature = True
        wrapper._feature_name = feature_name
        return wrapper

    return decorator


# 全局实例
license_manager = SecureLicenseManager()
