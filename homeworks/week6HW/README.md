# Homework — SQL Query Agent over MCP (LangGraph)

## Goal

Build a **LangGraph** graph that connects to a PostgreSQL (Chinook) database
**through an MCP server** and turns a user request into a correct, runnable,
optimized SQL query. The graph must **prepare → fix → optimize**.

The graph talks to the database *only* through MCP tools — no direct DB calls in
the graph code.

## What to build

A LangGraph graph with three stages:

1. **Prepare** — read the request, pull the schema via MCP (`list_tables`,
   `get_table_schema`), and generate a `SELECT` query.
2. **Fix** — validate/run it via MCP (`validate_query`, `execute_query`). If it
   errors, feed the error back and regenerate. Loop until it runs (cap retries,
   e.g. 3).
3. **Optimize** — rewrite the working query for efficiency (explicit columns not
   `SELECT *`, proper `JOIN`s, `WHERE`/`LIMIT` where sensible), then run it once
   more to confirm it still works.

Output: the final optimized SQL and its result rows.

Load the MCP tools with `langchain-mcp-adapters`:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
client = MultiServerMCPClient({"database": {
    "transport": "streamable_http", "url": "http://localhost:8000/mcp&quot;}})
tools = await client.get_tools()
```

## Setup

```bash
# 1. Postgres + Chinook data
docker run --name chinook-postgres -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=Ankara06 -e POSTGRES_DB=traindb -p 5432:5432 -d postgres:16
docker cp chinook_pg_serial_pk_proper_naming.sql chinook-postgres:/tmp/
docker exec -i chinook-postgres psql -U postgres -d traindb \
  -f /tmp/chinook_pg_serial_pk_proper_naming.sql

# 2. deps + key
pip install -r requirements.txt
echo "OPENROUTER_API_KEY=your_key" > .env

# 3. start the MCP server (terminal 1) -> http://localhost:8000/mcp
python database_mcp_server.py

# 4. run your graph (terminal 2)
python sql_optimizer_graph.py
```

MCP tools exposed by `database_mcp_server.py`: `list_tables`,
`get_table_schema(table_names)`, `execute_query(query)` (SELECT-only),
`validate_query(query)`, `get_database_info`.

## Acceptance criteria

- Graph loads its tools from the MCP server over HTTP — no direct DB access in the graph.
- `prepare`, `fix` (with a retry loop on error), and `optimize` are real graph nodes, wired with edges.
- Request `"top 10 customers by total spend"` → returns a runnable, optimized query + results.
- A deliberately broken query is fixed automatically by the `fix` loop.

## Deliverables

- `sql_optimizer_graph.py` — your graph.
- The rendered graph PNG.
- A short run transcript: request → prepared query → one fix cycle → final optimized query + results.