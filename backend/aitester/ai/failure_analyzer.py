"""
AI-powered failure analysis for failed test results.
Uses Gemini to explain why a test failed and suggest fixes.
"""

import json
import logging
from typing import Any

from aitester.ai.client import BaseAIClient, get_ai_client
from aitester.ai.prompts import FAILURE_ANALYSIS_PROMPT
from aitester.ai.validators import validate_failure_analysis_output
from aitester.db.models import TestCase, TestResult

logger = logging.getLogger("aitester.ai.failure_analyzer")


class FailureAnalyzer:
    """
    Analyzes failed test results using Gemini to determine root causes
    and suggest fixes.
    """

    def __init__(self, ai_client: BaseAIClient | None = None):
        self.ai_client = ai_client or get_ai_client()

    async def analyze(
        self, test_result: TestResult, test_case: TestCase
    ) -> dict[str, Any] | None:
        """
        Analyzes a single failed test result.
        `test_case` must be passed explicitly — Beanie has no lazy relationships.
        Returns a structured analysis dict or None on failure.
        """
        if test_result.passed:
            logger.info("Test passed. No failure analysis needed.")
            return None

        test_case_info = {
            "category": test_case.category,
            "endpoint": test_case.endpoint,
            "method": test_case.method,
            "expected_status_code": test_case.expected_status_code,
            "headers": test_case.headers,
            "query_params": test_case.query_params,
            "body": test_case.body,
        }

        prompt = FAILURE_ANALYSIS_PROMPT.format(
            test_case=json.dumps(test_case_info, indent=2),
            status_code=test_result.actual_status_code or "Unknown",
            response_body=test_result.actual_body or "None",
        )

        try:
            analysis: dict[str, Any] = await self.ai_client.generate_with_retry(
                prompt, validate_failure_analysis_output
            )
            return analysis
        except Exception as e:
            logger.error(
                f"Failure analysis failed for test_case {test_case.id}: {e}"
            )
            return None
