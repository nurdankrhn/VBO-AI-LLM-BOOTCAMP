import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.checkpoint.postgres import PostgresSaver

from vector_store import get_retriever


load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CHAT_MODEL = "openai:google/gemini-2.5-flash-lite"


SYSTEM_PROMPT = """
You are an HR RAG assistant.

Rules:
- Use the HR document search tool before answering HR policy questions.
- Answer only based on retrieved document context.
- Keep answers short: 2-3 sentences maximum.
- Always cite the source document using the file_name metadata.
- If the retrieved context does not contain the answer, say you could not find it in the HR documents.
- Use conversation history to understand follow-up references like "it", "that policy", "them", or "what about sick leave?".
"""


def get_chat_model():
    """
    OpenRouter üzerinden chat model oluşturur.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY bulunamadı. Lütfen .env dosyasına ekleyin.")

    model = init_chat_model(
        CHAT_MODEL,
        temperature=0,
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
    )

    return model


def create_hr_document_search_tool():
    """
    ChromaDB retriever'ını agent tool olarak sarar.
    Agent bu tool'u çağırarak HR dokümanlarında arama yapar.
    """
    retriever = get_retriever()

    @tool
    def search_hr_documents(query: str) -> str:
        """
        Search HR documents and return the most relevant document chunks with source file names.
        Use this tool for questions about leave policy, offboarding, onboarding, IT security,
        performance review, travel expenses, reimbursement, and other HR policies.
        """
        docs = retriever.invoke(query)

        if not docs:
            return "No relevant HR documents found."

        results = []

        for index, doc in enumerate(docs, start=1):
            file_name = doc.metadata.get("file_name", "unknown")
            page_number = doc.metadata.get("page_number", -1)
            chunk_index = doc.metadata.get("chunk_index", -1)
            section_title = doc.metadata.get("section_title", "unknown")

            result = f"""
Result {index}
file_name: {file_name}
page_number: {page_number}
chunk_index: {chunk_index}
section_title: {section_title}

content:
{doc.page_content}
""".strip()

            results.append(result)

        return "\n\n---\n\n".join(results)

    return search_hr_documents


def build_agent(checkpointer: Any):
    """
    RAG tool + OpenRouter chat model + PostgreSQL memory ile agent oluşturur.
    """
    model = get_chat_model()
    hr_search_tool = create_hr_document_search_tool()

    agent = create_agent(
        model=model,
        tools=[hr_search_tool],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent


def _extract_final_answer(response: dict) -> str | None:
    """
    Agent response içinden son dolu AI cevabını bulur.
    Tool call yapan boş AI mesajlarını atlar.
    """
    messages = response["messages"]

    for message in reversed(messages):
        message_type = getattr(message, "type", None)
        content = getattr(message, "content", "")
        tool_calls = getattr(message, "tool_calls", None)

        if message_type != "ai":
            continue

        if tool_calls:
            continue

        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            text_parts = []

            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)

            final_text = "\n".join(text_parts).strip()

            if final_text:
                return final_text

    return None


def ask_agent(agent: Any, question: str, thread_id: str = "default-user-session") -> str:
    """
    Agent'a soru sorar.
    Aynı thread_id kullanılırsa agent konuşma geçmişini hatırlar.
    """
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    answer = _extract_final_answer(response)

    if answer:
        return answer

    # Bazı OpenRouter/tool-calling durumlarında ilk tur sadece tool çağrısı ile bitebiliyor.
    # Bu durumda aynı thread_id ile final cevabı ayrıca istiyoruz.
    follow_up_response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Using the HR document context retrieved in the previous step, "
                        "answer my previous question in 2-3 sentences and cite the source file_name."
                    ),
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    follow_up_answer = _extract_final_answer(follow_up_response)

    if follow_up_answer:
        return follow_up_answer

    return "I could not generate a final answer from the retrieved HR documents."


def run_single_test():
    """
    rag_agent.py tek başına çalıştırıldığında hızlı test yapar.
    """
    db_uri = os.getenv("DB_URI")

    if not db_uri:
        raise ValueError("DB_URI bulunamadı. Lütfen .env dosyasına ekleyin.")

    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        checkpointer.setup()

        agent = build_agent(checkpointer)

        thread_id = "test-session-1"

        question_1 = "What is the leave policy?"
        answer_1 = ask_agent(agent, question_1, thread_id=thread_id)

        print("\nYou:", question_1)
        print("Bot:", answer_1)

        question_2 = "What about sick leave?"
        answer_2 = ask_agent(agent, question_2, thread_id=thread_id)

        print("\nYou:", question_2)
        print("Bot:", answer_2)


if __name__ == "__main__":
    run_single_test()