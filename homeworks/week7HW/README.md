# Homework — Data Investigation Deep Agent

## Goal

Build a deep agent that **investigates a real dataset by running code** and writes
a findings report. Every number in the report must come from **executed Python
(pandas)** — the agent is forbidden to estimate.

## The data

`orders.csv` — an online store's order log (6000 rows). Columns:

```
order_id, order_date, customer_id, country, category,
unit_price, quantity, discount_pct, status
```

- `status` is one of `completed`, `refunded`, `cancelled`.
- **Revenue per line** = `unit_price * quantity * (1 - discount_pct/100)`.

(Regenerate any time with `python3 generate_data.py` — it's deterministic.)

## What to produce

Seven files:

| File | Contents |
| ---- | -------- |
| `profile.md` | row count, date range, count of each `status` |
| `q1.md` | which calendar month (`YYYY-MM`) had the highest **completed**-order revenue |
| `q2.md` | which **category** generates the most completed-order revenue |
| `q3.md` | the **refund+cancellation rate at each discount level** — is there a trend? |
| `q4.md` | the **3 countries** with the most completed-order revenue |
| `q5.md` | the **% of total revenue lost** to refunded/cancelled orders |
| `REPORT.md` | combine `q1`–`q5` into one report, a short conclusion each |

Each answer file holds the exact number(s) plus a one-line takeaway.

## Requirements

Your solution must use **all five** Deep-Agent capabilities — and each must do real
work, not just be present:

1. **Skill.** Package the investigation *method* as a reusable
   `skills/data-investigation/SKILL.md` and load it (`skills=[...]`). The method —
   not the specific questions — lives in the skill, so the system prompt stays to a
   single line. The task supplies only the dataset + questions.
2. **Sub-agents.** Structure it as a **coordinator** + a **`question-analyst`
   sub-agent**. The coordinator plans, profiles, delegates, and synthesizes; each
   question is answered by the sub-agent **in its own isolated context** (called via
   the `task` tool, one question per call). Justify to yourself why isolation helps
   here.
3. **Planning.** The coordinator must decompose the work with `write_todos` and
   track each step to `completed`.
4. **Execute.** The analysis must actually **run pandas via the `execute` shell** —
   computed numbers, never estimates.
5. **Filesystem.** All seven files are real files on disk, shared between the
   coordinator and the sub-agents.

> **Watch the paths.** With a shell backend, the filesystem *tools* and the *shell*
> must agree on what a path means, or the agent will read the file from the wrong
> place and flail. Getting this right is the main trap in this homework — figure out
> the path setup that makes them consistent.

Print the tool calls in your run so you can prove the agent planned, delegated, and
actually executed code.

## Prerequisites

- `deepagents` and `pandas` installed.
- `OPENROUTER_API_KEY` in a `.env` (never commit it).
- `orders.csv` — ships with the homework, or regenerate with `python3 generate_data.py`.
- Model: **Claude Haiku 4.5 via OpenRouter** (deepagents is Claude-native; cap `max_tokens`).

## Acceptance criteria

- The tool-call summary shows **`write_todos`**, **`task` ×5** (each question
  delegated), and **`execute`** (pandas actually ran).
- All 7 files exist **on disk** — the `q*.md` files written by the sub-agents.
- All five answers are **correct** (reproducible — see the answer key).
- No number was estimated — each traces to an `execute` call.
- Only a **one-line** system prompt — the method comes from the skill.

## Deliverables

- `main.py` — your agent.
- `skills/data-investigation/SKILL.md` — the reusable method.
- The generated `REPORT.md`.
- A run transcript: the tool-call summary, the shell commands, and the report.

## Rubric

| Item | Points | Check |
| ---- | ------ | ----- |
| Skill | 15 | `SKILL.md` encodes the method; loaded via `skills=[...]`; drives the run from a one-line prompt |
| Sub-agents | 20 | `question-analyst` declared; each question delegated via `task` (isolated context) |
| Planning | 10 | `write_todos` — coordinator's own plan, tracked to completed |
| `execute` runs real analysis | 20 | pandas run via the shell, not prose math |
| Correct answers | 20 | All five match the answer key |
| Filesystem & hygiene | 15 | All 7 files on disk; paths handled right; numbers trace to `execute`; no key leaked |