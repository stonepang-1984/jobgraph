"""JobGraph data models - 求职图谱数据模型

聚焦场景: 求职 - 帮你找到靠谱的工作，避开坑人的公司
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class CompanySize(Enum):
    """公司规模分类."""
    STARTUP = "startup"          # <50人
    SMALL = "small"              # 50-150人
    MEDIUM = "medium"            # 150-500人
    LARGE = "large"              # 500-2000人
    ENTERPRISE = "enterprise"    # 2000-10000人
    GIANT = "giant"              # >10000人


class RiskLevel(Enum):
    """公司风险等级."""
    LOW = "low"                  # 低风险
    MEDIUM = "medium"            # 中风险
    HIGH = "high"                # 高风险
    BLACKLIST = "blacklist"      # 黑名单


class JobType(Enum):
    """岗位类型."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"
    REMOTE = "remote"


class FundingStage(Enum):
    """融资阶段."""
    ANGEL = "angel"              # 天使轮
    PRE_A = "pre_a"              # Pre-A轮
    A = "a"                      # A轮
    B = "b"                      # B轮
    C = "c"                      # C轮
    D = "d"                      # D轮
    E_PLUS = "e_plus"            # E轮及以上
    PRE_IPO = "pre_ipo"          # Pre-IPO
    IPO = "ipo"                  # 已上市
    UNKNOWN = "unknown"


# ============================================================
# 公司模型
# ============================================================

@dataclass
class Company:
    """公司实体."""
    id: str
    name: str
    name_en: Optional[str] = None
    
    # 基本信息
    industry: Optional[str] = None
    size: Optional[CompanySize] = None
    founded: Optional[int] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    
    # 融资信息
    funding_stage: Optional[FundingStage] = None
    funding_amount: Optional[str] = None
    valuation: Optional[float] = None  # 估值(万元)
    is_listed: bool = False
    stock_code: Optional[str] = None
    
    # 员工信息
    employees: Optional[int] = None
    avg_salary: Optional[float] = None  # 平均月薪
    
    # 评价信息
    avg_rating: Optional[float] = None  # 平均评分(1-5)
    review_count: int = 0
    
    # 风险信息
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: float = 0.5  # 0-1, 越高越危险
    risk_factors: list[str] = field(default_factory=list)
    
    # 标签
    tags: list[str] = field(default_factory=list)
    
    # 元数据
    source: Optional[str] = None
    source_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# 岗位模型
# ============================================================

@dataclass
class Job:
    """岗位实体."""
    id: str
    title: str
    company_id: str
    company_name: str
    
    # 岗位信息
    department: Optional[str] = None
    job_type: JobType = JobType.FULL_TIME
    location: Optional[str] = None
    is_remote: bool = False
    
    # 薪资信息
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_months: int = 12  # 几薪
    salary_description: Optional[str] = None
    
    # 要求
    experience_years: Optional[int] = None
    education: Optional[str] = None
    skills: list[str] = field(default_factory=list)
    
    # 描述
    description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: list[str] = field(default_factory=list)
    
    # 元数据
    source: Optional[str] = None
    source_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# 评价模型
# ============================================================

@dataclass
class Review:
    """员工评价实体."""
    id: str
    company_id: str
    
    # 评分 (1-5)
    overall_rating: float = 0.0
    salary_rating: Optional[float] = None
    work_life_rating: Optional[float] = None
    management_rating: Optional[float] = None
    culture_rating: Optional[float] = None
    growth_rating: Optional[float] = None
    
    # 内容
    title: Optional[str] = None
    pros: Optional[str] = None  # 优点
    cons: Optional[str] = None  # 缺点
    advice_to_management: Optional[str] = None
    
    # 评价者信息
    reviewer_title: Optional[str] = None  # 评价者职位
    reviewer_tenure: Optional[str] = None  # 在职时长
    is_current_employee: bool = True
    
    # 坑点标签
    pitfall_tags: list[str] = field(default_factory=list)  # 欠薪/PUA/996/...
    
    # 元数据
    source: Optional[str] = None
    posted_at: Optional[datetime] = None


# ============================================================
# 坑点模型
# ============================================================

@dataclass
class Pitfall:
    """公司坑点实体."""
    id: str
    company_id: str
    
    # 坑点信息
    pitfall_type: str  # 欠薪/PUA/996/内卷/裁员/...
    severity: int = 3  # 1-5, 越高越严重
    description: Optional[str] = None
    evidence: Optional[str] = None  # 证据来源
    
    # 统计
    report_count: int = 1  # 举报次数
    confirmed_count: int = 0  # 确认次数
    
    # 元数据
    source: Optional[str] = None
    reported_at: Optional[datetime] = None
    is_verified: bool = False


# ============================================================
# 用户模型
# ============================================================

@dataclass
class UserProfile:
    """用户档案."""
    id: str
    
    # 基本信息
    name: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    experience_years: int = 0
    education: Optional[str] = None
    location: Optional[str] = None
    
    # 技能
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    
    # 求职意向
    desired_titles: list[str] = field(default_factory=list)
    desired_locations: list[str] = field(default_factory=list)
    desired_salary_min: Optional[float] = None
    desired_salary_max: Optional[float] = None
    desired_company_size: Optional[CompanySize] = None
    
    # 偏好
    prefer_remote: bool = False
    prefer_work_life_balance: bool = True
    prefer_growth: bool = True
    
    # 简历
    resume_text: Optional[str] = None
    
    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# 匹配结果模型
# ============================================================

@dataclass
class MatchResult:
    """岗位匹配结果."""
    user_id: str
    job_id: str
    company_id: str
    
    # 匹配分数
    overall_score: float = 0.0  # 0-1
    skill_match_score: float = 0.0
    salary_match_score: float = 0.0
    location_match_score: float = 0.0
    experience_match_score: float = 0.0
    preference_match_score: float = 0.0
    
    # 风险评估
    risk_score: float = 0.0  # 0-1, 越高越危险
    risk_factors: list[str] = field(default_factory=list)
    
    # 匹配详情
    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    
    # 推荐理由
    recommendation: Optional[str] = None
    
    created_at: Optional[datetime] = None


# ============================================================
# 薪资数据模型
# ============================================================

@dataclass
class SalaryData:
    """薪资数据."""
    company_id: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    
    # 薪资分位数
    p10: Optional[float] = None
    p25: Optional[float] = None
    p50: Optional[float] = None  # 中位数
    p75: Optional[float] = None
    p90: Optional[float] = None
    mean: Optional[float] = None
    
    # 样本信息
    sample_count: int = 0
    updated_at: Optional[datetime] = None
