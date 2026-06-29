import os
from typing import TypedDict, List

from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.postgres import PostgresSaver
import re


load_dotenv()

DB_URI = os.getenv("DB_URI")

if not DB_URI:
    raise ValueError("DB_URI is missing. Please set it in your .env file.")


class BookingState(TypedDict):
    messages: List[str]
    restaurant: str
    people: int
    date: str
    booking_status: str


def parse_booking_request(state: BookingState):
    """
    Parses a simple booking request from the latest user message.
    Example:
    Book a table at Çiya for 2 on 2026-07-01.
    """
    user_message = state["messages"][-1]

    print("\n[Node] parse_booking_request")
    print("User request:", user_message)

    restaurant_match = re.search(r"at (.*?) for", user_message)
    people_match = re.search(r"for (\d+)", user_message)
    date_match = re.search(r"on (\d{4}-\d{2}-\d{2})", user_message)

    restaurant = restaurant_match.group(1) if restaurant_match else "Unknown"
    people = int(people_match.group(1)) if people_match else 1
    date = date_match.group(1) if date_match else "Unknown"

    return {
        "restaurant": restaurant,
        "people": people,
        "date": date,
        "booking_status": "pending_approval",
    }

def ask_human_approval(state: BookingState):
    """
    Sensitive action gate.
    The graph pauses here and waits for a human decision.
    """
    print("\n[Node] ask_human_approval")

    approval = interrupt(
        {
            "action": "book_table",
            "restaurant": state["restaurant"],
            "people": state["people"],
            "date": state["date"],
            "question": "Do you approve this booking?",
        }
    )

    if approval == "approve":
        return {
            "booking_status": "approved"
        }

    return {
        "booking_status": "rejected"
    }


def execute_or_cancel_booking(state: BookingState):
    """
    Executes the booking only if human approved.
    """
    print("\n[Node] execute_or_cancel_booking")

    if state["booking_status"] == "approved":
        message = (
            f"Booked {state['restaurant']} for {state['people']} "
            f"on {state['date']}."
        )
        print("Booking executed.")
        return {
            "messages": state["messages"] + [message],
            "booking_status": "booked",
        }

    message = "Booking cancelled. Nothing was executed."
    print("Booking rejected.")
    return {
        "messages": state["messages"] + [message],
        "booking_status": "cancelled",
    }


def build_graph(checkpointer):
    workflow = StateGraph(BookingState)

    workflow.add_node("parse_booking_request", parse_booking_request)
    workflow.add_node("ask_human_approval", ask_human_approval)
    workflow.add_node("execute_or_cancel_booking", execute_or_cancel_booking)

    workflow.add_edge(START, "parse_booking_request")
    workflow.add_edge("parse_booking_request", "ask_human_approval")
    workflow.add_edge("ask_human_approval", "execute_or_cancel_booking")
    workflow.add_edge("execute_or_cancel_booking", END)

    return workflow.compile(checkpointer=checkpointer)


def print_latest_state(graph, config, label):
    state = graph.get_state(config)

    print(f"\n=== {label} ===")
    print("Current values:", state.values)
    print("Next node(s):", state.next)

    if state.interrupts:
        print("Interrupts:", state.interrupts)


def print_state_history(graph, config, label):
    history = list(graph.get_state_history(config))

    print(f"\n=== {label} ===")
    print(f"Checkpoint count: {len(history)}")

    for index, checkpoint in enumerate(history):
        print(
            f"{index}. next={checkpoint.next}, "
            f"values={checkpoint.values}"
        )

    return history


with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()

    graph = build_graph(checkpointer)

    config = {
        "configurable": {
            "thread_id": "alice-1-hitl"
        }
    }

    print("\n==============================")
    print("Part 4: Human-in-the-loop")
    print("==============================")

    print("\n--- Step 1: User asks for booking ---")

    initial_state = {
        "messages": [
            "Book a table at Çiya for 2 on 2026-07-01."
        ],
        "restaurant": "",
        "people": 0,
        "date": "",
        "booking_status": "new",
    }

    result = graph.invoke(initial_state, config=config)

    print("\nGraph returned:")
    print(result)

    print_latest_state(graph, config, "After interrupt")

    print("\n--- Step 2A: Human approves ---")

    approved_result = graph.invoke(
        Command(resume="approve"),
        config=config,
    )

    print("\nApproved run result:")
    print(approved_result)

    print_latest_state(graph, config, "After approval")

    print("\n==============================")
    print("Alternative run: Human rejects")
    print("==============================")

    reject_config = {
        "configurable": {
            "thread_id": "alice-1-hitl-reject"
        }
    }

    reject_initial_state = {
        "messages": [
            "Book a table at Çiya for 2 on 2026-07-01."
        ],
        "restaurant": "",
        "people": 0,
        "date": "",
        "booking_status": "new",
    }

    reject_first_result = graph.invoke(
        reject_initial_state,
        config=reject_config,
    )

    print("\nReject run first result:")
    print(reject_first_result)

    rejected_result = graph.invoke(
        Command(resume="reject"),
        config=reject_config,
    )

    print("\nRejected run result:")
    print(rejected_result)

    print_latest_state(graph, reject_config, "After rejection")

    print("\n==============================")
    print("Bonus: Time Travel")
    print("==============================")

    history = print_state_history(
        graph,
        config,
        "Checkpoint history for approved thread"
    )

    if len(history) >= 3:
        rewind_checkpoint = history[-3]

        print("\nRewinding to an earlier checkpoint...")
        print("Selected checkpoint next:", rewind_checkpoint.next)
        print("Selected checkpoint values:", rewind_checkpoint.values)

        branched_result = graph.invoke(
            {
                "messages": [
                    "Book a table at Çiya for 4 on 2026-07-02."
                ],
                "restaurant": "",
                "people": 0,
                "date": "",
                "booking_status": "new",
            },
            config=rewind_checkpoint.config,
        )

        print("\nBranched run result:")
        print(branched_result)

        print_state_history(
            graph,
            config,
            "Checkpoint history after time travel branch"
        )
    else:
        print("Not enough checkpoints for time travel demo.")

    print("\n=== Final Proof ===")
    print("- Booking request pauses at interrupt before execution.")
    print("- Approve path executes the booking.")
    print("- Reject path cancels the booking.")
    print("- State history shows checkpoints.")
    print("- Time travel reuses an earlier checkpoint config to create a branch.")