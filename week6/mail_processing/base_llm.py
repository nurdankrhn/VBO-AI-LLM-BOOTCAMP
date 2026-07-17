from langchain.chat_models import init_chat_model
import os 
from dotenv import load_dotenv

load_dotenv()

# Embedding
llm = init_chat_model(
        "openai:google/gemini-2.5-flash-lite",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=500)