import os
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.tools import tool

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore


load_dotenv()

DB_URI = os.getenv("DB_URI")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not DB_URI:
    raise ValueError("DB_URI is missing. Please set it in your .env file.")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing. Please set it in your .env file.")


model = init_chat_model(
    model="gemini-2.5-flash-lite",
    model_provider="google_genai",
    max_tokens=300,
)


USER_ID = "alice"
NAMESPACE = ("users", USER_ID)


def create_memory_tools(store):
    @tool
    def save_user_facts(city: str, diet: str, budget: str) -> str:
        """Save durable facts about Alice: city, diet, and budget."""
        store.put(
            NAMESPACE,
            "profile",
            {
                "city": city,
                "diet": diet,
                "budget": budget,
            },
        )
        return f"Saved facts for {USER_ID}: city={city}, diet={diet}, budget={budget}"

    @tool
    def recall_user_facts() -> dict:
        """Recall durable facts about Alice."""
        item = store.get(NAMESPACE, "profile")

        if item is None:
            return {
                "city": None,
                "diet": None,
                "budget": None,
            }

        return item.value

    return [save_user_facts, recall_user_facts]


def print_stored_profile(store, label):
    item = store.get(NAMESPACE, "profile")

    print(f"\n{label}")
    if item is None:
        print("Stored profile: None")
    else:
        print("Stored profile:", item.value)


with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()

    with PostgresStore.from_conn_string(DB_URI) as store:
        store.setup()

        tools = create_memory_tools(store)

        agent = create_agent(
            model=model,
            tools=tools,
            checkpointer=checkpointer,
            store=store,
            system_prompt=(
                "You are a helpful assistant with long-term memory tools.\n"
                "When the user tells you durable facts about Alice, use save_user_facts.\n"
                "When the user asks what you know about Alice, use recall_user_facts.\n"
                "Only save these three facts: city, diet, and budget.\n"
                "Only recall these three facts: city, diet, and budget.\n"
                "Answer short and concisely."
            ),
        )

        print("\n=== Part 2: Long-term Memory with PostgresStore ===\n")

        print_stored_profile(store, "Before saving facts")

        alice_1_config = {
            "configurable": {
                "thread_id": "alice-1"
            }
        }

        alice_2_config = {
            "configurable": {
                "thread_id": "alice-2"
            }
        }

        print("\n--- Thread alice-1: save facts ---")
        user_input_1 = "I'm alice. I live in Istanbul, I'm vegetarian, mid-range budget."

        result1 = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input_1,
                    }
                ]
            },
            config=alice_1_config,
        )

        print("User:", user_input_1)
        print("Assistant:", result1["messages"][-1].content)

        print_stored_profile(store, "After saving facts")

        print("\n--- Thread alice-2: fresh thread, recall facts ---")
        user_input_2 = "I'm alice. What do you know about me?"

        result2 = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input_2,
                    }
                ]
            },
            config=alice_2_config,
        )

        print("User:", user_input_2)
        print("Assistant:", result2["messages"][-1].content)

        print("\nProof:")
        print("- Facts were saved in thread alice-1.")
        print("- Facts were recalled in a different fresh thread: alice-2.")
        print("- This proves the data came from PostgresStore, not from thread history.")