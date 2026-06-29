from rich.pretty import pprint
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import (
    SummarizationMiddleware,
    PIIMiddleware,
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
    ModelFallbackMiddleware,
    ToolRetryMiddleware,
    ModelRetryMiddleware,
    LLMToolSelectorMiddleware,
    ContextEditingMiddleware,
    HumanInTheLoopMiddleware,
    wrap_model_call,
    wrap_tool_call,
    before_agent,
    after_agent,
    before_model,
    after_model
)
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from dotenv import load_dotenv
import os

load_dotenv()

# Get a model using OpenRouter
def make_model():
    """Main model used by most demos — Gemini via OpenRouter.

    Why not Google AI Studio directly? The free tier is 20 requests/day
    on gemini-2.5-flash-lite, which runs out quickly when you cycle
    through this catalog. OpenRouter has its own quota and avoids that.

    This is itself one of the lessons in this lesson — when your default
    vendor's free tier rate-limits you, you swap. ModelFallbackMiddleware
    is the runtime version of this same decision.
    """
    return init_chat_model(
        "openai:google/gemini-2.5-flash-lite",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=500,
    )


# Get a model using Google AI Studio
def make_google_studio_model():
    """Gemini via Google AI Studio — used ONLY in demo_model_fallback as the
    primary, where we WANT it to fail (free tier 429s after 20 requests).
    """
    return init_chat_model(
        model="gemini-2.5-flash-lite",
        model_provider="google_genai",
        max_tokens=500,
    )

# Get a structured output model
def make_structured_output_model():
    """Small, reliable model for tasks that need structured output.

    Used by LLMToolSelectorMiddleware as the selector model. Gemini Flash
    Lite is unreliable here — it often returns tool DESCRIPTIONS instead
    of tool NAMES, raising `ValueError: Model selected invalid tools`.
    GPT-4o-mini via OpenRouter is cheap (~$0.0001 per selection) and
    handles the structured-output schema correctly.
    """
    return init_chat_model(
        "openai:openai/gpt-4o-mini",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=200,
    )

# ── Tools used across the demos ─────────────────────────────────────────────
@tool
def add(a: int, b: int) -> int:
    """Return a + b."""
    return a + b

# @tool wraps the function into a Pydantic StructuredTool, which won't
# accept arbitrary attributes — so we keep the call counter outside it.
# A single-element list is a common Python idiom for a mutable counter
# that closures (and inner functions) can update without `global`.
_flaky_calls = [0]

@tool
def flaky_lookup(name: str) -> str:
    """Look up a customer by name. This tool is flaky on purpose."""
    _flaky_calls[0] += 1
    attempt = _flaky_calls[0]
    if attempt <= 2:
        print(f"    [flaky_lookup] attempt #{attempt} — THROWING ConnectionError")
        raise ConnectionError(f"transient failure (attempt {attempt})")
    print(f"    [flaky_lookup] attempt #{attempt} — returning the result")
    return f"Customer {name!r} found."


@tool
def transfer_money(amount: float, to: str) -> str:
    """Transfer money to a recipient. Sensitive — should require human approval."""
    return f"Transferred ${amount} to {to}."


def run(agent, question: str):
    print(f"You: {question}")
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    pprint(result)


# 1. SummarizationMiddleware
# agent = create_agent(
#         model=make_model(),
#         tools=[add],
#         middleware=[
#             SummarizationMiddleware(
#                 model=make_model(),
#                 trigger=("messages", 4),
#                 keep=("messages", 2),
#             ),
#         ],
#     )
# run(agent, "Add 1 and 2. Then add 3 and 4. Then add 5 and 6.")

# 2. PIIMiddleware
# @tool
# def save_contact(name: str, email: str) -> str:
#     """Save a contact's name, email and credit card to the address book."""
#     return f"Saved contact: {name} <{email}>"

# agent = create_agent(
#         model=make_model(),
#         tools=[save_contact],
#         middleware=[
#             PIIMiddleware(pii_type="email", strategy="redact"),
#             PIIMiddleware(pii_type="credit_card", strategy="mask"),
#         ],
#         system_prompt="Just do what user asks. Don't ask follow up questions"
#     )
# run(agent, "Save Alice's contact: email alice@example.com, "
#                "card on file 4118 0006 1710 1453.")

# 3. ModelCallLimitMiddleware
# agent = create_agent(
#         model=make_model(),
#         tools=[add],
#         middleware=[ModelCallLimitMiddleware(run_limit=2)],
#     )

# run(agent, "Compute (1+2)+(3+4)+(5+6) step by step, calling add() each time.")

# 4. ToolCallLimitMiddleware
# agent = create_agent(
#         model=make_model(),
#         tools=[add],
#         middleware=[ToolCallLimitMiddleware(run_limit=1)],
#     )
# run(agent, "Add 1+2 and also add 3+4.")

# 5. ModelRetryMiddleware

# Skipping this refer to reference note

# 6. ToolRetryMiddleware
# Skipping this refer to reference note

# 7. ModelFallbackMiddleware

# _primary_failed_once = [False]

# @wrap_model_call
# def fail_primary_once(request, handler):
#     if not _primary_failed_once[0]:
#         _primary_failed_once[0] = True
#         print(f"    [fake-fail] PRIMARY model call — THROWING ConnectionError")
#         raise ConnectionError("fake primary failure")
#     print(f"    [fake-fail] passing through (fallback or subsequent call)")
#     return handler(request)

# _primary_failed_once[0] = False


# primary = make_model() # OpenRouter
# fallback = make_google_studio_model()

# agent = create_agent(
#         model=primary,
#         tools=[add],
#         middleware=[
#             ModelFallbackMiddleware(fallback),  # outer: catches primary failure
#         fail_primary_once, 
#         ],
#     )

# run(agent, "What is 17 + 25?")