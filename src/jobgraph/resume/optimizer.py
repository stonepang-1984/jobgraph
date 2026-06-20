"""简历优化建议模块

当匹配度不高时，分析原因并提供简历修改建议
在用户同意后执行简历修改，形成闭环优化
"""

from dataclasses import dataclass, field

from loguru import logger


@dataclass
class MatchGap:
    """匹配差距分析"""

    gap_type: str  # skill, experience, education, location, salary
    description: str  # 差距描述
    severity: int  # 1-5, 越高越严重
    suggestions: list[str] = field(default_factory=list)  # 改进建议


@dataclass
class ResumeOptimizationSuggestion:
    """简历优化建议"""

    overall_score: float  # 当前匹配度 0-1
    target_score: float  # 目标匹配度 0-1
    gaps: list[MatchGap] = field(default_factory=list)  # 匹配差距
    skill_suggestions: list[str] = field(default_factory=list)  # 技能建议
    experience_suggestions: list[str] = field(default_factory=list)  # 经验建议
    general_tips: list[str] = field(default_factory=list)  # 通用建议

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "target_score": self.target_score,
            "gaps": [
                {
                    "gap_type": g.gap_type,
                    "description": g.description,
                    "severity": g.severity,
                    "suggestions": g.suggestions,
                }
                for g in self.gaps
            ],
            "skill_suggestions": self.skill_suggestions,
            "experience_suggestions": self.experience_suggestions,
            "general_tips": self.general_tips,
        }


@dataclass
class ResumeModification:
    """简历修改操作"""

    field_name: str  # 修改的字段
    action: str  # add, remove, modify
    old_value: str | None = None
    new_value: str | None = None
    reason: str = ""


class ResumeOptimizer:
    """简历优化器"""

    # 匹配度阈值：低于此值需要优化
    LOW_MATCH_THRESHOLD = 0.5
    TARGET_MATCH_SCORE = 0.7

    def analyze_and_suggest(
        self,
        current_profile: dict,
        match_result: dict,
        target_job: dict | None = None,
    ) -> ResumeOptimizationSuggestion:
        """分析匹配结果并生成优化建议

        Args:
            current_profile: 当前简历信息
            match_result: 匹配结果
            target_job: 目标岗位信息（可选）

        Returns:
            优化建议
        """
        logger.info("开始分析匹配差距...")

        overall_score = match_result.get("total_score", 0)
        gaps = []

        # 1. 分析技能差距
        skill_gap = self._analyze_skill_gap(
            current_profile.get("skills", []),
            match_result.get("matching_skills", []),
            match_result.get("missing_skills", []),
            target_job.get("skills", []) if target_job else [],
        )
        if skill_gap:
            gaps.append(skill_gap)

        # 2. 分析经验差距
        exp_gap = self._analyze_experience_gap(
            current_profile.get("experience_years", 0),
            target_job.get("experience_years") if target_job else None,
            match_result.get("experience_match_score", 0),
        )
        if exp_gap:
            gaps.append(exp_gap)

        # 3. 分析教育差距
        edu_gap = self._analyze_education_gap(
            current_profile.get("education"),
            target_job.get("education") if target_job else None,
        )
        if edu_gap:
            gaps.append(edu_gap)

        # 4. 生成通用建议
        general_tips = self._generate_general_tips(overall_score, gaps)

        # 5. 生成技能建议
        skill_suggestions = self._generate_skill_suggestions(
            current_profile.get("skills", []),
            match_result.get("missing_skills", []),
            target_job,
        )

        # 6. 生成经验建议
        exp_suggestions = self._generate_experience_suggestions(
            current_profile.get("work_history", []),
            current_profile.get("projects", []),
            target_job,
        )

        return ResumeOptimizationSuggestion(
            overall_score=overall_score,
            target_score=self.TARGET_MATCH_SCORE,
            gaps=gaps,
            skill_suggestions=skill_suggestions,
            experience_suggestions=exp_suggestions,
            general_tips=general_tips,
        )

    def _analyze_skill_gap(
        self,
        current_skills: list[str],
        matching_skills: list[str],
        missing_skills: list[str],
        required_skills: list[str],
    ) -> MatchGap | None:
        """分析技能差距"""
        if not missing_skills and not required_skills:
            return None

        # 计算技能匹配率
        total_required = len(required_skills) if required_skills else len(matching_skills) + len(missing_skills)
        matched = len(matching_skills)
        match_rate = matched / total_required if total_required > 0 else 0

        if match_rate >= 0.8:
            return None

        severity = 5 if match_rate < 0.3 else 4 if match_rate < 0.5 else 3

        suggestions = []
        if missing_skills:
            suggestions.append(f"建议补充以下技能: {', '.join(missing_skills[:5])}")
        if match_rate < 0.5:
            suggestions.append("可以通过在线课程、项目实践快速提升技能")

        return MatchGap(
            gap_type="skill",
            description=f"技能匹配率 {match_rate:.0%}，缺少 {len(missing_skills)} 项技能",
            severity=severity,
            suggestions=suggestions,
        )

    def _analyze_experience_gap(
        self,
        current_years: int,
        required_years: int | None,
        exp_match_score: float,
    ) -> MatchGap | None:
        """分析经验差距"""
        if required_years is None:
            return None

        gap_years = required_years - current_years
        if gap_years <= 0:
            return None

        severity = 4 if gap_years > 3 else 3 if gap_years > 1 else 2

        suggestions = []
        if gap_years > 0:
            suggestions.append(f"岗位要求 {required_years} 年经验，您目前有 {current_years} 年")
            suggestions.append("可以突出项目经验中的相关部分")
            if gap_years <= 2:
                suggestions.append("可以强调学习能力和项目成果来弥补经验差距")

        return MatchGap(
            gap_type="experience",
            description=f"经验差距 {gap_years} 年",
            severity=severity,
            suggestions=suggestions,
        )

    def _analyze_education_gap(
        self,
        current_edu: str | None,
        required_edu: str | None,
    ) -> MatchGap | None:
        """分析教育差距"""
        if not required_edu or not current_edu:
            return None

        edu_levels = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}
        current_level = edu_levels.get(current_edu, 0)
        required_level = edu_levels.get(required_edu, 0)

        if current_level >= required_level:
            return None

        return MatchGap(
            gap_type="education",
            description=f"学历要求 {required_edu}，您目前是 {current_edu}",
            severity=2,
            suggestions=["可以通过工作经验和技能来弥补学历差距"],
        )

    def _generate_skill_suggestions(
        self,
        current_skills: list[str],
        missing_skills: list[str],
        target_job: dict | None,
    ) -> list[str]:
        """生成技能相关建议"""
        suggestions = []

        if missing_skills:
            suggestions.append(f"🔑 **关键技能补充**: {', '.join(missing_skills[:5])}")

            # 根据技能类型给出学习建议
            tech_skills = [s for s in missing_skills if self._is_tech_skill(s)]
            if tech_skills:
                suggestions.append(f"💻 **技术技能**: 可通过 LeetCode、GitHub 项目练习 {', '.join(tech_skills[:3])}")

            soft_skills = [s for s in missing_skills if self._is_soft_skill(s)]
            if soft_skills:
                suggestions.append(f"🤝 **软技能**: 可在简历中通过项目经历体现 {', '.join(soft_skills[:3])}")

        # 技能展示建议
        if len(current_skills) < 5:
            suggestions.append("📝 **技能展示**: 建议补充更多相关技能，至少 5-10 项")

        return suggestions

    def _generate_experience_suggestions(
        self,
        work_history: list[dict],
        projects: list[dict],
        target_job: dict | None,
    ) -> list[str]:
        """生成经验相关建议"""
        suggestions = []

        if not work_history:
            suggestions.append("📋 **工作经历**: 建议补充详细的工作经历，包括公司、职位、职责")
        elif len(work_history) < 2:
            suggestions.append("📋 **工作经历**: 建议补充更多工作经历，展示职业发展轨迹")

        if not projects:
            suggestions.append("🚀 **项目经验**: 建议补充 2-3 个重点项目，突出技术难点和成果")

        # 针对目标岗位的建议
        if target_job:
            job_title = target_job.get("title", "")
            if job_title:
                suggestions.append(f"🎯 **针对性优化**: 建议突出与「{job_title}」相关的项目经验")

        # 成果量化建议
        suggestions.append("📊 **成果量化**: 用数字量化工作成果，如「提升性能 30%」「节省成本 50 万」")

        return suggestions

    def _generate_general_tips(
        self,
        overall_score: float,
        gaps: list[MatchGap],
    ) -> list[str]:
        """生成通用建议"""
        tips = []

        if overall_score < 0.3:
            tips.append("⚠️ 匹配度较低，建议重点补充技能和项目经验")
        elif overall_score < 0.5:
            tips.append("💡 匹配度中等，针对性优化可显著提升")
        else:
            tips.append("✅ 匹配度不错，微调即可进一步提升")

        # 根据差距类型给出建议
        gap_types = [g.gap_type for g in gaps]
        if "skill" in gap_types:
            tips.append("🎯 技能是最关键的匹配因素，优先补充相关技能")
        if "experience" in gap_types:
            tips.append("📅 突出项目经验中的相关部分，可以弥补年限差距")

        tips.append("📝 简历格式清晰，重点突出，便于 HR 快速了解")
        tips.append("🔒 优化过程完全在本地进行，您的简历数据不会上传")

        return tips

    def _is_tech_skill(self, skill: str) -> bool:
        """判断是否为技术技能"""
        tech_keywords = [
            "python",
            "java",
            "javascript",
            "go",
            "rust",
            "c++",
            "react",
            "vue",
            "node",
            "django",
            "flask",
            "spring",
            "mysql",
            "redis",
            "mongodb",
            "docker",
            "kubernetes",
            "机器学习",
            "深度学习",
            "算法",
            "数据结构",
        ]
        return any(kw in skill.lower() for kw in tech_keywords)

    def _is_soft_skill(self, skill: str) -> bool:
        """判断是否为软技能"""
        soft_keywords = [
            "沟通",
            "协作",
            "领导",
            "管理",
            "团队",
            "解决问题",
            "学习能力",
            "抗压",
            "责任心",
        ]
        return any(kw in skill.lower() for kw in soft_keywords)

    def generate_modifications(
        self,
        current_profile: dict,
        suggestion: ResumeOptimizationSuggestion,
    ) -> list[ResumeModification]:
        """根据优化建议生成具体的修改操作

        Args:
            current_profile: 当前简历信息
            suggestion: 优化建议

        Returns:
            修改操作列表
        """
        modifications = []

        # 技能修改
        for gap in suggestion.gaps:
            if gap.gap_type == "skill":
                # 添加缺失技能
                missing = []
                for s in gap.suggestions:
                    if "补充以下技能" in s:
                        # 从建议中提取技能
                        skills_str = s.split(":")[-1].strip()
                        missing = [sk.strip() for sk in skills_str.split(",")]

                if missing:
                    current_skills = current_profile.get("skills", [])
                    new_skills = list(set(current_skills + missing))
                    modifications.append(
                        ResumeModification(
                            field_name="skills",
                            action="modify",
                            old_value=", ".join(current_skills),
                            new_value=", ".join(new_skills),
                            reason=f"补充缺失技能: {', '.join(missing[:3])}",
                        )
                    )

        return modifications

    def apply_modifications(
        self,
        profile: dict,
        modifications: list[ResumeModification],
        accepted_fields: list[str] | None = None,
    ) -> dict:
        """应用修改到简历

        Args:
            profile: 当前简历信息
            modifications: 修改操作列表
            accepted_fields: 用户接受的字段列表，None 表示全部接受

        Returns:
            修改后的简历信息
        """
        import copy

        updated = copy.deepcopy(profile)

        for mod in modifications:
            # 如果指定了接受字段，只应用接受的修改
            if accepted_fields and mod.field_name not in accepted_fields:
                continue

            if mod.field_name == "skills":
                if mod.action == "modify" and mod.new_value:
                    updated["skills"] = [s.strip() for s in mod.new_value.split(",")]
            elif mod.field_name == "experience_years":
                if mod.action == "modify" and mod.new_value:
                    updated["experience_years"] = int(mod.new_value)
            elif mod.field_name == "education":
                if mod.action == "modify" and mod.new_value:
                    updated["education"] = mod.new_value

        logger.info(f"已应用 {len(modifications)} 项修改")
        return updated


# 全局实例
resume_optimizer = ResumeOptimizer()
