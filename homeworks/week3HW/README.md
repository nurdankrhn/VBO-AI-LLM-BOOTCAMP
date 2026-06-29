# Homework — LangChain Structured Output ➜ PostgreSQL Database Storage

**Languages/Versions:** Python 3.12, `langchain>=1.2.0`  
**LLM:** Google Gemini or OpenAI GPT-4o-mini or any other model
**Database:** PostgreSQL 16 (Docker container)  
**Rule:** Do **not** expose your API key in code. Use environment variables / `.env` only.  
**Store** results in PostgreSQL database with single table and JSON entities column.

---

## Objective
Using the attached CSV (`support_tickets_minimal.csv`), parse each ticket text with an LLM and extract a **strict structured object** (validated by **Pydantic**). Store each validated record to:
1) **PostgreSQL database** with proper schema and indexing
2) **stdout** (pretty-printed JSON for monitoring)

### Target schema (must match exactly)
```python
from typing import Optional, Literal
from pydantic import BaseModel, Field

class Entities(BaseModel):
    amount: Optional[float] = Field(default=None, description="Numeric amount, e.g., 49.99")
    invoice_period: Optional[str] = None
    ticket_id: Optional[str] = None
    device: Optional[str] = None
    address_move: Optional[bool] = None

class TicketExtraction(BaseModel):
    issue_type: Literal["billing","technical","account","general"]
    urgency: Literal["low","medium","high"]
    channel: Literal["phone","email","chat","unknown"]
    entities: Entities
    summary: str
    status_suggestion: Literal["open","in_progress","resolved"]
```

### Expected Database Table Schema
```sql
id SERIAL PRIMARY KEY,
run_id VARCHAR(36) NOT NULL,
source_id VARCHAR(255) NOT NULL,
issue_type VARCHAR(50) NOT NULL,
urgency VARCHAR(50) NOT NULL,
channel VARCHAR(50) NOT NULL,
summary TEXT NOT NULL,
status_suggestion VARCHAR(50) NOT NULL,
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
entities JSON NOT NULL DEFAULT '{}'
```

**Rules**
- Use **Pydantic** models for validation (no `TypedDict`).
- No extra keys. Enforce enums. Coerce numeric/boolean fields when possible; otherwise `None`.
- If unknown/not present: use the closest enum (top-level) or `None` (nested fields).

---

## Tasks
1. **Environment Setup**
   - Create & activate a Python 3.12 venv.
   - Start PostgreSQL Docker container:
```bash
docker run -d --rm --name postgres-langgraph -e POSTGRES_USER=train -e POSTGRES_PASSWORD=Ankara06 -e POSTGRES_DB=langgraph_db -p 5432:5432 postgres:16
```
   - Create `.env` with database connection and API key

2. **Database Schema with SQLModel**
   - Define SQLModel class for ticket extractions with JSON entities column
   - Create single database table with proper indexes
   - Store run metadata (run_id, timestamp, source_id) and entities as JSON

3. **Pydantic schema + Structured output**
   - Define `Entities` and `TicketExtraction` Pydantic models (see rubric).
   - Build a LangChain >= 1.2.0 agent that reads each CSV row, calls OpenAI GPT-4o-mini or Gemini or other models, and **returns exactly** the target structure.

4. **Database Storage with SQLModel**
   - For each row:
     - Extract structured data using LLM
     - Store validated data in PostgreSQL using SQLModel
     - Print the validated model as formatted JSON to stdout for monitoring
   - Add proper error handling and transaction management

5. **CLI**
   - Command:
```bash
python main.py /path/to/support_tickets_minimal.csv
```

6. **Deliverables**
   - `README.md` with Docker setup steps and execution instructions
   - Database schema and sample queries to verify data

```
id|run_id                              |source_id|issue_type|urgency|channel|summary                                                                                             |status_suggestion|created_at             |entities                    |
--+------------------------------------+---------+----------+-------+-------+----------------------------------------------------------------------------------------------------+-----------------+-----------------------+----------------------------+
 1|b8b772ae-d459-4ad2-a9b9-a09602b6e502|CUST-001 |billing   |high   |phone  |Faturamda 200 TL fazla ücret var, acil düzeltilsin.                                                 |open             |2025-12-31 02:45:54.796|{"amount": 200.0}           |
 2|b8b772ae-d459-4ad2-a9b9-a09602b6e502|CUST-002 |technical |high   |chat   |Uygulama açılır açılmaz çöküyor, teknik ekip baksın.                                                |open             |2025-12-31 02:45:57.383|{}                          |
 3|b8b772ae-d459-4ad2-a9b9-a09602b6e502|CUST-003 |account   |high   |email  |Hesabım kilitlendi, şifre sıfırlama linki gelmiyor.                                                 |open             |2025-12-31 02:46:00.527|{}                          |
 4|b8b772ae-d459-4ad2-a9b9-a09602b6e502|CUST-004 |technical |high   |unknown|Dün akşamdan beri internet çok yavaş, modem resetledim ama düzelmedi. Önemli bir toplantım var acil.|open             |2025-12-31 02:46:03.823|{"device": "modem"}         |
 5|b8b772ae-d459-4ad2-a9b9-a09602b6e502|CUST-005 |account   |medium |unknown|Abonelik iptali talebi ve çağrı merkeziyle iletişimde sorun.                                        |open             |2025-12-31 02:46:06.568|{}                          |
 6|b8b772ae-d459-4ad2-a9b9-a09602b6e502|CUST-006 |billing   |high   |unknown|Ödeme yapıldı fakat sistemde görünmüyor. İki kez dekont gönderildi, çözüm bekleniyor.               |in_progress      |2025-12-31 02:46:10.665|{}                          |
 7|b8b772ae-d459-4ad2-a9b9-a09602b6e502|CUST-007 |technical |high   |unknown|Mobil uygulamada girişte 'yetkisiz' hatası alınıyor. Şirket hesabıyla ilgili olabilir.              |open             |2025-12-31 02:46:14.045|{"device": "mobil uygulama"}|
 8|b8b772ae-d459-4ad2-a9b9-a09602b6e502|CUST-008 |general   |medium |unknown|Yeni kampanyanın detaylarını öğrenmek istiyorum; SMS geldi ama link çalışmıyor.                     |open             |2025-12-31 02:46:18.549|{}                          |
```
---