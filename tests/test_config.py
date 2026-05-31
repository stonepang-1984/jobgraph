"""Tests for configuration."""

from src.jobgraph.config import (
    get_edition_info,
    get_features,
    get_limit_value,
    get_limits,
    get_upgrade_info,
    is_feature_available,
)


class TestConfig:
    """Test configuration functions."""

    def test_get_features_free(self):
        """Test getting free features."""
        features = get_features(is_pro=False)

        assert "job_search" in features
        assert "company_profile" in features
        assert "pitfall_guide" in features
        assert features["job_search"] is True

    def test_get_features_pro(self):
        """Test getting pro features."""
        features = get_features(is_pro=True)

        # Free features
        assert "job_search" in features
        assert "company_profile" in features

        # Pro features
        assert "advanced_matching" in features
        assert "data_export" in features
        assert "unlimited_search" in features

    def test_get_limits_free(self):
        """Test getting free limits."""
        limits = get_limits(is_pro=False)

        assert limits["max_search_per_day"] == 100
        assert limits["max_jobs_per_search"] == 50
        assert limits["max_matching_results"] == 10

    def test_get_limits_pro(self):
        """Test getting pro limits."""
        limits = get_limits(is_pro=True)

        assert limits["max_search_per_day"] == 10000
        assert limits["max_jobs_per_search"] == 500
        assert limits["max_matching_results"] == 100

    def test_is_feature_available(self):
        """Test feature availability check."""
        # Free features
        assert is_feature_available("job_search", is_pro=False) is True
        assert is_feature_available("company_profile", is_pro=False) is True

        # Pro features
        assert is_feature_available("advanced_matching", is_pro=False) is False
        assert is_feature_available("advanced_matching", is_pro=True) is True
        assert is_feature_available("data_export", is_pro=False) is False
        assert is_feature_available("data_export", is_pro=True) is True

    def test_get_limit_value(self):
        """Test getting limit values."""
        assert get_limit_value("max_search_per_day", is_pro=False) == 100
        assert get_limit_value("max_search_per_day", is_pro=True) == 10000

    def test_get_edition_info(self):
        """Test getting edition info."""
        info = get_edition_info(is_pro=False)

        assert info["is_pro"] is False
        assert info["edition"] == "免费版"
        assert "features" in info
        assert "limits" in info

    def test_get_edition_info_pro(self):
        """Test getting pro edition info."""
        info = get_edition_info(is_pro=True)

        assert info["is_pro"] is True
        assert info["edition"] == "专业版"

    def test_get_upgrade_info(self):
        """Test getting upgrade info."""
        info = get_upgrade_info()

        assert "current" in info
        assert "upgrade_to" in info
        assert "benefits" in info
        assert "pricing" in info
        assert "trial" in info
        assert info["trial"]["days"] == 7
