from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langchain.tools import tool, ToolRuntime
import os
from dotenv import load_dotenv
from rich.pretty import pprint

load_dotenv()


model = init_chat_model(
        "openai:google/gemini-2.5-flash-lite",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=500)

DB_URI = "postgresql://postgres:postgres@localhost:5432/langgraph_db?sslmode=disable"

thread_config = {"configurable": {"thread_id": "erkansirin06_20260625"}}


@tool
def save_preference(user_id: str, key: str, value: str, runtime: ToolRuntime) -> str:
    """Save a user preference (e.g. theme, language) for future recall."""
    runtime.store.put((user_id, "preferences"), key, {"value": value})
    return f"Saved {key}={value!r} for user {user_id}."


@tool
def get_preference(user_id: str, key: str, runtime: ToolRuntime) -> str:
    """Retrieve a previously-saved user preference."""
    item = runtime.store.get((user_id, "preferences"), key)
    if not item:
        return f"No '{key}' preference found for user {user_id}."
    return f"{user_id}'s {key} preference is {item.value['value']!r}."

# DB connection — from_conn_string() returns a CONTEXT MANAGER, not the object
# itself, so we must enter it with `with`. The connection (and therefore the
# store/checkpointer and the agent that use it) is only valid inside this block.
with (
    PostgresStore.from_conn_string(DB_URI) as store,
    PostgresSaver.from_conn_string(DB_URI) as checkpointer,
):
    # Prepare tables (idempotent — safe to call every run)
    store.setup()
    checkpointer.setup()

    agent = create_agent(
        model=model,
        tools=[save_preference, get_preference],
        checkpointer=checkpointer,
        store=store,
        system_prompt=(
            "You manage user preferences. When a user mentions a preference "
            "(theme, language, etc.), call save_preference. When they ask about "
            "one, call get_preference. The user_id is provided in the question."
        ),
    )

    while True:
        user_input = input("User: ")
        if user_input.lower() in ("exit", "quit"):
            break

        result = agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        }, thread_config)

        pprint(result['messages'][-1].content)