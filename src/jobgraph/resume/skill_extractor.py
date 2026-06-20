"""技能提取器

从职位描述、简历文本中提取技能关键词
"""

import re

from loguru import logger

# 常见技能关键词库（与 extractor.py 共享）
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
    "spring boot",
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
    "hbase",
    "clickhouse",
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
    "推荐系统",
    "推荐算法",
    "目标检测",
    "图像分割",
    "人脸识别",
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
    "数据平台",
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
    "wifi",
    "蓝牙",
    "bluetooth",
    "zigbee",
    "mqtt",
    "coap",
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
    # Web与服务器
    "web服务器",
    "nginx",
    "apache",
    "tomcat",
    "cgi",
    "web界面",
    "web开发",
    "全栈",
    # 微服务与架构
    "微服务",
    "分布式",
    "高并发",
    "高可用",
    "架构设计",
    "系统设计",
    "微前端",
    "monorepo",
    # 中间件
    "消息队列",
    "mq",
    "rabbitmq",
    "rocketmq",
    "redis",
    "memcached",
    "zookeeper",
    "etcd",
    # 工具
    "git",
    "svn",
    "cvs",
    "linux",
    "unix",
    "tcpdump",
    "wireshark",
    "抓包",
    # 协议
    "grpc",
    "restful",
    "graphql",
    "rpc",
    # 其他
    "数据结构",
    "算法",
    "设计模式",
    "项目管理",
    "敏捷开发",
    "scrum",
    "产品设计",
    "数据分析",
    "用户研究",
    "figma",
    "sketch",
    "photoshop",
    "sql",
    "nosql",
    "数据库",
    "性能优化",
    "代码审查",
    "技术方案",
}

# 技能标准化映射
SKILL_ALIASES = {
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "spring": "Spring",
    "node": "Node.js",
    "nodejs": "Node.js",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "react.js": "React",
    "reactjs": "React",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "k8s": "Kubernetes",
    "ci/cd": "CI/CD",
    "golang": "Go",
    "cpp": "C++",
    "csharp": "C#",
    "嵌入式linux": "嵌入式Linux",
    "linux内核": "Linux内核",
    "tcp/ip": "TCP/IP",
    "mqtt": "MQTT",
    "grpc": "gRPC",
    "restful": "RESTful",
    "graphql": "GraphQL",
}


def normalize_skill(skill: str) -> str:
    """标准化技能名称"""
    skill_lower = skill.lower().strip()
    return SKILL_ALIASES.get(skill_lower, skill)


def extract_skills_from_text(text: str) -> list[str]:
    """从文本中提取技能关键词

    Args:
        text: 输入文本（职位描述、简历等）

    Returns:
        提取的技能列表（标准化后）
    """
    if not text:
        return []

    text_lower = text.lower()
    found_skills = set()

    for skill in SKILL_KEYWORDS:
        skill_lower = skill.lower()

        # 判断是否为中文技能
        is_chinese = any("\u4e00" <= c <= "\u9fff" for c in skill)

        if is_chinese:
            # 中文技能直接匹配
            if skill_lower in text_lower:
                found_skills.add(normalize_skill(skill))
        else:
            # 英文技能使用单词边界匹配
            pattern = r"\b" + re.escape(skill_lower) + r"\b"
            if re.search(pattern, text_lower):
                found_skills.add(normalize_skill(skill))

    return sorted(list(found_skills))


def merge_skills(base_skills: list[str], extracted_skills: list[str]) -> list[str]:
    """合并技能列表

    Args:
        base_skills: 基础技能列表
        extracted_skills: 提取的技能列表

    Returns:
        合并后的技能列表（去重、标准化）
    """
    # 标准化基础技能
    normalized_base = set()
    for skill in base_skills:
        normalized_base.add(normalize_skill(skill))

    # 合并
    all_skills = normalized_base | set(extracted_skills)

    return sorted(list(all_skills))


def enrich_job_skills(job_data: dict) -> dict:
    """丰富职位技能列表

    从职位描述中提取技能，补充到 skills 列表中

    Args:
        job_data: 职位数据（包含 description, requirements, skills）

    Returns:
        丰富后的职位数据
    """
    # 合并描述文本
    description = job_data.get("description", "") or ""
    requirements = job_data.get("requirements", "") or ""
    full_text = f"{description} {requirements}"

    # 提取技能
    extracted_skills = extract_skills_from_text(full_text)

    # 合并技能
    base_skills = job_data.get("skills", []) or []
    merged_skills = merge_skills(base_skills, extracted_skills)

    # 更新数据
    job_data["skills"] = merged_skills

    if len(merged_skills) > len(base_skills):
        logger.debug(f"技能丰富: {len(base_skills)} -> {len(merged_skills)}")

    return job_data


# 全局实例
skill_extractor = type(
    "SkillExtractor",
    (),
    {
        "extract_from_text": staticmethod(extract_skills_from_text),
        "merge_skills": staticmethod(merge_skills),
        "enrich_job_skills": staticmethod(enrich_job_skills),
    },
)()
