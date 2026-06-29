import csv
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel, Session, create_engine


# -------------------------------------------------
# 1. Pydantic structured output schemas
# -------------------------------------------------

class Entities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Optional[float] = Field(
        default=None,
        description="Numeric amount, e.g., 49.99"
    )
    invoice_period: Optional[str] = None
    ticket_id: Optional[str] = None
    device: Optional[str] = None
    address_move: Optional[bool] = None


class TicketExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_type: Literal["billing", "technical", "account", "general"]
    urgency: Literal["low", "medium", "high"]
    channel: Literal["phone", "email", "chat", "unknown"]
    entities: Entities
    summary: str
    status_suggestion: Literal["open", "in_progress", "resolved"]


# -------------------------------------------------
# 2. SQLModel database table
# -------------------------------------------------

class TicketExtractionRow(SQLModel, table=True):
    __tablename__ = "ticket_extractions"

    __table_args__ = (
        Index("ix_ticket_extractions_run_source", "run_id", "source_id"),
        Index("ix_ticket_extractions_issue_type", "issue_type"),
        Index("ix_ticket_extractions_urgency", "urgency"),
        Index("ix_ticket_extractions_channel", "channel"),
    )

    id: Optional[int] = SQLField(default=None, primary_key=True)

    run_id: str = SQLField(
        sa_column=Column(String(36), nullable=False)
    )
    source_id: str = SQLField(
        sa_column=Column(String(255), nullable=False)
    )

    issue_type: str = SQLField(
        sa_column=Column(String(50), nullable=False)
    )
    urgency: str = SQLField(
        sa_column=Column(String(50), nullable=False)
    )
    channel: str = SQLField(
        sa_column=Column(String(50), nullable=False)
    )

    summary: str = SQLField(
        sa_column=Column(Text, nullable=False)
    )
    status_suggestion: str = SQLField(
        sa_column=Column(String(50), nullable=False)
    )

    created_at: Optional[datetime] = SQLField(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now()
        )
    )

    entities: dict[str, Any] = SQLField(
        default_factory=dict,
        sa_column=Column(
            JSON,
            nullable=False,
            server_default=text("'{}'::json")
        )
    )


# -------------------------------------------------
# 3. Environment / model / DB setup
# -------------------------------------------------

def build_engine():
    database_url = os.getenv("SQLALCHEMY_DATABASE_URL")

    if not database_url:
        raise RuntimeError("SQLALCHEMY_DATABASE_URL .env içinde bulunamadı.")

    return create_engine(database_url, echo=False)


def build_model():
    if os.getenv("OPENROUTER_API_KEY"):
        return init_chat_model(
            "openai:openai/gpt-4o-mini",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            max_tokens=500,
        )

    if os.getenv("GOOGLE_API_KEY"):
        return init_chat_model(
            model="gemini-2.5-flash-lite",
            model_provider="google_genai",
            temperature=0,
            max_tokens=500,
        )

    raise RuntimeError(
        "OPENROUTER_API_KEY veya GOOGLE_API_KEY .env içinde bulunamadı."
    )


def build_agent():
    model = build_model()

    return create_agent(
        model=model,
        tools=[],
        response_format=ToolStrategy(TicketExtraction),
    )


# -------------------------------------------------
# 4. CSV helpers
# -------------------------------------------------

SOURCE_ID_COLUMNS = [
    "source_id",
    "customer_id",
    "cust_id",
    "user_id",
    "id",
]

TEXT_COLUMNS = [
    "text",
    "ticket_text",
    "message",
    "content",
    "description",
    "sikayet",
]


def pick_first_existing(row: dict[str, str], candidates: list[str]) -> Optional[str]:
    for col in candidates:
        if col in row and row[col] is not None and row[col].strip():
            return row[col].strip()
    return None


def build_prompt(source_id: str, ticket_text: str) -> str:
    return f"""
Extract exactly ONE TicketExtraction object from the support ticket below.

Rules:
- Return exactly one structured response.
- Do not return multiple objects.
- No extra keys.
- issue_type must be one of: billing, technical, account, general.
- urgency must be one of: low, medium, high.
- channel must be one of: phone, email, chat, unknown.
- status_suggestion must be one of: open, in_progress, resolved.
- If a top-level value is unclear, choose the closest enum.
- If a nested entity is not present, use null.
- Coerce numeric amounts like "200 TL" to 200.0.
- Coerce boolean-like address move expressions to true/false when clear.
- If the text mentions modem, router, internet modem, or reset, set entities.device accordingly.
- If the text mentions mobile app, mobil uygulama, uygulama, app, set entities.device accordingly.
- If the ticket is about app crash, login error, unauthorized error, slow internet, modem or connection problem, issue_type should usually be technical.
- If the ticket asks about campaign details, SMS link, or information request, issue_type should usually be general unless the main problem is clearly technical.
- Do not copy source_id into entities.ticket_id unless the ticket text explicitly says it is a ticket id.
- Write the summary in Turkish, concise and faithful to the ticket.

source_id:
{source_id}

ticket_text:
{ticket_text}
""".strip()


# -------------------------------------------------
# 5. LLM extraction + DB insert
# -------------------------------------------------

def extract_ticket(agent, source_id: str, ticket_text: str) -> TicketExtraction:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": build_prompt(source_id, ticket_text),
                }
            ]
        }
    )

    structured = result["structured_response"]

    if isinstance(structured, TicketExtraction):
        return structured

    return TicketExtraction.model_validate(structured)


def process_csv(csv_path: str):
    load_dotenv()

    engine = build_engine()
    SQLModel.metadata.create_all(engine)

    agent = build_agent()
    run_id = str(uuid.uuid4())

    print(f"run_id = {run_id}")

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        print("CSV columns:", reader.fieldnames)

        with Session(engine) as session:
            for index, row in enumerate(reader, start=1):
                source_id = pick_first_existing(row, SOURCE_ID_COLUMNS)
                ticket_text = pick_first_existing(row, TEXT_COLUMNS)

                if not source_id:
                    source_id = f"row-{index}"

                if not ticket_text:
                    print(
                        f"[SKIP] row={index} text kolonu bulunamadı: {row}",
                        file=sys.stderr,
                    )
                    continue

                try:
                    extraction = extract_ticket(
                        agent=agent,
                        source_id=source_id,
                        ticket_text=ticket_text,
                    )

                    print(
                        json.dumps(
                            extraction.model_dump(),
                            ensure_ascii=False,
                            indent=2,
                        )
                    )

                    db_row = TicketExtractionRow(
                        run_id=run_id,
                        source_id=source_id,
                        issue_type=extraction.issue_type,
                        urgency=extraction.urgency,
                        channel=extraction.channel,
                        summary=extraction.summary,
                        status_suggestion=extraction.status_suggestion,
                        entities=extraction.entities.model_dump(exclude_none=True),
                    )

                    session.add(db_row)
                    session.commit()
                    session.refresh(db_row)

                    print(f"[OK] inserted id={db_row.id}, source_id={source_id}")

                except Exception as error:
                    session.rollback()
                    print(
                        f"[ERROR] row={index}, source_id={source_id}: {error}",
                        file=sys.stderr,
                    )


# -------------------------------------------------
# 6. CLI
# -------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py /path/to/support_tickets_minimal.csv")
        sys.exit(1)

    process_csv(sys.argv[1])