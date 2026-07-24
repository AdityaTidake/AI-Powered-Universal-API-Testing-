"""
MongoDB / Beanie initialisation for SpecGuard AI.

Call `init_db()` once at application startup (inside the FastAPI lifespan).
All Beanie document classes are registered here.
"""

import motor.motor_asyncio
from beanie import init_beanie

from aitester.core.config import settings
from aitester.db.models import (
    Organization,
    Project,
    TestCase,
    TestResult,
    TestRun,
    User,
)


async def init_db() -> None:
    """Connect to MongoDB and initialise Beanie with all document models."""
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    db     = client[settings.MONGODB_DB_NAME]

    await init_beanie(
        database=db,
        document_models=[
            User,
            Organization,
            Project,
            TestRun,
            TestCase,
            TestResult,
        ],
    )
