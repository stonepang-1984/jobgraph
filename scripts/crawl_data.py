#!/usr/bin/env python3
"""数据爬虫 - 从公开数据源获取公司和岗位信息

数据来源:
1. 天眼查 API (公司信息) - 需要 API Key
2. 行业公开数据
3. 示例数据生成
"""

import json
import hashlib
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


class DataCrawler:
    """数据爬虫基类"""

    def __init__(self):
        self.data_dir = Path("data/crawled")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_data(self, data: list[dict], filename: str) -> str:
        """保存爬取的数据"""
        filepath = self.data_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} records to {filepath}")
        return str(filepath)


class PublicDataLoader(DataCrawler):
    """公开数据加载器"""

    def generate_sample_companies(self) -> list[dict]:
        """生成示例公司数据 (35家公司)"""
        companies = [
            # 互联网大厂
            {"name": "腾讯", "name_en": "Tencent", "industry": "互联网", "size": "giant", "founded": 1998, "headquarters": "深圳", "employees": 100000, "avg_salary": 35000, "avg_rating": 3.8, "risk_level": "low", "risk_score": 0.2, "tags": "大厂,社交,游戏"},
            {"name": "阿里巴巴", "name_en": "Alibaba", "industry": "互联网", "size": "giant", "founded": 1999, "headquarters": "杭州", "employees": 200000, "avg_salary": 38000, "avg_rating": 3.5, "risk_level": "low", "risk_score": 0.3, "tags": "大厂,电商,云计算"},
            {"name": "字节跳动", "name_en": "ByteDance", "industry": "互联网", "size": "giant", "founded": 2012, "headquarters": "北京", "employees": 150000, "avg_salary": 42000, "avg_rating": 3.6, "risk_level": "low", "risk_score": 0.25, "tags": "大厂,短视频,高薪"},
            {"name": "美团", "name_en": "Meituan", "industry": "互联网", "size": "giant", "founded": 2010, "headquarters": "北京", "employees": 80000, "avg_salary": 32000, "avg_rating": 3.4, "risk_level": "low", "risk_score": 0.3, "tags": "大厂,本地生活"},
            {"name": "京东", "name_en": "JD.com", "industry": "电商", "size": "giant", "founded": 1998, "headquarters": "北京", "employees": 500000, "avg_salary": 30000, "avg_rating": 3.5, "risk_level": "low", "risk_score": 0.3, "tags": "大厂,电商,物流"},
            {"name": "百度", "name_en": "Baidu", "industry": "互联网", "size": "giant", "founded": 2000, "headquarters": "北京", "employees": 40000, "avg_salary": 33000, "avg_rating": 3.3, "risk_level": "low", "risk_score": 0.3, "tags": "大厂,搜索,AI"},
            {"name": "网易", "name_en": "NetEase", "industry": "互联网", "size": "giant", "founded": 1997, "headquarters": "杭州", "employees": 30000, "avg_salary": 35000, "avg_rating": 3.7, "risk_level": "low", "risk_score": 0.2, "tags": "大厂,游戏,音乐"},
            {"name": "拼多多", "name_en": "Pinduoduo", "industry": "电商", "size": "giant", "founded": 2015, "headquarters": "上海", "employees": 20000, "avg_salary": 40000, "avg_rating": 3.2, "risk_level": "medium", "risk_score": 0.4, "tags": "大厂,电商,高薪"},
            # AI 公司
            {"name": "商汤科技", "name_en": "SenseTime", "industry": "人工智能", "size": "large", "founded": 2014, "headquarters": "上海", "employees": 5000, "avg_salary": 38000, "avg_rating": 3.4, "risk_level": "medium", "risk_score": 0.4, "tags": "AI,计算机视觉"},
            {"name": "旷视科技", "name_en": "Megvii", "industry": "人工智能", "size": "large", "founded": 2011, "headquarters": "北京", "employees": 3000, "avg_salary": 36000, "avg_rating": 3.3, "risk_level": "medium", "risk_score": 0.4, "tags": "AI,人脸识别"},
            {"name": "科大讯飞", "name_en": "iFLYTEK", "industry": "人工智能", "size": "large", "founded": 1999, "headquarters": "合肥", "employees": 15000, "avg_salary": 30000, "avg_rating": 3.5, "risk_level": "low", "risk_score": 0.3, "tags": "AI,语音识别"},
            # 新能源
            {"name": "宁德时代", "name_en": "CATL", "industry": "新能源", "size": "giant", "founded": 2011, "headquarters": "宁德", "employees": 100000, "avg_salary": 25000, "avg_rating": 3.6, "risk_level": "low", "risk_score": 0.2, "tags": "新能源,电池"},
            {"name": "比亚迪", "name_en": "BYD", "industry": "汽车", "size": "giant", "founded": 1995, "headquarters": "深圳", "employees": 600000, "avg_salary": 22000, "avg_rating": 3.4, "risk_level": "low", "risk_score": 0.2, "tags": "新能源,汽车"},
            {"name": "蔚来", "name_en": "NIO", "industry": "汽车", "size": "large", "founded": 2014, "headquarters": "上海", "employees": 30000, "avg_salary": 30000, "avg_rating": 3.5, "risk_level": "medium", "risk_score": 0.4, "tags": "新能源,汽车"},
            {"name": "小鹏汽车", "name_en": "XPeng", "industry": "汽车", "size": "large", "founded": 2014, "headquarters": "广州", "employees": 20000, "avg_salary": 28000, "avg_rating": 3.4, "risk_level": "medium", "risk_score": 0.4, "tags": "新能源,汽车"},
            {"name": "理想汽车", "name_en": "Li Auto", "industry": "汽车", "size": "large", "founded": 2015, "headquarters": "北京", "employees": 15000, "avg_salary": 29000, "avg_rating": 3.5, "risk_level": "medium", "risk_score": 0.35, "tags": "新能源,汽车"},
            # 半导体
            {"name": "中芯国际", "name_en": "SMIC", "industry": "半导体", "size": "giant", "founded": 2000, "headquarters": "上海", "employees": 20000, "avg_salary": 28000, "avg_rating": 3.5, "risk_level": "low", "risk_score": 0.3, "tags": "半导体,芯片"},
            {"name": "华为海思", "name_en": "HiSilicon", "industry": "半导体", "size": "large", "founded": 2004, "headquarters": "深圳", "employees": 10000, "avg_salary": 35000, "avg_rating": 3.7, "risk_level": "low", "risk_score": 0.2, "tags": "半导体,芯片,华为"},
            # 金融科技
            {"name": "蚂蚁集团", "name_en": "Ant Group", "industry": "金融科技", "size": "giant", "founded": 2004, "headquarters": "杭州", "employees": 30000, "avg_salary": 40000, "avg_rating": 3.6, "risk_level": "medium", "risk_score": 0.3, "tags": "金融科技,支付"},
            {"name": "微众银行", "name_en": "WeBank", "industry": "金融科技", "size": "large", "founded": 2014, "headquarters": "深圳", "employees": 5000, "avg_salary": 35000, "avg_rating": 3.5, "risk_level": "low", "risk_score": 0.25, "tags": "金融科技,银行"},
            # 企业服务
            {"name": "用友网络", "name_en": "Yonyou", "industry": "企业服务", "size": "large", "founded": 1988, "headquarters": "北京", "employees": 20000, "avg_salary": 25000, "avg_rating": 3.2, "risk_level": "low", "risk_score": 0.3, "tags": "企业服务,ERP"},
            {"name": "金山办公", "name_en": "Kingsoft Office", "industry": "企业服务", "size": "large", "founded": 2011, "headquarters": "北京", "employees": 5000, "avg_salary": 30000, "avg_rating": 3.7, "risk_level": "low", "risk_score": 0.2, "tags": "企业服务,办公软件"},
            # 硬件
            {"name": "小米", "name_en": "Xiaomi", "industry": "硬件", "size": "giant", "founded": 2010, "headquarters": "北京", "employees": 30000, "avg_salary": 30000, "avg_rating": 3.5, "risk_level": "low", "risk_score": 0.25, "tags": "硬件,手机,IoT"},
            {"name": "OPPO", "name_en": "OPPO", "industry": "硬件", "size": "giant", "founded": 2004, "headquarters": "东莞", "employees": 40000, "avg_salary": 28000, "avg_rating": 3.4, "risk_level": "low", "risk_score": 0.25, "tags": "硬件,手机"},
            {"name": "vivo", "name_en": "vivo", "industry": "硬件", "size": "giant", "founded": 2009, "headquarters": "东莞", "employees": 30000, "avg_salary": 27000, "avg_rating": 3.3, "risk_level": "low", "risk_score": 0.25, "tags": "硬件,手机"},
            {"name": "大疆创新", "name_en": "DJI", "industry": "硬件", "size": "large", "founded": 2006, "headquarters": "深圳", "employees": 15000, "avg_salary": 32000, "avg_rating": 3.6, "risk_level": "low", "risk_score": 0.2, "tags": "硬件,无人机"},
            {"name": "海康威视", "name_en": "Hikvision", "industry": "硬件", "size": "giant", "founded": 2001, "headquarters": "杭州", "employees": 50000, "avg_salary": 25000, "avg_rating": 3.4, "risk_level": "low", "risk_score": 0.25, "tags": "硬件,安防"},
            # 游戏
            {"name": "米哈游", "name_en": "miHoYo", "industry": "游戏", "size": "large", "founded": 2012, "headquarters": "上海", "employees": 5000, "avg_salary": 35000, "avg_rating": 3.8, "risk_level": "low", "risk_score": 0.2, "tags": "游戏,二次元"},
            {"name": "莉莉丝", "name_en": "Lilith Games", "industry": "游戏", "size": "medium", "founded": 2013, "headquarters": "上海", "employees": 2000, "avg_salary": 33000, "avg_rating": 3.6, "risk_level": "low", "risk_score": 0.25, "tags": "游戏"},
            # 物流
            {"name": "顺丰", "name_en": "SF Express", "industry": "物流", "size": "giant", "founded": 1993, "headquarters": "深圳", "employees": 500000, "avg_salary": 15000, "avg_rating": 3.3, "risk_level": "low", "risk_score": 0.2, "tags": "物流,快递"},
            # 外企
            {"name": "微软中国", "name_en": "Microsoft China", "industry": "互联网", "size": "large", "founded": 1992, "headquarters": "北京", "employees": 10000, "avg_salary": 45000, "avg_rating": 4.2, "risk_level": "low", "risk_score": 0.1, "tags": "外企,云计算"},
            {"name": "苹果中国", "name_en": "Apple China", "industry": "硬件", "size": "large", "founded": 1993, "headquarters": "上海", "employees": 5000, "avg_salary": 40000, "avg_rating": 4.0, "risk_level": "low", "risk_score": 0.1, "tags": "外企,硬件"},
            # 有风险的公司
            {"name": "某创业公司A", "name_en": "Startup A", "industry": "SaaS", "size": "small", "founded": 2022, "headquarters": "北京", "employees": 50, "avg_salary": 25000, "avg_rating": 2.8, "risk_level": "high", "risk_score": 0.7, "risk_factors": "创业不稳定,加班严重", "tags": "创业,SaaS"},
            {"name": "某外包公司", "name_en": "Outsourcing Co", "industry": "IT服务", "size": "medium", "founded": 2010, "headquarters": "深圳", "employees": 1000, "avg_salary": 15000, "avg_rating": 2.5, "risk_level": "high", "risk_score": 0.8, "risk_factors": "外包不稳定,福利差", "tags": "外包,IT服务"},
        ]

        # 生成 ID
        for company in companies:
            company["id"] = hashlib.md5(company["name"].encode()).hexdigest()[:16]

        return companies

    def generate_sample_jobs(self, companies: list[dict]) -> list[dict]:
        """生成示例岗位数据"""
        import random

        jobs = []
        job_titles = {
            "技术": ["后端工程师", "前端工程师", "全栈工程师", "算法工程师", "数据工程师", "测试工程师"],
            "产品": ["产品经理", "高级产品经理", "产品总监"],
            "设计": ["UI设计师", "UX设计师", "视觉设计师"],
            "运营": ["运营专员", "运营经理", "内容运营"],
        }

        skills_map = {
            "后端工程师": "Java,Python,Go,MySQL,Redis,微服务",
            "前端工程师": "React,Vue,TypeScript,JavaScript,HTML/CSS",
            "算法工程师": "Python,PyTorch,TensorFlow,NLP,机器学习",
            "产品经理": "产品设计,数据分析,用户研究,Axure",
            "UI设计师": "Figma,Sketch,Photoshop,Illustrator",
        }

        for company in companies:
            job_count = random.randint(3, 6)
            category = random.choice(list(job_titles.keys()))

            for _ in range(job_count):
                title = random.choice(job_titles[category])
                base_salary = company.get("avg_salary", 25000)

                job = {
                    "id": hashlib.md5(f"{company['name']}_{title}_{random.randint(1000, 9999)}".encode()).hexdigest()[:16],
                    "title": title,
                    "company_id": company["id"],
                    "company_name": company["name"],
                    "department": category,
                    "location": company.get("headquarters", "北京"),
                    "salary_min": int(base_salary * random.uniform(0.7, 0.9)),
                    "salary_max": int(base_salary * random.uniform(1.1, 1.4)),
                    "salary_months": random.choice([12, 13, 14, 15, 16]),
                    "experience_years": random.choice([0, 1, 2, 3, 5]),
                    "education": random.choice(["大专", "本科", "硕士"]),
                    "skills": skills_map.get(title, "沟通能力,团队协作"),
                    "benefits": "五险一金,年终奖,带薪年假",
                    "is_active": True,
                }
                jobs.append(job)

        return jobs

    def generate_sample_reviews(self, companies: list[dict]) -> list[dict]:
        """生成示例评价数据"""
        import random

        reviews = []

        pros_templates = [
            "公司平台大，能学到很多东西",
            "薪资福利不错，年终奖丰厚",
            "团队氛围好，同事nice",
            "工作生活平衡，不强制加班",
            "技术栈新，能接触前沿技术",
        ]

        cons_templates = [
            "加班较多，项目紧的时候很累",
            "部分组内卷严重",
            "晋升竞争激烈",
            "流程繁琐，决策慢",
            "薪资涨幅有限",
        ]

        pitfall_types = ["996", "PUA", "内卷", "欠薪", "裁员", "画饼", "克扣"]

        for company in companies:
            review_count = random.randint(3, 8)

            for i in range(review_count):
                rating = round(random.uniform(2.5, 5.0), 1)

                pitfall_tags = ""
                if company.get("risk_level") in ["high", "blacklist"]:
                    if random.random() > 0.3:
                        pitfall_tags = random.choice(pitfall_types)
                elif company.get("risk_level") == "medium":
                    if random.random() > 0.7:
                        pitfall_tags = random.choice(pitfall_types)

                review = {
                    "id": hashlib.md5(f"{company['id']}_review_{i}".encode()).hexdigest()[:16],
                    "company_id": company["id"],
                    "company_name": company["name"],
                    "overall_rating": rating,
                    "salary_rating": round(random.uniform(2.0, 5.0), 1),
                    "work_life_rating": round(random.uniform(1.5, 5.0), 1),
                    "management_rating": round(random.uniform(2.0, 5.0), 1),
                    "title": random.choice(["还不错", "一般", "不推荐", "推荐", "看组"]),
                    "pros": random.choice(pros_templates),
                    "cons": random.choice(cons_templates),
                    "reviewer_title": random.choice(["工程师", "产品经理", "设计师", "运营"]),
                    "reviewer_tenure": random.choice(["不到1年", "1-2年", "2-3年", "3-5年"]),
                    "is_current_employee": "true" if random.random() > 0.3 else "false",
                    "pitfall_tags": pitfall_tags,
                }
                reviews.append(review)

        return reviews

    def export_to_csv(self, data: list[dict], filename: str) -> str:
        """导出数据为 CSV 格式"""
        if not data:
            return ""

        filepath = self.data_dir / filename
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            # 收集所有字段名
            fieldnames = set()
            for row in data:
                fieldnames.update(row.keys())
            fieldnames = sorted(fieldnames)

            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Exported {len(data)} records to {filepath}")
        return str(filepath)


def generate_and_save():
    """生成并保存所有数据"""
    loader = PublicDataLoader()

    logger.info("=" * 60)
    logger.info("Generating Sample Data")
    logger.info("=" * 60)

    # 生成数据
    companies = loader.generate_sample_companies()
    jobs = loader.generate_sample_jobs(companies)
    reviews = loader.generate_sample_reviews(companies)

    logger.info(f"Generated: {len(companies)} companies, {len(jobs)} jobs, {len(reviews)} reviews")

    # 保存为 JSON
    loader.save_data(companies, "companies.json")
    loader.save_data(jobs, "jobs.json")
    loader.save_data(reviews, "reviews.json")

    # 保存为 CSV
    loader.export_to_csv(companies, "companies.csv")
    loader.export_to_csv(jobs, "jobs.csv")
    loader.export_to_csv(reviews, "reviews.csv")

    logger.info("\n" + "=" * 60)
    logger.info("Data Generation Complete!")
    logger.info("=" * 60)
    logger.info(f"Companies: {len(companies)}")
    logger.info(f"Jobs: {len(jobs)}")
    logger.info(f"Reviews: {len(reviews)}")
    logger.info(f"Files saved to: {loader.data_dir}")
    logger.info("=" * 60)


if __name__ == "__main__":
    generate_and_save()
