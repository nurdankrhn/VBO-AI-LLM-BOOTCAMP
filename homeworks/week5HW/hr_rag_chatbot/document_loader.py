from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "hr_documents_pack" / "initial_docs"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def _timestamp_to_iso(timestamp: float) -> str:
    """
    Dosya tarihlerini okunabilir ISO formatına çevirir.
    """
    return datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")


def _get_document_type(file_extension: str) -> str:
    """
    Dosya uzantısına göre document_type metadata alanını belirler.
    """
    if file_extension == ".pdf":
        return "pdf"
    if file_extension == ".txt":
        return "text"
    if file_extension == ".docx":
        return "document"
    return "unknown"


def _infer_section_title(text: str) -> str:
    """
    Chunk içinden basit bir section title tahmini yapar.
    Eğer net bir başlık bulunamazsa 'unknown' döner.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines[:5]:
        clean_line = line.strip(":- ")

        if not clean_line:
            continue

        # Çok uzun satırları başlık kabul etmeyelim
        if len(clean_line) > 80:
            continue

        # Başlık gibi görünen satırları yakalamaya çalışıyoruz
        if (
            clean_line.isupper()
            or clean_line.istitle()
            or clean_line.endswith(":")
            or clean_line[0].isdigit()
        ):
            return clean_line

    return "unknown"


def _load_txt_documents(docs_dir: Path) -> List[Document]:
    loader = DirectoryLoader(
        str(docs_dir),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={
            "encoding": "utf-8",
            "autodetect_encoding": True,
        },
        show_progress=True,
    )
    return loader.load()


def _load_pdf_documents(docs_dir: Path) -> List[Document]:
    loader = DirectoryLoader(
        str(docs_dir),
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    return loader.load()


def _load_docx_documents(docs_dir: Path) -> List[Document]:
    loader = DirectoryLoader(
        str(docs_dir),
        glob="**/*.docx",
        loader_cls=Docx2txtLoader,
        show_progress=True,
    )
    return loader.load()


def load_documents(docs_dir: Path = DOCS_DIR) -> List[Document]:
    """
    initial_docs klasöründeki TXT, PDF ve DOCX dosyalarını yükler.

    Çıktı:
        list[Document]
    """
    if not docs_dir.exists():
        raise FileNotFoundError(f"Document folder not found: {docs_dir}")

    documents: List[Document] = []

    documents.extend(_load_txt_documents(docs_dir))
    documents.extend(_load_pdf_documents(docs_dir))
    documents.extend(_load_docx_documents(docs_dir))

    return documents


def _calculate_character_counts_by_source(
    documents: List[Document],
) -> Dict[str, int]:
    """
    Her kaynak dosya için toplam karakter sayısını hesaplar.
    PDF'lerde her sayfa ayrı Document olarak gelebileceği için
    aynı source'a sahip Document'ların karakterleri toplanır.
    """
    character_counts = defaultdict(int)

    for doc in documents:
        source = str(doc.metadata.get("source", "unknown"))
        character_counts[source] += len(doc.page_content)

    return dict(character_counts)


def split_documents(documents: List[Document]) -> List[Document]:
    """
    Document listesini chunk'lara böler ve her chunk'a 13 metadata alanını ekler.

    Çıktı:
        list[Document]
    """
    character_counts_by_source = _calculate_character_counts_by_source(documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    ingestion_timestamp = datetime.now().isoformat(timespec="seconds")
    chunk_counters_by_source = defaultdict(int)

    for chunk in chunks:
        source = str(chunk.metadata.get("source", "unknown"))
        source_path = Path(source)

        file_name = source_path.name
        file_extension = source_path.suffix.lower()

        if source_path.exists():
            stat = source_path.stat()
            file_size_bytes = stat.st_size
            creation_date = _timestamp_to_iso(stat.st_ctime)
            last_modified = _timestamp_to_iso(stat.st_mtime)
        else:
            file_size_bytes = 0
            creation_date = "unknown"
            last_modified = "unknown"

        # PyPDFLoader genelde page bilgisini 0-based verir.
        # TXT/DOCX için yoksa -1 kullanıyoruz.
        raw_page = chunk.metadata.get("page", -1)
        if isinstance(raw_page, int):
            page_number = raw_page + 1 if raw_page >= 0 else -1
        else:
            page_number = -1

        chunk_index = chunk_counters_by_source[source]
        chunk_counters_by_source[source] += 1

        # Ödevde istenen 13 metadata alanı
        chunk.metadata["file_name"] = file_name
        chunk.metadata["file_extension"] = file_extension
        chunk.metadata["file_size_bytes"] = file_size_bytes
        chunk.metadata["character_count"] = character_counts_by_source.get(source, 0)
        chunk.metadata["chunk_index"] = chunk_index
        chunk.metadata["chunk_size"] = len(chunk.page_content)
        chunk.metadata["chunk_overlap"] = CHUNK_OVERLAP
        chunk.metadata["document_type"] = _get_document_type(file_extension)
        chunk.metadata["creation_date"] = creation_date
        chunk.metadata["last_modified"] = last_modified
        chunk.metadata["ingestion_timestamp"] = ingestion_timestamp
        chunk.metadata["page_number"] = page_number
        chunk.metadata["section_title"] = _infer_section_title(chunk.page_content)

    return chunks


def load_and_split_documents(docs_dir: Path = DOCS_DIR) -> List[Document]:
    """
    Ana fonksiyon:
    1. Dokümanları yükler
    2. Chunk'lara böler
    3. Metadata ekler
    """
    documents = load_documents(docs_dir)
    chunks = split_documents(documents)
    return chunks


if __name__ == "__main__":
    chunks = load_and_split_documents()

    print(f"Toplam chunk sayısı: {len(chunks)}")

    if chunks:
        print("\nİlk chunk içeriği:")
        print(chunks[0].page_content[:500])

        print("\nİlk chunk metadata:")
        for key, value in chunks[0].metadata.items():
            print(f"{key}: {value}")