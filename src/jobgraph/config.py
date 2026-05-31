"""JobGraph Configuration - 统一版本配置"""



# Version
VERSION = "1.0.0"

# 免费功能
FREE_FEATURES = {
    "job_search": True,
    "company_profile": True,
    "pitfall_guide": True,
    "salary_analysis": True,
    "basic_matching": True,
    "privacy_mode": True,
}

# 付费功能
PRO_FEATURES = {
    "advanced_matching": True,
    "data_export": True,
    "auto_data_update": True,
    "unlimited_search": True,
    "career_suggestions": True,
}

# 免费版限制
FREE_LIMITS = {
    "max_search_per_day": 100,
    "max_jobs_per_search": 50,
    "max_matching_results": 10,
    "max_reviews_per_company": 10,
}

# 付费版限制
PRO_LIMITS = {
    "max_search_per_day": 10000,
    "max_jobs_per_search": 500,
    "max_matching_results": 100,
    "max_reviews_per_company": 100,
}


def get_features(is_pro: bool = False) -> dict:
    """获取功能列表"""
    features = FREE_FEATURES.copy()
    if is_pro:
        features.update(PRO_FEATURES)
    return features


def get_limits(is_pro: bool = False) -> dict:
    """获取限制"""
    if is_pro:
        return PRO_LIMITS.copy()
    return FREE_LIMITS.copy()


def is_feature_available(feature: str, is_pro: bool = False) -> bool:
    """检查功能是否可用"""
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
        "is_pro": is_pro,
        "edition": "专业版" if is_pro else "免费版",
        "features": get_features(is_pro),
        "limits": get_limits(is_pro),
    }


def get_upgrade_info() -> dict:
    """获取升级信息"""
    return {
        "current": "免费版",
        "upgrade_to": "专业版",
        "benefits": [
            "无限搜索次数",
            "高级岗位匹配",
            "数据导出功能",
            "自动数据更新",
            "职业发展建议",
            "7天免费试用",
        ],
        "pricing": {
            "monthly": "¥9.9/月",
            "yearly": "¥99/年",
            "lifetime": "¥299",
            "early_bird": "¥199 (限时)",
        },
        "trial": {
            "days": 7,
            "price": 0,
        },
    }
