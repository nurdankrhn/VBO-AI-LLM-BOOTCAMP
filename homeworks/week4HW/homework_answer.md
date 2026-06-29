# Week 4 Homework — Memory, Persistence & Context Engineering

## Overview

This homework implements a memory-enabled assistant across four independent scripts. Each script demonstrates one Week 4 topic:

1. Short-term memory with PostgreSQL checkpointer
2. Long-term memory with PostgreSQL store and tools
3. Context engineering with summarization and rolling window
4. Human-in-the-loop approval and time travel with LangGraph checkpoints

The project uses Python 3.12, LangChain, LangGraph, PostgreSQL, and environment variables for API keys.

---

## Environment Setup

Required packages:

```bash
uv add langchain langgraph langchain-openai langchain-google-genai langgraph-checkpoint-postgres psycopg[binary] python-dotenv
```

The `.env` file is used for secrets and database connection configuration:

```env
DB_URI=postgresql://postgres:postgres@localhost:5432/langgraph
OPENROUTER_API_KEY=your_openrouter_api_key
GOOGLE_API_KEY=your_google_api_key
```

API keys are not written directly in the source code.

---

## How to Run

Each part is implemented as a separate script.

```bash
uv run python main1_short_term_memory.py
uv run python main2_long_term_memory.py
uv run python main3_context_engineering.py
uv run python main4_hitl_and_time_travel.py
```

---

# Part 1 — Short-term Memory

## Goal

The goal of this part is to prove that the conversation state is persisted in PostgreSQL using `PostgresSaver`, not just kept in RAM.

The assistant uses the same thread id:

```python
thread_id = "alice-1"
```

## Scenario

First run:

```text
User: Hi, I'm alice. I live in Istanbul.
Assistant: Acknowledges the message.
```

Second run:

```text
User: What's my home city?
Assistant: Istanbul.
```

In the second run, the first message is not re-sent. The assistant answers using the persisted checkpoint state.

## Observation

The script prints the checkpoint count before and after execution.

Example output:

```text
Current checkpoint count for alice-1: 0
User: Hi, I'm alice. I live in Istanbul.
Assistant: Hi Alice! Nice to meet you.

New checkpoint count for alice-1: 2
```

After restarting the script:

```text
Current checkpoint count for alice-1: 2
User: What's my home city?
Assistant: Your home city is Istanbul.

New checkpoint count for alice-1: 4
```

This proves that the state survived a process restart and was stored on disk in PostgreSQL.

---

# Part 2 — Long-term Memory

## Goal

The goal of this part is to store durable user facts in `PostgresStore` and recall them from a different thread.

Unlike Part 1, this memory should not depend on the conversation history of one thread.

## Scenario

Thread `alice-1`:

```text
User: I'm alice. I live in Istanbul, I'm vegetarian, mid-range budget.
Assistant: Saves all three facts to the store.
```

Thread `alice-2`:

```text
User: I'm alice. What do you know about me?
Assistant: You live in Istanbul, you're vegetarian, and your budget is mid-range.
```

## Stored Facts

The following dictionary is stored in `PostgresStore`:

```python
{
    "city": "Istanbul",
    "diet": "vegetarian",
    "budget": "mid-range"
}
```

## Observation

The script prints the stored profile before and after saving.

Example output:

```text
Before saving facts
Stored profile: None

After saving facts
Stored profile: {'city': 'Istanbul', 'diet': 'vegetarian', 'budget': 'mid-range'}
```

Then, in a fresh thread:

```text
Thread alice-2: fresh thread, recall facts
User: I'm alice. What do you know about me?
Assistant: You live in Istanbul, you're vegetarian, and your budget is mid-range.
```

This proves that the facts came from the store, not from the thread history.

---

# Part 3 — Context Engineering

## Goal

The goal of this part is to prevent the message history from growing forever.

Two context engineering techniques are used:

1. Rolling window: keep only recent raw messages.
2. Summarization: fold older messages into one compact summary.

## Scenario

The script runs a 12-turn conversation with Alice. The assistant prints how many messages are sent to the model each turn.

## Observation

Example output:

```text
--- Turn 5 ---
Model received 10 messages.

--- Turn 6 ---
Context engineering: old messages summarized.
Model received 7 messages.

--- Turn 8 ---
Model received 11 messages.

--- Turn 9 ---
Context engineering: old messages summarized.
Model received 7 messages.

--- Turn 12 ---
Context engineering: old messages summarized.
Model received 7 messages.
```

The message count does not grow endlessly. It increases for a few turns, then old messages are summarized and the raw history is reduced.

Final proof:

```text
Remaining raw conversation messages: 6
Summary exists: Yes
```

Final summary example:

```text
- The user's name is Alice.
- Alice lives in Istanbul.
- Alice is vegetarian.
- Alice has a mid-range budget.
- Alice likes simple travel plans.
- Alice prefers restaurants with local food.
- Alice does not like very expensive places.
```

This proves that the context is bounded instead of growing toward the full conversation length.

---

# Part 4 — Human-in-the-loop

## Goal

The goal of this part is to gate a sensitive action behind human approval.

The sensitive action is booking a table.

## Scenario

User request:

```text
Book a table at Çiya for 2 on 2026-07-01.
```

The graph pauses before executing the booking.

## Observation

The graph returns an interrupt:

```text
'__interrupt__': [
    Interrupt(
        value={
            'action': 'book_table',
            'restaurant': 'Çiya',
            'people': 2,
            'date': '2026-07-01',
            'question': 'Do you approve this booking?'
        }
    )
]
```

At this point, the booking has not been executed yet.

## Approve Path

When the human approves:

```python
Command(resume="approve")
```

The graph continues and executes the booking:

```text
Booking executed.
Booked Çiya for 2 on 2026-07-01.
```

## Reject Path

When the human rejects:

```python
Command(resume="reject")
```

The graph cancels the booking:

```text
Booking rejected.
Booking cancelled. Nothing was executed.
```

This proves that the sensitive action is controlled by human approval.

---

# Bonus — Time Travel

## Goal

The goal of the bonus part is to rewind a thread to an earlier checkpoint and resume with a different message, creating a second branch under the same thread.

## Scenario

Original message:

```text
Book a table at Çiya for 2 on 2026-07-01.
```

Branched message after rewind:

```text
Book a table at Çiya for 4 on 2026-07-02.
```

## Observation

The state history shows existing checkpoints:

```text
Checkpoint history for approved thread
Checkpoint count: 13
```

After rewinding and sending a different message, a new branch appears:

```text
Branched run result:
{
    'messages': ['Book a table at Çiya for 4 on 2026-07-02.'],
    'restaurant': 'Çiya',
    'people': 4,
    'date': '2026-07-02',
    'booking_status': 'pending_approval',
    '__interrupt__': [...]
}
```

This proves that an earlier checkpoint was reused and a second branch was created.

---

# Checkpointer vs Store

A checkpointer and a store are different memory mechanisms.

## Checkpointer

A checkpointer saves the state of a graph or agent execution.

It answers the question:

```text
What happened in this thread?
```

Examples of data saved by a checkpointer:

* message history
* graph state
* current node
* next node
* interrupt state
* checkpoint history

In this homework, `PostgresSaver` is used as the checkpointer.

It is useful for short-term memory and persistence within a thread.

## Store

A store saves durable facts that should be reused across threads.

It answers the question:

```text
What do we know about this user?
```

Examples of data saved by a store:

* user profile
* preferences
* durable facts
* long-term memory

In this homework, `PostgresStore` is used as the store.

It is useful for long-term memory that can be recalled from a fresh conversation.

## Why an Agent May Need Both

An agent may need both because they solve different problems.

The checkpointer lets the agent continue a specific conversation. For example, it remembers what happened in `alice-1`.

The store lets the agent remember durable information about a user across multiple conversations. For example, it remembers that Alice lives in Istanbul, is vegetarian, and has a mid-range budget, even in a new thread like `alice-2`.

In short:

```text
Checkpointer = conversation state / thread memory
Store = durable user memory / cross-thread memory
```

Both are needed to build assistants that can continue conversations and remember users over time.

---

# Security Note

No API key is exposed in the code. API keys and database connection strings are loaded from the `.env` file using environment variables.

# DB
DB is created via docker:
```
docker run -d --rm \
  --name postgres-langgraph \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=langgraph_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```
