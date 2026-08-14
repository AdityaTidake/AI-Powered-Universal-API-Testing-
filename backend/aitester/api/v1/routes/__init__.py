"""
v1 routes package.
All routers imported here so main.py has a single import point.
"""

from aitester.api.v1.routes import analytics, auth, orgs, projects, reports, test_runs

__all__ = ["analytics", "auth", "orgs", "projects", "reports", "test_runs"]
