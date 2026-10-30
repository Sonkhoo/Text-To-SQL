from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must not be blank.")
        return value


class CustomerResult(BaseModel):
    customer_id: int
    name: str
    gender: str
    location: str


class QueryResponse(BaseModel):
    question: str
    sql: str
    results: list[CustomerResult]
    count: int
