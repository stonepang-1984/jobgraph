"""智能匹配引擎

支持两种匹配模式：
1. 基于用户档案匹配（从简历解析）
2. 基于手动输入匹配

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
    ):
        self.matches = matches
        self.need_manual_input = need_manual_input
        self.message = message
        self.total_count = total_count

    def to_dict(self) -> dict:
        return {
            "matches": self.matches,
            "need_manual_input": self.need_manual_input,
            "message": self.message,
            "total_count": self.total_count,
        }


class JobMatcher:
    """智能匹配引擎"""

    # 匹配结果阈值：少于此数量时提示手动输入
    MIN_MATCH_THRESHOLD = 5

    def match_by_profile(self, user_id: str, limit: int = 20) -> MatchResult:
        """基于用户档案匹配岗位

        Args:
            user_id: 用户 ID
            limit: 返回结果数量限制

        Returns:
            匹配结果
        """
        logger.info(f"开始基于档案匹配，用户: {user_id}")

        try:
            cypher = """
            MATCH (u:UserProfile {id: $user_id})
            MATCH (j:Job {is_active: true})
            OPTIONAL MATCH (c:Company)-[:HAS_JOB]->(j)

            WITH u, j, c,
                 // 技能匹配
                 size([s IN u.skills WHERE s IN j.skills]) AS matched_skills,
                 size(u.skills) AS user_skill_count,
                 size(j.skills) AS job_skill_count,

                 // 薪资匹配
                 CASE
                     WHEN u.desired_salary_min IS NULL AND u.desired_salary_max IS NULL THEN 0.5
                     WHEN j.salary_max >= u.desired_salary_min AND j.salary_min <= u.desired_salary_max THEN 1.0
                     WHEN j.salary_max >= u.desired_salary_min THEN 0.5
                     ELSE 0.0
                 END AS salary_match,

                 // 地点匹配
                 CASE
                     WHEN j.is_remote AND u.prefer_remote THEN 1.0
                     WHEN u.desired_locations IS NULL OR size(u.desired_locations) = 0 THEN 0.5
                     WHEN any(loc IN u.desired_locations WHERE j.location CONTAINS loc) THEN 1.0
                     ELSE 0.0
                 END AS location_match,

                 // 经验匹配
                 CASE
                     WHEN j.experience_years IS NULL THEN 0.5
                     WHEN abs(j.experience_years - u.experience_years) <= 2 THEN 1.0
                     WHEN abs(j.experience_years - u.experience_years) <= 5 THEN 0.5
                     ELSE 0.2
                 END AS experience_match

            WITH u, j, c, matched_skills,
                 CASE WHEN job_skill_count > 0
                      THEN toFloat(matched_skills) / job_skill_count
                      ELSE 0.0
                 END AS skill_score,
                 salary_match,
                 location_match,
                 experience_match,
                 CASE WHEN c.risk_level = 'low' THEN 0.9
                      WHEN c.risk_level = 'medium' THEN 0.6
                      WHEN c.risk_level = 'high' THEN 0.3
                      ELSE 0.5
                 END AS risk_factor

            WITH u, j, c, matched_skills,
                 (skill_score * 0.4 + salary_match * 0.25 + location_match * 0.2 + experience_match * 0.15) AS total_score,
                 risk_factor

            WHERE total_score > 0.3

            RETURN j.id AS job_id,
                   j.title AS job_title,
                   j.company_name AS company_name,
                   j.company_id AS company_id,
                   j.salary_min AS salary_min,
                   j.salary_max AS salary_max,
                   j.location AS location,
                   j.skills AS skills,
                   j.experience_years AS experience_years,
                   j.education AS education,
                   c.risk_level AS company_risk,
                   c.avg_rating AS company_rating,
                   matched_skills,
                   total_score
            ORDER BY total_score DESC
            LIMIT $limit
            """

            results = neo4j_client.execute_query(cypher, {"user_id": user_id, "limit": limit})

            logger.info(f"匹配完成，找到 {len(results)} 个岗位")

            return MatchResult(
                matches=results,
                need_manual_input=len(results) < self.MIN_MATCH_THRESHOLD,
                message="匹配结果较少，建议手动输入职位信息" if len(results) < self.MIN_MATCH_THRESHOLD else "",
                total_count=len(results),
            )

        except Exception as e:
            logger.error(f"档案匹配失败: {e}")
            return MatchResult(
                matches=[],
                need_manual_input=True,
                message=f"匹配出错: {e}，请尝试手动输入",
            )

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
            conditions = ["j.is_active = true"]
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

    def match_with_fallback(self, user_id: str, limit: int = 20) -> MatchResult:
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
