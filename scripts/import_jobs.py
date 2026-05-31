"""Import sample job data for JobGraph."""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.jobgraph.models import (
    Company, Job, Review, Pitfall, UserProfile,
    CompanySize, RiskLevel, JobType
)
from src.jobgraph.graph_manager import job_manager


# ============================================================
# Sample Companies
# ============================================================

COMPANIES = [
    # 互联网大厂
    Company(
        id="comp_tencent", name="腾讯", name_en="Tencent",
        industry="互联网", size=CompanySize.GIANT,
        founded=1998, headquarters="深圳",
        is_listed=True, stock_code="0700.HK",
        funding_stage="上市", risk_level=RiskLevel.LOW,
        risk_score=0.2, avg_salary=35000, avg_rating=3.8,
        tags=["大厂", "社交", "游戏", "稳定"]
    ),
    Company(
        id="comp_alibaba", name="阿里巴巴", name_en="Alibaba",
        industry="互联网", size=CompanySize.GIANT,
        founded=1999, headquarters="杭州",
        is_listed=True, stock_code="BABA",
        funding_stage="上市", risk_level=RiskLevel.LOW,
        risk_score=0.3, avg_salary=38000, avg_rating=3.5,
        tags=["大厂", "电商", "云计算"]
    ),
    Company(
        id="comp_bytedance", name="字节跳动", name_en="ByteDance",
        industry="互联网", size=CompanySize.GIANT,
        founded=2012, headquarters="北京",
        funding_stage="未上市", risk_level=RiskLevel.LOW,
        risk_score=0.25, avg_salary=42000, avg_rating=3.6,
        tags=["大厂", "短视频", "高薪", "加班多"]
    ),
    Company(
        id="comp_meituan", name="美团", name_en="Meituan",
        industry="互联网", size=CompanySize.GIANT,
        founded=2010, headquarters="北京",
        is_listed=True, stock_code="3690.HK",
        funding_stage="上市", risk_level=RiskLevel.LOW,
        risk_score=0.3, avg_salary=32000, avg_rating=3.4,
        tags=["大厂", "本地生活", "外卖"]
    ),
    
    # 中型公司
    Company(
        id="comp_xiaohongshu", name="小红书", name_en="Xiaohongshu",
        industry="互联网", size=CompanySize.LARGE,
        founded=2013, headquarters="上海",
        funding_stage="D轮", risk_level=RiskLevel.MEDIUM,
        risk_score=0.4, avg_salary=30000, avg_rating=3.7,
        tags=["社区", "电商", "年轻"]
    ),
    Company(
        id="comp_didi", name="滴滴出行", name_en="Didi",
        industry="互联网", size=CompanySize.GIANT,
        founded=2012, headquarters="北京",
        is_listed=True, stock_code="DIDI",
        funding_stage="上市", risk_level=RiskLevel.MEDIUM,
        risk_score=0.5, avg_salary=35000, avg_rating=3.2,
        tags=["出行", "监管风险", "裁员"]
    ),
    
    # 创业公司 (有风险)
    Company(
        id="comp_startup_a", name="某创业公司A", name_en="Startup A",
        industry="SaaS", size=CompanySize.SMALL,
        founded=2022, headquarters="北京",
        funding_stage="A轮", risk_level=RiskLevel.HIGH,
        risk_score=0.7, avg_salary=25000, avg_rating=2.8,
        tags=["创业", "不稳定", "加班多"]
    ),
    Company(
        id="comp_blacklist_a", name="黑心公司A", name_en="Bad Company A",
        industry="电商", size=CompanySize.MEDIUM,
        founded=2018, headquarters="深圳",
        funding_stage="B轮", risk_level=RiskLevel.BLACKLIST,
        risk_score=0.95, avg_salary=15000, avg_rating=1.5,
        risk_factors=["欠薪", "PUA", "996", "裁员"],
        tags=["黑名单", "避坑"]
    ),
]


# ============================================================
# Sample Jobs
# ============================================================

JOBS = [
    # 腾讯岗位
    Job(
        id="job_tencent_1", title="高级后端工程师",
        company_id="comp_tencent", company_name="腾讯",
        department="微信事业部", job_type=JobType.FULL_TIME,
        location="广州", salary_min=30000, salary_max=50000,
        salary_months=16, experience_years=3,
        education="本科", skills=["Java", "Go", "微服务", "分布式"],
        benefits=["年终奖", "股票", "五险一金", "弹性工作"],
        source="boss", is_active=True
    ),
    Job(
        id="job_tencent_2", title="前端开发工程师",
        company_id="comp_tencent", company_name="腾讯",
        department="QQ事业部", job_type=JobType.FULL_TIME,
        location="深圳", salary_min=25000, salary_max=40000,
        salary_months=16, experience_years=2,
        education="本科", skills=["React", "TypeScript", "Node.js"],
        benefits=["年终奖", "股票", "五险一金"],
        source="boss", is_active=True
    ),
    
    # 字节岗位
    Job(
        id="job_bytedance_1", title="算法工程师",
        company_id="comp_bytedance", company_name="字节跳动",
        department="抖音", job_type=JobType.FULL_TIME,
        location="北京", salary_min=35000, salary_max=60000,
        salary_months=15, experience_years=2,
        education="硕士", skills=["Python", "PyTorch", "推荐系统", "NLP"],
        benefits=["年终奖", "期权", "免费三餐", "租房补贴"],
        source="boss", is_active=True
    ),
    Job(
        id="job_bytedance_2", title="产品经理",
        company_id="comp_bytedance", company_name="字节跳动",
        department="飞书", job_type=JobType.FULL_TIME,
        location="北京", salary_min=25000, salary_max=45000,
        salary_months=15, experience_years=3,
        education="本科", skills=["产品设计", "数据分析", "用户研究"],
        benefits=["年终奖", "期权", "免费三餐"],
        source="boss", is_active=True
    ),
    
    # 黑心公司岗位 (避坑示例)
    Job(
        id="job_bad_1", title="全栈开发工程师",
        company_id="comp_blacklist_a", company_name="黑心公司A",
        job_type=JobType.FULL_TIME,
        location="深圳", salary_min=8000, salary_max=15000,
        salary_months=12, experience_years=1,
        education="大专", skills=["JavaScript", "PHP", "MySQL"],
        description="能接受加班，抗压能力强",
        source="拉勾", is_active=True
    ),
]


# ============================================================
# Sample Reviews
# ============================================================

REVIEWS = [
    # 腾讯评价
    Review(
        id="rev_tencent_1", company_id="comp_tencent",
        overall_rating=4.0, salary_rating=4.5,
        work_life_rating=3.5, management_rating=4.0,
        title="大厂光环，薪资不错",
        pros="薪资福利好，平台大，能学到东西",
        cons="加班较多，部分组内卷严重",
        reviewer_title="高级工程师", reviewer_tenure="3年",
        source="脉脉", posted_at=datetime(2025, 6, 1)
    ),
    Review(
        id="rev_tencent_2", company_id="comp_tencent",
        overall_rating=3.5, salary_rating=4.0,
        work_life_rating=3.0, management_rating=3.5,
        title="看组，有的组很卷",
        pros="福利好，年终奖丰厚",
        cons="部分组996，晋升困难",
        reviewer_title="产品经理", reviewer_tenure="2年",
        source="脉脉", posted_at=datetime(2025, 5, 15)
    ),
    
    # 字节评价
    Review(
        id="rev_bytedance_1", company_id="comp_bytedance",
        overall_rating=4.0, salary_rating=5.0,
        work_life_rating=2.5, management_rating=3.5,
        title="钱多但是真的累",
        pros="薪资业界顶尖，免费三餐，成长快",
        cons="大小周，工作强度大，压力大",
        reviewer_title="算法工程师", reviewer_tenure="1年",
        source="脉脉", posted_at=datetime(2025, 5, 20),
        pitfall_tags=["996", "内卷"]
    ),
    
    # 黑心公司评价
    Review(
        id="rev_bad_1", company_id="comp_blacklist_a",
        overall_rating=1.0, salary_rating=1.0,
        work_life_rating=1.0, management_rating=1.0,
        title="千万别来，欠薪三个月",
        pros="没有优点",
        cons="老板PUA，欠薪，996，不交社保",
        reviewer_title="开发工程师", reviewer_tenure="6个月",
        source="脉脉", posted_at=datetime(2025, 4, 1),
        pitfall_tags=["欠薪", "PUA", "996", "不交社保"]
    ),
    Review(
        id="rev_bad_2", company_id="comp_blacklist_a",
        overall_rating=1.5, salary_rating=1.0,
        work_life_rating=1.0, management_rating=1.0,
        title="黑心公司，避坑",
        pros="没有任何优点",
        cons="拖欠工资，老板天天画饼，加班没有加班费",
        reviewer_title="运营", reviewer_tenure="3个月",
        source="脉脉", posted_at=datetime(2025, 3, 15),
        pitfall_tags=["欠薪", "PUA", "画饼"]
    ),
]


# ============================================================
# Sample Pitfalls
# ============================================================

PITFALLS = [
    Pitfall(
        id="pit_bad_1", company_id="comp_blacklist_a",
        pitfall_type="欠薪", severity=5,
        description="多次被员工举报拖欠工资，最长拖欠3个月",
        evidence="脉脉多条评价，劳动仲裁记录",
        report_count=15, confirmed_count=10,
        source="脉脉", is_verified=True
    ),
    Pitfall(
        id="pit_bad_2", company_id="comp_blacklist_a",
        pitfall_type="PUA", severity=4,
        description="老板经常PUA员工，贬低工作成果",
        evidence="多名员工匿名举报",
        report_count=8, confirmed_count=5,
        source="脉脉", is_verified=True
    ),
    Pitfall(
        id="pit_bad_3", company_id="comp_blacklist_a",
        pitfall_type="996", severity=4,
        description="强制996，没有加班费",
        evidence="员工评价",
        report_count=12, confirmed_count=8,
        source="脉脉", is_verified=True
    ),
]


# ============================================================
# Import Function
# ============================================================

def import_data():
    """Import all sample data."""
    logger.info("=" * 60)
    logger.info("Importing Sample Job Data")
    logger.info("=" * 60)

    # Import companies
    logger.info(f"Importing {len(COMPANIES)} companies...")
    for company in COMPANIES:
        try:
            job_manager.create_company(company)
        except Exception as e:
            logger.error(f"Failed to import company {company.name}: {e}")

    # Import jobs
    logger.info(f"Importing {len(JOBS)} jobs...")
    for job in JOBS:
        try:
            job_manager.create_job(job)
        except Exception as e:
            logger.error(f"Failed to import job {job.title}: {e}")

    # Import reviews
    logger.info(f"Importing {len(REVIEWS)} reviews...")
    for review in REVIEWS:
        try:
            job_manager.create_review(review)
        except Exception as e:
            logger.error(f"Failed to import review: {e}")

    # Import pitfalls
    logger.info(f"Importing {len(PITFALLS)} pitfalls...")
    for pitfall in PITFALLS:
        try:
            job_manager.create_pitfall(pitfall)
        except Exception as e:
            logger.error(f"Failed to import pitfall: {e}")

    # Print statistics
    stats = job_manager.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Companies: {stats.get('companies', 0)}")
    logger.info(f"Jobs: {stats.get('jobs', 0)}")
    logger.info(f"Reviews: {stats.get('reviews', 0)}")
    logger.info(f"Pitfalls: {stats.get('pitfalls', 0)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import_data()
