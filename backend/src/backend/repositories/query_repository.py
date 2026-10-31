import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exception import QueryExecutionError, QueryTimeoutError
from backend.core.logging import get_logger

logger = get_logger(__name__)


class QueryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_read_only(
        self,
        sql: str,
        timeout_seconds: float = 10.0,
    ) -> list[dict[str, Any]]:
        

        try:
            result = await asyncio.wait_for(
                self.session.execute(text(sql)),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            await self.session.rollback()
            logger.warning("Database query timed out after %s seconds.", timeout_seconds)
            raise QueryTimeoutError() from None
        except SQLAlchemyError as error:
            await self.session.rollback()
            logger.exception("Database query execution failed.")
            raise QueryExecutionError() from error
        rows = result.mappings().all()

        return [dict(row) for row in rows]
