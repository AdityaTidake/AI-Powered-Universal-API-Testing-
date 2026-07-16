"""
v1 routes package.
All routers imported here so main.py has a single import point.
"""

from aitester.api.v1.routes import auth, projects, test_runs, reports

__all__ = ["auth", "projects", "test_runs", "reports"]
