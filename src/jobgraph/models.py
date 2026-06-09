"""JobGraph data models - 求职图谱数据模型

聚焦场景: 求职 - 帮你找到靠谱的工作，避开坑人的公司
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# ============================================================
# 枚举类型
# ============================================================


class CompanySize(Enum):
    """公司规模分类."""

    STARTUP = "startup"  # <50人
    SMALL = "small"  # 50-150人
    MEDIUM = "medium"  # 150-500人
    LARGE = "large"  # 500-2000人
    ENTERPRISE = "enterprise"  # 2000-10000人
    GIANT = "giant"  # >10000人


class RiskLevel(Enum):
    """公司风险等级."""

    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    BLACKLIST = "blacklist"  # 黑名单


class JobType(Enum):
    """岗位类型."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"
    REMOTE = "remote"


class FundingStage(Enum):
    """融资阶段."""

    ANGEL = "angel"  # 天使轮
    PRE_A = "pre_a"  # Pre-A轮
    A = "a"  # A轮
    B = "b"  # B轮
    C = "c"  # C轮
    D = "d"  # D轮
    E_PLUS = "e_plus"  # E轮及以上
    PRE_IPO = "pre_ipo"  # Pre-IPO
    IPO = "ipo"  # 已上市
    UNKNOWN = "unknown"


# ============================================================
# 公司模型
# ============================================================


@dataclass
class Company:
    """公司实体."""

    id: str
    name: str
    name_en: str | None = None

    # 基本信息
    industry: str | None = None
    size: CompanySize | None = None
    founded: int | None = None
    headquarters: str | None = None
    website: str | None = None
    description: str | None = None

    # 融资信息
    funding_stage: FundingStage | None = None
    funding_amount: str | None = None
    valuation: float | None = None  # 估值(万元)
    is_listed: bool = False
    stock_code: str | None = None

    # 员工信息
    employees: int | None = None
    avg_salary: float | None = None  # 平均月薪

    # 评价信息
    avg_rating: float | None = None  # 平均评分(1-5)
    review_count: int = 0

    # 风险信息
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: float = 0.5  # 0-1, 越高越危险
    risk_factors: list[str] = field(default_factory=list)

    # 标签
    tags: list[str] = field(default_factory=list)

    # 元数据
    source: str | None = None
    source_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
    department: str | None = None
    job_type: JobType = JobType.FULL_TIME
    location: str | None = None
    is_remote: bool = False

    # 薪资信息
    salary_min: float | None = None
    salary_max: float | None = None
    salary_months: int = 12  # 几薪
    salary_description: str | None = None

    # 要求
    experience_years: int | None = None
    education: str | None = None
    skills: list[str] = field(default_factory=list)

    # 描述
    description: str | None = None
    requirements: str | None = None
    benefits: list[str] = field(default_factory=list)

    # 元数据
    source: str | None = None
    source_url: str | None = None
    posted_at: datetime | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
    salary_rating: float | None = None
    work_life_rating: float | None = None
    management_rating: float | None = None
    culture_rating: float | None = None
    growth_rating: float | None = None

    # 内容
    title: str | None = None
    pros: str | None = None  # 优点
    cons: str | None = None  # 缺点
    advice_to_management: str | None = None

    # 评价者信息
    reviewer_title: str | None = None  # 评价者职位
    reviewer_tenure: str | None = None  # 在职时长
    is_current_employee: bool = True

    # 坑点标签
    pitfall_tags: list[str] = field(default_factory=list)  # 欠薪/PUA/996/...

    # 元数据
    source: str | None = None
    posted_at: datetime | None = None


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
    description: str | None = None
    evidence: str | None = None  # 证据来源

    # 统计
    report_count: int = 1  # 举报次数
    confirmed_count: int = 0  # 确认次数

    # 元数据
    source: str | None = None
    reported_at: datetime | None = None
    is_verified: bool = False


# ============================================================
# 用户模型
# ============================================================


@dataclass
class UserProfile:
    """用户档案."""

    id: str

    # 基本信息
    name: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    experience_years: int = 0
    education: str | None = None
    location: str | None = None

    # 技能
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)

    # 求职意向
    desired_titles: list[str] = field(default_factory=list)
    desired_locations: list[str] = field(default_factory=list)
    desired_salary_min: float | None = None
    desired_salary_max: float | None = None
    desired_company_size: CompanySize | None = None

    # 偏好
    prefer_remote: bool = False
    prefer_work_life_balance: bool = True
    prefer_growth: bool = True

    # 简历
    resume_text: str | None = None

    # 元数据
    source: str | None = None  # 来源：resume/smart/manual
    device_id: str | None = None  # 设备标识
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
    recommendation: str | None = None

    created_at: datetime | None = None


# ============================================================
# 薪资数据模型
# ============================================================


@dataclass
class ResumeProfile:
    """简历解析结果（不含隐私信息）"""

    id: str

    # 基本信息（不含隐私）
    current_title: str | None = None
    experience_years: int = 0
    education: str | None = None

    # 技能
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)

    # 工作经历
    work_history: list[dict] = field(default_factory=list)

    # 项目经验
    projects: list[dict] = field(default_factory=list)

    # 求职意向（可选）
    desired_titles: list[str] = field(default_factory=list)
    desired_locations: list[str] = field(default_factory=list)
    desired_salary_min: float | None = None
    desired_salary_max: float | None = None

    # 元数据
    source_file: str | None = None
    parsed_at: datetime | None = None
    privacy_filtered: bool = True


@dataclass
class SalaryData:
    """薪资数据."""

    company_id: str | None = None
    job_title: str | None = None
    industry: str | None = None
    location: str | None = None

    # 薪资分位数
    p10: float | None = None
    p25: float | None = None
    p50: float | None = None  # 中位数
    p75: float | None = None
    p90: float | None = None
    mean: float | None = None

    # 样本信息
    sample_count: int = 0
    updated_at: datetime | None = None
