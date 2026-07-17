import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from sqlalchemy import create_engine, inspect, text
from sqlmodel import Session
import uvicorn

load_dotenv()

mcp = FastMCP("Database")


def get_engine():
    dsn = os.getenv("PG_DSN")

    if not dsn:
        raise RuntimeError("PG_DSN environment variable not set")

    return create_engine(dsn, echo=False)


engine = get_engine()

@mcp.tool()
async def list_tables() -> list[str]:
    """
    Return all table names in the database.
    """

    print("TOOL CALLED -> list_tables")

    insp = inspect(engine)

    return insp.get_table_names()


@mcp.tool()
async def get_table_schema(table_name: str) -> str:
    """
    Describe a table schema including:
    - columns
    - types
    - nullable
    - primary keys
    - foreign keys
    """

    print(f"TOOL CALLED -> get_table_schema({table_name})")

    insp = inspect(engine)

    columns = insp.get_columns(table_name)
    pk_info = insp.get_pk_constraint(table_name)
    fk_info = insp.get_foreign_keys(table_name)

    primary_keys = set(pk_info.get("constrained_columns", []))

    lines = [f"TABLE: {table_name}", ""]

    lines.append("Columns:")

    for col in columns:
        lines.append(
            f"- {col['name']} "
            f"type={col['type']} "
            f"nullable={col['nullable']} "
            f"primary_key={col['name'] in primary_keys}"
        )

    if fk_info:
        lines.append("")
        lines.append("Foreign Keys:")

        for fk in fk_info:
            lines.append(
                f"- {fk['constrained_columns']} "
                f"-> {fk['referred_table']}."
                f"{fk['referred_columns']}"
            )

    return "\n".join(lines)


def ensure_select_only(sql: str) -> str:
    """
    Allow only a single SELECT statement.
    """
    cleaned_sql = sql.strip()

    if cleaned_sql.endswith(";"):
        cleaned_sql = cleaned_sql[:-1].strip()

    normalized = cleaned_sql.lower()

    if not normalized.startswith("select"):
        raise ValueError("Only SELECT statements are allowed.")

    if ";" in cleaned_sql:
        raise ValueError("Only one SQL statement is allowed.")

    return cleaned_sql


@mcp.tool()
async def validate_query(query: str) -> dict:
    """
    Validate a SELECT query using PostgreSQL EXPLAIN.
    It does not return data rows.
    """

    print(f"TOOL CALLED -> validate_query({query})")

    try:
        safe_query = ensure_select_only(query)

        with Session(engine) as session:
            session.exec(text(f"EXPLAIN {safe_query}"))

        return {
            "ok": True,
            "error": None
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


@mcp.tool()
async def execute_query(query: str, max_rows: int = 50) -> str:
    """
    Execute a read-only SELECT query and return results as markdown.
    """

    print(f"TOOL CALLED -> execute_query({query})")

    safe_query = ensure_select_only(query)

    with Session(engine) as session:
        result = session.exec(text(safe_query))

        rows = result.fetchall()
        column_names = result.keys()

        rows = rows[:max_rows]

        if not rows:
            return "No rows returned."

        header = "| " + " | ".join(column_names) + " |"
        separator = "| " + " | ".join("---" for _ in column_names) + " |"

        body = []

        for row in rows:
            body.append(
                "| " + " | ".join(str(value) for value in row) + " |"
            )

        return "\n".join([header, separator] + body)


@mcp.tool()
async def get_database_info() -> str:
    """
    Return a compact database overview with table names and columns.
    """

    print("TOOL CALLED -> get_database_info")

    insp = inspect(engine)
    lines = []

    for table_name in insp.get_table_names():
        columns = insp.get_columns(table_name)
        column_names = [col["name"] for col in columns]

        lines.append(f"- {table_name}: {', '.join(column_names)}")

    return "\n".join(lines)



app = mcp.streamable_http_app()

if __name__ == "__main__":
   uvicorn.run(app, host="0.0.0.0", port=8000)