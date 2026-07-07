5# Week 6 Homework: RAG Chatbot with Short-Term Memory

## 🎯 Objective

Build a RAG (Retrieval-Augmented Generation) chatbot that:
1. Answers questions about HR documents
2. Remembers conversation context (short-term memory)

---

## 📋 Requirements

### Technical Requirements

- Python >= 3.10
- LangChain >= 1.2.0
- Use `create_agent` from `langchain.agents` (not deprecated methods)
- Use `DirectoryLoader` for loading documents
- Use ChromaDB for vector storage with `persist_directory="./chroma_db"`
- **Collection Name:** `vbo-aillm-bc-rag`
- Use OpenRouter for both chat model and embeddings
  - Chat model: `init_chat_model("openai:google/gemini-2.5-flash-lite", ..., base_url="https://openrouter.ai/api/v1&quot;)`
  - Embeddings: `OpenAIEmbeddings(model="openai/text-embedding-3-small", openai_api_base="https://openrouter.ai/api/v1&quot;)`
- Use PostgreSQL-backed `PostgresSaver` checkpointer for conversation memory

### Functional Requirements

| Feature | Description |
|---------|-------------|
| Document Ingestion | Load DOCX, PDF, TXT files and store in vector database |
| RAG Query | Answer questions using retrieved document context |
| Short-Term Memory | Remember conversation for follow-up questions |

---

## 📁 Expected Structure

```
hr_rag_chatbot/
├── document_loader.py    # Document loading and processing
├── vector_store.py       # ChromaDB operations
├── rag_agent.py          # Agent with memory
├── main.py               # CLI application
├── requirements.txt
├── .env.example
├── README.md
└── hr_documents_pack/
    └── initial_docs/     # Original documents
```

---

## 📝 Tasks

### Task 1: Document Loading (20 points)

- Use `DirectoryLoader` to load DOCX, PDF, TXT files from `hr_documents_pack/initial_docs/`
- Chunk with `RecursiveCharacterTextSplitter` (500 chars, 100 overlap)
- Add 13 metadata fields (see Metadata section below)

### Task 2: Vector Store (20 points)

- Embeddings via `OpenAIEmbeddings` with model `openai/text-embedding-3-small` and OpenRouter `base_url`
- Persist to `./chroma_db` with collection name `vbo-aillm-bc-rag`
- Ingest with `Chroma.from_documents`; load for query with `Chroma(...)` + `as_retriever(search_kwargs={"k": 4})`
- If you hit a Chroma SQLite version error, add the `pysqlite3` shim at the top of the file

### Task 3: Short-Term Memory (25 points)

- Use `PostgresSaver.from_conn_string(DB_URI)` and call `checkpointer.setup()` once
- Pass `checkpointer` to `create_agent`
- Use a stable `thread_id` per user session so follow-up turns reuse the same memory
- The agent must understand references across turns ("it", "them", "that policy")

### Task 4: RAG Agent (35 points)

- Build `retriever = vectorstore.as_retriever(search_kwargs={"k": 4})` and call `retriever.invoke(query)` inside a `@tool`-decorated function
- Use `init_chat_model("openai:google/gemini-2.5-flash-lite", ..., base_url="https://openrouter.ai/api/v1&quot;)`
- Wire the tool into `create_agent` together with the `checkpointer` from Task 3
- Keep answers SHORT (2-3 sentences) and always cite the source document (`file_name` metadata)

---

## 📊 Required Metadata (13 Fields)

Each chunk must include these metadata fields:

| Field | Description |
|-------|-------------|
| `file_name` | Original filename for update tracking |
| `file_extension` | File extension (.docx, .pdf, .txt) |
| `file_size_bytes` | Original file size in bytes |
| `character_count` | Total character count of document |
| `chunk_index` | Position within the document |
| `chunk_size` | Size of current chunk in characters |
| `chunk_overlap` | Overlap size used during chunking |
| `document_type` | Format category (document, text, pdf) |
| `creation_date` | File creation timestamp |
| `last_modified` | File last modified timestamp |
| `ingestion_timestamp` | When ingested into system |
| `page_number` | Page number (for PDFs) |
| `section_title` | Section heading if available |

---

## 🧪 Testing

### Test Questions (Required)

Run these questions with `python main.py test`:

1. "What is the company's leave policy?"
2. "How many vacation days do employees get?"
3. "What are the steps in the offboarding process?"
4. "What are the IT security requirements for new employees?"
5. "What is the performance review process?"
6. "How do I submit travel expenses for reimbursement?"

### Short-Term Memory Test

```
You: What is the leave policy?
Bot: Employees get 20 vacation days...

You: What about sick leave?
Bot: [Should understand context and answer about sick leave]

```

---

## 📊 Grading

| Task | Points |
|------|--------|
| Document Loading (13 metadata) | 20 |
| Vector Store | 20 |
| Short-Term Memory | 25 |
| RAG Agent | 35 |
| **Total** | **100** |