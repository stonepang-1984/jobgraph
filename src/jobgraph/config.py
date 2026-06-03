"""JobGraph Configuration - 统一版本配置

当前策略: 完全免费，积累用户
付费架构保留，后续可调整
"""

# Version
VERSION = "1.0.0"

# 免费功能 (当前所有功能免费)
FREE_FEATURES = {
    "job_search": True,
    "company_profile": True,
    "pitfall_guide": True,
    "salary_analysis": True,
    "basic_matching": True,
    "privacy_mode": True,
    # 以下功能暂时免费开放
    "advanced_matching": True,
    "data_export": True,
    "auto_data_update": True,
    "unlimited_search": True,
    "career_suggestions": True,
}

# 付费功能 (保留架构，当前不启用)
PRO_FEATURES = {
    "advanced_matching": True,
    "data_export": True,
    "auto_data_update": True,
    "unlimited_search": True,
    "career_suggestions": True,
    # 未来付费功能
    "priority_support": True,
    "api_access": True,
}

# 免费版限制 (当前无限制)
FREE_LIMITS = {
    "max_search_per_day": 10000,
    "max_jobs_per_search": 500,
    "max_matching_results": 100,
    "max_reviews_per_company": 100,
}

# 付费版限制
PRO_LIMITS = {
    "max_search_per_day": 10000,
    "max_jobs_per_search": 500,
    "max_matching_results": 100,
    "max_reviews_per_company": 100,
}

# 捐赠信息
DONATION = {
    "enabled": True,
    "message": "如果觉得有用，欢迎请作者喝杯咖啡 ☕",
    "links": {
        "wechat": "",  # 微信收款码
        "alipay": "",  # 支付宝收款码
        "github": "https://github.com/sponsors/stonepang-1984",
    },
}


def get_features(is_pro: bool = False) -> dict:
    """获取功能列表"""
    # 当前所有功能免费
    return FREE_FEATURES.copy()


def get_limits(is_pro: bool = False) -> dict:
    """获取限制"""
    # 当前无限制
    return FREE_LIMITS.copy()


def is_feature_available(feature: str, is_pro: bool = False) -> bool:
    """检查功能是否可用"""
    # 当前所有功能可用
    features = get_features(is_pro)
    return features.get(feature, False)


def get_limit_value(limit_name: str, is_pro: bool = False) -> int:
    """获取限制值"""
    limits = get_limits(is_pro)
    return limits.get(limit_name, 0)


def get_edition_info(is_pro: bool = False) -> dict:
    """获取版本信息"""
    return {
        "version": VERSION,
        "is_pro": True,  # 当前所有用户都是"专业版"
        "edition": "免费版",  # 但显示为免费版
        "features": get_features(is_pro),
        "limits": get_limits(is_pro),
        "donation": DONATION,
    }


def get_upgrade_info() -> dict:
    """获取升级信息 (当前不需要升级)"""
    return {
        "current": "免费完整版",
        "upgrade_to": None,
        "benefits": [
            "所有功能免费使用",
            "无搜索次数限制",
            "无匹配结果限制",
        ],
        "pricing": {
            "monthly": "免费",
            "yearly": "免费",
            "lifetime": "免费",
        },
        "donation": DONATION,
        "trial": {
            "days": 0,
            "price": 0,
        },
    }
