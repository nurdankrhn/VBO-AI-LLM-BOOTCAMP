---
name: data-investigation
description: Investigate tabular datasets with reproducible pandas analysis, delegated questions, planning, and file-based reporting.
---

# Data Investigation Method

Use this skill to analyze `orders.csv` and produce reproducible Markdown reports.

## Rules

- Never estimate or invent numerical results.
- Calculate every numerical result with pandas through `execute`.
- Do not create Python files such as `analyze_orders.py`.
- Do not put long Python scripts inside `write_file`.
- Run short pandas code directly with `execute`, and use `write_file` only for short Markdown output files.
- The dataset date column is `order_date`.
- The coordinator handles planning, profiling, delegation, verification, and `REPORT.md`.
- Delegate each question separately to the `question-analyst`.
- Run sub-agents sequentially, not in parallel.
- Give each sub-agent exactly one question and one output filename.
- The coordinator's first tool call must be `write_todos`.
- Do not call `read_file`, `execute`, or `task` before creating the todo list.
- Update todo statuses throughout the investigation.
- Mark every todo as completed before finishing.

## Paths

Filesystem tools and `execute` use different path formats.

- With filesystem tools, use virtual paths such as `/orders.csv` and `/q1.md`.
- With `execute`, shell commands, and pandas, use relative paths such as `orders.csv`.
- Load the dataset with:

  ```python
  df = pd.read_csv("orders.csv")
  ```

- Never use `pd.read_csv("/orders.csv")`.
- Do not inspect `orders.csv` with `read_file`, `glob`, `cat`, `head`, or similar tools.
- Write all output files in the project root.

## Workflow

1. Call `write_todos` as the first tool call.
2. Create separate todos for:
   - dataset profiling,
   - question 1,
   - question 2,
   - question 3,
   - question 4,
   - question 5,
   - output verification,
   - final report generation.
3. Use `execute` and pandas to create `profile.md`.
4. Delegate questions 1–5 separately to the `question-analyst`.
5. Verify the generated files.
6. Create `REPORT.md`.
7. Mark all todos as completed.

## Question Analyst

The `question-analyst` must:

- solve only the assigned question,
- use pandas through `execute`,
- load `orders.csv` with `pd.read_csv("orders.csv")`,
- calculate exact results without estimation,
- write only the requested Markdown file,
- include exact values and a one-line takeaway,
- return a brief completion message.

## Output Quality

- Use clear Markdown headings.
- Preserve meaningful numerical precision.
- Explain percentage calculations when relevant.
- State whether revenue includes completed orders or all statuses.