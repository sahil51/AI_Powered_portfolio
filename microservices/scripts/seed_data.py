import asyncio
import logging
import uuid

from infrastructure.database.models import UserModel
from infrastructure.database.session import db

logger = logging.getLogger("ai_assistant")


async def seed_users():
    async with db.session_factory() as session:
        user = UserModel(
            id=uuid.uuid4(),
            name="Sahil",
            email="sahil@example.com",
            user_type="visitor",
        )
        session.add(user)
        await session.commit()
        logger.info(f"Seeded user: {user.id}")


if __name__ == "__main__":
    asyncio.run(seed_users())
