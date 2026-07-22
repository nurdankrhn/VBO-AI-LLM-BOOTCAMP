import os
import tempfile

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from deepagents.backends import StateBackend, FilesystemBackend

load_dotenv()


def make_model():
    return init_chat_model(
        "openai:anthropic/claude-haiku-4.5",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=4000,
    )


TASK = "Write the text 'hello from deepagents' to a file note.txt, then read it back."

# 
workdir = tempfile.mkdtemp(prefix="deepagents_")
print(workdir)
agent = create_deep_agent(
    model=make_model(),
    tools=[],
    # virtual_mode=True maps the agent's paths (e.g. /note.txt) INTO root_dir,
    # instead of letting absolute paths escape to the real filesystem root.
    backend=FilesystemBackend(root_dir=workdir, virtual_mode=True),
    system_prompt="You are a careful assistant. Use the filesystem tools.",
)
result = agent.invoke({"messages": [{"role": "user", "content": TASK}]})

print(result)