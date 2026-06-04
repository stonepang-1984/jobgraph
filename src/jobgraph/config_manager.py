"""配置管理模块

支持通过 Web 界面配置 LLM 等设置
"""

from pathlib import Path
from loguru import logger


class ConfigManager:
    """配置管理器"""

    def __init__(self, env_path: str = ".env"):
        self.env_path = Path(env_path)

    def read_env(self) -> dict:
        """读取 .env 文件"""
        config = {}
        if not self.env_path.exists():
            return config

        with open(self.env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()

        return config

    def update_env(self, updates: dict) -> bool:
        """更新 .env 文件

        Args:
            updates: 要更新的键值对

        Returns:
            是否成功
        """
        try:
            # 读取现有配置
            lines = []
            if self.env_path.exists():
                with open(self.env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

            # 更新配置
            updated_keys = set()
            new_lines = []

            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = stripped.split("=", 1)[0].strip()
                    if key in updates:
                        new_lines.append(f"{key}={updates[key]}\n")
                        updated_keys.add(key)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            # 添加新增的配置
            for key, value in updates.items():
                if key not in updated_keys:
                    new_lines.append(f"{key}={value}\n")

            # 写入文件
            with open(self.env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            logger.info(f"配置已更新: {list(updates.keys())}")
            return True

        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False

    def get_llm_config(self) -> dict:
        """获取 LLM 配置"""
        config = self.read_env()
        return {
            "openai_api_key": config.get("OPENAI_API_KEY", ""),
            "openai_api_base": config.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
            "openai_model": config.get("OPENAI_MODEL", "gpt-4o"),
            "ollama_base_url": config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            "ollama_model": config.get("OLLAMA_MODEL", "qwen2.5:14b"),
        }

    def save_llm_config(
        self,
        provider: str = "openai",
        openai_api_key: str = "",
        openai_api_base: str = "",
        openai_model: str = "",
        ollama_base_url: str = "",
        ollama_model: str = "",
    ) -> bool:
        """保存 LLM 配置

        Args:
            provider: 提供商 (openai/ollama)
            openai_api_key: OpenAI API Key
            openai_api_base: OpenAI API Base URL
            openai_model: OpenAI 模型名称
            ollama_base_url: Ollama 服务地址
            ollama_model: Ollama 模型名称

        Returns:
            是否成功
        """
        updates = {}

        if provider == "openai":
            if openai_api_key:
                updates["OPENAI_API_KEY"] = openai_api_key
            if openai_api_base:
                updates["OPENAI_API_BASE"] = openai_api_base
            if openai_model:
                updates["OPENAI_MODEL"] = openai_model
        elif provider == "ollama":
            if ollama_base_url:
                updates["OLLAMA_BASE_URL"] = ollama_base_url
            if ollama_model:
                updates["OLLAMA_MODEL"] = ollama_model

        return self.update_env(updates)

    def is_llm_configured(self) -> bool:
        """检查 LLM 是否已配置"""
        config = self.get_llm_config()
        api_key = config.get("openai_api_key", "")
        return bool(api_key and api_key != "sk-your-openai-api-key" and len(api_key) > 10)


# 全局实例
config_manager = ConfigManager()
