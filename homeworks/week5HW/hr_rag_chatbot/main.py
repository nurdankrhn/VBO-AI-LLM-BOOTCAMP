import argparse
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver

from rag_agent import build_agent, ask_agent
from vector_store import ingest_documents


load_dotenv()


TEST_QUESTIONS = [
    "What is the company's leave policy?",
    "How many vacation days do employees get?",
    "What are the steps in the offboarding process?",
    "What are the IT security requirements for new employees?",
    "What is the performance review process?",
    "How do I submit travel expenses for reimbursement?",
]


def get_db_uri() -> str:
    db_uri = os.getenv("DB_URI")

    if not db_uri:
        raise ValueError(
            "DB_URI bulunamadı. Lütfen .env dosyasına PostgreSQL bağlantısını ekleyin."
        )

    return db_uri


def run_ingest() -> None:
    """
    HR dokümanlarını yükler, chunk'lara böler,
    embedding üretir ve ChromaDB'ye kaydeder.
    """
    print("Document ingestion started...\n")

    ingest_documents()

    print("\nDocument ingestion completed successfully.")


def run_required_tests() -> None:
    """
    Ödevde istenen 6 test sorusunu çalıştırır.
    """
    db_uri = get_db_uri()

    thread_id = f"required-test-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        checkpointer.setup()

        agent = build_agent(checkpointer)

        print("Running required test questions...\n")

        for index, question in enumerate(TEST_QUESTIONS, start=1):
            print("=" * 80)
            print(f"Test Question {index}")
            print(f"You: {question}")

            answer = ask_agent(
                agent=agent,
                question=question,
                thread_id=thread_id,
            )

            print(f"Bot: {answer}\n")

        print("=" * 80)
        print("Required tests completed.")


def run_memory_test() -> None:
    """
    Short-term memory testini çalıştırır.
    """
    db_uri = get_db_uri()

    thread_id = f"memory-test-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    memory_questions = [
        "What is the leave policy?",
        "What about sick leave?",
    ]

    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        checkpointer.setup()

        agent = build_agent(checkpointer)

        print("Running short-term memory test...\n")

        for question in memory_questions:
            print(f"You: {question}")

            answer = ask_agent(
                agent=agent,
                question=question,
                thread_id=thread_id,
            )

            print(f"Bot: {answer}\n")

        print("Short-term memory test completed.")


def run_chat() -> None:
    """
    Terminal üzerinden etkileşimli chatbot başlatır.
    Aynı thread_id kullanıldığı için konuşma boyunca memory korunur.
    """
    db_uri = get_db_uri()

    thread_id = thread_id = "nurdan-hr-rag-chat-session"

    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        checkpointer.setup()

        agent = build_agent(checkpointer)

        print("HR RAG Chatbot started.")
        print("Type 'exit', 'quit', or 'q' to stop.\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in {"exit", "quit", "q"}:
                print("Chat ended.")
                break

            if not user_input:
                continue

            answer = ask_agent(
                agent=agent,
                question=user_input,
                thread_id=thread_id,
            )

            print(f"Bot: {answer}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HR RAG Chatbot with ChromaDB and PostgreSQL short-term memory"
    )

    parser.add_argument(
        "command",
        choices=["ingest", "test", "memory-test", "chat"],
        help="Command to run: ingest, test, memory-test, or chat",
    )

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest()

    elif args.command == "test":
        run_required_tests()

    elif args.command == "memory-test":
        run_memory_test()

    elif args.command == "chat":
        run_chat()


if __name__ == "__main__":
    main()