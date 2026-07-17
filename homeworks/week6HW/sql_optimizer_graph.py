import os
import re
import asyncio
from typing import Any, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
import json


load_dotenv()

MCP_URL = "http://localhost:8000/mcp"
MAX_RETRIES = 3

# Demo için deliberately broken query üretmek istersen True yap.
# Normal çalışmada False kalsın.
FORCE_BROKEN_QUERY_FOR_DEMO = False


model = init_chat_model(
    "openai:google/gemini-2.5-flash-lite",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    max_tokens=1000,
)


class SQLAgentState(TypedDict, total=False):
    user_question: str
    schema_context: str

    prepared_query: str
    fixed_query: str
    optimized_query: str

    result_rows: str
    validation_error: str
    optimization_error: str

    retry_count: int
    force_broken_query: bool


def extract_sql(text: str) -> str:
    """
    LLM bazen SQL'i ```sql ... ``` içinde döndürebilir.
    Bu fonksiyon sadece SQL kısmını temiz şekilde alır.
    """
    text = text.strip()

    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    # Baştaki açıklama varsa SELECT'ten itibaren al.
    select_match = re.search(r"\bselect\b", text, re.IGNORECASE)
    if select_match:
        text = text[select_match.start():].strip()

    return text.rstrip(";").strip()


def mcp_text(result: Any) -> str:
    """
    MCP tool result bazen direkt string/dict,
    bazen de [{'type': 'text', 'text': '...'}] formatında döner.
    Bu fonksiyon text içeriğini temiz şekilde alır.
    """

    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        if "text" in result:
            return str(result["text"])
        return json.dumps(result, ensure_ascii=False)

    if isinstance(result, list):
        texts = []

        for item in result:
            if isinstance(item, dict) and "text" in item:
                texts.append(str(item["text"]))
            else:
                texts.append(str(item))

        return "\n".join(texts)

    return str(result)


def mcp_text_list(result: Any) -> list[str]:
    """
    list_tables sonucu content block olarak gelirse sadece text alanlarını alır.
    """

    if isinstance(result, list):
        values = []

        for item in result:
            if isinstance(item, dict) and "text" in item:
                values.append(str(item["text"]))
            else:
                values.append(str(item))

        return values

    if isinstance(result, str):
        return [result]

    return [str(result)]


def normalize_validation_result(result: Any) -> dict:
    """
    validate_query MCP sonucu content block içinde JSON string olarak gelebilir.
    Bunu {'ok': bool, 'error': str | None} formatına çevirir.
    """

    text_result = mcp_text(result).strip()

    try:
        parsed = json.loads(text_result)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    if '"ok": true' in text_result.lower() or "'ok': true" in text_result.lower():
        return {"ok": True, "error": None}

    return {
        "ok": False,
        "error": text_result,
    }

async def build_graph(tools):
    tool_map = {tool.name: tool for tool in tools}

    required_tools = [
        "list_tables",
        "get_table_schema",
        "validate_query",
        "execute_query",
    ]

    missing_tools = [name for name in required_tools if name not in tool_map]

    if missing_tools:
        raise RuntimeError(f"Missing MCP tools: {missing_tools}")

    async def prepare_query(state: SQLAgentState) -> dict:
        """
        Prepare node:
        1. MCP ile tabloları alır.
        2. MCP ile schema bilgilerini alır.
        3. LLM ile ilk SELECT query'yi üretir.
        """

        print("\n===== NODE: prepare_query =====")

        tables_raw = await tool_map["list_tables"].ainvoke({})
        tables = mcp_text_list(tables_raw)

        print("Tables:", tables)

        schema_parts = []

        for table_name in tables:
            schema_raw = await tool_map["get_table_schema"].ainvoke(
                {"table_name": table_name}
            )

            schema_parts.append(mcp_text(schema_raw))

        schema_context = "\n\n".join(schema_parts)

        prompt = f"""
You are a PostgreSQL expert.

Generate one correct PostgreSQL SELECT query for the user request.

Rules:
- Use only the tables and columns from the schema.
- Do not guess table names.
- Do not guess column names.
- Return only SQL.
- Do not include markdown.
- Do not explain.

Database schema:
{schema_context}

User request:
{state["user_question"]}
"""

        msg = await model.ainvoke(prompt)
        prepared_query = extract_sql(msg.content)

        if state.get("force_broken_query") or FORCE_BROKEN_QUERY_FOR_DEMO:
            print("Forcing a deliberately broken query for demo...")
            prepared_query = """
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    SUM(i.total) AS total_spend
FROM customers c
JOIN invoices i ON i.customer_id = c.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spend DESC
LIMIT 10
""".strip()

        print("\nPrepared query:")
        print(prepared_query)

        return {
            "schema_context": schema_context,
            "prepared_query": prepared_query,
            "fixed_query": prepared_query,
            "retry_count": 0,
        }

    async def fix_query(
        state: SQLAgentState,
    ) -> Command[Literal["fix_query", "optimize_query", "__end__"]]:
        """
        Fix node:
        1. Query'yi MCP validate_query ile kontrol eder.
        2. Hata varsa LLM'e hata mesajını verip query'yi düzelttirir.
        3. Retry limitine kadar kendine döner.
        4. Çalışırsa execute_query ile sonucu alır ve optimize_query'ye gider.
        """

        print("\n===== NODE: fix_query =====")

        current_query = state.get("fixed_query") or state["prepared_query"]
        retry_count = state.get("retry_count", 0)

        validation_raw = await tool_map["validate_query"].ainvoke(
            {"query": current_query}
        )
        validation = normalize_validation_result(validation_raw)

        print("Validation result:", validation)

        if validation.get("ok"):
            print("Query is valid. Executing query...")

            result_rows_raw = await tool_map["execute_query"].ainvoke(
                {
                    "query": current_query,
                    "max_rows": 50,
                }
            )

            result_rows = mcp_text(result_rows_raw)

            return Command(
                update={
                    "fixed_query": current_query,
                    "result_rows": result_rows,
                    "validation_error": "",
                },
                goto="optimize_query",
            )

        if retry_count >= MAX_RETRIES:
            print("Max retries reached. Stopping graph.")

            return Command(
                update={
                    "validation_error": validation.get("error", "Unknown error"),
                },
                goto=END,
            )

        fix_prompt = f"""
You are a PostgreSQL expert.

Fix the broken SQL query using the database schema and the database error.

Rules:
- Return only corrected SQL.
- Do not include markdown.
- Do not explain.
- Keep the query meaning aligned with the user request.
- Use only SELECT.

User request:
{state["user_question"]}

Database schema:
{state["schema_context"]}

Broken SQL:
{current_query}

Database error:
{validation.get("error")}
"""

        msg = await model.ainvoke(fix_prompt)
        fixed_query = extract_sql(msg.content)

        print("\nFixed query candidate:")
        print(fixed_query)

        return Command(
            update={
                "fixed_query": fixed_query,
                "validation_error": validation.get("error", ""),
                "retry_count": retry_count + 1,
            },
            goto="fix_query",
        )

    async def optimize_query(state: SQLAgentState) -> dict:
        """
        Optimize node:
        1. Çalışan query'yi LLM ile optimize eder.
        2. Optimize edilmiş query'yi MCP ile validate eder.
        3. Çalışırsa onu execute eder.
        4. Çalışmazsa fixed_query'yi final olarak bırakır.
        """

        print("\n===== NODE: optimize_query =====")

        working_query = state["fixed_query"]

        optimize_prompt = f"""
You are a PostgreSQL query optimizer.

Rewrite the working SQL query for better readability and efficiency.

Rules:
- Do not change the meaning.
- Do not use SELECT *.
- Use explicit column names.
- Use proper JOINs.
- Keep LIMIT if it is useful.
- Return only SQL.
- Do not include markdown.
- Do not explain.

Database schema:
{state["schema_context"]}

Working SQL:
{working_query}
"""

        msg = await model.ainvoke(optimize_prompt)
        optimized_query = extract_sql(msg.content)

        print("\nOptimized query candidate:")
        print(optimized_query)

        validation_raw = await tool_map["validate_query"].ainvoke(
            {"query": optimized_query}
        )
        validation = normalize_validation_result(validation_raw)

        print("Optimized validation result:", validation)

        if validation.get("ok"):
            result_rows_raw = await tool_map["execute_query"].ainvoke(
                {
                    "query": optimized_query,
                    "max_rows": 50,
                }
            )

            result_rows = mcp_text(result_rows_raw)

            return {
                "optimized_query": optimized_query,
                "result_rows": result_rows,
                "optimization_error": "",
            }

        print("Optimized query failed. Falling back to fixed query.")

        return {
            "optimized_query": working_query,
            "optimization_error": validation.get("error", ""),
        }

    workflow = StateGraph(SQLAgentState)

    workflow.add_node("prepare_query", prepare_query)
    workflow.add_node("fix_query", fix_query)
    workflow.add_node("optimize_query", optimize_query)

    workflow.add_edge(START, "prepare_query")
    workflow.add_edge("prepare_query", "fix_query")
    workflow.add_edge("optimize_query", END)

    return workflow.compile()


async def main():
    client = MultiServerMCPClient(
        {
            "database": {
                "transport": "streamable_http",
                "url": MCP_URL,
            }
        }
    )

    tools = await client.get_tools()

    print("\nLoaded MCP tools:")
    for tool in tools:
        print(f"- {tool.name}")

    graph = await build_graph(tools)

    try:
        graph_png = graph.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(graph_png)
        print("\nGraph saved as workflow_graph.png")
    except Exception as e:
        print(f"\nCould not render graph PNG: {e}")

    result = await graph.ainvoke(
        {
            "user_question": "top 10 customers by total spend",
            "force_broken_query": False,
        }
    )

    print("\n===== FINAL RESULT =====")
    print("\nPrepared SQL:")
    print(result.get("prepared_query"))

    print("\nFixed SQL:")
    print(result.get("fixed_query"))

    print("\nOptimized SQL:")
    print(result.get("optimized_query"))

    print("\nResult rows:")
    print(result.get("result_rows"))

    if result.get("validation_error"):
        print("\nValidation error:")
        print(result.get("validation_error"))

    if result.get("optimization_error"):
        print("\nOptimization error:")
        print(result.get("optimization_error"))


if __name__ == "__main__":
    asyncio.run(main())