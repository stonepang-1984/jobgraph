"""Generate sample job data for testing and demonstration."""

import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from src.jobgraph.models import (
    Company, Job, Review, Pitfall,
    CompanySize, RiskLevel, JobType, FundingStage
)


# ============================================================
# 数据配置
# ============================================================

INDUSTRIES = [
    "互联网", "人工智能", "电子商务", "金融科技", "游戏",
    "企业服务", "医疗健康", "教育", "新能源", "半导体",
    "汽车", "物流", "本地生活", "社交", "内容平台"
]

CITIES = ["北京", "上海", "深圳", "杭州", "广州", "成都", "南京", "武汉", "西安", "苏州"]

JOB_TITLES = {
    "技术": [
        "后端工程师", "前端工程师", "全栈工程师", "算法工程师",
        "数据工程师", "测试工程师", "运维工程师", "架构师",
        "移动端工程师", "安全工程师"
    ],
    "产品": [
        "产品经理", "高级产品经理", "产品总监", "产品专家"
    ],
    "设计": [
        "UI设计师", "UX设计师", "视觉设计师", "交互设计师"
    ],
    "运营": [
        "运营专员", "运营经理", "内容运营", "用户运营", "活动运营"
    ],
    "市场": [
        "市场专员", "市场经理", "品牌经理", "公关经理"
    ],
    "销售": [
        "销售代表", "销售经理", "大客户销售", "销售总监"
    ]
}

SKILLS = {
    "后端工程师": ["Java", "Python", "Go", "MySQL", "Redis", "微服务", "Docker", "K8s"],
    "前端工程师": ["React", "Vue", "TypeScript", "JavaScript", "HTML/CSS", "Webpack"],
    "算法工程师": ["Python", "PyTorch", "TensorFlow", "NLP", "推荐系统", "机器学习"],
    "产品经理": ["产品设计", "数据分析", "用户研究", "Axure", "SQL"],
    "UI设计师": ["Figma", "Sketch", "Photoshop", "Illustrator", "设计规范"],
}

COMPANY_NAMES = [
    # 互联网大厂
    "腾讯", "阿里巴巴", "字节跳动", "美团", "京东", "百度", "网易", "拼多多",
    # AI 公司
    "商汤科技", "旷视科技", "云从科技", "依图科技", "第四范式", "地平线",
    # 新能源
    "宁德时代", "比亚迪", "蔚来", "小鹏汽车", "理想汽车",
    # 半导体
    "中芯国际", "华为海思", "紫光集团", "长江存储",
    # 金融科技
    "蚂蚁集团", "微众银行", "陆金所", "京东数科",
    # 企业服务
    "用友网络", "金蝶软件", "金山办公", "石墨文档",
    # 其他
    "小米", "OPPO", "vivo", "大疆创新", "海康威视"
]

PITFALL_TYPES = [
    ("欠薪", "拖欠工资，不按时发放"),
    ("PUA", "精神控制，贬低员工价值"),
    ("996", "强制996工作制，没有加班费"),
    ("内卷", "过度竞争，无效加班"),
    ("裁员", "频繁裁员，不稳定"),
    ("画饼", "老板天天画饼，承诺不兑现"),
    ("社保", "不交或少交社保公积金"),
    ("克扣", "以各种理由克扣工资"),
]


def generate_id(prefix: str, name: str) -> str:
    """Generate a unique ID."""
    return f"{prefix}_{hashlib.md5(name.encode()).hexdigest()[:12]}"


def generate_companies(count: int = 50) -> list[Company]:
    """Generate sample companies."""
    companies = []
    
    for i, name in enumerate(COMPANY_NAMES[:count]):
        # Determine company size
        if name in ["腾讯", "阿里巴巴", "字节跳动", "美团", "京东", "百度"]:
            size = CompanySize.GIANT
            employees = random.randint(50000, 100000)
            risk_level = RiskLevel.LOW
            risk_score = random.uniform(0.1, 0.3)
        elif name in ["网易", "拼多多", "小米"]:
            size = CompanySize.GIANT
            employees = random.randint(10000, 50000)
            risk_level = RiskLevel.LOW
            risk_score = random.uniform(0.1, 0.3)
        elif "科技" in name or "智能" in name:
            size = random.choice([CompanySize.MEDIUM, CompanySize.LARGE])
            employees = random.randint(500, 5000)
            risk_level = RiskLevel.MEDIUM
            risk_score = random.uniform(0.3, 0.6)
        else:
            size = random.choice([CompanySize.SMALL, CompanySize.MEDIUM])
            employees = random.randint(100, 1000)
            risk_level = RiskLevel.MEDIUM
            risk_score = random.uniform(0.3, 0.6)
        
        # Random funding stage
        funding_stages = [FundingStage.ANGEL, FundingStage.A, FundingStage.B, 
                         FundingStage.C, FundingStage.D, FundingStage.IPO]
        funding_stage = random.choice(funding_stages)
        
        # Random industry
        industry = random.choice(INDUSTRIES)
        
        # Random location
        location = random.choice(CITIES)
        
        # Random salary
        avg_salary = random.randint(15000, 50000)
        
        # Random rating
        avg_rating = round(random.uniform(2.5, 4.8), 1)
        
        company = Company(
            id=generate_id("comp", name),
            name=name,
            industry=industry,
            size=size,
            founded=random.randint(2000, 2020),
            headquarters=location,
            employees=employees,
            avg_salary=avg_salary,
            avg_rating=avg_rating,
            review_count=random.randint(10, 500),
            funding_stage=funding_stage,
            risk_level=risk_level,
            risk_score=risk_score,
            tags=[industry, size.value],
            source="sample"
        )
        companies.append(company)
    
    return companies


def generate_jobs(companies: list[Company], count_per_company: int = 5) -> list[Job]:
    """Generate sample jobs for companies."""
    jobs = []
    
    for company in companies:
        # Generate 3-8 jobs per company
        job_count = random.randint(3, min(count_per_company, 8))
        
        for _ in range(job_count):
            # Random job category and title
            category = random.choice(list(JOB_TITLES.keys()))
            title = random.choice(JOB_TITLES[category])
            
            # Random salary based on company
            base_salary = company.avg_salary or 20000
            salary_min = int(base_salary * random.uniform(0.6, 0.9))
            salary_max = int(base_salary * random.uniform(1.1, 1.5))
            
            # Random requirements
            experience_years = random.choice([0, 1, 2, 3, 5])
            education = random.choice(["大专", "本科", "硕士"])
            
            # Skills
            skills = SKILLS.get(title, ["沟通能力", "团队协作"])
            
            # Location
            location = company.headquarters or random.choice(CITIES)
            
            job = Job(
                id=generate_id("job", f"{company.name}_{title}_{random.randint(1000, 9999)}"),
                title=title,
                company_id=company.id,
                company_name=company.name,
                department=category,
                job_type=JobType.FULL_TIME,
                location=location,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_months=random.choice([12, 13, 14, 15, 16]),
                experience_years=experience_years,
                education=education,
                skills=skills[:random.randint(3, 6)],
                benefits=["五险一金", "年终奖", "带薪年假"],
                source="sample",
                is_active=True,
                posted_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            jobs.append(job)
    
    return jobs


def generate_reviews(companies: list[Company], count_per_company: int = 5) -> list[Review]:
    """Generate sample reviews for companies."""
    reviews = []
    
    pros_templates = [
        "公司平台大，能学到很多东西",
        "薪资福利不错，年终奖丰厚",
        "团队氛围好，同事nice",
        "工作生活平衡，不强制加班",
        "技术栈新，能接触前沿技术",
        "晋升机制清晰，有成长空间",
        "公司发展稳定，前景看好",
        "弹性工作时间，不打卡"
    ]
    
    cons_templates = [
        "加班较多，项目紧的时候很累",
        "部分组内卷严重",
        "晋升竞争激烈",
        "流程繁琐，决策慢",
        "薪资涨幅有限",
        "部分领导管理能力差",
        "工作内容重复性高",
        "公司文化一般"
    ]
    
    for company in companies:
        # Generate 3-10 reviews per company
        review_count = random.randint(3, min(count_per_company, 10))
        
        for i in range(review_count):
            # Random ratings
            overall = round(random.uniform(2.0, 5.0), 1)
            salary = round(random.uniform(2.0, 5.0), 1)
            work_life = round(random.uniform(1.0, 5.0), 1)
            management = round(random.uniform(2.0, 5.0), 1)
            
            # Pitfall tags (more likely for bad companies)
            pitfall_tags = []
            if company.risk_level in [RiskLevel.HIGH, RiskLevel.BLACKLIST]:
                if random.random() > 0.3:
                    pitfall_tags.append(random.choice(["996", "PUA", "欠薪", "内卷"]))
            elif company.risk_level == RiskLevel.MEDIUM:
                if random.random() > 0.7:
                    pitfall_tags.append(random.choice(["996", "内卷"]))
            
            review = Review(
                id=generate_id("rev", f"{company.name}_{i}"),
                company_id=company.id,
                overall_rating=overall,
                salary_rating=salary,
                work_life_rating=work_life,
                management_rating=management,
                title=random.choice(["还不错", "一般", "不推荐", "推荐", "看组"]),
                pros=random.choice(pros_templates),
                cons=random.choice(cons_templates),
                reviewer_title=random.choice(["工程师", "产品经理", "设计师", "运营"]),
                reviewer_tenure=random.choice(["不到1年", "1-2年", "2-3年", "3-5年"]),
                is_current_employee=random.random() > 0.3,
                source="sample",
                posted_at=datetime.now() - timedelta(days=random.randint(0, 365)),
                pitfall_tags=pitfall_tags
            )
            reviews.append(review)
    
    return reviews


def generate_pitfalls(companies: list[Company]) -> list[Pitfall]:
    """Generate sample pitfalls for high-risk companies."""
    pitfalls = []
    
    for company in companies:
        if company.risk_level in [RiskLevel.HIGH, RiskLevel.BLACKLIST]:
            # Generate 1-3 pitfalls
            pitfall_count = random.randint(1, 3)
            selected_types = random.sample(PITFALL_TYPES, pitfall_count)
            
            for pitfall_type, description in selected_types:
                pitfall = Pitfall(
                    id=generate_id("pit", f"{company.name}_{pitfall_type}"),
                    company_id=company.id,
                    pitfall_type=pitfall_type,
                    severity=random.randint(3, 5),
                    description=description,
                    report_count=random.randint(5, 50),
                    confirmed_count=random.randint(2, 20),
                    source="sample",
                    is_verified=True
                )
                pitfalls.append(pitfall)
    
    return pitfalls


def generate_all_data(
    company_count: int = 50,
    jobs_per_company: int = 5,
    reviews_per_company: int = 5
) -> tuple[list[Company], list[Job], list[Review], list[Pitfall]]:
    """Generate all sample data."""
    logger.info(f"Generating {company_count} companies...")
    companies = generate_companies(company_count)
    
    logger.info(f"Generating jobs ({jobs_per_company} per company)...")
    jobs = generate_jobs(companies, jobs_per_company)
    
    logger.info(f"Generating reviews ({reviews_per_company} per company)...")
    reviews = generate_reviews(companies, reviews_per_company)
    
    logger.info("Generating pitfalls...")
    pitfalls = generate_pitfalls(companies)
    
    logger.info(f"Generated: {len(companies)} companies, {len(jobs)} jobs, "
                f"{len(reviews)} reviews, {len(pitfalls)} pitfalls")
    
    return companies, jobs, reviews, pitfalls
