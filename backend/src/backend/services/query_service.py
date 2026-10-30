import asyncio
import re

from groq import APITimeoutError, AsyncGroq, GroqError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.exception import (
    LLMProviderError,
    QueryTimeoutError,
    QueryValidationError,
)
from backend.repositories.query_repository import QueryRepository
from backend.schemas.query import QueryRequest, QueryResponse


_SQL_BLOCK = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)

_SYSTEM_PROMPT = """You convert customer questions into one PostgreSQL SELECT query.
The only available table is customers with these columns:
customer_id INTEGER, name TEXT, gender TEXT, location TEXT.
Return only SQL, without markdown or explanation.
Select only customer_id, name, gender, and location.
Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or multiple statements.
"""
_DISALLOWED_SQL = re.compile(
    r"\b(ALTER|CALL|CREATE|DELETE|DROP|EXEC|GRANT|INSERT|REVOKE|TRUNCATE|UPDATE)\b",
    re.IGNORECASE,
)


class QueryService:
    def __init__(
        self,
        session: AsyncSession,
        client: AsyncGroq | None = None,
    ):
        self.repository = QueryRepository(session)
        settings = get_settings()
        self.client = client or AsyncGroq(
            api_key=settings.groq_api_key.get_secret_value(),
            timeout=settings.llm_timeout_seconds,
        )
        self.model = settings.groq_model
        self.llm_timeout_seconds = settings.llm_timeout_seconds
        self.database_timeout_seconds = settings.database_timeout_seconds

    async def answer(self, request: QueryRequest) -> QueryResponse:
        try:
            completion = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": request.question},
                    ],
                ),
                timeout=self.llm_timeout_seconds,
            )
        except (asyncio.TimeoutError, APITimeoutError):
            raise QueryTimeoutError() from None
        except GroqError as error:
            raise LLMProviderError() from error

        content = completion.choices[0].message.content
        if not content:
            raise QueryValidationError()

        sql = _extract_sql(content)
        statement = _validate_sql(sql)
        results = await self.repository.execute_read_only(
            statement,
            timeout_seconds=self.database_timeout_seconds,
        )

        return QueryResponse(
            question=request.question,
            sql=statement,
            results=results,
            count=len(results),
        )


def _extract_sql(content: str) -> str:
    match = _SQL_BLOCK.search(content)
    return (match.group(1) if match else content).strip()


def _validate_sql(sql: str) -> str:
    statement = sql.strip().rstrip(";").strip()

    if not statement:
        raise QueryValidationError()
    if not re.match(r"^SELECT\b", statement, re.IGNORECASE):
        raise QueryValidationError()
    if ";" in statement or "--" in statement or "/*" in statement or "*/" in statement:
        raise QueryValidationError()
    if _DISALLOWED_SQL.search(statement):
        raise QueryValidationError()
    if not re.search(r"\bFROM\s+customers\b", statement, re.IGNORECASE):
        raise QueryValidationError()
    if re.search(r"\b(JOIN|UNION|INTERSECT|EXCEPT|WITH)\b", statement, re.IGNORECASE):
        raise QueryValidationError()

    return statement
