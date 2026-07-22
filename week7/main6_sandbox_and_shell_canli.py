import os
import tempfile

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

load_dotenv()


def make_model():
    return init_chat_model(
        "openai:anthropic/claude-haiku-4.5",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=4000,
    )

workdir = tempfile.mkdtemp(prefix="deepagents_shell_")
print(f"Workspace: {workdir}\n")


agent = create_deep_agent(
        model=make_model(),
        tools=[],
        backend=LocalShellBackend(root_dir=workdir, virtual_mode=True),
        system_prompt=(
            "You are a shell-capable assistant. Use the execute tool to run shell "
            "commands. Keep commands simple and safe."
        ),
    )

task = (
        "Use execute to: (1) print the python version, (2) create a file "
        "hello.txt containing the word 'shell', then (3) cat hello.txt. "
        "Report the outputs."
    )
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

print(result)