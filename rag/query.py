"""
rag/query.py
============
CLI interface for the Ofgem compliance RAG assistant.

Usage:
    python rag/query.py
    python rag/query.py --question "What are the DRS eligibility criteria?"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.chain import build_chain


def ask(chain, question: str) -> None:
    print(f"\nQ: {question}")
    print("-" * 60)
    result = chain.invoke({"query": question})
    print(f"A: {result['result']}")
    print("\nSources:")
    seen = set()
    for doc in result["source_documents"]:
        title = doc.metadata.get("source_title", "Unknown")
        page  = doc.metadata.get("page", "?")
        key   = f"{title} p.{page}"
        if key not in seen:
            print(f"  - {title} (page {page})")
            seen.add(key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ofgem compliance RAG assistant")
    parser.add_argument("--question", "-q", type=str, help="Ask a single question and exit")
    args = parser.parse_args()

    print("Loading RAG chain (first load may take ~30s) ...")
    chain = build_chain()
    print("Ready.\n")

    if args.question:
        ask(chain, args.question)
        return

    print("Ofgem Compliance Assistant")
    print("Type 'exit' to quit.\n")
    while True:
        try:
            question = input("Q: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not question:
            continue
        if question.lower() in ("exit", "quit", "q"):
            print("Bye.")
            break
        ask(chain, question)


if __name__ == "__main__":
    main()
