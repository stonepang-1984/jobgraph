"""Tests for License system."""

from datetime import datetime, timedelta

from src.jobgraph.license.manager import SecureLicenseManager


class TestLicenseManager:
    """Test License Manager."""

    def test_init_with_trial(self):
        """Test initialization with trial."""
        manager = SecureLicenseManager()

        # First run activates trial
        assert manager.is_pro is True
        assert manager.is_trial is True

    def test_verify_format_valid(self):
        """Test valid license format."""
        manager = SecureLicenseManager()

        # Valid format - each part is 4 chars
        assert manager._verify_format("JGP-ABCD-1234-EFGH-5678") is True

    def test_verify_format_invalid(self):
        """Test invalid license format."""
        manager = SecureLicenseManager()

        # Invalid format
        assert manager._verify_format("INVALID") is False
        assert manager._verify_format("JGP-0000-260629-PRO0-1234") is False
        assert manager._verify_format("XXX-00000000-260629-PRO0-1234") is False

    def test_compute_signature(self):
        """Test signature computation."""
        manager = SecureLicenseManager()

        sig1 = manager._compute_signature("test-data")
        sig2 = manager._compute_signature("test-data")
        sig3 = manager._compute_signature("other-data")

        assert sig1 == sig2
        assert sig1 != sig3
        assert len(sig1) == 4

    def test_extract_expire_time(self):
        """Test expire time extraction."""
        manager = SecureLicenseManager()

        # Valid key with expire date
        expire = manager._extract_expire_time("JGP-00000000-260629-PRO0-1234")
        assert expire is not None
        assert expire.year == 2026
        assert expire.month == 6
        assert expire.day == 29

    def test_extract_expire_time_invalid(self):
        """Test invalid expire time extraction."""
        manager = SecureLicenseManager()

        # Invalid key
        expire = manager._extract_expire_time("INVALID")
        assert expire is None

    def test_get_license_info_trial(self):
        """Test getting license info with trial."""
        manager = SecureLicenseManager()

        info = manager.get_license_info()

        assert info["is_pro"] is True
        assert info["is_trial"] is True
        assert info["days_remaining"] > 0

    def test_get_license_info_pro(self):
        """Test getting license info with pro license."""
        manager = SecureLicenseManager()
        manager.is_pro = True
        manager.is_trial = False
        manager.license_key = "JGP-TEST1234"
        manager.expire_at = datetime.now() + timedelta(days=30)

        info = manager.get_license_info()

        assert info["is_pro"] is True
        assert info["is_trial"] is False
        assert info["days_remaining"] >= 29  # Allow for timing differences


class TestLicenseVerification:
    """Test License verification."""

    def test_verify_offline_no_license(self):
        """Test offline verification without license."""
        manager = SecureLicenseManager()
        manager.license_key = None
        manager.is_trial = False

        assert manager._verify_offline() is False

    def test_verify_offline_trial_active(self):
        """Test offline verification with active trial."""
        manager = SecureLicenseManager()
        manager.is_trial = True
        manager.trial_expire_at = datetime.now() + timedelta(days=5)

        assert manager._verify_offline() is True

    def test_verify_offline_trial_expired(self):
        """Test offline verification with expired trial."""
        manager = SecureLicenseManager()
        manager.is_trial = True
        manager.trial_expire_at = datetime.now() - timedelta(days=1)

        assert manager._verify_offline() is False

    def test_check_pro_access_trial_active(self):
        """Test pro access check with active trial."""
        manager = SecureLicenseManager()
        manager.is_pro = True
        manager.is_trial = True
        manager.trial_expire_at = datetime.now() + timedelta(days=5)
        manager.expire_at = manager.trial_expire_at

        assert manager.check_pro_access() is True

    def test_check_pro_access_trial_expired(self):
        """Test pro access check with expired trial."""
        manager = SecureLicenseManager()
        manager.is_pro = True
        manager.is_trial = True
        manager.trial_expire_at = datetime.now() - timedelta(days=1)
        manager.expire_at = manager.trial_expire_at

        assert manager.check_pro_access() is False
