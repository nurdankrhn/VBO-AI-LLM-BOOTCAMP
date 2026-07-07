# HR RAG Chatbot with Short-Term Memory

This project implements a RAG (Retrieval-Augmented Generation) chatbot for HR documents.  
The chatbot answers questions using retrieved HR document context and remembers previous conversation turns with PostgreSQL-backed short-term memory.

---

## Objective

The goal of this project is to build a chatbot that can:

1. Answer questions about HR documents
2. Retrieve relevant document chunks from ChromaDB
3. Use short-term memory for follow-up questions
4. Cite the source document in each answer

---

## Features

- Loads HR documents from a directory
- Supports `.txt`, `.pdf`, and `.docx` files
- Uses `DirectoryLoader` for document loading
- Splits documents into chunks with `RecursiveCharacterTextSplitter`
- Adds 13 required metadata fields to each chunk
- Stores embeddings in ChromaDB
- Persists vector database to `./chroma_db`
- Uses OpenRouter for chat model and embeddings
- Uses LangChain `create_agent`
- Uses a `@tool`-decorated RAG search function
- Uses PostgreSQL-backed `PostgresSaver` for short-term memory
- Supports required test questions and interactive CLI chat mode

---

## Project Structure

```text
hr_rag_chatbot/
├── document_loader.py
├── vector_store.py
├── rag_agent.py
├── main.py
├── requirements.txt
├── .env.example
├── README.md
└── hr_documents_pack/
    └── initial_docs/
        ├── leave_policy.docx
        ├── employee_handbook.docx
        ├── offboarding_checklist.txt
        ├── it_security.pdf
        ├── performance_review.docx
        └── travel_expense_policy.docx
```

---

## Requirements

- Python >= 3.10
- PostgreSQL
- OpenRouter API key
- LangChain >= 1.2.0

Install dependencies:

```bash
pip install -r requirements.txt
```

If using `uv`:

```bash
uv pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file based on `.env.example`.

Example `.env.example`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here

DB_URI=postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable
```

The real `.env` file should contain your own OpenRouter API key:

```env
OPENROUTER_API_KEY=sk-or-...

DB_URI=postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable
```

---

## PostgreSQL Setup

PostgreSQL is used for short-term memory through `PostgresSaver`.

You can start PostgreSQL with Docker:

```bash
docker run --name rag-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -d postgres:16
```

Check if the PostgreSQL container is running:

```bash
docker ps
```

Expected database URI:

```text
postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable
```

---

## Document Ingestion

Place HR documents inside:

```text
hr_documents_pack/initial_docs/
```

Supported formats:

- `.txt`
- `.pdf`
- `.docx`

Run document ingestion:

```bash
python main.py ingest
```

With `uv`:

```bash
uv run main.py ingest
```

This command:

1. Loads documents using `DirectoryLoader`
2. Splits documents into chunks
3. Adds metadata fields
4. Creates embeddings
5. Stores vectors in ChromaDB
6. Persists the vector database to `./chroma_db`

---

## ChromaDB Configuration

This project uses local persistent ChromaDB storage.

```text
persist_directory="./chroma_db"
collection_name="vbo-aillm-bc-rag"
```

ChromaDB does not need to be started with Docker for this project.  
It works locally as a persistent folder inside the project directory.

---

## Embedding Configuration

Embeddings are created through OpenRouter using the OpenAI-compatible API.

```python
OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    openai_api_base="https://openrouter.ai/api/v1"
)
```

Embedding model:

```text
openai/text-embedding-3-small
```

---

## Chat Model Configuration

The chatbot uses OpenRouter for the chat model.

```python
init_chat_model(
    "openai:google/gemini-2.5-flash-lite",
    base_url="https://openrouter.ai/api/v1"
)
```

Chat model:

```text
openai:google/gemini-2.5-flash-lite
```

---

## Required Metadata Fields

Each chunk includes the following 13 metadata fields:

| Field | Description |
|---|---|
| `file_name` | Original filename for update tracking |
| `file_extension` | File extension such as `.docx`, `.pdf`, `.txt` |
| `file_size_bytes` | Original file size in bytes |
| `character_count` | Total character count of the document |
| `chunk_index` | Position of the chunk within the document |
| `chunk_size` | Size of the current chunk in characters |
| `chunk_overlap` | Overlap size used during chunking |
| `document_type` | Format category such as document, text, or pdf |
| `creation_date` | File creation timestamp |
| `last_modified` | File last modified timestamp |
| `ingestion_timestamp` | Time when the document was ingested |
| `page_number` | Page number for PDFs |
| `section_title` | Section heading if available |

---

## Running Required Tests

Run the required homework test questions:

```bash
python main.py test
```

With `uv`:

```bash
uv run main.py test
```

The required test questions are:

1. What is the company's leave policy?
2. How many vacation days do employees get?
3. What are the steps in the offboarding process?
4. What are the IT security requirements for new employees?
5. What is the performance review process?
6. How do I submit travel expenses for reimbursement?

Example output:

```text
Test Question 1
You: What is the company's leave policy?
Bot: The company offers 20 paid vacation days annually, with requests submitted 5 days in advance through the HR Portal. Employees also receive 10 sick days per year. (leave_policy.docx)
```

---

## Short-Term Memory Test

Run:

```bash
python main.py memory-test
```

With `uv`:

```bash
uv run main.py memory-test
```

Example:

```text
You: What is the leave policy?
Bot: The company offers 20 paid vacation days annually and 10 sick days per year. (leave_policy.docx)

You: What about sick leave?
Bot: Employees are entitled to 10 sick days per year. A doctor's report is required for sick leave exceeding two consecutive days. (leave_policy.docx)
```

The second question depends on the first one.  
This verifies that the chatbot remembers previous turns in the same conversation thread.

---

## Interactive Chat Mode

Start the CLI chatbot:

```bash
python main.py chat
```

With `uv`:

```bash
uv run main.py chat
```

Example:

```text
HR RAG Chatbot started.
Type 'exit', 'quit', or 'q' to stop.

You: What is the leave policy?
Bot: The company offers 20 paid vacation days annually. (leave_policy.docx)

You: What about sick leave?
Bot: Employees are entitled to 10 sick days per year. (leave_policy.docx)
```

To exit:

```text
q
```

or:

```text
exit
```

---

## Memory Behavior

Short-term memory is stored in PostgreSQL through `PostgresSaver`.

The memory depends on `thread_id`.

If the same stable `thread_id` is used, the chatbot can remember previous conversation turns even after restarting the CLI.

Example:

```text
You: What is the leave policy?
Bot: The company offers 20 paid vacation days annually. (leave_policy.docx)

You: q
Chat ended.
```

After restarting the chatbot with the same `thread_id`:

```text
You: What policy did I ask about earlier?
Bot: You asked about the leave policy.
```

---

## RAG Flow

The project follows this RAG pipeline:

```text
HR Documents
↓
DirectoryLoader
↓
Document objects
↓
RecursiveCharacterTextSplitter
↓
Chunked Document objects
↓
OpenRouter Embeddings
↓
ChromaDB
↓
Retriever
↓
RAG Tool
↓
LangChain Agent
↓
Final Answer with Source Citation
```

---

## Main Commands

```bash
python main.py ingest
python main.py test
python main.py memory-test
python main.py chat
```

With `uv`:

```bash
uv run main.py ingest
uv run main.py test
uv run main.py memory-test
uv run main.py chat
```

---

## Notes

- The chatbot answers only using retrieved HR document context.
- Answers are kept short.
- Each answer cites the source document using the `file_name` metadata.
- ChromaDB is persisted locally under `./chroma_db`.
- PostgreSQL is used only for short-term conversation memory.
- If Chroma raises a SQLite version error, the `pysqlite3` shim can be added at the top of the vector store file.
- API keys and local database folders should not be committed to GitHub.

---

## Recommended `.gitignore`

```gitignore
.env
chroma_db/
__pycache__/
*.pyc
.venv/
```