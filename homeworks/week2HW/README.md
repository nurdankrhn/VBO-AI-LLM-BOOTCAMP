# Week 2 Homework — A schema-aware Database MCP server

The problem with a single `run_sql_query(sql)` tool is that the agent is **blind**: it has
to guess table and column names. The right way to connect a database through MCP is to give
the agent **discovery tools** so it can read the schema at runtime, then write correct SQL.

You will build a FastMCP database server and reach it from an
agent through `MultiServerMCPClient`.

## The design — three tools, not one

| Tool | Returns |
|------|---------|
| `list_tables()` | the names of all tables in the database |
| `describe_table(table_name)` | each column with its type and whether it's nullable / a key |
| `run_select(sql, max_rows=50)` | the rows of a read-only `SELECT`, as a markdown table |

The agent should naturally chain them: **`list_tables` → `describe_table` → `run_select`**.
Nothing about the schema is hardcoded — the model discovers it.

## Task 1 — Build the server (`hw_db_server.py`)

- `FastMCP("Database")`, run with `mcp.run(transport="streamable-http")` on **its own port**.
- Implement the three tools above.
- **`describe_table` must use live introspection**, not a hardcoded DDL string. Use
  SQLAlchemy's inspector:
  ```python
  from sqlalchemy import inspect
  insp = inspect(engine)
  insp.get_table_names()
  insp.get_columns(table_name)   # -> name, type, nullable, ...
  ```
- `run_select` must **reject anything that isn't a SELECT** (safety guard), and cap rows.

## Task 2 — Client + agent (`hw_db_client.py`)

- Use `MultiServerMCPClient` to connect to your database server.
- Give all the tools to one `create_agent`.
- Ask a question that needs a **JOIN across two tables**, e.g.
  *"Engineering departmanındaki en yüksek maaşlı çalışanın adını ve maaşını ver."*
- Print the message trace and confirm the agent called `list_tables` / `describe_table`
  on **both** tables **before** `run_select` — i.e. it discovered the columns and the
  foreign key, it didn't guess them.

> **Seed two related tables** (PostgreSQL, via `PG_DSN`) so that the answer requires a JOIN:
> - `departments(id, name, location)`
> - `employees(id, full_name, department_id → departments.id, salary, country)`
>
> The department name lives in `departments` but the salary lives in `employees`, so the
> agent must read both schemas and JOIN on the foreign key. A short seed script with a few
> `INSERT`s is fine.

## Task 3 — Short answer (in comments)

1. Why is `list_tables` + `describe_table` + `run_select` better than a single
   `run_sql_query(sql)` tool? Give two concrete failure modes the discovery tools prevent.
2. `describe_table` reads the schema live with `inspect()`. Why is that better than writing
   the table's columns into the tool's docstring?
3. What is still unsafe about `run_select` even with the "SELECT only" guard, and name one
   way to harden it (think: row limits, timeouts, read-only DB role).

## Run / submit

```bash
# once: create + fill the two tables (needs PG_DSN)
python hw_db_seed.py
# terminal 1 (optional, for the multi-server bonus)
python main2_http_server.py
# terminal 2
python hw_db_server.py          # different port from the weather server
# terminal 3
python hw_db_client.py
```

Checklist:
- [ ] Two related tables seeded (`departments`, `employees`) so the answer needs a JOIN
- [ ] `describe_table` uses `inspect()` — no hardcoded column names anywhere
- [ ] `run_select` rejects non-SELECT statements and caps rows
- [ ] The agent calls a discovery tool *before* `run_select` in the trace
- [ ] Task 3 answered in comments
