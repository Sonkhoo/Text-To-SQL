# Text-To-SQL

An LLM-powered chat application that converts natural-language questions into
read-only SQL queries against a PostgreSQL customer database.

The application has:

- A FastAPI backend
- A React and Vite frontend
- Groq for SQL generation
- PostgreSQL with SQLAlchemy and asyncpg
- Read-only SQL validation
- Configurable rate limiting and query result limits
- Generic result rendering for customer rows, aggregates, groups, and distinct values

## Demo

![Queryly chat interface](docs/demo.svg)

The frontend provides suggested questions, natural-language query input,
generated SQL, and dynamically-rendered result tables.

## Requirements

- Python 3.13 or later
- `uv`
- Node.js and npm
- PostgreSQL
- A Groq API key

## Project structure

```text
backend/     FastAPI application, database models, seed script
frontend/    React and Vite chat interface
docs/        Project documentation assets
```

## Backend setup

Open a terminal in the `backend` directory:

```powershell
cd backend
uv sync
```

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your PostgreSQL connection string and Groq API key:

```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/text_to_sql
GROQ_MODEL=openai/gpt-oss-20b
QUERY_RATE_LIMIT=10/minute
QUERY_MAX_ROWS=100
```

Create the database and seed sample customers:

```powershell
uv run python -m backend.db.seed
```

Start the API:

```powershell
uv run uvicorn backend.main:app --reload
```

The API is available at `http://localhost:8000`.

Health check:

```text
GET http://localhost:8000/api/health
```

## Frontend setup

Open a second terminal in the `frontend` directory:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

The frontend environment file should contain:

```env
VITE_API_URL=http://localhost:8000
```

Start the development server:

```powershell
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

## API usage

Send a natural-language question to the query endpoint:

```powershell
curl -X POST http://localhost:8000/api/query `
  -H "Content-Type: application/json" `
  -d '{\"question\":\"Show all female customers from Mumbai\"}'
```

Example response:

```json
{
  "question": "Show all female customers from Mumbai",
  "sql": "SELECT customer_id, name, gender, location FROM customers WHERE location = 'Mumbai' LIMIT 100",
  "results": [
    {
      "customer_id": 8,
      "name": "Hannah Taylor",
      "gender": "Female",
      "location": "Mumbai"
    }
  ],
  "count": 1,
  "abstained": false,
  "message": null
}
```

Aggregate and grouped results are also supported:

```json
{
  "results": [
    {
      "location": "Mumbai",
      "customer_count": 1
    }
  ],
  "count": 1
}
```

## Supported query types

The service supports read-only questions involving:

- Filtering with `WHERE`, `AND`, `OR`, and `NOT`
- Aggregations such as `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX`
- `GROUP BY` and `HAVING`
- Sorting and ordering
- Result limits
- Distinct values
- Joins and read-only subqueries
- Ranking queries that return ties
- Case-insensitive text matching

Write operations and schema changes are rejected. The generated SQL is never
allowed to insert, update, delete, drop, alter, truncate, or modify database
state. Queries without an explicit limit receive the configured
`QUERY_MAX_ROWS` limit.

If the model cannot safely generate SQL, the API returns an abstention response
with `abstained: true` and does not execute a database query.

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `GROQ_API_KEY` | Groq API key | Required |
| `GROQ_MODEL` | Groq model used for SQL generation | `openai/gpt-oss-20b` |
| `DATABASE_URL` | Async PostgreSQL connection string | Required |
| `LLM_TIMEOUT_SECONDS` | LLM request timeout | `30` |
| `DATABASE_TIMEOUT_SECONDS` | Database query timeout | `10` |
| `QUERY_RATE_LIMIT` | Per-client API rate limit | `10/minute` |
| `QUERY_MAX_ROWS` | Maximum returned rows | `100` |
| `LOG_LEVEL` | Backend log level | `INFO` |
| `VITE_API_URL` | Backend URL used by the frontend | `http://localhost:8000` |

## Validation

Backend Python compilation:

```powershell
cd backend
python -m compileall -q src
```

Frontend linting:

```powershell
cd frontend
npm run lint
```
