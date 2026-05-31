"""Test configuration."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_company():
    """Sample company data for testing."""
    return {
        "id": "test_company_001",
        "name": "测试公司",
        "name_en": "Test Corp",
        "industry": "互联网",
        "size": "large",
        "founded": 2020,
        "headquarters": "北京",
        "employees": 1000,
        "avg_salary": 30000,
        "avg_rating": 3.5,
        "risk_level": "medium",
        "risk_score": 0.4,
        "tags": ["测试", "互联网"],
    }


@pytest.fixture
def sample_job():
    """Sample job data for testing."""
    return {
        "id": "test_job_001",
        "title": "后端工程师",
        "company_id": "test_company_001",
        "company_name": "测试公司",
        "department": "技术",
        "location": "北京",
        "salary_min": 25000,
        "salary_max": 40000,
        "salary_months": 14,
        "experience_years": 3,
        "education": "本科",
        "skills": ["Java", "Python", "MySQL"],
        "benefits": ["五险一金", "年终奖"],
        "is_active": True,
    }


@pytest.fixture
def sample_review():
    """Sample review data for testing."""
    return {
        "id": "test_review_001",
        "company_id": "test_company_001",
        "overall_rating": 4.0,
        "salary_rating": 4.0,
        "work_life_rating": 3.5,
        "management_rating": 3.5,
        "title": "还不错",
        "pros": "平台大，能学到东西",
        "cons": "加班较多",
        "reviewer_title": "工程师",
        "reviewer_tenure": "2年",
        "is_current_employee": True,
        "pitfall_tags": [],
    }
