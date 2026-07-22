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
        permissions=[
            FilesystemPermission(operations=["write"], paths=["/secret/**"], mode="deny"),
        ],
        system_prompt="You are helpful.",
    )

result = agent.invoke({"messages": [{"role": "user", "content":
        "Write 'hi' to /secret/pw.txt and also write 'hi' to /public/note.txt."}]})

print(result)