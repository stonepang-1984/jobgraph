"""隐私信息过滤器

自动识别并移除简历中的隐私信息：
- 手机号码
- 邮箱地址
- 身份证号
- 银行卡号
- 姓名（可选）
"""

import re

from loguru import logger


class PrivacyFilter:
    """隐私信息过滤器"""

    # 隐私信息匹配模式
    PATTERNS = {
        # 手机号码（中国大陆）
        "phone": [
            r"1[3-9]\d{9}",  # 11位手机号
            r"(?:\+86|86)?[-\s]?1[3-9]\d{9}",  # 带国际区号
            r"(?:电话|手机|联系方式|Phone|Tel)[：:]\s*\d{7,11}",  # 标签后跟数字
        ],
        # 邮箱地址
        "email": [
            r"[\w.+-]+@[\w-]+\.[\w.]+",
            r"(?:邮箱|邮件|Email|E-mail)[：:]\s*[\w.+-]+@[\w-]+\.[\w.]+",
        ],
        # 身份证号
        "id_card": [
            r"\d{17}[\dXx]",  # 18位身份证
            r"\d{15}",  # 15位身份证（旧版）
            r"(?:身份证|ID)[：:]\s*[\dXx]{15,18}",
        ],
        # 银行卡号
        "bank_card": [
            r"\d{16,19}",  # 16-19位银行卡号
            r"(?:银行卡|卡号|Bank Card)[：:]\s*\d{16,19}",
        ],
        # 地址（较复杂，使用宽松匹配）
        "address": [
            r"(?:地址|住址|Address)[：:]\s*.{10,50}(?:路|街|巷|号|楼|室|村|镇|区|市|省)",
        ],
    }

    # 常见姓名（2-4个中文字符，在简历开头）
    NAME_PATTERNS = [
        r"^[\u4e00-\u9fa5]{2,4}$",  # 单独一行的中文名
        r"(?:姓名|名字|Name)[：:]\s*[\u4e00-\u9fa5]{2,4}",  # 标签后的姓名
    ]

    # 替换标记
    REPLACEMENTS = {
        "phone": "***手机号***",
        "email": "***邮箱***",
        "id_card": "***身份证***",
        "bank_card": "***银行卡***",
        "address": "***地址***",
        "name": "***姓名***",
    }

    def __init__(self, filter_name: bool = False):
        """
        Args:
            filter_name: 是否过滤姓名（默认不过滤，因为姓名有时是必要的）
        """
        self.filter_name = filter_name

    def filter(self, text: str) -> str:
        """过滤文本中的隐私信息

        Args:
            text: 原始文本

        Returns:
            过滤后的文本
        """
        if not text:
            return text

        filtered = text
        filtered_count = 0

        # 过滤各类隐私信息
        for privacy_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, filtered))
                if matches:
                    replacement = self.REPLACEMENTS[privacy_type]
                    # 从后往前替换，避免位置偏移
                    for match in reversed(matches):
                        filtered = filtered[: match.start()] + replacement + filtered[match.end() :]
                        filtered_count += 1

        # 可选：过滤姓名
        if self.filter_name:
            for pattern in self.NAME_PATTERNS:
                matches = list(re.finditer(pattern, filtered, re.MULTILINE))
                if matches:
                    replacement = self.REPLACEMENTS["name"]
                    for match in reversed(matches):
                        filtered = filtered[: match.start()] + replacement + filtered[match.end() :]
                        filtered_count += 1

        if filtered_count > 0:
            logger.info(f"已过滤 {filtered_count} 处隐私信息")

        return filtered

    def filter_structured(self, data: dict) -> dict:
        """从结构化数据中移除隐私字段

        Args:
            data: 包含用户信息的字典

        Returns:
            移除隐私字段后的字典
        """
        # 需要移除的隐私字段
        privacy_fields = [
            "name",
            "phone",
            "mobile",
            "email",
            "id_card",
            "identity",
            "bank_card",
            "address",
            "home_address",
            "contact",
        ]

        filtered_data = data.copy()
        removed_fields = []

        for field in privacy_fields:
            if field in filtered_data:
                del filtered_data[field]
                removed_fields.append(field)

        # 检查嵌套字段
        for key, value in filtered_data.items():
            if isinstance(value, dict):
                filtered_data[key] = self.filter_structured(value)
            elif isinstance(value, str):
                # 检查字符串值中是否包含隐私信息
                filtered_data[key] = self.filter(value)

        if removed_fields:
            logger.info(f"已移除隐私字段: {', '.join(removed_fields)}")

        return filtered_data

    def scan(self, text: str) -> dict:
        """扫描文本中的隐私信息（不修改原文）

        Args:
            text: 要扫描的文本

        Returns:
            包含各类隐私信息数量的字典
        """
        scan_result = {}

        for privacy_type, patterns in self.PATTERNS.items():
            count = 0
            for pattern in patterns:
                matches = re.findall(pattern, text)
                count += len(matches)
            if count > 0:
                scan_result[privacy_type] = count

        # 扫描姓名
        if self.filter_name:
            name_count = 0
            for pattern in self.NAME_PATTERNS:
                matches = re.findall(pattern, text, re.MULTILINE)
                name_count += len(matches)
            if name_count > 0:
                scan_result["name"] = name_count

        return scan_result

    def has_privacy_info(self, text: str) -> bool:
        """检查文本是否包含隐私信息

        Args:
            text: 要检查的文本

        Returns:
            是否包含隐私信息
        """
        scan_result = self.scan(text)
        return len(scan_result) > 0


# 全局实例（默认不过滤姓名）
privacy_filter = PrivacyFilter(filter_name=False)
