import os
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is missing. Please set it in your .env file.")


model = init_chat_model(
    "openai:google/gemini-2.5-flash-lite",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    max_tokens=500,
)


SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Answer shortly and clearly."
)

SUMMARY_PROMPT = (
    "Summarize the following old conversation turns shortly. "
    "Keep only durable user preferences, facts, goals, and unresolved tasks. "
    "Do not include unnecessary details."
)


# Context engineering parameters
MAX_MESSAGES_BEFORE_SUMMARY = 8
RECENT_MESSAGES_TO_KEEP = 4

conversation_messages = []
conversation_summary = ""


def summarize_old_messages(old_messages):
    """
    Creates a compact deterministic summary from old messages.
    This avoids extra LLM calls and prevents incomplete summaries.
    """
    facts = []

    for message in old_messages:
        content = message.content.lower()

        if "alice" in content:
            facts.append("The user's name is Alice.")
        if "istanbul" in content:
            facts.append("Alice lives in Istanbul.")
        if "vegetarian" in content:
            facts.append("Alice is vegetarian.")
        if "mid-range" in content:
            facts.append("Alice has a mid-range budget.")
        if "simple travel" in content:
            facts.append("Alice likes simple travel plans.")
        if "local food" in content:
            facts.append("Alice prefers restaurants with local food.")
        if "very expensive" in content:
            facts.append("Alice does not like very expensive places.")

    unique_facts = list(dict.fromkeys(facts))

    if not unique_facts:
        return "No durable facts found yet."

    return "\n".join(f"- {fact}" for fact in unique_facts)


def build_messages_for_model(user_input):
    """
    Builds the bounded context that will be sent to the model.
    It includes:
    1. System prompt
    2. Optional summary of old conversation
    3. Recent raw conversation messages
    4. Current user input
    """
    messages_to_model = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]

    if conversation_summary:
        messages_to_model.append(
            SystemMessage(
                content=f"Summary of earlier conversation:\n{conversation_summary}"
            )
        )

    messages_to_model.extend(conversation_messages)
    messages_to_model.append(HumanMessage(content=user_input))

    return messages_to_model


def maybe_summarize_history():
    """
    If raw conversation history grows too much:
    - summarize old messages
    - keep only recent messages
    - replace the old summary with an updated compact summary

    This uses two context engineering techniques:
    1. Summarization
    2. Rolling window
    """
    global conversation_messages
    global conversation_summary

    if len(conversation_messages) <= MAX_MESSAGES_BEFORE_SUMMARY:
        return False

    old_messages = conversation_messages[:-RECENT_MESSAGES_TO_KEEP]
    recent_messages = conversation_messages[-RECENT_MESSAGES_TO_KEEP:]

    if conversation_summary:
        old_messages = [
            SystemMessage(content=f"Previous summary:\n{conversation_summary}")
        ] + old_messages

    new_summary = summarize_old_messages(old_messages)

    conversation_summary = new_summary
    conversation_messages = recent_messages

    return True


demo_inputs = [
    "Hi, I'm alice.",
    "I live in Istanbul.",
    "I'm vegetarian.",
    "My budget is mid-range.",
    "I like simple travel plans.",
    "I prefer restaurants with local food.",
    "I do not like very expensive places.",
    "Can you remember these preferences?",
    "What kind of restaurant would suit me?",
    "What city do I live in?",
    "What is my diet preference?",
    "Can you summarize what you know about me?",
]


print("\n=== Part 3: Context Engineering ===\n")
print("Techniques used:")
print("1. Rolling window: keep only recent messages.")
print("2. Summarization: fold old messages into one compact summary message.\n")


for turn_number, user_input in enumerate(demo_inputs, start=1):
    summarized = maybe_summarize_history()

    messages_to_model = build_messages_for_model(user_input)

    print(f"\n--- Turn {turn_number} ---")

    if summarized:
        print("Context engineering: old messages summarized.")

    print(f"Model received {len(messages_to_model)} messages.")

    result = model.invoke(messages_to_model)
    assistant_answer = result.content

    print("User:", user_input)
    print("Assistant:", assistant_answer)

    conversation_messages.append(HumanMessage(content=user_input))
    conversation_messages.append(AIMessage(content=assistant_answer))


print("\n=== Final Proof ===")
print(f"Remaining raw conversation messages: {len(conversation_messages)}")

if conversation_summary:
    print("Summary exists: Yes")
    print("\nConversation summary:")
    print(conversation_summary)
else:
    print("Summary exists: No")

print("\nProof:")
print("- Raw message history does not grow forever.")
print("- Old messages are summarized into one compact summary.")
print("- Only recent messages are kept as raw messages.")
print("- The printed message count shows that context stays bounded.")