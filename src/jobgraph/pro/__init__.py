"""JobGraph Pro - 付费功能模块

注意:
- 此目录下的 .py 文件需要加密后才能使用
- 加密后会生成 .py.enc 文件
- 用户需要购买 License 才能使用付费功能
"""


# 延迟导入，避免源代码不存在时报错
def get_advanced_matching():
    """获取高级匹配模块"""
    from src.jobgraph.license.loader import pro_loader

    return pro_loader.load_module("advanced_matching")


def get_data_updater():
    """获取数据更新模块"""
    from src.jobgraph.license.loader import pro_loader

    return pro_loader.load_module("data_updater")


def get_data_export():
    """获取数据导出模块"""
    from src.jobgraph.license.loader import pro_loader

    return pro_loader.load_module("data_export")


__all__ = [
    "get_advanced_matching",
    "get_data_updater",
    "get_data_export",
]
