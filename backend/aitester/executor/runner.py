"""
Async test runner — executes a batch of TestCase documents against a target API
and returns a list of TestResult documents ready to be saved to MongoDB.
"""

import asyncio
import logging
import time

from beanie import PydanticObjectId

from aitester.core.config import settings
from aitester.core.exceptions import HTTPClientError
from aitester.db.models import TestCase, TestResult
from aitester.executor.http_client import ExecutorHTTPClient
from aitester.security.detector import SecurityDetector
from aitester.ai.failure_analyzer import FailureAnalyzer
import redis.asyncio as aioredis
import json

logger = logging.getLogger("aitester.executor")


class AsyncTestRunner:
    """
    Executes a batch of test cases concurrently against a target API.
    """

    def __init__(self, base_url: str, enable_ai: bool = False):
        self.client = ExecutorHTTPClient(base_url)
        # Limit concurrency to avoid overloading the target or the local machine
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TESTS)
        self.enable_ai = enable_ai
        self.failure_analyzer = FailureAnalyzer() if enable_ai else None
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def execute_all(self, test_cases: list[TestCase]) -> list[TestResult]:
        """
        Runs all provided test cases concurrently, up to MAX_CONCURRENT_TESTS at a time.
        """
        tasks = [self.execute_single(tc) for tc in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results: list[TestResult] = []
        for res in results:
            if isinstance(res, TestResult):
                valid_results.append(res)
            elif isinstance(res, Exception):
                logger.error(f"Unexpected runner error: {res}")

        try:
            await self.redis.close()
        except Exception:
            pass

        return valid_results

    async def execute_single(self, test_case: TestCase) -> TestResult:
        """
        Executes a single test case within the bounds of the concurrency semaphore.
        """
        async with self.semaphore:
            start_time = time.monotonic()

            # Ensure IDs are PydanticObjectId for Beanie
            run_id  = test_case.test_run_id  if isinstance(test_case.test_run_id,  PydanticObjectId) else PydanticObjectId(str(test_case.test_run_id))
            case_id = test_case.id           if isinstance(test_case.id,           PydanticObjectId) else PydanticObjectId(str(test_case.id))

            try:
                response = await self.client.request(
                    method=test_case.method,
                    path=test_case.endpoint,
                    headers=test_case.headers,
                    query_params=test_case.query_params,
                    body=test_case.body,
                )

                latency_ms  = (time.monotonic() - start_time) * 1000.0
                status_code = response.status_code
                response_text = response.text
                response_headers = dict(response.headers)

                # Determine pass/fail based on status code
                passed = status_code == test_case.expected_status_code

                # Security test — if detector flags vulnerability, mark as failed
                if test_case.category.startswith("SECURITY_"):
                    is_vuln = SecurityDetector.is_vulnerable(
                        test_case, status_code, response_text, response_headers
                    )
                    if is_vuln:
                        passed = False
                        response_text = f"[VULNERABILITY DETECTED]\n{response_text}"

                result = TestResult(
                    test_run_id=run_id,
                    test_case_id=case_id,
                    actual_status_code=status_code,
                    latency_ms=latency_ms,
                    response_time_ms=latency_ms,
                    actual_body=response_text[:4096],  # cap stored body size
                    passed=passed,
                    status="passed" if passed else "failed",
                    ai_failure_analysis=None,
                )

                if not passed and self.enable_ai and self.failure_analyzer:
                    try:
                        logger.info(f"Test case {case_id} failed. Running AI failure analysis...")
                        analysis = await self.failure_analyzer.analyze(result, test_case)
                        result.ai_failure_analysis = analysis
                    except Exception as e:
                        logger.error(f"Error during AI failure analysis: {e}")

                try:
                    await self.redis.publish(
                        f"run_progress:{str(run_id)}",
                        json.dumps({"passed": passed, "status": "completed"})
                    )
                except Exception as pub_exc:
                    logger.error(f"Failed to publish progress for run {run_id}: {pub_exc}")

                return result


            except HTTPClientError as e:
                latency_ms = (time.monotonic() - start_time) * 1000.0
                res = TestResult(
                    test_run_id=run_id,
                    test_case_id=case_id,
                    actual_status_code=0,   # 0 = network error
                    latency_ms=latency_ms,
                    response_time_ms=latency_ms,
                    actual_body=str(e),
                    passed=False,
                    status="failed",
                    ai_failure_analysis={"error": "network_error", "detail": str(e)},
                )
                try:
                    await self.redis.publish(
                        f"run_progress:{str(run_id)}",
                        json.dumps({"passed": False, "status": "completed"})
                    )
                except Exception:
                    pass
                return res
            except Exception as e:
                latency_ms = (time.monotonic() - start_time) * 1000.0
                logger.exception(f"Unhandled error executing {test_case.method} {test_case.endpoint}")
                res = TestResult(
                    test_run_id=run_id,
                    test_case_id=case_id,
                    actual_status_code=0,
                    latency_ms=latency_ms,
                    response_time_ms=latency_ms,
                    actual_body=str(e),
                    passed=False,
                    status="failed",
                    ai_failure_analysis={"error": "unhandled_exception", "detail": str(e)},
                )
                try:
                    await self.redis.publish(
                        f"run_progress:{str(run_id)}",
                        json.dumps({"passed": False, "status": "completed"})
                    )
                except Exception:
                    pass
                return res
