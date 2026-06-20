"""智能匹配引擎

两层匹配流程：
1. 第一层：字段初筛（硬性条件：工作年限、学历、地点、薪资、技能）
2. 第二层：语义匹配（软性条件：LLM 分析工作经历与岗位匹配度）

降级策略：匹配结果不足时提示用户手动输入
"""

from loguru import logger

from src.graph.neo4j_client import neo4j_client


class MatchResult:
    """匹配结果"""

    def __init__(
        self,
        matches: list[dict],
        need_manual_input: bool = False,
        message: str = "",
        total_count: int = 0,
        filter_stats: dict | None = None,
    ):
        self.matches = matches
        self.need_manual_input = need_manual_input
        self.message = message
        self.total_count = total_count
        self.filter_stats = filter_stats or {}

    def to_dict(self) -> dict:
        return {
            "matches": self.matches,
            "need_manual_input": self.need_manual_input,
            "message": self.message,
            "total_count": self.total_count,
            "filter_stats": self.filter_stats,
        }


class JobMatcher:
    """智能匹配引擎"""

    # 匹配结果阈值：少于此数量时提示手动输入
    MIN_MATCH_THRESHOLD = 5

    # LLM 可用性缓存
    _llm_available = None
    _llm = None

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
                return True

            # 检查 Ollama
            import requests

            ollama_url = settings.llm.ollama_base_url
            response = requests.get(f"{ollama_url}/api/tags", timeout=3)
            if response.status_code == 200:
                self._llm_available = True
                return True

            self._llm_available = False
            return False
        except Exception:
            self._llm_available = False
            return False

    def _get_llm(self):
        """获取 LLM 实例"""
        if self._llm is not None:
            return self._llm

        try:
            from langchain_openai import ChatOpenAI

            from config.settings import settings

            api_key = settings.llm.openai_api_key

            if api_key and api_key != "sk-your-openai-api-key" and len(api_key) > 10:
                # 使用 OpenAI API
                self._llm = ChatOpenAI(
                    model=settings.llm.openai_model,
                    api_key=api_key,
                    base_url=settings.llm.openai_api_base,
                    temperature=0,
                    request_timeout=300,
                )
            else:
                # 使用 Ollama
                ollama_url = settings.llm.ollama_base_url
                ollama_model = settings.llm.ollama_model
                self._llm = ChatOpenAI(
                    model=ollama_model,
                    api_key="ollama",
                    base_url=f"{ollama_url}/v1",
                    temperature=0,
                    request_timeout=300,
                )

            return self._llm
        except Exception as e:
            logger.error(f"获取 LLM 失败: {e}")
            return None

    def filter_by_fields(
        self,
        user_profile: dict,
        limit: int = 50,
    ) -> list[dict]:
        """第一层：字段初筛（硬性条件）

        筛选条件：
        - 工作年限：职位要求 <= 用户年限 + 2
        - 学历：职位要求 <= 用户学历
        - 地点：匹配或接受远程
        - 薪资：职位薪资 >= 用户期望
        - 技能：至少匹配 1 项

        Args:
            user_profile: 用户档案
            limit: 返回结果数量限制

        Returns:
            初筛后的职位列表
        """
        logger.info("第一层：字段初筛...")

        # 获取用户条件
        user_exp = user_profile.get("experience_years", 0)
        user_education = user_profile.get("education")
        user_skills = user_profile.get("skills", [])
        user_locations = user_profile.get("desired_locations", [])
        user_salary_min = user_profile.get("desired_salary_min")
        user_prefer_remote = user_profile.get("prefer_remote", False)

        # 学历优先级
        edu_priority = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}
        user_edu_level = edu_priority.get(user_education, 0)

        # 构建学历列表（包含用户学历及以下）
        edu_list = [k for k, v in edu_priority.items() if v <= user_edu_level] if user_edu_level > 0 else []

        # 构建查询条件
        conditions = ["j.is_active = true", "j.description IS NOT NULL", "j.description <> ''"]
        params = {"limit": limit}

        # 工作年限筛选
        if user_exp > 0:
            conditions.append("(j.experience_years IS NULL OR j.experience_years <= $user_exp + 2)")
            params["user_exp"] = user_exp

        # 学历筛选
        if edu_list:
            conditions.append("(j.education IS NULL OR j.education IN $edu_list)")
            params["edu_list"] = edu_list

        # 地点筛选
        if user_locations:
            location_conditions = []
            for i, loc in enumerate(user_locations):
                param_name = f"location_{i}"
                location_conditions.append(f"j.location CONTAINS ${param_name}")
                params[param_name] = loc
            if user_prefer_remote:
                location_conditions.append("j.is_remote = true")
            conditions.append(f"({' OR '.join(location_conditions)})")

        # 薪资筛选
        if user_salary_min:
            conditions.append("(j.salary_max IS NULL OR j.salary_max >= $salary_min)")
            params["salary_min"] = user_salary_min

        # 技能筛选（至少匹配 1 项）
        if user_skills:
            conditions.append("any(s IN $skills WHERE s IN j.skills)")
            params["skills"] = user_skills

        where_clause = " AND ".join(conditions)

        # 查询
        cypher = f"""
        MATCH (j:Job)
        OPTIONAL MATCH (c:Company)-[:HAS_JOB]->(j)

        WITH j, c,
             // 技能匹配数
             size([s IN $skills WHERE s IN j.skills]) AS matched_skill_count,
             // 经验匹配度
             CASE
                 WHEN j.experience_years IS NULL THEN 0.5
                 WHEN abs(j.experience_years - $user_exp) <= 2 THEN 1.0
                 WHEN abs(j.experience_years - $user_exp) <= 5 THEN 0.5
                 ELSE 0.2
             END AS exp_match_score

        WHERE {where_clause}

        RETURN j.id AS job_id,
               j.title AS job_title,
               j.company_name AS company_name,
               j.company_id AS company_id,
               j.salary_min AS salary_min,
               j.salary_max AS salary_max,
               j.location AS location,
               j.is_remote AS is_remote,
               j.skills AS skills,
               j.description AS description,
               j.requirements AS requirements,
               j.experience_years AS experience_years,
               j.education AS education,
               c.risk_level AS company_risk,
               c.avg_rating AS company_rating,
               matched_skill_count,
               exp_match_score
        ORDER BY matched_skill_count DESC, exp_match_score DESC
        LIMIT $limit
        """

        try:
            results = neo4j_client.execute_query(cypher, params)
            logger.info(f"字段初筛完成，找到 {len(results)} 个职位")
            return results
        except Exception as e:
            logger.error(f"字段初筛失败: {e}")
            return []

    def rank_by_semantic(
        self,
        user_profile: dict,
        jobs: list[dict],
        limit: int = 10,
    ) -> list[dict]:
        """第二层：语义匹配（批量调用）

        Args:
            user_profile: 用户档案
            jobs: 初筛后的职位列表
            limit: 返回结果数量限制

        Returns:
            语义匹配后的职位列表
        """
        logger.info(f"第二层：语义匹配，{len(jobs)} 个职位...")

        if not self._check_llm_available():
            logger.warning("LLM 不可用，跳过语义匹配")
            return jobs[:limit]

        # 批量调用 LLM
        scores = self.batch_semantic_match(user_profile, jobs)

        # 合并结果
        for job, score in zip(jobs, scores):
            if score is not None:
                job["semantic_score"] = score
                job["total_score"] = score
            else:
                # 降级：使用初筛分数
                job["semantic_score"] = None
                job["total_score"] = job.get("matched_skill_count", 0) * 0.15 + job.get("exp_match_score", 0) * 0.4

        # 排序
        jobs.sort(key=lambda x: x.get("total_score", 0), reverse=True)

        logger.info(f"语义匹配完成，返回 {min(len(jobs), limit)} 个职位")
        return jobs[:limit]

    def batch_semantic_match(
        self,
        user_profile: dict,
        jobs: list[dict],
    ) -> list[float | None]:
        """批量语义匹配

        一次调用 LLM 评估所有职位的匹配度

        Args:
            user_profile: 用户档案
            jobs: 职位列表

        Returns:
            匹配分数列表 (0-1)，失败返回 None
        """
        if not jobs:
            return []

        try:
            llm = self._get_llm()
            if not llm:
                return [None] * len(jobs)

            # 限制职位数量，避免 prompt 过长
            max_jobs = 8
            jobs_to_eval = jobs[:max_jobs]
            remaining_jobs = jobs[max_jobs:]

            # 构建 prompt（包含职位描述，但限制长度）
            job_list = "\n".join(
                [
                    f"{i + 1}. {job.get('title', '')} - {(job.get('description', '') or '')[:150]}"
                    for i, job in enumerate(jobs_to_eval)
                ]
            )

            user_skills = ", ".join(user_profile.get("skills", [])[:8])
            user_exp = user_profile.get("experience_years", 0)
            user_title = user_profile.get("current_title", "未提供")
            user_summary = user_profile.get("resume_text", "")

            # 构建用户信息部分
            user_info = f"用户：{user_title}，{user_exp}年，技能：{user_skills}"
            if user_summary:
                user_info += f"\n个人简介：{user_summary[:200]}"

            prompt = f"""评估用户与岗位的匹配度。

{user_info}

岗位：
{job_list}

返回每个岗位匹配度（0-100），逗号分隔，只返回数字。"""

            from langchain_core.messages import HumanMessage

            response = llm.invoke([HumanMessage(content=prompt)])

            # 解析结果
            scores = self._parse_batch_scores(response.content, len(jobs_to_eval))

            # 对于超出限制的职位，返回 None
            scores.extend([None] * len(remaining_jobs))

            logger.info(f"批量语义匹配完成，{len(scores)} 个分数")
            return scores

        except Exception as e:
            logger.warning(f"批量语义匹配失败: {e}")
            return [None] * len(jobs)

    def _parse_batch_scores(self, text: str, expected_count: int) -> list[float | None]:
        """解析批量匹配分数

        Args:
            text: LLM 返回的文本
            expected_count: 期望的分数数量

        Returns:
            分数列表 (0-1)
        """
        import re

        numbers = re.findall(r"\d+", text)

        scores = []
        for num in numbers[:expected_count]:
            score = int(num)
            if 0 <= score <= 100:
                scores.append(score / 100.0)
            else:
                scores.append(None)

        # 补充缺失的分数
        while len(scores) < expected_count:
            scores.append(None)

        return scores

    def semantic_match_score(
        self,
        user_profile: dict,
        job: dict,
    ) -> float | None:
        """使用 LLM 分析简历与职位描述的语义匹配度

        Args:
            user_profile: 用户档案
            job: 岗位信息（包含 description, requirements）

        Returns:
            匹配分数 (0-1)，失败返回 None
        """
        if not self._check_llm_available():
            return None

        # 获取职位描述
        description = job.get("description", "") or ""
        requirements = job.get("requirements", "") or ""

        if not description and not requirements:
            return None

        try:
            llm = self._get_llm()
            if not llm:
                return None

            # 构建提示词
            user_skills = ", ".join(user_profile.get("skills", []))
            user_exp = user_profile.get("experience_years", 0)
            user_title = user_profile.get("current_title", "未提供")

            prompt = f"""评估以下用户与岗位的匹配度。

用户信息：
- 当前职位：{user_title}
- 工作年限：{user_exp} 年
- 技能：{user_skills}

岗位信息：
- 职位：{job.get("title", "")}
- 岗位职责：{description[:500]}
- 任职要求：{requirements[:500]}

请评估匹配度（0-100的整数），只返回数字，不要其他内容。"""

            from langchain_core.messages import HumanMessage

            response = llm.invoke([HumanMessage(content=prompt)])

            # 解析分数
            score_text = response.content.strip()
            # 提取数字
            import re

            numbers = re.findall(r"\d+", score_text)
            if numbers:
                score = int(numbers[0])
                if 0 <= score <= 100:
                    return score / 100.0

            return None

        except Exception as e:
            logger.warning(f"LLM 语义匹配失败: {e}")
            return None

    def match_by_profile(self, user_id: str, limit: int = 10, use_semantic: bool = True) -> MatchResult:
        """基于用户档案匹配岗位（两层匹配）

        流程：
        1. 第一层：字段初筛（硬性条件）
        2. 第二层：语义匹配（软性条件）

        Args:
            user_id: 用户 ID
            limit: 返回结果数量限制
            use_semantic: 是否使用 LLM 语义匹配

        Returns:
            匹配结果
        """
        logger.info(f"开始两层匹配，用户: {user_id}")

        try:
            # 获取用户档案
            user_profile = self.get_user_profile(user_id)
            if not user_profile:
                logger.error(f"未找到用户档案: {user_id}")
                return MatchResult(
                    matches=[],
                    need_manual_input=True,
                    message="未找到用户档案，请先上传简历或填写信息",
                )

            # 第一层：字段初筛
            filtered_jobs = self.filter_by_fields(user_profile, limit=50)
            filter_stats = {
                "total_jobs": self._get_total_job_count(),
                "filtered_count": len(filtered_jobs),
            }

            if not filtered_jobs:
                logger.warning("字段初筛无结果")
                return MatchResult(
                    matches=[],
                    need_manual_input=True,
                    message="未找到符合条件的职位，建议调整筛选条件或手动输入",
                    filter_stats=filter_stats,
                )

            # 第二层：语义匹配
            if use_semantic and self._check_llm_available():
                final_jobs = self.rank_by_semantic(user_profile, filtered_jobs, limit=limit)
                filter_stats["semantic_used"] = True
            else:
                # 不使用语义匹配，计算综合分数
                for job in filtered_jobs:
                    matched_skill_count = job.get("matched_skill_count", 0)
                    exp_match_score = job.get("exp_match_score", 0)
                    # 综合分数：技能匹配 60% + 经验匹配 40%
                    job["total_score"] = matched_skill_count * 0.15 + exp_match_score * 0.4
                final_jobs = filtered_jobs[:limit]
                filter_stats["semantic_used"] = False

            filter_stats["final_count"] = len(final_jobs)

            logger.info(f"匹配完成: 初筛 {filter_stats['filtered_count']} -> 最终 {filter_stats['final_count']}")

            return MatchResult(
                matches=final_jobs,
                need_manual_input=len(final_jobs) < self.MIN_MATCH_THRESHOLD,
                message="匹配结果较少，建议手动输入职位信息" if len(final_jobs) < self.MIN_MATCH_THRESHOLD else "",
                total_count=len(final_jobs),
                filter_stats=filter_stats,
            )

        except Exception as e:
            logger.error(f"档案匹配失败: {e}")
            return MatchResult(
                matches=[],
                need_manual_input=True,
                message=f"匹配出错: {e}，请尝试手动输入",
            )

    def _get_total_job_count(self) -> int:
        """获取职位总数"""
        try:
            result = neo4j_client.execute_query("MATCH (j:Job {is_active: true}) RETURN count(j) AS cnt")
            return result[0]["cnt"] if result else 0
        except Exception:
            return 0

    def match_by_manual_input(
        self,
        job_title: str | None = None,
        skills: list[str] | None = None,
        experience_years: int | None = None,
        education: str | None = None,
        location: str | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        limit: int = 20,
    ) -> MatchResult:
        """基于手动输入匹配岗位

        Args:
            job_title: 期望职位
            skills: 技能列表
            experience_years: 工作年限
            education: 学历
            location: 期望地点
            salary_min: 最低薪资
            salary_max: 最高薪资
            limit: 返回结果数量限制

        Returns:
            匹配结果
        """
        logger.info(f"开始手动输入匹配，职位: {job_title}")

        try:
            # 构建查询条件
            conditions = ["j.is_active = true", "j.description IS NOT NULL", "j.description <> ''"]
            params = {"limit": limit}

            # 技能条件（可选）
            if skills:
                conditions.append("any(s IN $skills WHERE s IN j.skills)")
                params["skills"] = skills

            # 经验条件（可选）
            if experience_years is not None:
                conditions.append("(j.experience_years IS NULL OR j.experience_years <= $exp_years + 2)")
                params["exp_years"] = experience_years

            # 学历条件（可选）
            if education and education != "不限":
                # 学历优先级
                edu_priority = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}
                if education in edu_priority:
                    conditions.append("(j.education IS NULL OR j.education IN $edu_list)")
                    # 包含当前学历及以下
                    edu_list = [k for k, v in edu_priority.items() if v >= edu_priority[education]]
                    params["edu_list"] = edu_list

            # 地点条件（可选）
            if location:
                conditions.append("j.location CONTAINS $location")
                params["location"] = location

            # 薪资条件（可选）
            if salary_min:
                conditions.append("(j.salary_max IS NULL OR j.salary_max >= $salary_min)")
                params["salary_min"] = salary_min

            where_clause = " AND ".join(conditions)

            # 构建匹配分数计算
            cypher = f"""
            MATCH (j:Job)
            OPTIONAL MATCH (c:Company)-[:HAS_JOB]->(j)

            WITH j, c,
                 // 标题匹配
                 CASE
                     WHEN $job_title IS NULL THEN 0.5
                     WHEN j.title CONTAINS $job_title OR $job_title CONTAINS j.title THEN 1.0
                     WHEN any(word IN split($job_title, ' ') WHERE j.title CONTAINS word) THEN 0.5
                     ELSE 0.0
                 END AS title_match,

                 // 技能匹配
                 CASE
                     WHEN $skills IS NULL OR size($skills) = 0 THEN 0.5
                     ELSE toFloat(size([s IN $skills WHERE s IN j.skills])) / size($skills)
                 END AS skill_match,

                 // 经验匹配
                 CASE
                     WHEN $exp_years IS NULL OR j.experience_years IS NULL THEN 0.5
                     WHEN abs(j.experience_years - $exp_years) <= 2 THEN 1.0
                     WHEN abs(j.experience_years - $exp_years) <= 5 THEN 0.5
                     ELSE 0.2
                 END AS exp_match,

                 // 风险因子
                 CASE WHEN c.risk_level = 'low' THEN 0.9
                      WHEN c.risk_level = 'medium' THEN 0.6
                      WHEN c.risk_level = 'high' THEN 0.3
                      ELSE 0.5
                 END AS risk_factor

            WHERE {where_clause}

            WITH j, c, title_match, skill_match, exp_match, risk_factor,
                 (title_match * 0.4 + skill_match * 0.3 + exp_match * 0.2 + risk_factor * 0.1) AS total_score

            WHERE total_score > 0.2

            RETURN j.id AS job_id,
                   j.title AS job_title,
                   j.company_name AS company_name,
                   j.company_id AS company_id,
                   j.salary_min AS salary_min,
                   j.salary_max AS salary_max,
                   j.location AS location,
                   j.skills AS skills,
                   j.description AS description,
                   j.requirements AS requirements,
                   j.experience_years AS experience_years,
                   j.education AS education,
                   c.risk_level AS company_risk,
                   c.avg_rating AS company_rating,
                   size([s IN $skills WHERE s IN j.skills]) AS matched_skills,
                   total_score
            ORDER BY total_score DESC
            LIMIT $limit
            """

            params["job_title"] = job_title
            params["skills"] = skills or []
            params["exp_years"] = experience_years

            results = neo4j_client.execute_query(cypher, params)

            logger.info(f"手动匹配完成，找到 {len(results)} 个岗位")

            return MatchResult(
                matches=results,
                need_manual_input=False,
                total_count=len(results),
            )

        except Exception as e:
            logger.error(f"手动匹配失败: {e}")
            return MatchResult(
                matches=[],
                need_manual_input=False,
                message=f"匹配出错: {e}",
            )

    def match_with_fallback(self, user_id: str, limit: int = 10) -> MatchResult:
        """带降级策略的匹配

        先尝试档案匹配，如果结果不足则提示手动输入

        Args:
            user_id: 用户 ID
            limit: 返回结果数量限制

        Returns:
            匹配结果
        """
        result = self.match_by_profile(user_id, limit)

        if result.total_count < self.MIN_MATCH_THRESHOLD:
            result.need_manual_input = True
            result.message = f"仅找到 {result.total_count} 个匹配岗位，建议手动输入职位信息获取更多匹配"

        return result

    def get_user_profile(self, user_id: str) -> dict | None:
        """获取用户档案

        Args:
            user_id: 用户 ID

        Returns:
            用户档案字典
        """
        try:
            cypher = """
            MATCH (u:UserProfile {id: $user_id})
            RETURN u
            """
            results = neo4j_client.execute_query(cypher, {"user_id": user_id})
            if results:
                return dict(results[0].get("u", {}))
            return None
        except Exception as e:
            logger.error(f"获取用户档案失败: {e}")
            return None

    def analyze_match_details(
        self,
        user_profile: dict,
        job: dict,
    ) -> dict:
        """分析用户与岗位的匹配详情

        Args:
            user_profile: 用户档案
            job: 岗位信息

        Returns:
            匹配详情
        """
        user_skills = set(user_profile.get("skills", []))
        job_skills = set(job.get("skills", []))

        matching_skills = list(user_skills & job_skills)
        missing_skills = list(job_skills - user_skills)

        # 计算各项匹配分数
        skill_score = len(matching_skills) / len(job_skills) if job_skills else 0

        # 经验匹配
        user_exp = user_profile.get("experience_years", 0)
        job_exp = job.get("experience_years")
        if job_exp is None:
            exp_score = 0.5
        elif abs(user_exp - job_exp) <= 2:
            exp_score = 1.0
        elif abs(user_exp - job_exp) <= 5:
            exp_score = 0.5
        else:
            exp_score = 0.2

        # 总分
        total_score = skill_score * 0.5 + exp_score * 0.3 + 0.2  # 0.2 是基础分

        return {
            "total_score": total_score,
            "skill_score": skill_score,
            "experience_score": exp_score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "user_skill_count": len(user_skills),
            "job_skill_count": len(job_skills),
        }


# 全局实例
job_matcher = JobMatcher()
