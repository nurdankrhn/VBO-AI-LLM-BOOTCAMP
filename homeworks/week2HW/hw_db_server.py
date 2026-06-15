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
async def describe_table(table_name: str) -> str:
    """
    Describe a table schema including:
    - columns
    - types
    - nullable
    - primary keys
    - foreign keys
    """

    print(f"TOOL CALLED -> describe_table({table_name})")

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


@mcp.tool()
async def run_select(sql: str, max_rows: int = 50) -> str:
    """
    Execute a read-only SELECT query and return results as markdown.
    """

    print(f"TOOL CALLED -> run_select({sql})")

    normalized = sql.strip().lower()

    if not normalized.startswith("select"):
        raise ValueError("Only SELECT statements are allowed.")

    with Session(engine) as session:

        result = session.exec(text(sql))

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

        markdown = "\n".join(
            [header, separator] + body
        )

        return markdown

app = mcp.streamable_http_app()

if __name__ == "__main__":
   uvicorn.run(app, host="0.0.0.0", port=8001)