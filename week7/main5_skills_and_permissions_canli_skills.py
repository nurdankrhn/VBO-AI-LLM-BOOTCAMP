import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import FilesystemBackend

load_dotenv()


def make_model():
    return init_chat_model(
        "openai:anthropic/claude-haiku-4.5",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=3000,
    )

workspace = tempfile.mkdtemp(prefix="deepagents_skills_")
skill_dir = Path(workspace) / "skills" / "haiku-writer"
skill_dir.mkdir(parents=True)
(skill_dir / "SKILL.md").write_text(
    "---\n"
    "name: haiku-writer\n"
    "description: Write a haiku (5-7-5) about a topic and save it.\n"
    "---\n"
    "When asked for a haiku, write a 3-line haiku (5,7,5 syllables) about the "
    "topic and save it to <topic>_haiku.md using write_file.\n"
)

agent = create_deep_agent(
        model=make_model(),
        tools=[],
        backend=FilesystemBackend(root_dir=workspace, virtual_mode=True),
        skills=["/skills/"],                      # backend path to the skill source
        system_prompt="You are helpful. Use an available skill when it fits the request.",
    )

result = agent.invoke({"messages": [{"role": "user",
                                "content": "Use your haiku-writer skill to make a haiku about the ocean."}]})

print(result)