"""数据融合引擎

合并多个来源的数据，解决冲突，去重
"""

from datetime import datetime

from loguru import logger

from src.jobgraph.fusion.matcher import entity_matcher
from src.jobgraph.fusion.sources import PREDEFINED_SOURCES, SOURCE_PRIORITY, DataSource


class DataFusionEngine:
    """数据融合引擎"""

    def __init__(self):
        self.match_threshold = 0.8  # 匹配阈值

    def fuse_company(self, existing: dict | None, new_data: dict, source: str) -> dict:
        """融合公司数据

        Args:
            existing: 已有数据 (可能为 None)
            new_data: 新数据
            source: 数据来源

        Returns:
            融合后的数据
        """
        source_info = PREDEFINED_SOURCES.get(source, PREDEFINED_SOURCES["crawler"])

        if existing is None:
            # 新实体，直接添加来源信息
            return self._add_source_info(new_data, source_info)

        # 已有实体，合并数据
        fused = existing.copy()

        for field, new_value in new_data.items():
            if field in ("id", "created_at"):
                continue  # 跳过不可变字段

            if new_value is None:
                continue  # 跳过空值

            existing_field = existing.get(field)

            if existing_field is None:
                # 新字段，直接添加
                fused[field] = new_value
                fused[f"{field}_source"] = source
                fused[f"{field}_updated_at"] = datetime.now().isoformat()
            else:
                # 已有字段，比较优先级
                existing_source = existing.get(f"{field}_source", "crawler")
                existing_priority = SOURCE_PRIORITY.get(
                    PREDEFINED_SOURCES.get(existing_source, PREDEFINED_SOURCES["crawler"]).source_type, 0
                )
                new_priority = SOURCE_PRIORITY.get(source_info.source_type, 0)

                # 新数据优先级更高，或者数据不同且来源可信度高
                if new_priority > existing_priority:
                    fused[field] = new_value
                    fused[f"{field}_source"] = source
                    fused[f"{field}_updated_at"] = datetime.now().isoformat()
                elif new_value != existing_field and source_info.confidence > 0.9:
                    # 数据不同且来源可信，记录冲突
                    if "conflicts" not in fused:
                        fused["conflicts"] = []
                    fused["conflicts"].append(
                        {
                            "field": field,
                            "existing_value": existing_field,
                            "new_value": new_value,
                            "existing_source": existing_source,
                            "new_source": source,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        # 更新时间
        fused["updated_at"] = datetime.now().isoformat()

        return fused

    def fuse_job(self, existing: dict | None, new_data: dict, source: str) -> dict:
        """融合岗位数据"""
        source_info = PREDEFINED_SOURCES.get(source, PREDEFINED_SOURCES["crawler"])

        if existing is None:
            return self._add_source_info(new_data, source_info)

        # 岗位数据通常以最新为准
        fused = existing.copy()

        # 更新可变字段
        update_fields = ["salary_min", "salary_max", "is_active", "skills", "benefits"]
        for field in update_fields:
            if field in new_data and new_data[field] is not None:
                fused[field] = new_data[field]

        fused["updated_at"] = datetime.now().isoformat()
        return fused

    def fuse_review(self, existing: dict | None, new_data: dict, source: str) -> dict:
        """融合评价数据"""
        # 评价通常不合并，直接添加
        source_info = PREDEFINED_SOURCES.get(source, PREDEFINED_SOURCES["user"])
        return self._add_source_info(new_data, source_info)

    def merge_entities(self, entities: list[dict]) -> dict:
        """合并多个相同实体

        Args:
            entities: 同一实体的多个版本

        Returns:
            合并后的实体
        """
        if not entities:
            return {}

        if len(entities) == 1:
            return entities[0]

        # 以第一个为基础
        merged = entities[0].copy()

        # 合并其他版本
        for entity in entities[1:]:
            merged = self.fuse_company(merged, entity, entity.get("source", "crawler"))

        return merged

    def deduplicate_companies(self, companies: list[dict]) -> list[dict]:
        """公司去重

        Returns:
            去重后的公司列表
        """
        if not companies:
            return []

        # 查找重复
        duplicate_groups = entity_matcher.find_duplicates(companies, self.match_threshold)

        # 标记已合并的索引
        merged_indices = set()
        result = []

        for group in duplicate_groups:
            # 合并重复实体
            entities = [companies[i] for i in group]
            merged = self.merge_entities(entities)
            result.append(merged)

            # 标记已合并
            merged_indices.update(group)

        # 添加未重复的实体
        for i, company in enumerate(companies):
            if i not in merged_indices:
                result.append(company)

        logger.info(f"Deduplication: {len(companies)} -> {len(result)} companies")
        return result

    def _add_source_info(self, data: dict, source: DataSource) -> dict:
        """添加来源信息"""
        result = data.copy()
        result["source"] = source.source_name
        result["source_type"] = source.source_type.value
        result["confidence"] = source.confidence
        result["created_at"] = datetime.now().isoformat()
        result["updated_at"] = datetime.now().isoformat()
        return result


class DataQualityChecker:
    """数据质量检查"""

    # 必填字段
    REQUIRED_FIELDS = {
        "company": ["id", "name"],
        "job": ["id", "title", "company_id"],
        "review": ["id", "company_id"],
    }

    # 字段格式验证
    FIELD_VALIDATORS = {
        "email": r"^[\w\.-]+@[\w\.-]+\.\w+$",
        "phone": r"^\d{11}$",
        "url": r"^https?://",
        "salary": lambda x: 0 < x < 1000000 if x else True,
    }

    def check_company(self, data: dict) -> dict:
        """检查公司数据质量

        Returns:
            {"valid": bool, "score": float, "issues": list}
        """
        issues = []
        score = 1.0

        # 检查必填字段
        for field in self.REQUIRED_FIELDS["company"]:
            if not data.get(field):
                issues.append(f"缺少必填字段: {field}")
                score -= 0.3

        # 检查数据完整性
        optional_fields = ["industry", "headquarters", "founded", "employees"]
        filled = sum(1 for f in optional_fields if data.get(f))
        completeness = filled / len(optional_fields)
        score *= 0.5 + 0.5 * completeness

        # 检查数值范围
        if data.get("avg_rating"):
            if not 0 <= data["avg_rating"] <= 5:
                issues.append("评分超出范围 (0-5)")
                score -= 0.2

        if data.get("risk_score"):
            if not 0 <= data["risk_score"] <= 1:
                issues.append("风险分数超出范围 (0-1)")
                score -= 0.2

        return {
            "valid": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
        }

    def check_job(self, data: dict) -> dict:
        """检查岗位数据质量"""
        issues = []
        score = 1.0

        # 检查必填字段
        for field in self.REQUIRED_FIELDS["job"]:
            if not data.get(field):
                issues.append(f"缺少必填字段: {field}")
                score -= 0.3

        # 检查薪资合理性
        salary_min = data.get("salary_min")
        salary_max = data.get("salary_max")
        if salary_min and salary_max:
            if salary_min > salary_max:
                issues.append("最低薪资大于最高薪资")
                score -= 0.3
            if salary_max > 1000000:
                issues.append("薪资异常高")
                score -= 0.1

        # 检查经验年限
        exp = data.get("experience_years")
        if exp is not None:
            if exp < 0 or exp > 50:
                issues.append("经验年限不合理")
                score -= 0.2

        return {
            "valid": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
        }

    def check_review(self, data: dict) -> dict:
        """检查评价数据质量"""
        issues = []
        score = 1.0

        # 检查必填字段
        for field in self.REQUIRED_FIELDS["review"]:
            if not data.get(field):
                issues.append(f"缺少必填字段: {field}")
                score -= 0.3

        # 检查评分
        rating = data.get("overall_rating")
        if rating is not None:
            if not 0 <= rating <= 5:
                issues.append("评分超出范围 (0-5)")
                score -= 0.2

        # 检查内容长度
        pros = data.get("pros", "")
        cons = data.get("cons", "")
        if len(pros) < 5 and len(cons) < 5:
            issues.append("评价内容过短")
            score -= 0.2

        return {
            "valid": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
        }


# 全局实例
fusion_engine = DataFusionEngine()
quality_checker = DataQualityChecker()
