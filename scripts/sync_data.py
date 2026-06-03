#!/usr/bin/env python3
"""数据同步脚本

用法:
    # 场景A: 导入离线数据包
    python sync_data.py --mode package --input data_package.zip

    # 场景B: Tailscale 同步
    python sync_data.py --mode tailscale --server http://100.x.x.1:8000

    # 场景C: 云服务器同步
    python sync_data.py --mode cloud --url https://api.jobgraph.com --token YOUR_TOKEN

    # 查看同步状态
    python sync_data.py --status
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.jobgraph.sync.data_sync import data_sync


def main():
    parser = argparse.ArgumentParser(description="数据同步脚本")
    parser.add_argument(
        "--mode",
        choices=["package", "tailscale", "cloud"],
        help="同步模式",
    )
    parser.add_argument("--input", help="数据包路径 (package 模式)")
    parser.add_argument("--server", help="Tailscale 服务器地址")
    parser.add_argument("--url", help="云服务器地址")
    parser.add_argument("--token", help="认证 Token")
    parser.add_argument("--status", action="store_true", help="查看同步状态")
    args = parser.parse_args()

    # 查看状态
    if args.status:
        status = data_sync.get_status()
        print("\n" + "=" * 50)
        print("同步状态")
        print("=" * 50)
        print(f"模式: {status.get('mode', '未设置')}")
        print(f"最后同步: {status.get('last_sync', '从未同步')}")
        print(f"版本: {status.get('version', '未知')}")
        if status.get("counts"):
            print(f"数据量: {status['counts']}")
        print("=" * 50)
        return

    # 同步模式
    if not args.mode:
        print("请指定同步模式: --mode package|tailscale|cloud")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info(f"开始同步 (模式: {args.mode})")
    logger.info("=" * 50)

    try:
        if args.mode == "package":
            if not args.input:
                print("请指定数据包路径: --input <path>")
                sys.exit(1)
            stats = data_sync.import_package(args.input)

        elif args.mode == "tailscale":
            if not args.server:
                print("请指定服务器地址: --server <url>")
                sys.exit(1)
            stats = data_sync.sync_via_tailscale(args.server, args.token)

        elif args.mode == "cloud":
            if not args.url:
                print("请指定云服务器地址: --url <url>")
                sys.exit(1)
            stats = data_sync.sync_via_cloud(args.url, args.token)

        # 打印结果
        logger.info("\n" + "=" * 50)
        logger.info("同步完成")
        logger.info("=" * 50)
        if isinstance(stats, dict):
            for key, value in stats.items():
                if key != "counts":
                    logger.info(f"{key}: {value}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"同步失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
