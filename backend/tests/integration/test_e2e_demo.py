"""
Skipped: CLI-based e2e tests removed in Phase 1 (CLI module dropped).
These tests will be replaced with HTTP API integration tests in Phase 3.
"""

import pytest


@pytest.mark.skip(reason="CLI removed — will be replaced with API integration tests in Phase 3")
def test_e2e_placeholder():
    """Placeholder — kept so pytest doesn't error on empty module."""
    pass
