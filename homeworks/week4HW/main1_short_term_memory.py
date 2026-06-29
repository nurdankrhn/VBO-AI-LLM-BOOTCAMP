import os
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver


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
    max_tokens=300
)


thread_config = {
    "configurable": {
        "thread_id": "alice-1"
    }
}


def get_checkpoint_count(checkpointer):
    checkpoints = list(checkpointer.list(thread_config))
    return len(checkpoints)


with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()

    agent = create_agent(
        model=model,
        checkpointer=checkpointer,
        system_prompt=(
            "You are a helpful assistant. "
            "Answer user questions short and concisely."
        )
    )

    print("\n=== Part 1: Short-term Memory with PostgresSaver ===\n")

    checkpoint_count = get_checkpoint_count(checkpointer)
    print(f"Current checkpoint count for alice-1: {checkpoint_count}")

    if checkpoint_count == 0:
        print("\nNo previous checkpoint found.")
        print("This looks like the first run.\n")

        user_input = input("User: ")

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            },
            config=thread_config
        )

        print("Assistant:", result["messages"][-1].content)

        print("\nNow stop the script and run it again.")
        print("On the next run, it will ask: What's my home city?")

    else:
        print("\nPrevious checkpoint found.")
        print("This looks like a restarted process.\n")

        user_input = "What's my home city?"

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            },
            config=thread_config
        )

        print("User:", user_input)
        print("Assistant:", result["messages"][-1].content)

    new_checkpoint_count = get_checkpoint_count(checkpointer)
    print(f"\nNew checkpoint count for alice-1: {new_checkpoint_count}")