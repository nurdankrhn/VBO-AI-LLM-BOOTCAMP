from sqlmodel import Session, create_engine
import os
from langchain.tools import tool
from sqlmodel import Session
from sqlalchemy import text
from textwrap import shorten
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv


load_dotenv()  # GOOGLE_API_KEY (and any other secrets like PG_DSN) come from .env


class EmployeeTableSchema(BaseModel):
    """Arguments for querying the `employees` table.

    Table schema (PostgreSQL):
        CREATE TABLE employees (
            id          SERIAL PRIMARY KEY,
            full_name   VARCHAR(100) NOT NULL,
            department  VARCHAR(50)  NOT NULL,
            salary      INTEGER      NOT NULL CHECK (salary > 0),
            country     VARCHAR(50)  NOT NULL,
            created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
        );
    """

    sql: str = Field(
        description=(
            "A read-only PostgreSQL SELECT statement against the employees table. "
            "Use single quotes for string literals, e.g. WHERE country = 'USA'."
        )
    )
    max_rows: int = Field(
        default=20,
        description="Maximum number of rows to return.",
    )


# Get db engine
def get_engine():
    dsn = os.getenv("PG_DSN")
    if not dsn:
        raise RuntimeError("PG_DSN environment variable not set")
    return create_engine(dsn, echo=False)

engine = get_engine()

@tool(args_schema=EmployeeTableSchema)
def run_sql_query(sql: str, max_rows: int = 20) -> str:
    """
    Execute a read-only PostgreSQL SELECT statement and return results
    as a markdown table.

    Rules:
    - Only SELECT queries are allowed (safety guard).
    - Target dialect is PostgreSQL.
    - Use SINGLE quotes for string literals: WHERE country = 'France'.
    - Use DOUBLE quotes only for identifiers when needed: "Order Date".
    - Do not use backticks (those are MySQL).
    """
     
    normalized = sql.strip().lower()
    if not normalized.startswith("select"):
        raise ValueError("This tool only supports SELECT queries.")
    
    with Session(engine) as session:
        result = session.exec(text(sql))
        rows = result.fetchall()
        if not rows:
            return "Query executed successfully, but returned 0 rows."
        
        col_names = result.keys()
        rows = rows[:max_rows]

        # Format as Markdown
    header = "| " + " | ".join(col_names) + " |"
    sep = "| " + " | ".join("---" for _ in col_names) + " |"

    body = []
    for r in rows:
        body.append(
            "| "
            + " | ".join(shorten(str(v), width=80, placeholder="…") for v in r)
            + " |"
        )

    table = "\n".join([header, sep] + body)
    if len(body) == max_rows:
        table += f"\n\n_NOTE: truncated to {max_rows} rows._"

    return table

llm = init_chat_model(
    model="gemini-2.5-flash-lite",
    model_provider="google_genai",
    temperature=0.1,
)

agent = create_agent(
    model=llm,
    tools=[run_sql_query],
    system_prompt="You are helpful assistant. Answer user questions using tools provided."
)

result = agent.invoke({
    "messages": [
        HumanMessage(content="Bana employees tablosunda country USA en yüksek maşı olan 3 çalışanın isimlerini ver ")
        #HumanMessage(content="Show me the last 10 employees ordered by salary desc.")
    ]
})

print(result)