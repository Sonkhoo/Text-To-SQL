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
from backend.core.logging import get_logger
from backend.repositories.query_repository import QueryRepository
from backend.schemas.query import QueryRequest, QueryResponse


_SQL_BLOCK = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)

_SYSTEM_PROMPT = """You convert customer questions into one PostgreSQL SELECT query.
The only available table is customers with these columns:
customer_id INTEGER, name TEXT, gender TEXT, location TEXT.
Return only SQL, without markdown or explanation.
For customer-row results, select customer_id, name, gender, and location.
Return the columns or aggregate values needed to answer the question.
Allowed operations include WHERE, AND, OR, NOT, COUNT, SUM, AVG, MIN, MAX,
DISTINCT, GROUP BY, HAVING, ORDER BY, LIMIT, joins, and read-only subqueries.
Use only the customers table and its columns.
When asking for the city or cities with the highest or lowest value, return all
ties using a read-only subquery or ranking expression. Do not use LIMIT 1 for
an extremum unless the user explicitly asks for exactly one result.
All name, gender, and location values should be returned in lowercase.
Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or multiple statements.
"""
_DISALLOWED_SQL = re.compile(
    r"\b("
    r"ALTER|ANALYZE|CALL|COMMENT|COMMIT|COPY|CREATE|DELETE|DO|DROP|"
    r"EXECUTE|GRANT|INSERT|INTO|LOCK|MERGE|REFRESH|REINDEX|RELEASE|RENAME|"
    r"REVOKE|ROLLBACK|SAVEPOINT|SET|TRUNCATE|UPDATE|VACUUM"
    r")\b",
    re.IGNORECASE,
)
logger = get_logger(__name__)


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
        self.query_max_rows = settings.query_max_rows

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
            logger.warning("LLM request timed out after %s seconds.", self.llm_timeout_seconds)
            raise QueryTimeoutError() from None
        except GroqError as error:
            logger.exception("LLM provider request failed.")
            raise LLMProviderError() from error

        content = completion.choices[0].message.content
        if not content:
            logger.warning("LLM returned an empty SQL response.")
            raise QueryValidationError()

        sql = _extract_sql(content)
        try:
            statement = _validate_sql(sql, max_rows=self.query_max_rows)
        except QueryValidationError:
            logger.warning("Rejected generated SQL: %s", sql)
            raise
        logger.info("Generated read-only SQL: %s", statement)
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


def _validate_sql(sql: str, max_rows: int = 100) -> str:
    statement = sql.strip().rstrip(";").strip()

    if not statement:
        raise QueryValidationError()
    if _DISALLOWED_SQL.search(_mask_sql_literals(statement)):
        raise QueryValidationError()

    return _apply_row_limit(statement, max_rows)


def _mask_sql_literals(sql: str) -> str:
    return re.sub(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", " ", sql)


def _apply_row_limit(sql: str, max_rows: int) -> str:
    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", sql, re.IGNORECASE)
    if limit_match:
        requested_limit = int(limit_match.group(1))
        if requested_limit <= max_rows:
            return sql
        return (
            sql[:limit_match.start(1)]
            + str(max_rows)
            + sql[limit_match.end(1):]
        )
    return f"{sql} LIMIT {max_rows}"
