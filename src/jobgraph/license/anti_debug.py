"""Anti-Debug - 反调试检测模块

功能:
1. 检测调试器
2. 检测代码注入
3. 检测内存修改
4. 自毁机制
"""

import os
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

from loguru import logger


class AntiDebug:
    """反调试检测"""

    def __init__(self):
        self.is_debugged = False
        self.check_interval = 5  # 秒
        self._stop_event = threading.Event()
        self._monitor_thread = None

    def start_monitoring(self) -> None:
        """启动监控线程"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.debug("Anti-debug monitoring started")

    def stop_monitoring(self) -> None:
        """停止监控线程"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        logger.debug("Anti-debug monitoring stopped")

    def _monitor_loop(self) -> None:
        """监控循环"""
        while not self._stop_event.is_set():
            if self.detect_debugger():
                self.is_debugged = True
                self.on_debug_detected()
                break

            if self.detect_code_injection():
                self.is_debugged = True
                self.on_debug_detected()
                break

            self._stop_event.wait(self.check_interval)

    def detect_debugger(self) -> bool:
        """检测调试器"""
        try:
            # 方法1: 检测 sys.gettrace
            if sys.gettrace() is not None:
                logger.warning("Debugger detected: sys.gettrace")
                return True

            # 方法2: 检测 sys.getprofile
            if sys.getprofile() is not None:
                logger.warning("Debugger detected: sys.getprofile")
                return True

            # 方法3: 检测常见调试器进程
            if self._check_debugger_processes():
                return True

            # 方法4: 检测环境变量
            if self._check_debug_env():
                return True

            # 方法5: 时间检测 (调试时执行会变慢)
            if self._timing_check():
                return True

            return False

        except Exception as e:
            logger.error(f"Debug detection error: {e}")
            return False

    def _check_debugger_processes(self) -> bool:
        """检测调试器进程"""
        debugger_processes = [
            "gdb",
            "lldb",
            "windbg",
            "x64dbg",
            "ollydbg",
            "ida",
            "ida64",
            "idaq",
            "idaq64",
            "radare2",
            "r2",
            "ghidra",
            "pycharm",
            "debugpy",
        ]

        try:
            import psutil

            for proc in psutil.process_iter(["name"]):
                proc_name = proc.info["name"].lower()
                if any(dbg in proc_name for dbg in debugger_processes):
                    logger.warning(f"Debugger process detected: {proc_name}")
                    return True
        except ImportError:
            pass

        return False

    def _check_debug_env(self) -> bool:
        """检测调试环境变量"""
        debug_vars = [
            "PYDEVD_USE_FRAME_EVAL",
            "PYCHARM_DEBUG",
            "PYTHONDEBUG",
            "DEBUG",
            "REMOTE_DEBUG",
        ]

        for var in debug_vars:
            if os.environ.get(var):
                logger.warning(f"Debug env var detected: {var}")
                return True

        return False

    def _timing_check(self) -> bool:
        """时间检测"""
        # 正常执行应该很快，调试时会变慢
        start = time.perf_counter()

        # 执行一些计算
        result = 0
        for i in range(10000):
            result += i * i

        elapsed = time.perf_counter() - start

        # 如果执行时间超过阈值，可能是调试
        if elapsed > 0.1:  # 100ms
            logger.warning(f"Timing anomaly detected: {elapsed:.3f}s")
            return True

        return False

    def detect_code_injection(self) -> bool:
        """检测代码注入"""
        try:
            # 检测模块是否被修改
            for module_name, module in sys.modules.items():
                if module_name.startswith("jobgraph"):
                    if hasattr(module, "__file__") and module.__file__:
                        # 检查文件是否被修改
                        if self._check_file_modified(module.__file__):
                            return True

            return False

        except Exception:
            return False

    def _check_file_modified(self, file_path: str) -> bool:
        """检查文件是否被修改"""
        # 这里可以实现文件完整性检查
        return False

    def on_debug_detected(self) -> None:
        """检测到调试时的处理"""
        logger.critical("Debug detected! Security violation!")

        # 可选: 自毁或退出
        # self._self_destruct()
        # sys.exit(1)

    def _self_destruct(self) -> None:
        """自毁机制"""
        logger.critical("Self-destructing...")

        # 删除关键文件
        try:
            import shutil

            target_dirs = [
                Path.home() / ".jobgraph",
                Path(__file__).parent.parent / "pro",
            ]

            for dir_path in target_dirs:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    logger.info(f"Deleted: {dir_path}")

        except Exception as e:
            logger.error(f"Self-destruct failed: {e}")

    def is_compromised(self) -> bool:
        """检查是否被攻破"""
        return self.is_debugged


def anti_debug_decorator(func: Callable) -> Callable:
    """反调试装饰器"""

    def wrapper(*args, **kwargs):
        checker = AntiDebug()
        if checker.detect_debugger():
            raise SecurityError("Debug environment detected")
        return func(*args, **kwargs)

    return wrapper


class SecurityError(Exception):
    """安全错误"""

    pass


# 全局实例
anti_debug = AntiDebug()
