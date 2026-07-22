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


# A specialized worker. The main agent delegates to it by name ("fact-writer")
# via the task tool. Its context is isolated from the coordinator's.
fact_writer = {
    "name": "fact-writer",
    "description": "Writes one concise factual sentence about a single topic to "
                   "<topic>.md. Delegate one topic per call.",
    "system_prompt": (
        "You are a fact writer. Given a topic, write exactly ONE concise factual "
        "sentence about it and save it to a file named <topic>.md using write_file. "
        "Reply with just the sentence."
    ),
}

workdir = tempfile.mkdtemp(prefix="deepagents_")
print(workdir)
agent = create_deep_agent(
        model=make_model(),
        tools=[],
        subagents=[fact_writer],
        backend=FilesystemBackend(root_dir=workdir, virtual_mode=True),
        system_prompt=(
            "You are a coordinator. You do NOT write files yourself. For each topic "
            "the user names, delegate the work to the 'fact-writer' sub-agent using "
            "the task tool, one topic per call. Then report what was created."
        ),
    )


task = "Create fact files for these three topics: python, sql, docker."

result = agent.invoke({"messages": [{"role": "user", "content": task}]})

print(result)