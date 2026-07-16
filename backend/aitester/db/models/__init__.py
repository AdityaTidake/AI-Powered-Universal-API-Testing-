"""
Export all DB models so Alembic can discover them via Base.metadata.
Import order matters — base entities before join tables.
"""

from aitester.db.models.user import User
from aitester.db.models.organization import Organization
from aitester.db.models.org_member import OrgMember
from aitester.db.models.project import Project
from aitester.db.models.test_run import TestRun
from aitester.db.models.test_case import TestCase
from aitester.db.models.test_result import TestResult
from aitester.db.models.report import Report

__all__ = [
    "User",
    "Organization",
    "OrgMember",
    "Project",
    "TestRun",
    "TestCase",
    "TestResult",
    "Report",
]
