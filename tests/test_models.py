"""Tests for data models."""

import pytest
from src.jobgraph.models import (
    Company, Job, Review, Pitfall, UserProfile,
    CompanySize, RiskLevel, JobType, FundingStage
)


class TestCompany:
    """Test Company model."""

    def test_create_company(self):
        """Test creating a company."""
        company = Company(
            id="test_001",
            name="测试公司",
            industry="互联网",
            size=CompanySize.LARGE,
            headquarters="北京",
        )
        
        assert company.id == "test_001"
        assert company.name == "测试公司"
        assert company.industry == "互联网"
        assert company.size == CompanySize.LARGE
        assert company.headquarters == "北京"

    def test_company_defaults(self):
        """Test company default values."""
        company = Company(id="test_001", name="测试公司")
        
        assert company.risk_level == RiskLevel.MEDIUM
        assert company.risk_score == 0.5
        assert company.tags == []
        assert company.is_listed is False

    def test_company_size_enum(self):
        """Test CompanySize enum values."""
        assert CompanySize.STARTUP.value == "startup"
        assert CompanySize.GIANT.value == "giant"

    def test_risk_level_enum(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.BLACKLIST.value == "blacklist"


class TestJob:
    """Test Job model."""

    def test_create_job(self):
        """Test creating a job."""
        job = Job(
            id="job_001",
            title="后端工程师",
            company_id="comp_001",
            company_name="测试公司",
            location="北京",
            salary_min=25000,
            salary_max=40000,
        )
        
        assert job.id == "job_001"
        assert job.title == "后端工程师"
        assert job.salary_min == 25000
        assert job.salary_max == 40000

    def test_job_defaults(self):
        """Test job default values."""
        job = Job(
            id="job_001",
            title="工程师",
            company_id="comp_001",
            company_name="公司",
        )
        
        assert job.job_type == JobType.FULL_TIME
        assert job.salary_months == 12
        assert job.is_remote is False
        assert job.is_active is True
        assert job.skills == []

    def test_job_type_enum(self):
        """Test JobType enum values."""
        assert JobType.FULL_TIME.value == "full_time"
        assert JobType.INTERN.value == "intern"
        assert JobType.REMOTE.value == "remote"


class TestReview:
    """Test Review model."""

    def test_create_review(self):
        """Test creating a review."""
        review = Review(
            id="rev_001",
            company_id="comp_001",
            overall_rating=4.0,
            pros="优点",
            cons="缺点",
        )
        
        assert review.id == "rev_001"
        assert review.overall_rating == 4.0
        assert review.pros == "优点"
        assert review.cons == "缺点"

    def test_review_defaults(self):
        """Test review default values."""
        review = Review(id="rev_001", company_id="comp_001")
        
        assert review.overall_rating == 0.0
        assert review.is_current_employee is True
        assert review.pitfall_tags == []


class TestPitfall:
    """Test Pitfall model."""

    def test_create_pitfall(self):
        """Test creating a pitfall."""
        pitfall = Pitfall(
            id="pit_001",
            company_id="comp_001",
            pitfall_type="996",
            severity=4,
            description="强制996",
        )
        
        assert pitfall.id == "pit_001"
        assert pitfall.pitfall_type == "996"
        assert pitfall.severity == 4
        assert pitfall.report_count == 1

    def test_pitfall_defaults(self):
        """Test pitfall default values."""
        pitfall = Pitfall(
            id="pit_001",
            company_id="comp_001",
            pitfall_type="PUA",
        )
        
        assert pitfall.severity == 3
        assert pitfall.report_count == 1
        assert pitfall.confirmed_count == 0
        assert pitfall.is_verified is False


class TestUserProfile:
    """Test UserProfile model."""

    def test_create_user_profile(self):
        """Test creating a user profile."""
        user = UserProfile(
            id="user_001",
            name="张三",
            current_title="工程师",
            experience_years=3,
            skills=["Python", "Java"],
        )
        
        assert user.id == "user_001"
        assert user.name == "张三"
        assert user.experience_years == 3
        assert "Python" in user.skills

    def test_user_defaults(self):
        """Test user default values."""
        user = UserProfile(id="user_001")
        
        assert user.experience_years == 0
        assert user.skills == []
        assert user.prefer_remote is False
        assert user.prefer_work_life_balance is True
