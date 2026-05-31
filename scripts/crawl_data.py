"""数据爬虫 - 从公开数据源获取公司和岗位信息"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger

import requests


class DataCrawler:
    """数据爬虫基类"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送 GET 请求"""
        try:
            response = self.session.get(url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Request failed: {url} - {e}")
            return None

    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送 POST 请求"""
        try:
            response = self.session.post(url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Request failed: {url} - {e}")
            return None


class TianyanchaCrawler(DataCrawler):
    """天眼查数据爬虫 (公开信息)"""

    BASE_URL = "https://www.tianyancha.com"

    def search_company(self, keyword: str) -> list[dict]:
        """搜索公司 (使用公开搜索)"""
        url = f"{self.BASE_URL}/search"
        params = {"key": keyword}

        response = self.get(url, params=params)
        if not response:
            return []

        # 解析结果 (需要根据实际页面结构)
        # 这里返回示例数据结构
        return []

    def get_company_info(self, company_id: str) -> Optional[dict]:
        """获取公司详情"""
        url = f"{self.BASE_URL}/company/{company_id}"
        response = self.get(url)
        if not response:
            return None

        # 解析公司信息
        return None


class BossZhipinCrawler(DataCrawler):
    """Boss直聘数据爬虫 (公开信息)"""

    BASE_URL = "https://www.zhipin.com"

    def search_jobs(self, keyword: str, city: str = "101010100") -> list[dict]:
        """搜索岗位"""
        url = f"{self.BASE_URL}/web/geek/job"
        params = {
            "query": keyword,
            "city": city,
        }

        response = self.get(url, params=params)
        if not response:
            return []

        # 解析结果
        return []


class OpenDataCrawler(DataCrawler):
    """公开数据源爬虫"""

    def crawl_from_opendata(self) -> list[dict]:
        """从公开数据源获取公司数据"""
        # 使用公开的公司信息 API
        companies = []

        # 示例: 从公开 API 获取上市公司信息
        try:
            # 这里可以接入公开的数据源
            # 例如: 东方财富、同花顺等公开 API
            pass
        except Exception as e:
            logger.error(f"Failed to crawl open data: {e}")

        return companies


class ManualDataLoader:
    """手动数据加载器"""

    def __init__(self):
        self.data_dir = Path("data/manual")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_companies(self, filepath: str) -> list[dict]:
        """从文件加载公司数据"""
        path = Path(filepath)
        if not path.exists():
            logger.error(f"File not found: {filepath}")
            return []

        if path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        elif path.suffix == ".csv":
            import csv
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        else:
            logger.error(f"Unsupported file format: {path.suffix}")
            return []

    def save_companies(self, companies: list[dict], filepath: str) -> None:
        """保存公司数据到文件"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(companies)} companies to {filepath}")


def generate_company_id(name: str) -> str:
    """生成公司 ID"""
    return hashlib.md5(name.encode()).hexdigest()[:16]


def generate_sample_companies() -> list[dict]:
    """生成示例公司数据"""
    companies = [
        # 互联网大厂
        {
            "id": generate_company_id("腾讯"),
            "name": "腾讯",
            "name_en": "Tencent",
            "industry": "互联网",
            "size": "giant",
            "founded": 1998,
            "headquarters": "深圳",
            "employees": 100000,
            "avg_salary": 35000,
            "avg_rating": 3.8,
            "risk_level": "low",
            "risk_score": 0.2,
            "tags": ["大厂", "社交", "游戏"],
        },
        {
            "id": generate_company_id("阿里巴巴"),
            "name": "阿里巴巴",
            "name_en": "Alibaba",
            "industry": "互联网",
            "size": "giant",
            "founded": 1999,
            "headquarters": "杭州",
            "employees": 200000,
            "avg_salary": 38000,
            "avg_rating": 3.5,
            "risk_level": "low",
            "risk_score": 0.3,
            "tags": ["大厂", "电商", "云计算"],
        },
        {
            "id": generate_company_id("字节跳动"),
            "name": "字节跳动",
            "name_en": "ByteDance",
            "industry": "互联网",
            "size": "giant",
            "founded": 2012,
            "headquarters": "北京",
            "employees": 150000,
            "avg_salary": 42000,
            "avg_rating": 3.6,
            "risk_level": "low",
            "risk_score": 0.25,
            "tags": ["大厂", "短视频", "高薪"],
        },
        {
            "id": generate_company_id("美团"),
            "name": "美团",
            "name_en": "Meituan",
            "industry": "互联网",
            "size": "giant",
            "founded": 2010,
            "headquarters": "北京",
            "employees": 80000,
            "avg_salary": 32000,
            "avg_rating": 3.4,
            "risk_level": "low",
            "risk_score": 0.3,
            "tags": ["大厂", "本地生活"],
        },
        {
            "id": generate_company_id("京东"),
            "name": "京东",
            "name_en": "JD.com",
            "industry": "电商",
            "size": "giant",
            "founded": 1998,
            "headquarters": "北京",
            "employees": 500000,
            "avg_salary": 30000,
            "avg_rating": 3.5,
            "risk_level": "low",
            "risk_score": 0.3,
            "tags": ["大厂", "电商", "物流"],
        },
        {
            "id": generate_company_id("百度"),
            "name": "百度",
            "name_en": "Baidu",
            "industry": "互联网",
            "size": "giant",
            "founded": 2000,
            "headquarters": "北京",
            "employees": 40000,
            "avg_salary": 33000,
            "avg_rating": 3.3,
            "risk_level": "low",
            "risk_score": 0.3,
            "tags": ["大厂", "搜索", "AI"],
        },
        {
            "id": generate_company_id("网易"),
            "name": "网易",
            "name_en": "NetEase",
            "industry": "互联网",
            "size": "giant",
            "founded": 1997,
            "headquarters": "杭州",
            "employees": 30000,
            "avg_salary": 35000,
            "avg_rating": 3.7,
            "risk_level": "low",
            "risk_score": 0.2,
            "tags": ["大厂", "游戏", "音乐"],
        },
        {
            "id": generate_company_id("拼多多"),
            "name": "拼多多",
            "name_en": "Pinduoduo",
            "industry": "电商",
            "size": "giant",
            "founded": 2015,
            "headquarters": "上海",
            "employees": 20000,
            "avg_salary": 40000,
            "avg_rating": 3.2,
            "risk_level": "medium",
            "risk_score": 0.4,
            "tags": ["大厂", "电商", "高薪"],
        },
        # AI 公司
        {
            "id": generate_company_id("商汤科技"),
            "name": "商汤科技",
            "name_en": "SenseTime",
            "industry": "人工智能",
            "size": "large",
            "founded": 2014,
            "headquarters": "上海",
            "employees": 5000,
            "avg_salary": 38000,
            "avg_rating": 3.4,
            "risk_level": "medium",
            "risk_score": 0.4,
            "tags": ["AI", "计算机视觉"],
        },
        {
            "id": generate_company_id("旷视科技"),
            "name": "旷视科技",
            "name_en": "Megvii",
            "industry": "人工智能",
            "size": "large",
            "founded": 2011,
            "headquarters": "北京",
            "employees": 3000,
            "avg_salary": 36000,
            "avg_rating": 3.3,
            "risk_level": "medium",
            "risk_score": 0.4,
            "tags": ["AI", "人脸识别"],
        },
        # 新能源
        {
            "id": generate_company_id("宁德时代"),
            "name": "宁德时代",
            "name_en": "CATL",
            "industry": "新能源",
            "size": "giant",
            "founded": 2011,
            "headquarters": "宁德",
            "employees": 100000,
            "avg_salary": 25000,
            "avg_rating": 3.6,
            "risk_level": "low",
            "risk_score": 0.2,
            "tags": ["新能源", "电池"],
        },
        {
            "id": generate_company_id("比亚迪"),
            "name": "比亚迪",
            "name_en": "BYD",
            "industry": "汽车",
            "size": "giant",
            "founded": 1995,
            "headquarters": "深圳",
            "employees": 600000,
            "avg_salary": 22000,
            "avg_rating": 3.4,
            "risk_level": "low",
            "risk_score": 0.2,
            "tags": ["新能源", "汽车"],
        },
        # 汽车新势力
        {
            "id": generate_company_id("蔚来"),
            "name": "蔚来",
            "name_en": "NIO",
            "industry": "汽车",
            "size": "large",
            "founded": 2014,
            "headquarters": "上海",
            "employees": 30000,
            "avg_salary": 30000,
            "avg_rating": 3.5,
            "risk_level": "medium",
            "risk_score": 0.4,
            "tags": ["新能源", "汽车"],
        },
        {
            "id": generate_company_id("小鹏汽车"),
            "name": "小鹏汽车",
            "name_en": "XPeng",
            "industry": "汽车",
            "size": "large",
            "founded": 2014,
            "headquarters": "广州",
            "employees": 20000,
            "avg_salary": 28000,
            "avg_rating": 3.4,
            "risk_level": "medium",
            "risk_score": 0.4,
            "tags": ["新能源", "汽车"],
        },
        # 半导体
        {
            "id": generate_company_id("中芯国际"),
            "name": "中芯国际",
            "name_en": "SMIC",
            "industry": "半导体",
            "size": "giant",
            "founded": 2000,
            "headquarters": "上海",
            "employees": 20000,
            "avg_salary": 28000,
            "avg_rating": 3.5,
            "risk_level": "low",
            "risk_score": 0.3,
            "tags": ["半导体", "芯片"],
        },
        # 金融科技
        {
            "id": generate_company_id("蚂蚁集团"),
            "name": "蚂蚁集团",
            "name_en": "Ant Group",
            "industry": "金融科技",
            "size": "giant",
            "founded": 2004,
            "headquarters": "杭州",
            "employees": 30000,
            "avg_salary": 40000,
            "avg_rating": 3.6,
            "risk_level": "medium",
            "risk_score": 0.3,
            "tags": ["金融科技", "支付"],
        },
        # 企业服务
        {
            "id": generate_company_id("用友网络"),
            "name": "用友网络",
            "name_en": "Yonyou",
            "industry": "企业服务",
            "size": "large",
            "founded": 1988,
            "headquarters": "北京",
            "employees": 20000,
            "avg_salary": 25000,
            "avg_rating": 3.2,
            "risk_level": "low",
            "risk_score": 0.3,
            "tags": ["企业服务", "ERP"],
        },
        {
            "id": generate_company_id("金山办公"),
            "name": "金山办公",
            "name_en": "Kingsoft Office",
            "industry": "企业服务",
            "size": "large",
            "founded": 2011,
            "headquarters": "北京",
            "employees": 5000,
            "avg_salary": 30000,
            "avg_rating": 3.7,
            "risk_level": "low",
            "risk_score": 0.2,
            "tags": ["企业服务", "办公软件"],
        },
        # 硬件
        {
            "id": generate_company_id("小米"),
            "name": "小米",
            "name_en": "Xiaomi",
            "industry": "硬件",
            "size": "giant",
            "founded": 2010,
            "headquarters": "北京",
            "employees": 30000,
            "avg_salary": 30000,
            "avg_rating": 3.5,
            "risk_level": "low",
            "risk_score": 0.25,
            "tags": ["硬件", "手机", "IoT"],
        },
        {
            "id": generate_company_id("大疆创新"),
            "name": "大疆创新",
            "name_en": "DJI",
            "industry": "硬件",
            "size": "large",
            "founded": 2006,
            "headquarters": "深圳",
            "employees": 15000,
            "avg_salary": 32000,
            "avg_rating": 3.6,
            "risk_level": "low",
            "risk_score": 0.2,
            "tags": ["硬件", "无人机"],
        },
        # 有风险的公司示例
        {
            "id": generate_company_id("某创业公司A"),
            "name": "某创业公司A",
            "name_en": "Startup A",
            "industry": "SaaS",
            "size": "small",
            "founded": 2022,
            "headquarters": "北京",
            "employees": 50,
            "avg_salary": 25000,
            "avg_rating": 2.8,
            "risk_level": "high",
            "risk_score": 0.7,
            "risk_factors": ["创业不稳定", "加班严重"],
            "tags": ["创业", "SaaS"],
        },
    ]

    return companies


def generate_sample_jobs(companies: list[dict]) -> list[dict]:
    """生成示例岗位数据"""
    import random

    jobs = []
    job_titles = {
        "技术": ["后端工程师", "前端工程师", "算法工程师", "数据工程师", "测试工程师"],
        "产品": ["产品经理", "高级产品经理", "产品总监"],
        "设计": ["UI设计师", "UX设计师", "视觉设计师"],
        "运营": ["运营专员", "运营经理", "内容运营"],
    }

    skills_map = {
        "后端工程师": ["Java", "Python", "Go", "MySQL", "Redis", "微服务"],
        "前端工程师": ["React", "Vue", "TypeScript", "JavaScript", "HTML/CSS"],
        "算法工程师": ["Python", "PyTorch", "TensorFlow", "NLP", "机器学习"],
        "产品经理": ["产品设计", "数据分析", "用户研究", "Axure"],
        "UI设计师": ["Figma", "Sketch", "Photoshop", "Illustrator"],
    }

    cities = ["北京", "上海", "深圳", "杭州", "广州", "成都"]

    for company in companies:
        # 每个公司生成 3-5 个岗位
        job_count = random.randint(3, 5)
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
                "location": company.get("headquarters", random.choice(cities)),
                "salary_min": int(base_salary * random.uniform(0.7, 0.9)),
                "salary_max": int(base_salary * random.uniform(1.1, 1.4)),
                "salary_months": random.choice([12, 13, 14, 15, 16]),
                "experience_years": random.choice([0, 1, 2, 3, 5]),
                "education": random.choice(["大专", "本科", "硕士"]),
                "skills": skills_map.get(title, ["沟通能力", "团队协作"])[:random.randint(3, 5)],
                "benefits": ["五险一金", "年终奖", "带薪年假"],
                "is_active": True,
            }
            jobs.append(job)

    return jobs


def generate_sample_reviews(companies: list[dict]) -> list[dict]:
    """生成示例评价数据"""
    import random

    reviews = []

    pros_templates = [
        "公司平台大，能学到很多东西",
        "薪资福利不错，年终奖丰厚",
        "团队氛围好，同事nice",
        "工作生活平衡，不强制加班",
        "技术栈新，能接触前沿技术",
        "晋升机制清晰，有成长空间",
    ]

    cons_templates = [
        "加班较多，项目紧的时候很累",
        "部分组内卷严重",
        "晋升竞争激烈",
        "流程繁琐，决策慢",
        "薪资涨幅有限",
        "部分领导管理能力差",
    ]

    pitfall_types = ["996", "PUA", "内卷", "欠薪", "裁员"]

    for company in companies:
        # 每个公司生成 3-8 条评价
        review_count = random.randint(3, 8)

        for i in range(review_count):
            rating = round(random.uniform(2.5, 5.0), 1)

            # 高风险公司更可能有坑点
            pitfall_tags = []
            if company.get("risk_level") in ["high", "blacklist"]:
                if random.random() > 0.3:
                    pitfall_tags.append(random.choice(pitfall_types))
            elif company.get("risk_level") == "medium":
                if random.random() > 0.7:
                    pitfall_tags.append(random.choice(pitfall_types))

            review = {
                "id": hashlib.md5(f"{company['id']}_review_{i}".encode()).hexdigest()[:16],
                "company_id": company["id"],
                "overall_rating": rating,
                "salary_rating": round(random.uniform(2.0, 5.0), 1),
                "work_life_rating": round(random.uniform(1.5, 5.0), 1),
                "management_rating": round(random.uniform(2.0, 5.0), 1),
                "title": random.choice(["还不错", "一般", "不推荐", "推荐", "看组"]),
                "pros": random.choice(pros_templates),
                "cons": random.choice(cons_templates),
                "reviewer_title": random.choice(["工程师", "产品经理", "设计师", "运营"]),
                "reviewer_tenure": random.choice(["不到1年", "1-2年", "2-3年", "3-5年"]),
                "is_current_employee": random.random() > 0.3,
                "pitfall_tags": pitfall_tags,
            }
            reviews.append(review)

    return reviews


def import_all_data():
    """导入所有数据"""
    from src.jobgraph.graph_manager import job_manager
    from src.jobgraph.models import Company, Job, Review, Pitfall, CompanySize, RiskLevel

    logger.info("=" * 60)
    logger.info("Importing Data")
    logger.info("=" * 60)

    # 生成数据
    companies_data = generate_sample_companies()
    jobs_data = generate_sample_jobs(companies_data)
    reviews_data = generate_sample_reviews(companies_data)

    logger.info(f"Generated: {len(companies_data)} companies, {len(jobs_data)} jobs, {len(reviews_data)} reviews")

    # 导入公司
    logger.info("Importing companies...")
    for data in companies_data:
        try:
            company = Company(
                id=data["id"],
                name=data["name"],
                name_en=data.get("name_en"),
                industry=data.get("industry"),
                size=CompanySize(data["size"]) if data.get("size") else None,
                founded=data.get("founded"),
                headquarters=data.get("headquarters"),
                employees=data.get("employees"),
                avg_salary=data.get("avg_salary"),
                avg_rating=data.get("avg_rating"),
                risk_level=RiskLevel(data.get("risk_level", "medium")),
                risk_score=data.get("risk_score", 0.5),
                risk_factors=data.get("risk_factors", []),
                tags=data.get("tags", []),
            )
            job_manager.create_company(company)
        except Exception as e:
            logger.error(f"Failed to import company {data.get('name')}: {e}")

    # 导入岗位
    logger.info("Importing jobs...")
    for data in jobs_data:
        try:
            from src.jobgraph.models import JobType
            job = Job(
                id=data["id"],
                title=data["title"],
                company_id=data["company_id"],
                company_name=data["company_name"],
                department=data.get("department"),
                location=data.get("location"),
                salary_min=data.get("salary_min"),
                salary_max=data.get("salary_max"),
                salary_months=data.get("salary_months", 12),
                experience_years=data.get("experience_years"),
                education=data.get("education"),
                skills=data.get("skills", []),
                benefits=data.get("benefits", []),
                is_active=data.get("is_active", True),
            )
            job_manager.create_job(job)
        except Exception as e:
            logger.error(f"Failed to import job {data.get('title')}: {e}")

    # 导入评价
    logger.info("Importing reviews...")
    for data in reviews_data:
        try:
            review = Review(
                id=data["id"],
                company_id=data["company_id"],
                overall_rating=data.get("overall_rating", 0),
                salary_rating=data.get("salary_rating"),
                work_life_rating=data.get("work_life_rating"),
                management_rating=data.get("management_rating"),
                title=data.get("title"),
                pros=data.get("pros"),
                cons=data.get("cons"),
                reviewer_title=data.get("reviewer_title"),
                reviewer_tenure=data.get("reviewer_tenure"),
                is_current_employee=data.get("is_current_employee", True),
                pitfall_tags=data.get("pitfall_tags", []),
            )
            job_manager.create_review(review)
        except Exception as e:
            logger.error(f"Failed to import review: {e}")

    # 打印统计
    stats = job_manager.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Companies: {stats.get('companies', 0)}")
    logger.info(f"Jobs: {stats.get('jobs', 0)}")
    logger.info(f"Reviews: {stats.get('reviews', 0)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import_all_data()
