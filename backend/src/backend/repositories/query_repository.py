import asyncio
import re

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exception import QueryExecutionError, QueryTimeoutError
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
            raise QueryTimeoutError() from None
        except SQLAlchemyError as error:
            await self.session.rollback()
            raise QueryExecutionError() from error
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


