import asyncio

from backend.db.connection import AsyncSessionLocal, engine
from backend.models.customer import Base, Customer


CUSTOMERS = [
    {"name": "Alice Johnson", "gender": "Female", "location": "New York"},
    {"name": "Bob Smith", "gender": "Male", "location": "London"},
    {"name": "Charlie Brown", "gender": "Male", "location": "Toronto"},
    {"name": "Diana Wilson", "gender": "Female", "location": "Sydney"},
    {"name": "Ethan Davis", "gender": "Male", "location": "Berlin"},
    {"name": "Fiona Miller", "gender": "Female", "location": "Paris"},
    {"name": "George Moore", "gender": "Male", "location": "Tokyo"},
    {"name": "Hannah Taylor", "gender": "Female", "location": "Mumbai"},
    {"name": "Ian Anderson", "gender": "Male", "location": "Singapore"},
    {"name": "Julia Thomas", "gender": "Female", "location": "Dubai"},
]

async def seed_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        try:
            for customer_data in CUSTOMERS:
                customer = Customer(**customer_data)
                session.add(customer)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())