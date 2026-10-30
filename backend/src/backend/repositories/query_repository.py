import asyncio
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.query import CustomerResult



class QueryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_read_only(
        self,
        sql: str,
        timeout_seconds: float = 10.0,
    ) -> list[CustomerResult]:
        

        try:
            result = await asyncio.wait_for(
                self.session.execute(text(sql)),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            await self.session.rollback()
            raise TimeoutError("The database query timed out.") from None
        rows = result.mappings().all()

        return [
            CustomerResult(
                customer_id=row["customer_id"],
                name=row["name"],
                gender=row["gender"],
                location=row["location"],
            )
            for row in rows
        ]



