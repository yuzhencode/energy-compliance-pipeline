"""
rag/ingest.py
=============
Downloads Ofgem PDFs, extracts text, chunks, embeds, and stores in ChromaDB.

Sources (all official Ofgem documents):
  - Debt Strategy Update, Nov 2025
  - DRS Delivery Guidance V1.0, Nov 2025
  - DRS Working Paper, Aug 2025
  - Guide for energy suppliers and debt advice providers, Jan 2026

Usage:
    python rag/ingest.py
"""

import os
import sys
from pathlib import Path

import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings

sys.path.insert(0, str(Path(__file__).parent.parent))

DOCS_DIR   = Path(__file__).parent / "docs"
CHROMA_DIR = Path(__file__).parent / "chroma_db"

OFGEM_DOCS = [
    {
        "url":      "https://www.ofgem.gov.uk/sites/default/files/2025-11/DRS_Delivery_Guidance_V1.0.pdf",
        "filename": "DRS_Delivery_Guidance_V1.0.pdf",
        "title":    "Ofgem DRS Delivery Guidance V1.0 (Nov 2025)",
    },
    {
        "url":      "https://www.ofgem.gov.uk/sites/default/files/2025-08/DRS-working-paper-final.pdf",
        "filename": "DRS_working_paper_Aug2025.pdf",
        "title":    "Ofgem DRS Working Paper (Aug 2025)",
    },
    {
        "url":      "https://www.ofgem.gov.uk/sites/default/files/2026-01/Guide_for_energy_suppliers_and_debt_advice_providers.pdf",
        "filename": "Guide_suppliers_debt_advice_Jan2026.pdf",
        "title":    "Guide for energy suppliers and debt advice providers (Jan 2026)",
    },
]


def download_docs() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for doc in OFGEM_DOCS:
        dest = DOCS_DIR / doc["filename"]
        if dest.exists():
            print(f"  [skip] {doc['filename']} already downloaded")
            continue
        print(f"  [download] {doc['filename']} ...")
        r = requests.get(doc["url"], timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  [ok] {dest} ({len(r.content) // 1024} KB)")


def load_and_chunk() -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "],
    )
    all_chunks = []
    for doc in OFGEM_DOCS:
        path = DOCS_DIR / doc["filename"]
        if not path.exists():
            print(f"  [warn] {path} not found, skipping")
            continue
        print(f"  [load] {doc['filename']}")
        loader = PyPDFLoader(str(path))
        pages  = loader.load()
        # Tag each chunk with source metadata
        for page in pages:
            page.metadata["source_title"] = doc["title"]
            page.metadata["source_url"]   = doc["url"]
        chunks = splitter.split_documents(pages)
        all_chunks.extend(chunks)
        print(f"         → {len(pages)} pages, {len(chunks)} chunks")
    return all_chunks


def embed_and_store(chunks: list) -> None:
    print("\n  [embed] Loading sentence-transformers/all-MiniLM-L6-v2 ...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    print(f"  [store] Writing {len(chunks)} chunks to ChromaDB ...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="ofgem_docs",
    )
    print(f"  [ok] ChromaDB persisted to {CHROMA_DIR}")


def main() -> None:
    print("=== Ofgem RAG Ingest ===\n")
    print("1. Downloading PDFs ...")
    download_docs()
    print("\n2. Loading and chunking ...")
    chunks = load_and_chunk()
    print(f"\n   Total chunks: {len(chunks)}")
    print("\n3. Embedding and storing ...")
    embed_and_store(chunks)
    print("\n=== Ingest complete ===")


if __name__ == "__main__":
    main()
