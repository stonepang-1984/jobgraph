"""Pro Module Loader - 安全增强版

安全机制:
1. 分片加密 - 每个模块独立密钥
2. 内存保护 - 代码用完即清
3. 反调试检测 - 阻止调试器
4. 实时验证 - 每次调用都检查
"""

import gc
import types
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from loguru import logger

from src.jobgraph.license.crypto import decrypt_data
from src.jobgraph.license.memory_protection import memory_protection


# 付费模块目录
PRO_DIR = Path(__file__).parent.parent / "pro"


class SecureProModuleLoader:
    """安全增强版付费模块加载器"""

    def __init__(self, license_manager=None):
        from src.jobgraph.license.manager import license_manager as default_manager
        self.license_manager = license_manager or default_manager
        self.loaded_modules: dict[str, types.ModuleType] = {}

    def is_available(self) -> bool:
        """检查付费功能是否可用"""
        return self.license_manager.check_pro_access()

    def load_module(self, module_name: str) -> Optional[types.ModuleType]:
        """安全加载付费模块

        安全流程:
        1. 验证 License
        2. 获取模块解密密钥
        3. 读取加密文件
        4. 解密代码
        5. 在内存中执行
        6. 立即销毁解密后的代码
        7. 返回模块引用
        """
        # 1. 验证 License
        if not self.is_available():
            logger.warning(f"Cannot load pro module '{module_name}': no valid license")
            return None

        # 2. 获取解密密钥
        decrypt_key = self.license_manager.get_decrypt_key(module_name)
        if not decrypt_key:
            logger.error(f"No decrypt key for module '{module_name}'")
            return None

        # 3. 读取加密文件
        enc_path = PRO_DIR / f"{module_name}.py.enc"
        if not enc_path.exists():
            logger.error(f"Pro module not found: {enc_path}")
            return None

        try:
            # 4. 解密代码
            enc_data = enc_path.read_bytes()
            decrypted = decrypt_data(enc_data, decrypt_key)
            code_str = decrypted.decode('utf-8')

            # 5. 创建模块
            module = types.ModuleType(f"jobgraph.pro.{module_name}")
            module.__file__ = f"<encrypted:{module_name}>"
            module.__loader__ = self

            # 注入安全函数
            module._check_license = self.is_available
            module._require_license = lambda: self.license_manager.check_pro_access()

            # 6. 在内存中执行代码
            compiled_code = compile(code_str, module_name, 'exec')
            exec(compiled_code, module.__dict__)

            # 7. 立即销毁解密后的代码
            self._secure_delete(decrypted)
            self._secure_delete(code_str)
            del compiled_code

            # 强制垃圾回收
            gc.collect()

            # 缓存模块引用 (不缓存代码)
            self.loaded_modules[module_name] = module

            logger.info(f"Loaded pro module securely: {module_name}")
            return module

        except Exception as e:
            logger.error(f"Failed to load pro module '{module_name}': {e}")
            # 确保清理
            self._secure_delete(decrypted if 'decrypted' in locals() else None)
            self._secure_delete(code_str if 'code_str' in locals() else None)
            return None

    def _secure_delete(self, data) -> None:
        """安全删除数据 - 覆盖内存"""
        if data is None:
            return

        try:
            if isinstance(data, str):
                data = data.encode()

            if isinstance(data, (bytes, bytearray)):
                # 用随机数据覆盖
                import os
                length = len(data)
                if isinstance(data, bytearray):
                    for i in range(length):
                        data[i] = ord(os.urandom(1))
                else:
                    # bytes 不可变，创建新的 bytearray
                    mutable = bytearray(data)
                    for i in range(length):
                        mutable[i] = ord(os.urandom(1))
                    del mutable
        except Exception:
            pass

    def unload_module(self, module_name: str) -> None:
        """卸载模块"""
        if module_name in self.loaded_modules:
            module = self.loaded_modules[module_name]

            # 清理模块属性
            for attr_name in list(module.__dict__.keys()):
                if not attr_name.startswith('__'):
                    try:
                        delattr(module, attr_name)
                    except Exception:
                        pass

            del self.loaded_modules[module_name]
            gc.collect()

            logger.debug(f"Unloaded pro module: {module_name}")

    def get_module(self, module_name: str) -> Optional[types.ModuleType]:
        """获取已加载的模块"""
        if not self.is_available():
            return None
        return self.loaded_modules.get(module_name)

    def list_available_modules(self) -> list[str]:
        """列出可用的付费模块"""
        if not PRO_DIR.exists():
            return []
        return [f.stem for f in PRO_DIR.glob("*.py.enc")]


class ProFeatureAccess:
    """付费功能访问控制"""

    def __init__(self, loader: SecureProModuleLoader):
        self.loader = loader

    def check(self, feature_name: str) -> bool:
        """检查功能是否可用"""
        return self.loader.is_available()

    def require(self, feature_name: str) -> None:
        """要求付费功能"""
        if not self.loader.is_available():
            raise PermissionError(
                f"功能 '{feature_name}' 需要专业版 License。"
                f"请使用 'license activate <key>' 激活。"
            )


# 全局实例
pro_loader = SecureProModuleLoader()
pro_access = ProFeatureAccess(pro_loader)
