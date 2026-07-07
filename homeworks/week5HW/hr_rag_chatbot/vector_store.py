# ChromaDB SQLite version hatası alınırsa bu shim çözüm olur.
# Bu importlar Chroma import edilmeden önce en üstte durmalı.
try:
    import pysqlite3
    import sys

    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

import os
import shutil
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from document_loader import load_and_split_documents


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "vbo-aillm-bc-rag"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
EMBEDDING_MODEL = "openai/text-embedding-3-small"


def get_embeddings() -> OpenAIEmbeddings:
    """
    OpenRouter üzerinden OpenAI uyumlu embedding modeli oluşturur.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY bulunamadı. Lütfen .env dosyasına ekleyin."
        )

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=api_key,
        openai_api_base=OPENROUTER_BASE_URL,
    )

    return embeddings


def create_vector_store(
    documents: List[Document],
    reset_db: bool = True,
) -> Chroma:
    """
    Verilen chunk Document listesini embedding'e çevirir
    ve ChromaDB içine kaydeder.

    Ödev gereği Chroma.from_documents kullanıyoruz.
    """
    if reset_db and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )

    return vectorstore


def load_vector_store() -> Chroma:
    """
    Daha önce oluşturulmuş ChromaDB'yi sorgulama için tekrar yükler.

    Ödev gereği query tarafında Chroma(...) kullanıyoruz.
    """
    embeddings = get_embeddings()

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )

    return vectorstore


def get_retriever():
    """
    ChromaDB üzerinden retriever oluşturur.
    k=4 demek: her soru için en alakalı 4 chunk getir.
    """
    vectorstore = load_vector_store()

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 4}
    )

    return retriever


def ingest_documents() -> Chroma:
    """
    Ana ingestion fonksiyonu:
    1. Dokümanları yükler
    2. Chunk'lara böler
    3. ChromaDB'ye kaydeder
    """
    chunks = load_and_split_documents()

    if not chunks:
        raise ValueError("Hiç doküman chunk'ı bulunamadı.")

    print(f"Toplam chunk sayısı: {len(chunks)}")
    print("Embedding oluşturuluyor ve ChromaDB'ye kaydediliyor...")

    vectorstore = create_vector_store(
        documents=chunks,
        reset_db=True,
    )

    print(f"ChromaDB oluşturuldu: {CHROMA_DIR}")
    print(f"Collection name: {COLLECTION_NAME}")

    return vectorstore


def test_retrieval(query: str):
    """
    Retriever'ın çalışıp çalışmadığını test etmek için kullanılır.
    """
    retriever = get_retriever()

    docs = retriever.invoke(query)

    print(f"\nSoru: {query}")
    print(f"Bulunan chunk sayısı: {len(docs)}")

    for index, doc in enumerate(docs, start=1):
        print("\n" + "-" * 50)
        print(f"Sonuç {index}")
        print(f"Kaynak dosya: {doc.metadata.get('file_name')}")
        print(f"Sayfa: {doc.metadata.get('page_number')}")
        print(f"Chunk index: {doc.metadata.get('chunk_index')}")
        print("\nİçerik:")
        print(doc.page_content[:700])


if __name__ == "__main__":
    ingest_documents()

    test_retrieval("What is the company's leave policy?")