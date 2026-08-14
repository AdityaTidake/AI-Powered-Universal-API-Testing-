"""
Database Models Tests — Beanie/MongoDB edition.

Tests verify the Beanie Document schema definitions are structurally correct.
Since we use MongoDB/Beanie, these tests check field existence and defaults
without requiring a live DB connection.
"""

import pytest
from datetime import datetime


class TestBeanieModelDefaults:
    """Verify Beanie models have correct field definitions and defaults."""

    def test_user_model_fields(self):
        """User model should have all required fields with correct defaults."""
        from aitester.db.models import User
        # Check that required fields exist in model annotations
        fields = User.model_fields
        assert "email" in fields
        assert "hashed_password" in fields
        assert "full_name" in fields
        assert "is_active" in fields
        assert "plan" in fields
        assert "monthly_run_count" in fields

    def test_user_model_defaults(self):
        """User defaults should be sensible."""
        from aitester.db.models import User
        fields = User.model_fields
        # plan defaults to "free"
        assert fields["plan"].default == "free"
        # is_active defaults to True
        assert fields["is_active"].default is True
        # monthly_run_count defaults to 0
        assert fields["monthly_run_count"].default == 0

    def test_organization_model_fields(self):
        """Organization model should have owner_id and member_ids."""
        from aitester.db.models import Organization
        fields = Organization.model_fields
        assert "name" in fields
        assert "slug" in fields
        assert "owner_id" in fields
        assert "member_ids" in fields

    def test_project_model_fields(self):
        """Project model should have owner_id and optional org_id."""
        from aitester.db.models import Project
        fields = Project.model_fields
        assert "name" in fields
        assert "owner_id" in fields
        assert "org_id" in fields
        assert "openapi_spec" in fields

    def test_test_run_model_fields(self):
        """TestRun should have project_id, base_url, and status."""
        from aitester.db.models import TestRun
        fields = TestRun.model_fields
        assert "project_id" in fields
        assert "base_url" in fields
        assert "status" in fields
        assert fields["status"].default == "PENDING"

    def test_test_case_model_fields(self):
        """TestCase should have test_run_id, category, endpoint, method."""
        from aitester.db.models import TestCase
        fields = TestCase.model_fields
        assert "test_run_id" in fields
        assert "category" in fields
        assert "endpoint" in fields
        assert "method" in fields

    def test_test_result_model_fields(self):
        """TestResult should have passed, latency_ms, and ai_failure_analysis."""
        from aitester.db.models import TestResult
        fields = TestResult.model_fields
        assert "test_run_id" in fields
        assert "test_case_id" in fields
        assert "passed" in fields
        assert "latency_ms" in fields
        assert "ai_failure_analysis" in fields
        # Default not passed
        assert fields["passed"].default is False

    def test_collection_names(self):
        """All Beanie documents should declare their collection name."""
        from aitester.db.models import (
            User, Organization, Project, TestRun, TestCase, TestResult
        )
        assert User.Settings.name == "users"
        assert Organization.Settings.name == "organizations"
        assert Project.Settings.name == "projects"
        assert TestRun.Settings.name == "test_runs"
        assert TestCase.Settings.name == "test_cases"
        assert TestResult.Settings.name == "test_results"
