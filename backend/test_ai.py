import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import sys

from aitester.db.models import TestCase, TestResult, Project, TestRun, User
from aitester.ai.failure_analyzer import FailureAnalyzer
import logging

logging.basicConfig(level=logging.DEBUG)

async def test_ai():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["specguard"]
    
    # Initialize beanie
    await init_beanie(
        database=db, 
        document_models=[TestCase, TestResult, Project, TestRun, User]
    )
    
    # Find a failed result
    result = await TestResult.find_one({"passed": False})
    if not result:
        print("No failed results found!")
        return
        
    test_case = await TestCase.get(result.test_case_id)
    if not test_case:
        print("Test case not found!")
        return
        
    print(f"Testing FailureAnalyzer for test case {test_case.id} (endpoint: {test_case.endpoint})")
    print(f"Result Status: {result.actual_status_code}")
    
    analyzer = FailureAnalyzer()
    analysis = await analyzer.analyze(result, test_case)
    
    print("\n--- ANALYSIS RESULT ---")
    print(analysis)

if __name__ == "__main__":
    asyncio.run(test_ai())
