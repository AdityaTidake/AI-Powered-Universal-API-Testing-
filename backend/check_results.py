import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["specguard"]
    results = db["test_results"]
    
    total = await results.count_documents({})
    print(f"Total TestResult documents: {total}")
    
    with_ai = await results.count_documents({"ai_failure_analysis": {"$ne": None}})
    print(f"TestResult documents with ai_failure_analysis: {with_ai}")
    
    failures = await results.count_documents({"passed": False})
    print(f"Total failed tests: {failures}")

    doc = await results.find_one({"ai_failure_analysis": {"$ne": None}})
    if doc:
        print("Sample AI analysis:")
        print(doc["ai_failure_analysis"])

if __name__ == "__main__":
    asyncio.run(check_db())
