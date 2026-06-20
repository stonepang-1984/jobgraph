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
    "python",
    "java",
    "javascript",
    "typescript",
    "go",
    "golang",
    "rust",
    "c",
    "c++",
    "c#",
    "php",
    "ruby",
    "swift",
    "kotlin",
    "scala",
    "r",
    "matlab",
    "perl",
    # 前端
    "react",
    "vue",
    "angular",
    "next.js",
    "nuxt",
    "svelte",
    "html",
    "css",
    "scss",
    "tailwind",
    "bootstrap",
    "jquery",
    "webpack",
    "vite",
    "rollup",
    # 后端
    "node.js",
    "express",
    "django",
    "flask",
    "fastapi",
    "spring",
    "springboot",
    "laravel",
    "rails",
    "gin",
    "echo",
    "fiber",
    # 数据库
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "elasticsearch",
    "oracle",
    "sqlserver",
    "sqlite",
    "cassandra",
    "neo4j",
    "dynamodb",
    "tidb",
    "oceanbase",
    # 云和DevOps
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "k8s",
    "jenkins",
    "gitlab",
    "github",
    "ci/cd",
    "terraform",
    "ansible",
    "prometheus",
    "grafana",
    # AI/ML
    "机器学习",
    "深度学习",
    "自然语言处理",
    "nlp",
    "计算机视觉",
    "cv",
    "tensorflow",
    "pytorch",
    "keras",
    "scikit-learn",
    "pandas",
    "numpy",
    "大模型",
    "llm",
    "gpt",
    "transformer",
    "bert",
    "aigc",
    # 大数据
    "hadoop",
    "spark",
    "flink",
    "kafka",
    "hive",
    "presto",
    "airflow",
    "数据仓库",
    "etl",
    "数据治理",
    "数据湖",
    # 移动开发
    "android",
    "ios",
    "react native",
    "flutter",
    "uniapp",
    "小程序",
    # 网络与通信
    "tcp/ip",
    "tcp",
    "ip",
    "udp",
    "http",
    "https",
    "dns",
    "dhcp",
    "arp",
    "交换机",
    "路由器",
    "网络编程",
    "网络协议",
    "协议栈",
    "snmp",
    "ssh",
    "telnet",
    "ftp",
    "smtp",
    "socket",
    "vlan",
    "vpn",
    "nat",
    "acl",
    "qos",
    "stp",
    "rstp",
    "rip",
    "ospf",
    "bgp",
    "mpls",
    "lldp",
    "ntp",
    # 嵌入式与系统
    "嵌入式",
    "嵌入式linux",
    "嵌入式系统",
    "arm",
    "mips",
    "risc-v",
    "linux内核",
    "内核开发",
    "驱动开发",
    "bootloader",
    "ucos",
    "freertos",
    "rtos",
    "vxworks",
    "交叉编译",
    "交叉编译器",
    "gcc",
    "gdb",
    "makefile",
    "shell脚本",
    "bash",
    "awk",
    "sed",
    "busybox",
    "rootfs",
    "文件系统",
    "syslog",
    "日志系统",
    # Web与服务器
    "web服务器",
    "nginx",
    "apache",
    "tomcat",
    "cgi",
    "web界面",
    "web开发",
    "tcp服务器",
    "socket编程",
    # 数据库与存储
    "底层数据库",
    "数据存储",
    "数据同步",
    # 认证与安全
    "用户认证",
    "安全认证",
    "radius",
    "tacacs",
    "ldap",
    "ssl",
    "tls",
    "加密",
    "解密",
    # 开发工具
    "gcc",
    "gdb",
    "vim",
    "emacs",
    "vscode",
    "git",
    "svn",
    "cvs",
    "svn",
    "tcpdump",
    "wireshark",
    "抓包",
    # 其他技术
    "微服务",
    "分布式",
    "高并发",
    "高可用",
    "架构设计",
    "系统设计",
    "linux",
    "nginx",
    "git",
    "svn",
    "restful",
    "graphql",
    "grpc",
    "消息队列",
    "mq",
    "rabbitmq",
    "rocketmq",
    "通信协议",
    "板间通信",
    "tipc",
    "交换芯片",
    "芯片驱动",
    "驱动适配",
    "软件升级",
    "热升级",
    "在线升级",
    "cli",
    "命令行",
    "命令行界面",
}

# 技能名称标准化映射（小写 -> 标准名称）
SKILL_STANDARD_MAP = {
    # 编程语言
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "c": "C",
    "c++": "C++",
    "c#": "C#",
    "php": "PHP",
    "ruby": "Ruby",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "r": "R",
    # 前端
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "next.js": "Next.js",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "html": "HTML",
    "css": "CSS",
    "scss": "SCSS",
    "tailwind": "Tailwind",
    "bootstrap": "Bootstrap",
    "jquery": "jQuery",
    "webpack": "Webpack",
    "vite": "Vite",
    # 后端
    "node.js": "Node.js",
    "express": "Express",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "springboot": "Spring Boot",
    "laravel": "Laravel",
    "rails": "Rails",
    "gin": "Gin",
    # 数据库
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "oracle": "Oracle",
    "sqlserver": "SQL Server",
    "sqlite": "SQLite",
    "cassandra": "Cassandra",
    "neo4j": "Neo4j",
    "dynamodb": "DynamoDB",
    "tidb": "TiDB",
    "oceanbase": "OceanBase",
    # 云和DevOps
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "jenkins": "Jenkins",
    "gitlab": "GitLab",
    "github": "GitHub",
    "ci/cd": "CI/CD",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    # AI/ML
    "nlp": "NLP",
    "cv": "CV",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "keras": "Keras",
    "scikit-learn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "llm": "LLM",
    "gpt": "GPT",
    "transformer": "Transformer",
    "bert": "BERT",
    "aigc": "AIGC",
    # 大数据
    "hadoop": "Hadoop",
    "spark": "Spark",
    "flink": "Flink",
    "kafka": "Kafka",
    "hive": "Hive",
    "presto": "Presto",
    "airflow": "Airflow",
    # 移动开发
    "android": "Android",
    "ios": "iOS",
    "react native": "React Native",
    "flutter": "Flutter",
    # 网络与通信
    "tcp/ip": "TCP/IP",
    "tcp": "TCP",
    "ip": "IP",
    "udp": "UDP",
    "http": "HTTP",
    "https": "HTTPS",
    "dns": "DNS",
    "dhcp": "DHCP",
    "arp": "ARP",
    "snmp": "SNMP",
    "ssh": "SSH",
    "telnet": "Telnet",
    "ftp": "FTP",
    "smtp": "SMTP",
    "socket": "Socket",
    "vlan": "VLAN",
    "vpn": "VPN",
    "nat": "NAT",
    "acl": "ACL",
    "qos": "QoS",
    "stp": "STP",
    "rstp": "RSTP",
    "rip": "RIP",
    "ospf": "OSPF",
    "bgp": "BGP",
    "mpls": "MPLS",
    "lldp": "LLDP",
    "ntp": "NTP",
    # 嵌入式与系统
    "嵌入式linux": "嵌入式Linux",
    "arm": "ARM",
    "mips": "MIPS",
    "risc-v": "RISC-V",
    "rtos": "RTOS",
    "vxworks": "VxWorks",
    "gcc": "GCC",
    "gdb": "GDB",
    "makefile": "Makefile",
    "bash": "Bash",
    "awk": "Awk",
    "sed": "Sed",
    "busybox": "BusyBox",
    "rootfs": "RootFS",
    "syslog": "Syslog",
    # Web与服务器
    "nginx": "Nginx",
    "apache": "Apache",
    "tomcat": "Tomcat",
    "cgi": "CGI",
    # 认证与安全
    "radius": "RADIUS",
    "tacacs": "TACACS",
    "ldap": "LDAP",
    "ssl": "SSL",
    "tls": "TLS",
    # 开发工具
    "vim": "Vim",
    "emacs": "Emacs",
    "vscode": "VSCode",
    "git": "Git",
    "svn": "SVN",
    "cvs": "CVS",
    "tcpdump": "Tcpdump",
    "wireshark": "Wireshark",
    # 其他技术
    "restful": "RESTful",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "mq": "MQ",
    "rabbitmq": "RabbitMQ",
    "rocketmq": "RocketMQ",
    "tipc": "TIPC",
    "cli": "CLI",
    # 中文技能标准化
    "linux": "Linux",
    "shell脚本": "Shell脚本",
    "web服务器": "Web服务器",
    "web界面": "Web界面",
    "web开发": "Web开发",
    "tcp服务器": "TCP服务器",
    "socket编程": "Socket编程",
    "交叉编译器": "交叉编译器",
    "日志系统": "日志系统",
    "文件系统": "文件系统",
    "命令行": "命令行",
    "命令行界面": "命令行界面",
    "在线升级": "在线升级",
    "热升级": "热升级",
    # 嵌入式和网络相关技能
    "交换机": "交换机",
    "交换芯片": "交换芯片",
    "协议栈": "协议栈",
    "安全认证": "安全认证",
    "嵌入式": "嵌入式",
    "底层数据库": "底层数据库",
    "数据同步": "数据同步",
    "数据存储": "数据存储",
    "板间通信": "板间通信",
    "网络编程": "网络编程",
    "芯片驱动": "芯片驱动",
    "软件升级": "软件升级",
    "通信协议": "通信协议",
    "驱动适配": "驱动适配",
    "路由器": "路由器",
    "网络协议": "网络协议",
    "用户认证": "用户认证",
    "内核开发": "内核开发",
    "驱动开发": "驱动开发",
    "交叉编译": "交叉编译",
}


class ResumeExtractor:
    """简历信息提取器"""

    def __init__(self, use_llm: bool = True, llm_timeout: int = 600):
        """
        Args:
            use_llm: 是否使用 LLM 提取（需要配置 OpenAI API）
            llm_timeout: LLM 调用超时时间（秒），默认 10 分钟
        """
        self.use_llm = use_llm
        self.llm_timeout = llm_timeout
        self._llm = None
        self._llm_available = None  # 缓存 LLM 可用性

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
        if self.use_llm and self._check_llm_available():
            try:
                return self._extract_with_llm(text)
            except Exception as e:
                logger.warning(f"LLM 提取失败，降级到规则提取: {e}")

        # 规则提取
        return self._extract_with_rules(text)

    def _check_llm_available(self) -> bool:
        """检查 LLM 是否可用"""
        if self._llm_available is not None:
            return self._llm_available

        try:
            from config.settings import settings

            # 检查 OpenAI API Key
            api_key = settings.llm.openai_api_key
            if api_key and api_key != "sk-your-openai-api-key" and len(api_key) > 10:
                self._llm_available = True
                logger.info("使用 OpenAI API 模式")
                return True

            # 检查 Ollama 配置
            ollama_url = settings.llm.ollama_base_url
            if ollama_url:
                # 尝试连接 Ollama
                try:
                    import requests

                    response = requests.get(f"{ollama_url}/api/tags", timeout=3)
                    if response.status_code == 200:
                        self._llm_available = True
                        logger.info(f"使用 Ollama 模式: {ollama_url}")
                        return True
                except Exception:
                    pass

            logger.info("LLM 未配置或不可用，使用规则提取模式")
            self._llm_available = False
            return False
        except Exception as e:
            logger.warning(f"检查 LLM 配置失败: {e}")
            self._llm_available = False
            return False

    def _extract_with_llm(self, text: str) -> ExtractedProfile:
        """使用 LLM 提取信息"""
        try:
            from langchain_openai import ChatOpenAI

            from config.settings import settings

            if self._llm is None:
                # 根据配置选择 LLM
                api_key = settings.llm.openai_api_key

                # 检查是否使用 Ollama
                if api_key == "sk-your-openai-api-key" or not api_key or len(api_key) < 10:
                    # 使用 Ollama（通过 OpenAI 兼容接口）
                    ollama_url = settings.llm.ollama_base_url
                    ollama_model = settings.llm.ollama_model

                    # 创建带超时配置的 http_client
                    import httpx

                    http_client = httpx.Client(timeout=httpx.Timeout(self.llm_timeout, connect=10.0))

                    self._llm = ChatOpenAI(
                        model=ollama_model,
                        api_key="ollama",  # Ollama 不需要真实的 API Key
                        base_url=f"{ollama_url}/v1",
                        temperature=0,
                        request_timeout=self.llm_timeout,
                        http_client=http_client,
                    )
                    logger.info(f"使用 Ollama: {ollama_url}, 模型: {ollama_model}")
                else:
                    # 使用 OpenAI API
                    self._llm = ChatOpenAI(
                        model=settings.llm.openai_model,
                        api_key=api_key,
                        base_url=settings.llm.openai_api_base,
                        temperature=0,
                        request_timeout=self.llm_timeout,
                    )
                    logger.info(f"使用 OpenAI API: {settings.llm.openai_model}")

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

            chat_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "你是一个专业的简历解析专家。"),
                    ("human", prompt),
                ]
            )

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
            skill_lower = skill.lower()

            # 判断是否为中文技能
            is_chinese = any("\u4e00" <= c <= "\u9fff" for c in skill)

            if is_chinese:
                # 中文技能直接匹配
                if skill_lower in text_lower:
                    # 使用标准化名称
                    standard_name = SKILL_STANDARD_MAP.get(skill_lower, skill)
                    found_skills.append(standard_name)
            else:
                # 英文技能使用单词边界匹配
                pattern = r"\b" + re.escape(skill_lower) + r"\b"
                if re.search(pattern, text_lower):
                    # 使用标准化名称
                    standard_name = SKILL_STANDARD_MAP.get(skill_lower, skill)
                    found_skills.append(standard_name)

        return sorted(list(set(found_skills)))

    def _extract_experience_years(self, text: str) -> int:
        """提取工作年限"""
        # 模式1：直接写明 "X年经验"
        patterns = [
            r"(\d+)\s*年(?:以上)?(?:工作)?(?:经验|经历)",
            r"工作(?:经验|经历)[：:]\s*(\d+)\s*年",
            r"(\d+)\+?\s*years?\s*(?:of\s+)?experience",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        # 模式2：从工作经历推算（支持多种日期格式）
        # 支持: 2008/7-2013/2, 2008-2013, 2008年-2013年, 2008.7-2013.2
        year_patterns = [
            r"(\d{4})\s*[/年.]\s*\d{1,2}\s*[-.至到~]\s*(?:(\d{4})\s*[/年.]\s*\d{1,2}|至今|现在|present)",
            r"(\d{4})\s*[-.至到~]\s*(?:(\d{4})|至今|现在|present)",
        ]

        all_years = []
        for year_pattern in year_patterns:
            matches = re.findall(year_pattern, text, re.IGNORECASE)
            for match in matches:
                start = int(match[0])
                end = int(match[1]) if match[1] else datetime.now().year
                # 过滤掉不合理的年份
                if 1990 <= start <= datetime.now().year and start <= end:
                    all_years.append((start, end))

        if all_years:
            min_year = min(y[0] for y in all_years)
            max_year = max(y[1] for y in all_years)
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
            r"(?:高级|资深|首席|主任)?(?:软件|前端|后端|全栈|数据|算法|测试|运维|产品|项目|运营|设计|市场|销售)(?:工程师|开发|架构师|分析师|经理|总监|主管|专员)",
            r"(?:Senior|Junior|Lead|Staff|Principal|Chief)?\s*(?:Software|Frontend|Backend|Full Stack|Data|Algorithm|DevOps|Product|Project|Design|Marketing)\s*(?:Engineer|Developer|Architect|Analyst|Manager|Director)",
            r"(?:技术负责人|CTO|CEO|COO|CFO|VP|技术总监|研发总监)",
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def _extract_certifications(self, text: str) -> list[str]:
        """提取证书"""
        cert_patterns = [
            r"(?:PMP|ACP|CSM|AWS|Azure|GCP|CKA|CKS|RHCE|RHCA|CCNA|CCNP|CCIE|OCP|OCM)",
            r"(?:注册会计师|CPA|CFA|FRM|ACCA)",
            r"(?:软件设计师|系统架构师|数据库工程师|网络工程师)",
        ]

        certifications = []
        text_upper = text.upper()

        for pattern in cert_patterns:
            matches = re.findall(pattern, text_upper, re.IGNORECASE)
            certifications.extend(matches)

        return list(set(certifications))


# 全局实例
resume_extractor = ResumeExtractor(use_llm=True)
