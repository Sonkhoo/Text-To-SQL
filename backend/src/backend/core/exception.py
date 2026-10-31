class AppException(Exception):
    def __init__(self, message, code, status_code):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class LLMProviderError(AppException):
    def __init__(self):
        super().__init__(
            message="Unable to generate response",
            code="LLM_PROVIDER_ERROR",
            status_code=502
        )


class QueryExecutionError(AppException):
    def __init__(self):
        super().__init__(
            message="Unable to execute the generated query",
            code="QUERY_EXECUTION_ERROR",
            status_code=500
        )


class QueryValidationError(AppException):
    def __init__(self):
        super().__init__(
            message="The generated query is invalid",
            code="QUERY_VALIDATION_ERROR",
            status_code=400
        )


class QueryTimeoutError(AppException):
    def __init__(self):
        super().__init__(
            message="The query execution timed out",
            code="QUERY_TIMEOUT_ERROR",
            status_code=504
        )

class RateLimitExceededError(AppException):
    def __init__(self):
        super().__init__(
            message="Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )