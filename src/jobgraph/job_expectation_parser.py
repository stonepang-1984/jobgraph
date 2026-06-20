"""职位期望解析模块

支持从文本和图片中提取职位期望信息
"""

import re


class JobExpectationParser:
    """职位期望解析器"""

    # 常见职位关键词
    JOB_TITLES = [
        "工程师",
        "开发",
        "架构师",
        "分析师",
        "经理",
        "总监",
        "主管",
        "专员",
        "前端",
        "后端",
        "全栈",
        "数据",
        "算法",
        "测试",
        "运维",
        "产品",
        "项目",
        "运营",
        "设计",
        "市场",
        "销售",
        "HR",
        "人事",
        "财务",
        "法务",
        "Python",
        "Java",
        "Go",
        "C++",
        "JavaScript",
        "TypeScript",
        "React",
        "Vue",
        "Node",
        "Android",
        "iOS",
    ]

    # 技能关键词
    SKILLS = [
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "Go",
        "Golang",
        "Rust",
        "C",
        "C++",
        "React",
        "Vue",
        "Angular",
        "Node.js",
        "Express",
        "Django",
        "Flask",
        "FastAPI",
        "Spring",
        "MySQL",
        "PostgreSQL",
        "MongoDB",
        "Redis",
        "Elasticsearch",
        "Docker",
        "Kubernetes",
        "K8s",
        "AWS",
        "Azure",
        "GCP",
        "机器学习",
        "深度学习",
        "NLP",
        "计算机视觉",
        "TensorFlow",
        "PyTorch",
        "微服务",
        "分布式",
        "高并发",
        "Linux",
        "Git",
        "CI/CD",
        "HTML",
        "CSS",
        "Webpack",
        "Vite",
    ]

    # 学历关键词
    EDUCATION_LEVELS = {
        "博士": ["博士", "Ph.D", "PhD"],
        "硕士": ["硕士", "研究生", "Master", "MBA"],
        "本科": ["本科", "学士", "Bachelor", "大学"],
        "大专": ["大专", "专科", "高职"],
    }

    def parse_text(self, text: str) -> dict:
        """从文本中解析职位期望和个人简介

        Args:
            text: 输入文本

        Returns:
            解析结果
        """
        if not text or not text.strip():
            return {}

        result = {
            "job_title": self._extract_job_title(text),
            "skills": self._extract_skills(text),
            "experience_years": self._extract_experience_years(text),
            "education": self._extract_education(text),
            "location": self._extract_location(text),
            "salary_min": self._extract_salary_min(text),
            "salary_max": self._extract_salary_max(text),
            "summary": self._extract_summary(text),
        }

        # 过滤空值
        return {k: v for k, v in result.items() if v is not None and v != [] and v != 0}

    def _extract_job_title(self, text: str) -> str | None:
        """提取职位名称"""
        # 模式1：明确写明"期望职位"或"求职意向"
        patterns = [
            r"(?:期望|求职|应聘|目标)\s*(?:职位|岗位|方向)[：:]\s*(.+?)(?:\n|$|，|,)",
            r"(?:职位|岗位)[：:]\s*(.+?)(?:\n|$|，|,)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        # 模式2：包含职位关键词
        for keyword in self.JOB_TITLES:
            if keyword in text:
                # 找到包含关键词的句子
                sentences = re.split(r"[，。；\n]", text)
                for sentence in sentences:
                    if keyword in sentence and len(sentence) < 20:
                        return sentence.strip()

        return None

    def _extract_skills(self, text: str) -> list[str]:
        """提取技能"""
        found_skills = []

        for skill in self.SKILLS:
            # 中文技能直接匹配
            if any("\u4e00" <= c <= "\u9fff" for c in skill):
                if skill in text:
                    found_skills.append(skill)
            else:
                # 英文技能使用单词边界匹配
                pattern = r"\b" + re.escape(skill.lower()) + r"\b"
                if re.search(pattern, text.lower()):
                    found_skills.append(skill)

        return list(set(found_skills))

    def _extract_experience_years(self, text: str) -> int | None:
        """提取工作年限"""
        patterns = [
            r"(\d+)\s*(?:年|years?)\s*(?:以上)?(?:工作)?(?:经验|经历)",
            r"(?:经验|经历)[：:]\s*(\d+)\s*年",
            r"(\d+)\+?\s*(?:years?\s*)?(?:of\s+)?experience",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _extract_education(self, text: str) -> str | None:
        """提取学历"""
        for level, keywords in self.EDUCATION_LEVELS.items():
            for keyword in keywords:
                if keyword in text:
                    return level

        return None

    def _extract_location(self, text: str) -> str | None:
        """提取地点"""
        # 模式1：明确写明"地点"或"城市"
        patterns = [
            r"(?:地点|城市|工作地|期望地)[：:]\s*(.+?)(?:\n|$|，|,)",
            r"(?:在|去)\s*([^\s，。]{2,6})\s*(?:工作|发展)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        # 模式2：常见城市名
        cities = [
            "北京",
            "上海",
            "广州",
            "深圳",
            "杭州",
            "成都",
            "武汉",
            "南京",
            "西安",
            "苏州",
            "天津",
            "重庆",
            "长沙",
            "郑州",
            "青岛",
            "厦门",
        ]

        for city in cities:
            if city in text:
                return city

        return None

    def _extract_salary_min(self, text: str) -> float | None:
        """提取最低薪资"""
        # 模式：XX-XXK 或 XXK-XXK
        pattern = r"(\d+)\s*[-~至到]\s*(\d+)\s*[kK千]"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1)) * 1000

        # 模式：XXK以上
        pattern = r"(\d+)\s*[kK千]\s*以上"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1)) * 1000

        return None

    def _extract_salary_max(self, text: str) -> float | None:
        """提取最高薪资"""
        # 模式：XX-XXK
        pattern = r"(\d+)\s*[-~至到]\s*(\d+)\s*[kK千]"
        match = re.search(pattern, text)
        if match:
            return float(match.group(2)) * 1000

        return None

    def _extract_summary(self, text: str) -> str | None:
        """提取个人简介

        支持的格式：
        - 个人简介：xxx
        - 自我介绍：xxx
        - 关于我：xxx
        - 个人介绍：xxx
        - 直接的描述文本（如果没有明确标签，取前200字）

        Args:
            text: 输入文本

        Returns:
            个人简介
        """
        # 模式1：明确写明"个人简介"或"自我介绍"
        patterns = [
            r"(?:个人简介|自我介绍|关于我|个人介绍|自我评价|个人描述)[：:]\s*(.+?)(?:\n\n|\Z)",
            r"(?:简介|介绍|描述)[：:]\s*(.+?)(?:\n\n|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                summary = match.group(1).strip()
                # 限制长度
                if len(summary) > 500:
                    summary = summary[:500] + "..."
                return summary

        # 模式2：如果没有明确标签，检查是否包含描述性文本
        # 查找包含"我"或"擅长"或"熟悉"的段落
        sentences = re.split(r"\n", text)
        summary_parts = []

        for sentence in sentences:
            sentence = sentence.strip()
            # 跳过空行和包含特定关键词的行（如职位、技能等）
            if not sentence:
                continue
            if any(kw in sentence for kw in ["期望职位", "技能：", "薪资", "地点", "学历"]):
                continue
            # 包含描述性关键词的行
            if any(kw in sentence for kw in ["我", "擅长", "熟悉", "精通", "工作经验", "项目经验", "负责", "参与"]):
                summary_parts.append(sentence)

        if summary_parts:
            summary = " ".join(summary_parts)
            if len(summary) > 500:
                summary = summary[:500] + "..."
            return summary

        return None

    def parse_image_text(self, ocr_text: str) -> dict:
        """从 OCR 识别的文本中解析职位期望

        Args:
            ocr_text: OCR 识别的文本

        Returns:
            解析结果
        """
        # 清理 OCR 文本
        cleaned_text = ocr_text.replace("\n", " ").replace("  ", " ")
        return self.parse_text(cleaned_text)


# 全局实例
job_expectation_parser = JobExpectationParser()
