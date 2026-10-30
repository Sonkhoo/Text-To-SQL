import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exception import AppException
from backend.db.connection import get_db
from backend.schemas.query import QueryRequest, QueryResponse
from backend.services.query_service import QueryService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "Up and running"
    }

@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    tags=["Query"],
)
async def query(
    request: QueryRequest,
    session: AsyncSession = Depends(get_db),
) -> QueryResponse:
    logger.info("Received customer query: %s", request.question)

    try:
        return await QueryService(session).answer(request)
    except AppException as error:
        logger.warning(
            "Query failed with %s: %s",
            error.code,
            error.message,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "code": error.code,
                "message": error.message,
            },
        ) from error
    except Exception as error:
        logger.exception("Unexpected customer query failure.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "The query could not be completed.",
            },
        ) from error