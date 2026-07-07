"""
langchain_unstructured.UnstructuredLoader wraps the unstructured library, which uses spaCy for NLP during document partitioning (sentence/element segmentation, etc.). The first time it runs, it auto-downloads spaCy's small English model en_core_web_sm (~12 MB). Those two INFO lines are just it saying "downloading… installed." It's cached now, so you won't see it again.
So:
Downloading spaCy model … → fetching the dependency (once).
Installed en_core_web_sm 3.8.0 → done, success.

docker run -d --rm --name postgres-langgraph -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=langgraph_db -p 5432:5432 pgvector/pgvector:pg16
"""

from langchain_unstructured import UnstructuredLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_postgres import PGVector
import os 
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

#to find the path of the current file
BASE_DIR = Path(__file__).parent

# Chunking options for Unstructured. The default max_characters is only ~500,
# which is why the Documents came out tiny. Raise the caps so the loader emits
# larger, section-based Documents (then RecursiveCharacterTextSplitter refines
# them to chunk_size=1000).
CHUNK_KW = dict(
    chunking_strategy="by_title",
    max_characters=4000,              # hard cap per chunk
    new_after_n_chars=3000,           # soft target — start a new chunk around here
    combine_text_under_n_chars=1000,  # merge tiny sections instead of leaving fragments
)

# Txt dosyasını oku
txt_loader = UnstructuredLoader(file_path=BASE_DIR / "company_docs" / "my_text_doc.txt", **CHUNK_KW)

txt_docs = txt_loader.load()

print("txt_docs",len(txt_docs))

# PDF dosyasını oku
pdf_loader = UnstructuredLoader(file_path=BASE_DIR / "company_docs" / "Information_Security_Policy.pdf", **CHUNK_KW)

pdf_docs = pdf_loader.load()
print("pdf_docs", len(pdf_docs))



word_loader = UnstructuredLoader(file_path=BASE_DIR / "company_docs" / "Company_Policy_Handbook.docx", **CHUNK_KW)

word_docs = word_loader.load()
print(type(word_docs))
print("word_docs", len(word_docs))

# manul document
manual_documents = [
    Document(page_content='Manual document conten-1', metadata={"source": "manual-1"}),
    Document(page_content='Manual document conten-2', metadata={"source": "manual-2"})
]

print("manual_documents", len(manual_documents))

# Tüm dokümanları birleştir.
all_docs = pdf_docs + txt_docs + word_docs + manual_documents
print(len(all_docs))
# Show the size of each loaded Document so you can confirm they're no longer tiny.
print("doc sizes (chars):", sorted(len(d.page_content) for d in all_docs))

# Chunking
splitter = RecursiveCharacterTextSplitter( 
    chunk_size=1000,  
    chunk_overlap=200,  
    add_start_index=True
    )

chunks = splitter.split_documents(all_docs)

print("len of chunks", len(chunks))
# len of chunks 26
print("type of one chunk", type(chunks[0]))

# Embedding
embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",   # or "qwen/qwen3-embedding-8b", etc.
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
)

# Vector db
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="my_docs",
    connection=os.environ['PG_DSN'],
)

document_ids = vector_store.add_documents(documents=chunks)

print("len of document_ids", len(document_ids))
print(document_ids[:3])