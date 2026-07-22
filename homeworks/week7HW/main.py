import json
import os
import sys
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter


PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_EXECUTABLE = sys.executable

ORDERS_FILE = PROJECT_ROOT / "orders.csv"
SKILL_FILE = (
    PROJECT_ROOT
    / "skills"
    / "data-investigation"
    / "SKILL.md"
)
TRANSCRIPT_FILE = PROJECT_ROOT / "run_transcript.jsonl"

QUESTION_FILES = [
    "q1.md",
    "q2.md",
    "q3.md",
    "q4.md",
    "q5.md",
]

EXPECTED_FILES = [
    "profile.md",
    *QUESTION_FILES,
    "REPORT.md",
]

load_dotenv(PROJECT_ROOT / ".env")


# Yaklaşık 5 saniyede bir model isteğine izin verir.
MODEL_RATE_LIMITER = InMemoryRateLimiter(
    requests_per_second=0.2,
    check_every_n_seconds=0.1,
    max_bucket_size=1,
)


def validate_project_files() -> None:
    """Gerekli proje dosyalarının mevcut olduğunu doğrular."""

    missing_files = []

    if not ORDERS_FILE.is_file():
        missing_files.append(str(ORDERS_FILE))

    if not SKILL_FILE.is_file():
        missing_files.append(str(SKILL_FILE))

    if missing_files:
        raise FileNotFoundError(
            "Required project files are missing:\n- "
            + "\n- ".join(missing_files)
        )


def clear_previous_outputs() -> None:
    """Önceki çalıştırmadan kalan çıktı dosyalarını temizler."""

    files_to_remove = [
        *EXPECTED_FILES,
        "analyze_orders.py",
    ]

    removed_files = []

    for filename in files_to_remove:
        file_path = PROJECT_ROOT / filename

        if file_path.is_file():
            file_path.unlink()
            removed_files.append(
                str(file_path.relative_to(PROJECT_ROOT))
            )

    # Önceki hatalı write_file yollarından kalabilecek dosyaları temizle.
    accidental_patterns = [
        "home/**/profile.md",
        "home/**/q1.md",
        "home/**/q2.md",
        "home/**/q3.md",
        "home/**/q4.md",
        "home/**/q5.md",
        "home/**/REPORT.md",
    ]

    for pattern in accidental_patterns:
        for file_path in PROJECT_ROOT.glob(pattern):
            if file_path.is_file():
                file_path.unlink()
                removed_files.append(
                    str(file_path.relative_to(PROJECT_ROOT))
                )

    if removed_files:
        print("\nPrevious output files removed:")
        for filename in removed_files:
            print(f"- {filename}")
    else:
        print("\nNo previous output files found.")


def make_model():
    """Anthropic Claude modelini oluşturur."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY was not found in "
            "homeworks/week7HW/.env."
        )

    return init_chat_model(
        model="claude-haiku-4-5-20251001",
        model_provider="anthropic",
        temperature=0,
        max_tokens=2500,
        timeout=180,
        max_retries=5,
        rate_limiter=MODEL_RATE_LIMITER,
    )


QUESTION_ANALYST_PROMPT = f"""
You are a question-specific data analyst.

You receive exactly:
- one analytics question,
- one virtual output path.

Your job is to calculate the exact answer and create only the requested
Markdown file.

Mandatory dataset rules:
- Load the dataset only with:
  pd.read_csv("orders.csv")
- Never use pd.read_csv("/orders.csv").
- Never inspect orders.csv with read_file, ls, glob, grep, cat, head, or tail.
- Never estimate or invent numerical results.

Mandatory execute rules:
- execute accepts shell commands, not bare Python statements.
- Use exactly one execute call.
- Run pandas with this exact shell structure:

  {PYTHON_EXECUTABLE} - <<'PY'
  import pandas as pd
  df = pd.read_csv("orders.csv")
  # analysis code
  PY

- Never use a bare `python`, `python3`, or `python -c` command.
- Use the exact absolute interpreter path shown above.
- Do not create Python files such as analyze_orders.py.

Mandatory output-path rules:
- Filesystem tools use virtual paths.
- The requested file_path must be exactly one of:
  /q1.md
  /q2.md
  /q3.md
  /q4.md
  /q5.md
- Never use a real operating-system path such as /home/nurdan/...
  with write_file.
- Never derive a write_file path from PYTHON_EXECUTABLE.
- Use exactly one write_file call.
- Write only the requested question file.

Mandatory workflow:
1. Read the assigned question and requested virtual output path.
2. Use exactly one execute call to calculate the complete answer.
3. Use exactly one write_file call with the requested virtual path.
4. Include exact values and a one-line takeaway in the Markdown file.
5. After write_file succeeds, do not call another tool.
6. Return a brief completion message containing the exact result.

Do not call read_file after writing the output.
Do not solve questions other than the assigned question.
"""


question_analyst = {
    "name": "question-analyst",
    "description": (
        "Solves exactly one analytics question about orders.csv "
        "using pandas, then writes exactly one requested q1.md-q5.md "
        "file through its virtual path."
    ),
    "system_prompt": QUESTION_ANALYST_PROMPT,
}


TASK = f"""
Investigate orders.csv and produce a reproducible Markdown report.

Revenue per line is:

unit_price * quantity * (1 - discount_pct / 100)

Required files:

1. /profile.md
   Include:
   - exact row count,
   - minimum and maximum order_date,
   - exact count of every status.

2. /q1.md
   Determine which calendar month in YYYY-MM format had the highest
   completed-order revenue.

3. /q2.md
   Determine which category generated the most completed-order revenue.

4. /q3.md
   For every discount_pct level, calculate:

   100 * count(status in ["refunded", "cancelled"])
   / total order count at that discount level

   Include every discount level and state whether there is a trend.

5. /q4.md
   Determine the three countries with the most completed-order revenue.

6. /q5.md
   Calculate:

   100 * revenue of refunded or cancelled orders
   / revenue of all orders

   Report the exact percentage of potential revenue lost.

7. /REPORT.md
   Combine the results of q1.md through q5.md.
   Include a short conclusion for every question.

Global accuracy rules:
- Every numerical result must come from pandas through execute.
- Never estimate, approximate, or invent a result.
- Revenue calculations must use the formula given above.
- Clearly state whether each revenue result uses completed orders
  or all order statuses.

Mandatory planning rules:
- Your first tool call must be write_todos.
- Do not call read_file, execute, task, ls, or any other tool before
  write_todos.
- Create separate todos for:
  - profiling,
  - question 1,
  - question 2,
  - question 3,
  - question 4,
  - question 5,
  - output verification,
  - final report generation.
- Keep exactly one active in_progress todo at a time.
- Update the todo list after completing every major step.
- Mark every todo completed before finishing.

Mandatory coordinator rules:
- The coordinator may calculate only profile.md.
- The coordinator must not calculate or write q1.md through q5.md.
- Create profile.md before delegating question 1.
- Delegate questions 1 through 5 separately.
- Use the question-analyst sub-agent exactly once per question.
- Delegate questions sequentially, never in parallel.
- Wait for one sub-agent to finish before delegating the next.
- Include the exact requested virtual output path in every delegation:
  - question 1: /q1.md
  - question 2: /q2.md
  - question 3: /q3.md
  - question 4: /q4.md
  - question 5: /q5.md
- Use the exact result returned by each sub-agent when preparing REPORT.md.
- Do not recalculate sub-agent answers.

Mandatory coordinator dataset rules:
- Do not call read_file on orders.csv.
- Do not inspect orders.csv using ls, glob, grep, cat, head, or tail.
- Analyze the profile using exactly one execute call.
- Load the dataset only with:
  pd.read_csv("orders.csv")
- Use this exact interpreter:

  {PYTHON_EXECUTABLE}

- Run the profile calculation with a heredoc:

  {PYTHON_EXECUTABLE} - <<'PY'
  import pandas as pd
  df = pd.read_csv("orders.csv")
  # profile calculation
  PY

Mandatory filesystem path rules:
- Filesystem tools use virtual paths relative to the backend root.
- Write the profile using exactly:
  /profile.md
- Sub-agents must write question files using exactly:
  /q1.md
  /q2.md
  /q3.md
  /q4.md
  /q5.md
- Write the final report using exactly:
  /REPORT.md
- Never use /home/nurdan/... with write_file or read_file.
- Never use PROJECT_ROOT or PYTHON_EXECUTABLE to construct a write_file
  path.
- Real operating-system paths may be used only inside execute commands.

Mandatory output workflow:
- For profile.md, use one execute call and one write_file call.
- Do not read profile.md again after writing it.
- Do not read q1.md through q5.md after sub-agents create them.
- Use the exact completion summaries returned by the sub-agents to create
  REPORT.md.
- Create REPORT.md with exactly one write_file call.
- After REPORT.md is created, use exactly one ls call with path "/"
  to verify that all seven expected files exist.
- Do not use read_file for final verification.
- After verification, mark every todo completed and finish.
"""


def validate_outputs() -> None:
    """Beklenen çıktıların mevcut ve boş olmadığını doğrular."""

    missing_files = []
    empty_files = []

    for filename in EXPECTED_FILES:
        file_path = PROJECT_ROOT / filename

        if not file_path.is_file():
            missing_files.append(filename)
            continue

        if file_path.stat().st_size == 0:
            empty_files.append(filename)

    errors = []

    if missing_files:
        errors.append(
            "Missing files: " + ", ".join(missing_files)
        )

    if empty_files:
        errors.append(
            "Empty files: " + ", ".join(empty_files)
        )

    if errors:
        raise RuntimeError(
            "Output validation failed.\n"
            + "\n".join(errors)
        )

    print("\nAll expected output files were created successfully:")

    for filename in EXPECTED_FILES:
        file_path = PROJECT_ROOT / filename
        print(
            f"- {filename} "
            f"({file_path.stat().st_size} bytes)"
        )


def main() -> None:
    """Deep-agent veri analizi akışını çalıştırır."""

    validate_project_files()
    clear_previous_outputs()

    backend = LocalShellBackend(
        root_dir=str(PROJECT_ROOT),
        virtual_mode=True,
    )

    agent = create_deep_agent(
        model=make_model(),
        tools=[],
        subagents=[question_analyst],
        backend=backend,
        skills=["/skills/"],
        system_prompt=(
            "You are a coordinator. Follow the data-investigation skill."
        ),
    )

    try:
        with TRANSCRIPT_FILE.open(
            "w",
            encoding="utf-8",
        ) as transcript:
            for chunk in agent.stream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": TASK,
                        }
                    ]
                },
                stream_mode="updates",
                subgraphs=True,
                version="v2",
            ):
                print(chunk)

                transcript.write(
                    json.dumps(
                        chunk,
                        ensure_ascii=False,
                        default=str,
                    )
                    + "\n"
                )
                transcript.flush()

    except Exception:
        print(
            "\nAgent execution failed. "
            f"The partial transcript is available at: "
            f"{TRANSCRIPT_FILE}"
        )
        raise

    validate_outputs()


if __name__ == "__main__":
    main()