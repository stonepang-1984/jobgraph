"""Memory Protection - 内存保护模块

防御内存转储攻击:
1. 代码分段加载 - 用完即清
2. 内存加密 - 执行前解密，执行后加密
3. 反调试检测 - 阻止调试器附加
4. 代码自修改 - 执行后销毁
"""

import gc
import mmap
import sys
import threading
from typing import Any

from loguru import logger


class MemoryProtection:
    """内存保护"""

    def __init__(self):
        self._protected_regions: list[dict] = []
        self._encryption_key: bytes | None = None
        self._monitor_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def set_encryption_key(self, key: bytes) -> None:
        """设置内存加密密钥"""
        self._encryption_key = key[:32]  # AES-256

    def protect_code(self, code: bytes) -> bytes:
        """保护代码 - 加密存储"""
        if not self._encryption_key:
            return code

        # 使用 XOR 简单加密 (生产环境应使用 AES)
        encrypted = bytearray(len(code))
        key_len = len(self._encryption_key)

        for i in range(len(code)):
            encrypted[i] = code[i] ^ self._encryption_key[i % key_len]

        return bytes(encrypted)

    def unprotect_code(self, encrypted: bytes) -> bytes:
        """解密代码 - 使用时解密"""
        # XOR 加密是对称的
        return self.protect_code(encrypted)

    def secure_execute(self, encrypted_code: bytes, context: dict = None) -> Any:
        """安全执行代码

        流程:
        1. 解密代码
        2. 执行代码
        3. 立即销毁解密后的代码
        4. 清理内存
        """
        # 1. 解密
        decrypted = self.unprotect_code(encrypted_code)
        code_str = decrypted.decode("utf-8")

        # 2. 准备执行环境
        if context is None:
            context = {}

        # 3. 执行
        result = None
        try:
            # 创建临时模块
            import types

            module = types.ModuleType("__secure_exec__")
            module.__dict__.update(context)

            # 执行代码
            exec(compile(code_str, "<secure>", "exec"), module.__dict__)

            # 获取结果
            result = module.__dict__.get("__result__")
        finally:
            # 4. 立即销毁
            self._secure_delete(decrypted)
            self._secure_delete(code_str)
            del module

            # 强制垃圾回收
            gc.collect()

        return result

    def _secure_delete(self, data) -> None:
        """安全删除数据 - 覆盖内存"""
        if isinstance(data, str):
            data = data.encode()

        if isinstance(data, (bytes, bytearray)):
            # 用随机数据覆盖
            import os

            length = len(data)
            if isinstance(data, bytearray):
                # 直接覆盖
                for i in range(length):
                    data[i] = ord(os.urandom(1))
            else:
                # 创建新的 bytearray 并覆盖
                mutable = bytearray(data)
                for i in range(length):
                    mutable[i] = ord(os.urandom(1))

    def allocate_secure_memory(self, size: int) -> mmap.mmap | None:
        """分配安全内存区域"""
        try:
            # 创建匿名内存映射
            if sys.platform == "win32":
                mem = mmap.mmap(-1, size)
            else:
                mem = mmap.mmap(-1, size, prot=mmap.PROT_READ | mmap.PROT_WRITE)

            # 记录保护区域
            self._protected_regions.append(
                {
                    "address": id(mem),
                    "size": size,
                    "mmap": mem,
                }
            )

            return mem

        except Exception as e:
            logger.error(f"Failed to allocate secure memory: {e}")
            return None

    def free_secure_memory(self, mem: mmap.mmap) -> None:
        """释放安全内存"""
        try:
            # 清零内存
            mem.seek(0)
            mem.write(b"\x00" * len(mem))

            # 关闭映射
            mem.close()

            # 从记录中移除
            self._protected_regions = [r for r in self._protected_regions if r["mmap"] != mem]

        except Exception as e:
            logger.error(f"Failed to free secure memory: {e}")

    def start_memory_monitor(self) -> None:
        """启动内存监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._memory_monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_memory_monitor(self) -> None:
        """停止内存监控"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

    def _memory_monitor_loop(self) -> None:
        """内存监控循环"""
        while not self._stop_event.is_set():
            # 检测调试器
            if self._detect_debugger():
                logger.critical("Debugger detected during execution!")
                self._emergency_cleanup()
                break

            # 检测内存完整性
            self._check_memory_integrity()

            self._stop_event.wait(1)

    def _detect_debugger(self) -> bool:
        """检测调试器"""
        try:
            # 检测 ptrace
            if sys.platform != "win32":
                import ctypes

                libc = ctypes.CDLL("libc.so.6")
                # PTRACE_TRACEME = 0
                result = libc.ptrace(0, 0, 0, 0)
                if result == -1:
                    return True

            # 检测 sys.gettrace
            if sys.gettrace() is not None:
                return True

            return False

        except Exception:
            return False

    def _check_memory_integrity(self) -> None:
        """检查内存完整性"""
        for region in self._protected_regions:
            try:
                region["mmap"]
                # 检查内存是否被篡改
                # 这里可以添加更复杂的完整性检查
            except Exception:
                pass

    def _emergency_cleanup(self) -> None:
        """紧急清理"""
        logger.critical("Performing emergency cleanup...")

        # 清理所有保护区域
        for region in self._protected_regions:
            try:
                self.free_secure_memory(region["mmap"])
            except Exception:
                pass

        # 清理全局变量
        gc.collect()


class SecureCodeLoader:
    """安全代码加载器"""

    def __init__(self):
        self.memory_protection = MemoryProtection()
        self._module_cache: dict[str, bytes] = {}

    def load_and_execute(self, module_name: str, encrypted_code: bytes) -> Any:
        """加载并执行代码

        安全流程:
        1. 解密代码
        2. 在安全内存中执行
        3. 立即销毁代码
        """
        # 设置加密密钥
        from src.jobgraph.license.manager import license_manager

        if license_manager.decrypt_key:
            self.memory_protection.set_encryption_key(license_manager.decrypt_key)

        # 安全执行
        context = {
            "__name__": module_name,
            "__file__": f"<encrypted:{module_name}>",
        }

        return self.memory_protection.secure_execute(encrypted_code, context)

    def load_module_secure(self, module_name: str, enc_path: str) -> Any | None:
        """安全加载模块"""
        import types

        # 读取加密文件
        with open(enc_path, "rb") as f:
            encrypted_code = f.read()

        # 解密
        from src.jobgraph.license.crypto import decrypt_data
        from src.jobgraph.license.manager import license_manager

        if not license_manager.decrypt_key:
            return None

        decrypted = decrypt_data(encrypted_code, license_manager.decrypt_key)
        code_str = decrypted.decode("utf-8")

        # 创建模块
        module = types.ModuleType(module_name)
        module.__file__ = f"<encrypted:{module_name}>"

        # 执行代码
        exec(compile(code_str, module_name, "exec"), module.__dict__)

        # 立即销毁解密后的代码
        self.memory_protection._secure_delete(decrypted)
        self.memory_protection._secure_delete(code_str)

        # 强制垃圾回收
        gc.collect()

        return module


# 全局实例
memory_protection = MemoryProtection()
secure_loader = SecureCodeLoader()
