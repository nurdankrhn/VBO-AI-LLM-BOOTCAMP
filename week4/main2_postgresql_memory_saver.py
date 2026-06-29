from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver
import os
from dotenv import load_dotenv
from rich.pretty import pprint

load_dotenv()

# model = init_chat_model(
#     model="gemini-2.5-flash-lite", 
#     model_provider="google_genai", 
#     max_tokens=300
# )
model = init_chat_model(
        "openai:google/gemini-2.5-flash-lite",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=500)



DB_URI = "postgresql://postgres:postgres@localhost:5432/langgraph_db?sslmode=disable"

thread_config = {"configurable": {"thread_id": "2"}}
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # Prepare tables
    checkpointer.setup()


    agent = create_agent(
    model=model,
    checkpointer=checkpointer,
    system_prompt="You are a helpful assistant. Answer user questions short and concisely."
)
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ("exit", "quit"):
            break

        result = agent.invoke({
            "messages":          
            {"role": "user", "content": user_input }
        }, thread_config)
        
        pprint(result['messages'][-1].content)