# Week 4 Homework — Memory, Persistence & Context Engineering

**Duration:** ~4 hours
**Languages/Versions:** Python 3.12, `langchain>=1.2.0`, `langgraph`
**LLM:** OpenRouter (`google/gemini-2.5-flash-lite`) or any model you prefer
**Database:** PostgreSQL 16 with pgvector (Docker container)
**Rule:** Do **not** expose your API key in code. Use environment variables / `.env` only.

---

## Objective

Build a **memory-enabled assistant** that actually remembers its users. Across
**four small scripts** (one per part), you'll cover all four Week 4 lessons:

1. **Short-term memory** — a `checkpointer` so a conversation survives across
   `invoke` calls *and* across a process restart.
2. **Long-term memory** — a `store` the agent writes to via tools, so facts
   learned in one conversation are recalled in a brand-new conversation.
3. **Context engineering** — keep the token cost bounded as the chat grows.
4. **Human-in-the-loop** — gate a sensitive action behind a human approval.

---

## What you'll need

Set this up however you like — your call on tooling:

- A running **PostgreSQL** instance (pgvector image recommended, reachable on a
  `DB_URI` you control). The same `langgraph_db` container from earlier weeks works.
- **langchain ≥ 1.2.0**, **langgraph**, and the Postgres checkpointer/store
  (`PostgresSaver` and `PostgresStore` both live in `langgraph-checkpoint-postgres`).
- Your LLM API key in a `.env` (never in code).

---

## Tasks

### Part 1 — Short-term memory

Give the agent a checkpointer so a conversation persists within a thread and
survives a process restart (state in Postgres, not RAM).

Target scenario — same thread `alice-1`:

| # | Human says | Expected agent behaviour |
| - | ---------- | ------------------------ |
| 1 | "Hi, I'm alice. I live in Istanbul." | Acknowledges. |
| 2 | "What's my home city?" | "Istanbul." — answered from memory, **you did not re-send turn 1**. |

Then **stop and re-run the script**: the checkpoint count for `alice-1` must have
grown — proof the state was on disk, not in RAM.

### Part 2 — Long-term memory

Give the agent a store plus tools to save and recall durable facts about a user.

Target scenario — two **different** threads:

| Thread | Human says | Expected agent behaviour |
| ------ | ---------- | ------------------------ |
| `alice-1` | "I'm alice. I live in Istanbul, I'm vegetarian, mid-range budget." | Saves all three facts to the store. |
| `alice-2` (fresh, no shared history) | "I'm alice. What do you know about me?" | "You live in Istanbul, you're vegetarian, mid-range budget." — recalled from the store. |

Same three facts go in (thread `alice-1`) and come back out (thread `alice-2`) —
nothing extra, nothing missing.

### Part 3 — Context engineering

Once the conversation passes **10 messages**, summarize the old turns so the
history stops growing. Print proof — the message count the model receives each
turn. With summarization it stays **bounded** (peaks, then drops as old turns are
folded) instead of climbing one-per-turn:

```
Turn  8 → model received  9 messages
Turn  9 → model received  5 messages   ← summarized: old turns folded into 1
Turn 10 → model received  7 messages
Turn 12 → model received  5 messages   ← bounded, not growing toward 24
```

### Part 4 — Human-in-the-loop

Gate a sensitive action (e.g. a booking) behind a human approval.

Target scenario — thread `alice-1`:

| Step | Human / decision | Expected agent behaviour |
| ---- | ---------------- | ------------------------ |
| 1 | "Book a table at Çiya for 2 on 2026-07-01." | **Pauses** — returns an interrupt, does **not** book yet. |
| 2 | human **approves** | Booking executes: "Booked Çiya for 2…". |
| 3 | (alt run) human **rejects** | Booking is cancelled, nothing executed. |

### Bonus — Time travel

Rewind a thread to an earlier checkpoint and resume with a different message,
creating a second branch under the same thread.

Target scenario:

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | run a few turns on `alice-1` | a history of checkpoints exists |
| 2 | rewind to an earlier checkpoint, send a *different* message | a second branch under the same thread — original timeline still intact |

---

## CLI

One file per part — each runs on its own:

```bash
uv run python main1_short_term_memory.py
uv run python main2_long_term_memory.py
uv run python main3_context_engineering.py
uv run python main4_hitl_and_time_travel.py     # Part 4 + the time-travel bonus
```

Each script prints clearly labelled output proving its scenario.

---

## Deliverables

- `main1_short_term_memory.py` — Part 1
- `main2_long_term_memory.py` — Part 2
- `main3_context_engineering.py` — Part 3
- `main4_hitl_and_time_travel.py` — Part 4 + bonus
- `homework_answer.md` — reference write-up: setup, how to run, and the
  verification queries / observations that prove each part works.
- A short note answering: **what's the difference between a `checkpointer` and a
  `store`, and why might an agent need both?**

---

## Rubric

| Part | Points | What we check |
| ---- | ------ | ------------- |
| Short-term memory | 20 | Checkpointer + thread_id; survives restart |
| Long-term memory | 25 | Store tools; cross-thread recall; dict values |
| Context engineering | 20 | ≥2 techniques; bounded context shown via trace |
| Human-in-the-loop | 20 | interrupt → approve/reject via `Command(resume=...)` |
| Bonus: time travel | 10 | `get_state_history` rewind + branch |
| Write-up & hygiene | 5 | No leaked keys; clear README; checkpointer-vs-store answer |