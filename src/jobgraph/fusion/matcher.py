"""实体匹配算法

识别不同来源的同一实体（公司、岗位等）
"""

import re
from difflib import SequenceMatcher
from typing import Optional
from loguru import logger


class EntityMatcher:
    """实体匹配器"""

    # 公司名称别名库
    COMPANY_ALIASES = {
        "腾讯": ["腾讯科技", "腾讯公司", "腾讯控股", "Tencent", "Tencent Holdings"],
        "阿里巴巴": ["阿里", "阿里巴巴集团", "阿里巴巴网络", "Alibaba", "Alibaba Group"],
        "字节跳动": ["字节", "字节跳动有限公司", "ByteDance", "Beijing ByteDance"],
        "百度": ["百度公司", "百度在线", "Baidu", "Baidu Inc"],
        "美团": ["美团点评", "美团公司", "Meituan", "Meituan Dianping"],
        "京东": ["京东集团", "京东商城", "JD.com", "JD"],
        "华为": ["华为技术", "华为公司", "Huawei", "Huawei Technologies"],
        "小米": ["小米科技", "小米公司", "Xiaomi", "Xiaomi Corporation"],
        "网易": ["网易公司", "网易杭州", "NetEase"],
        "拼多多": ["拼多多公司", "Pinduoduo", "PDD"],
    }

    def match_company(self, company1: dict, company2: dict) -> float:
        """计算两个公司的匹配度

        Returns:
            匹配度 0-1
        """
        scores = []

        # 1. 名称匹配 (权重 0.4)
        name_score = self._match_name(
            company1.get("name", ""),
            company2.get("name", "")
        )
        scores.append(("name", name_score, 0.4))

        # 2. 英文名匹配 (权重 0.2)
        name_en1 = company1.get("name_en", "")
        name_en2 = company2.get("name_en", "")
        if name_en1 and name_en2:
            en_score = self._match_name(name_en1, name_en2)
            scores.append(("name_en", en_score, 0.2))

        # 3. 统一社会信用代码 (权重 1.0 - 完全匹配)
        code1 = company1.get("credit_code", "")
        code2 = company2.get("credit_code", "")
        if code1 and code2:
            if code1 == code2:
                return 1.0  # 完全匹配

        # 4. 行业匹配 (权重 0.1)
        if company1.get("industry") and company2.get("industry"):
            industry_score = 1.0 if company1["industry"] == company2["industry"] else 0.0
            scores.append(("industry", industry_score, 0.1))

        # 5. 总部匹配 (权重 0.1)
        if company1.get("headquarters") and company2.get("headquarters"):
            hq_score = 1.0 if company1["headquarters"] == company2["headquarters"] else 0.0
            scores.append(("headquarters", hq_score, 0.1))

        # 6. 法人匹配 (权重 0.2)
        lp1 = company1.get("legal_person", "")
        lp2 = company2.get("legal_person", "")
        if lp1 and lp2:
            lp_score = 1.0 if lp1 == lp2 else 0.0
            scores.append(("legal_person", lp_score, 0.2))

        # 计算加权分数
        if not scores:
            return 0.0

        total_weight = sum(weight for _, _, weight in scores)
        total_score = sum(score * weight for _, score, weight in scores)

        return total_score / total_weight if total_weight > 0 else 0.0

    def match_job(self, job1: dict, job2: dict) -> float:
        """计算两个岗位的匹配度"""
        scores = []

        # 1. 公司匹配 (权重 0.3)
        if job1.get("company_id") == job2.get("company_id"):
            scores.append(("company", 1.0, 0.3))
        elif job1.get("company_name") and job2.get("company_name"):
            company_score = self._match_name(job1["company_name"], job2["company_name"])
            scores.append(("company", company_score, 0.3))

        # 2. 职位名称匹配 (权重 0.4)
        title_score = self._match_name(job1.get("title", ""), job2.get("title", ""))
        scores.append(("title", title_score, 0.4))

        # 3. 地点匹配 (权重 0.15)
        if job1.get("location") and job2.get("location"):
            loc_score = 1.0 if job1["location"] == job2["location"] else 0.0
            scores.append(("location", loc_score, 0.15))

        # 4. 薪资范围匹配 (权重 0.15)
        salary_score = self._match_salary(
            job1.get("salary_min"), job1.get("salary_max"),
            job2.get("salary_min"), job2.get("salary_max")
        )
        if salary_score is not None:
            scores.append(("salary", salary_score, 0.15))

        if not scores:
            return 0.0

        total_weight = sum(weight for _, _, weight in scores)
        total_score = sum(score * weight for _, score, weight in scores)

        return total_score / total_weight if total_weight > 0 else 0.0

    def _match_name(self, name1: str, name2: str) -> float:
        """匹配名称"""
        if not name1 or not name2:
            return 0.0

        # 精确匹配
        if name1 == name2:
            return 1.0

        # 别名匹配
        if self._is_alias(name1, name2):
            return 0.95

        # 去除空格和标点后匹配
        clean1 = re.sub(r'[\s\-_，。、]', '', name1)
        clean2 = re.sub(r'[\s\-_，。、]', '', name2)
        if clean1 == clean2:
            return 0.9

        # 包含关系
        if clean1 in clean2 or clean2 in clean1:
            return 0.8

        # 模糊匹配
        return SequenceMatcher(None, name1, name2).ratio()

    def _is_alias(self, name1: str, name2: str) -> bool:
        """检查是否是别名"""
        for aliases in self.COMPANY_ALIASES.values():
            if name1 in aliases and name2 in aliases:
                return True
        return False

    def _match_salary(
        self,
        min1: Optional[float],
        max1: Optional[float],
        min2: Optional[float],
        max2: Optional[float],
    ) -> Optional[float]:
        """匹配薪资范围"""
        if min1 is None or max1 is None or min2 is None or max2 is None:
            return None

        # 计算重叠比例
        overlap_min = max(min1, min2)
        overlap_max = min(max1, max2)

        if overlap_min > overlap_max:
            return 0.0  # 无重叠

        overlap_range = overlap_max - overlap_min
        total_range = max(max1, max2) - min(min1, min2)

        if total_range == 0:
            return 1.0

        return overlap_range / total_range

    def find_duplicates(self, entities: list[dict], threshold: float = 0.8) -> list[list[int]]:
        """查找重复实体

        Returns:
            重复实体的索引组
        """
        n = len(entities)
        visited = [False] * n
        groups = []

        for i in range(n):
            if visited[i]:
                continue

            group = [i]
            visited[i] = True

            for j in range(i + 1, n):
                if visited[j]:
                    continue

                score = self.match_company(entities[i], entities[j])
                if score >= threshold:
                    group.append(j)
                    visited[j] = True

            if len(group) > 1:
                groups.append(group)

        return groups


# 全局实例
entity_matcher = EntityMatcher()
