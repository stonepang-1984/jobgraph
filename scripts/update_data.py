#!/usr/bin/env python3
"""数据更新脚本

用法:
    python update_data.py                  # 检查并更新所有数据
    python update_data.py --companies     # 只更新公司数据
    python update_data.py --jobs          # 只更新岗位数据
    python update_data.py --force         # 强制更新
    python update_data.py --status        # 查看更新状态
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.jobgraph.updater import update_manager, incremental_updater


def load_data(filepath: str) -> list[dict]:
    """加载数据文件"""
    path = Path(filepath)
    if not path.exists():
        logger.error(f"File not found: {filepath}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_companies(force: bool = False) -> dict:
    """更新公司数据"""
    if not force and not update_manager.check_update_needed("companies", interval_hours=24):
        logger.info("Companies data is up to date")
        return {"skipped": True}

    data_file = Path("data/crawled/companies.json")
    if not data_file.exists():
        logger.error("Companies data file not found. Run crawl_data.py first.")
        return {"error": "data file not found"}

    companies = load_data(str(data_file))
    logger.info(f"Updating {len(companies)} companies...")
    stats = incremental_updater.update_companies(companies)
    logger.info(f"Companies update: {stats}")
    return stats


def update_jobs(force: bool = False) -> dict:
    """更新岗位数据"""
    if not force and not update_manager.check_update_needed("jobs", interval_hours=12):
        logger.info("Jobs data is up to date")
        return {"skipped": True}

    data_file = Path("data/crawled/jobs.json")
    if not data_file.exists():
        logger.error("Jobs data file not found. Run crawl_data.py first.")
        return {"error": "data file not found"}

    jobs = load_data(str(data_file))
    logger.info(f"Updating {len(jobs)} jobs...")
    stats = incremental_updater.update_jobs(jobs)
    logger.info(f"Jobs update: {stats}")
    return stats


def show_status():
    """显示更新状态"""
    stats = update_manager.get_statistics()

    print("\n" + "=" * 50)
    print("数据更新状态")
    print("=" * 50)
    print(f"最后更新: {stats['last_update'] or '从未更新'}")
    print(f"总更新次数: {stats['total_updates']}")
    print(f"数据类型: {', '.join(stats['data_types']) or '无'}")

    if stats["versions"]:
        print("\n各数据类型:")
        for dtype, info in stats["versions"].items():
            print(f"  {dtype}: {info.get('last_update', 'N/A')} ({info.get('count', 0)} 条)")

    # 最近更新记录
    history = update_manager.get_update_history(5)
    if history:
        print("\n最近更新:")
        for record in history:
            print(f"  [{record['timestamp'][:16]}] {record['type']}: {record['count']} 条")

    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Data update script")
    parser.add_argument("--companies", action="store_true", help="Update companies only")
    parser.add_argument("--jobs", action="store_true", help="Update jobs only")
    parser.add_argument("--force", action="store_true", help="Force update")
    parser.add_argument("--status", action="store_true", help="Show update status")
    args = parser.parse_args()

    # 显示状态
    if args.status:
        show_status()
        return

    # 更新数据
    logger.info("=" * 50)
    logger.info("开始数据更新")
    logger.info("=" * 50)

    results = {}

    if args.companies:
        results["companies"] = update_companies(args.force)
    elif args.jobs:
        results["jobs"] = update_jobs(args.force)
    else:
        # 更新所有
        results["companies"] = update_companies(args.force)
        results["jobs"] = update_jobs(args.force)

    # 打印结果
    logger.info("\n" + "=" * 50)
    logger.info("更新完成")
    logger.info("=" * 50)
    for dtype, stats in results.items():
        if isinstance(stats, dict):
            if stats.get("skipped"):
                logger.info(f"{dtype}: 跳过 (已是最新)")
            elif stats.get("error"):
                logger.error(f"{dtype}: 错误 - {stats['error']}")
            else:
                logger.info(f"{dtype}: 创建={stats.get('created', 0)}, "
                          f"更新={stats.get('updated', 0)}, "
                          f"不变={stats.get('unchanged', 0)}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
