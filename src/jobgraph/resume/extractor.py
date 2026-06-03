"""简历信息提取器

从简历文本中提取结构化信息：
- 技能
- 工作年限
- 教育背景
- 工作经历
- 项目经验
- 证书
"""

import re
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field


class ExtractedProfile(BaseModel):
    """提取的简历信息"""
    current_title: str | None = Field(None, description="当前/最近职位")
    experience_years: int = Field(0, description="工作年限")
    education: str | None = Field(None, description="最高学历")
    skills: list[str] = Field(default_factory=list, description="技能列表")
    certifications: list[str] = Field(default_factory=list, description="证书列表")
    work_history: list[dict] = Field(default_factory=list, description="工作经历")
    projects: list[dict] = Field(default_factory=list, description="项目经验")


# 常见技能关键词库
SKILL_KEYWORDS = {
    # 编程语言
    "python", "java", "javascript", "typescript", "go", "golang", "rust", "c", "c++",
    "c#", "php", "ruby", "swift", "kotlin", "scala", "r", "matlab", "perl",
    # 前端
    "react", "vue", "angular", "next.js", "nuxt", "svelte", "html", "css", "scss",
    "tailwind", "bootstrap", "jquery", "webpack", "vite", "rollup",
    # 后端
    "node.js", "express", "django", "flask", "fastapi", "spring", "springboot",
    "laravel", "rails", "gin", "echo", "fiber",
    # 数据库
    "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "oracle", "sqlserver",
    "sqlite", "cassandra", "neo4j", "dynamodb", "tidb", "oceanbase",
    # 云和DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "jenkins", "gitlab",
    "github", "ci/cd", "terraform", "ansible", "prometheus", "grafana",
    # AI/ML
    "机器学习", "深度学习", "自然语言处理", "nlp", "计算机视觉", "cv",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "大模型", "llm", "gpt", "transformer", "bert", "aigc",
    # 大数据
    "hadoop", "spark", "flink", "kafka", "hive", "presto", "airflow",
    "数据仓库", "etl", "数据治理", "数据湖",
    # 移动开发
    "android", "ios", "react native", "flutter", "uniapp", "小程序",
    # 其他技术
    "微服务", "分布式", "高并发", "高可用", "架构设计", "系统设计",
    "linux", "nginx", "git", "svn", "restful", "graphql", "grpc",
    "消息队列", "mq", "rabbitmq", "rocketmq",
}


class ResumeExtractor:
    """简历信息提取器"""

    def __init__(self, use_llm: bool = True):
        """
        Args:
            use_llm: 是否使用 LLM 提取（需要配置 OpenAI API）
        """
        self.use_llm = use_llm
        self._llm = None

    def extract(self, text: str) -> ExtractedProfile:
        """从简历文本提取结构化信息

        Args:
            text: 简历文本内容

        Returns:
            提取的结构化信息
        """
        if not text or not text.strip():
            return ExtractedProfile()

        logger.info("开始提取简历信息...")

        # 尝试 LLM 提取
        if self.use_llm:
            try:
                return self._extract_with_llm(text)
            except Exception as e:
                logger.warning(f"LLM 提取失败，降级到规则提取: {e}")

        # 规则提取
        return self._extract_with_rules(text)

    def _extract_with_llm(self, text: str) -> ExtractedProfile:
        """使用 LLM 提取信息"""
        try:
            from langchain_openai import ChatOpenAI
            from config.settings import settings

            if self._llm is None:
                self._llm = ChatOpenAI(
                    model=settings.llm.openai_model,
                    api_key=settings.llm.openai_api_key,
                    base_url=settings.llm.openai_api_base,
                    temperature=0,
                )

            prompt = """你是一个专业的简历解析专家。请从以下简历文本中提取结构化信息。

注意：
- 不要提取姓名、手机号、邮箱、身份证号等隐私信息
- 技能列表要标准化（使用常见名称）
- 工作年限从工作经历中推算
- 学历取最高学历

请以JSON格式返回结果，包含以下字段：
- current_title: 当前/最近职位
- experience_years: 工作年限（整数）
- education: 最高学历（大专/本科/硕士/博士）
- skills: 技能列表
- certifications: 证书列表
- work_history: 工作经历列表，每项包含 company, title, period, description
- projects: 项目经验列表，每项包含 name, role, period, description

简历文本：
{text}"""

            from langchain_core.prompts import ChatPromptTemplate

            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个专业的简历解析专家。"),
                ("human", prompt),
            ])

            chain = chat_prompt | self._llm.with_structured_output(ExtractedProfile)
            result = chain.invoke({"text": text[:4000]})  # 限制长度避免 token 超限

            logger.info(f"LLM 提取完成，识别到 {len(result.skills)} 个技能")
            return result

        except ImportError:
            logger.warning("未安装 langchain_openai，使用规则提取")
            return self._extract_with_rules(text)
        except Exception as e:
            logger.error(f"LLM 提取出错: {e}")
            return self._extract_with_rules(text)

    def _extract_with_rules(self, text: str) -> ExtractedProfile:
        """使用规则提取信息"""
        logger.info("使用规则模式提取简历信息...")

        # 提取技能
        skills = self._extract_skills(text)

        # 提取工作年限
        experience_years = self._extract_experience_years(text)

        # 提取学历
        education = self._extract_education(text)

        # 提取当前职位
        current_title = self._extract_current_title(text)

        # 提取证书
        certifications = self._extract_certifications(text)

        return ExtractedProfile(
            current_title=current_title,
            experience_years=experience_years,
            education=education,
            skills=skills,
            certifications=certifications,
            work_history=[],
            projects=[],
        )

    def _extract_skills(self, text: str) -> list[str]:
        """提取技能"""
        text_lower = text.lower()
        found_skills = []

        for skill in SKILL_KEYWORDS:
            # 使用单词边界匹配
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                # 保留原始大小写
                found_skills.append(skill)

        return sorted(list(set(found_skills)))

    def _extract_experience_years(self, text: str) -> int:
        """提取工作年限"""
        # 模式1：直接写明 "X年经验"
        patterns = [
            r'(\d+)\s*年(?:以上)?(?:工作)?(?:经验|经历)',
            r'工作(?:经验|经历)[：:]\s*(\d+)\s*年',
            r'(\d+)\+?\s*years?\s*(?:of\s+)?experience',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        # 模式2：从工作经历推算
        year_pattern = r'(\d{4})\s*[-.至到]\s*(?:(\d{4})|至今|现在|present)'
        matches = re.findall(year_pattern, text)

        if matches:
            years = []
            for match in matches:
                start = int(match[0])
                end = int(match[1]) if match[1] else datetime.now().year
                years.append((start, end))

            if years:
                min_year = min(y[0] for y in years)
                max_year = max(y[1] for y in years)
                return max(0, max_year - min_year)

        return 0

    def _extract_education(self, text: str) -> str | None:
        """提取最高学历"""
        education_levels = [
            ("博士", ["博士", "Ph.D", "PhD", "doctorate"]),
            ("硕士", ["硕士", "研究生", "Master", "MBA", "EMBA"]),
            ("本科", ["本科", "学士", "Bachelor", "大学", "学院"]),
            ("大专", ["大专", "专科", "高职", "College"]),
        ]

        text_upper = text.upper()

        for level, keywords in education_levels:
            for keyword in keywords:
                if keyword.upper() in text_upper:
                    return level

        return None

    def _extract_current_title(self, text: str) -> str | None:
        """提取当前/最近职位"""
        # 常见职位关键词
        title_patterns = [
            r'(?:高级|资深|首席|主任)?(?:软件|前端|后端|全栈|数据|算法|测试|运维|产品|项目|运营|设计|市场|销售)(?:工程师|开发|架构师|分析师|经理|总监|主管|专员)',
            r'(?:Senior|Junior|Lead|Staff|Principal|Chief)?\s*(?:Software|Frontend|Backend|Full Stack|Data|Algorithm|DevOps|Product|Project|Design|Marketing)\s*(?:Engineer|Developer|Architect|Analyst|Manager|Director)',
            r'(?:技术负责人|CTO|CEO|COO|CFO|VP|技术总监|研发总监)',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def _extract_certifications(self, text: str) -> list[str]:
        """提取证书"""
        cert_patterns = [
            r'(?:PMP|ACP|CSM|AWS|Azure|GCP|CKA|CKS|RHCE|RHCA|CCNA|CCNP|CCIE|OCP|OCM)',
            r'(?:注册会计师|CPA|CFA|FRM|ACCA)',
            r'(?:软件设计师|系统架构师|数据库工程师|网络工程师)',
        ]

        certifications = []
        text_upper = text.upper()

        for pattern in cert_patterns:
            matches = re.findall(pattern, text_upper, re.IGNORECASE)
            certifications.extend(matches)

        return list(set(certifications))


# 全局实例
resume_extractor = ResumeExtractor(use_llm=True)
