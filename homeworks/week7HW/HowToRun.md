# Deep Agents Order Investigation

A multi-agent data investigation project built with **Deep Agents**, **LangChain**, **Claude Haiku 4.5**, and a local shell backend.

The project analyzes `orders.csv` by executing real pandas code. A coordinator agent plans the workflow, profiles the dataset, delegates five isolated questions to a `question-analyst` sub-agent, verifies the generated files, and synthesizes the findings into `REPORT.md`.

## Deep-Agent Capabilities Used

| Capability | How it is used |
|---|---|
| Skill | The reusable investigation method is defined in `skills/data-investigation/SKILL.md` and loaded with `skills=["/skills/"]`. |
| Sub-agents | The coordinator delegates each of the five questions separately to the `question-analyst` through the `task` tool. |
| Planning | The coordinator creates and updates a plan with `write_todos` until every step is completed. |
| Execute | Every numerical result is calculated by running pandas through the `execute` shell tool. |
| Filesystem | The coordinator and sub-agents write seven real Markdown files to the shared backend root. |

Question isolation keeps each analysis focused on one calculation, reduces context interference, and makes every result easier to trace to its own `execute` call.

## Project Structure

```text
week7HW/
├── main.py
├── generate_data.py
├── orders.csv
├── requirements.txt
├── README.md
├── .env
├── run_transcript.jsonl
├── profile.md
├── q1.md
├── q2.md
├── q3.md
├── q4.md
├── q5.md
├── REPORT.md
└── skills/
    └── data-investigation/
        └── SKILL.md
```

## Dataset

`orders.csv` contains 6,000 online-store order records with the following columns:

```text
order_id, order_date, customer_id, country, category,
unit_price, quantity, discount_pct, status
```

Revenue per order line is calculated as:

```text
unit_price * quantity * (1 - discount_pct / 100)
```

The dataset can be regenerated deterministically with:

```bash
python3 homeworks/week7HW/generate_data.py
```

## Installation

From the repository root:

```bash
uv pip install -r homeworks/week7HW/requirements.txt
```

Alternatively:

```bash
pip install -r homeworks/week7HW/requirements.txt
```

## Environment Variable

Create `homeworks/week7HW/.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
```

Never commit the `.env` file. Ensure `.gitignore` contains:

```gitignore
.env
```

## Running the Project

From the repository root:

```bash
uv run homeworks/week7HW/main.py
```

The execution stream is printed to the terminal and also saved to:

```text
homeworks/week7HW/run_transcript.jsonl
```

## Workflow

1. Validate that `orders.csv` and `SKILL.md` exist.
2. Remove outputs left from an earlier run.
3. Create the coordinator and load the reusable investigation skill.
4. Call `write_todos` and track every step.
5. Run pandas through `execute` to create `profile.md`.
6. Delegate questions 1–5 sequentially to `question-analyst`.
7. Save each isolated answer to `q1.md` through `q5.md`.
8. Verify the generated files.
9. Combine the five findings into `REPORT.md`.
10. Mark every todo as completed and validate all outputs in Python.

## Backend and Path Rules

The backend is configured as:

```python
LocalShellBackend(
    root_dir=str(PROJECT_ROOT),
    virtual_mode=True,
)
```

Filesystem tools use virtual paths:

```text
/profile.md
/q1.md
/REPORT.md
```

Shell commands and pandas run inside the backend root and use relative dataset paths:

```python
pd.read_csv("orders.csv")
```

Real operating-system paths are used only for the Python interpreter passed to `execute`, never for `write_file`.

## Generated Results

| File | Result |
|---|---|
| `profile.md` | 6,000 rows; 2023-01-01 to 2024-12-27; 5,356 completed, 389 refunded, 255 cancelled |
| `q1.md` | Highest completed-order revenue month: `2023-11`, revenue `245728.354` |
| `q2.md` | Highest completed-order revenue category: Electronics, revenue `2112140.5985` |
| `q3.md` | Refund/cancel rate rises from 4.49% at 0% discount to 30.34% at 40%; strong positive trend |
| `q4.md` | US `1008048.9535`, DE `452360.7115`, UK `444536.917` |
| `q5.md` | Lost revenue percentage: `8.721975031476381%` |
| `REPORT.md` | Combined findings and a conclusion for every question |

## Acceptance Evidence

The successful run demonstrates:

- `write_todos` used for coordinator planning and all todos completed
- `task` called exactly five times, once per question
- pandas executed through the shell
- five isolated sub-agent analyses
- all seven Markdown outputs written to disk
- final Python validation confirming that every expected file exists and is non-empty
- a one-line coordinator system prompt

## Provider Note

The successful transcript in this repository uses Claude Haiku 4.5 through the direct Anthropic API. The original homework brief specifies Claude Haiku 4.5 through OpenRouter. The Deep-Agent workflow and acceptance behavior are the same, but the provider configuration should be changed to OpenRouter if that prerequisite is evaluated literally.