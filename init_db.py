"""
One-time script to load knowledge base documents into ChromaDB.

Run this before starting the API server:
    python init_db.py

What it does:
  1. Creates the .chromadb/ persistent store at the project root
  2. Reads all .md files from knowledge/
  3. Chunks them by paragraph
  4. Embeds each chunk using Ollama (nomic-embed-text)
  5. Inserts into the 'onboarding_policies' collection

Re-running is safe — it checks if the collection already has data
and skips indexing unless you pass --force to re-index from scratch.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv  # optional, safe to remove if not using python-dotenv

# Load .env so API_BASE is available for Ollama
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add src/ to path so the package is importable without installing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from onboarding_agent.tools.rag_tool import (
    _get_collection,
    _index_knowledge_base,
    KNOWLEDGE_DIR,
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    _client,
)
import chromadb
from onboarding_agent.tools.rag_tool import OllamaEmbeddingFunction


def init(force: bool = False) -> None:
    force = force or ("--force" in sys.argv)

    print(f"Knowledge dir : {KNOWLEDGE_DIR}")
    print(f"ChromaDB path : {CHROMA_PERSIST_DIR}")

    # List files that will be indexed
    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not md_files:
        print("\nERROR: No .md files found in knowledge/. Nothing to index.")
        sys.exit(1)

    print(f"\nFiles to index:")
    for f in md_files:
        print(f"  - {f.name}")

    # Connect to ChromaDB
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))

    if force:
        print("\n--force flag set: dropping existing collection...")
        try:
            client.delete_collection(COLLECTION_NAME)
            print("  Existing collection dropped.")
        except Exception:
            pass  # collection didn't exist yet

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=OllamaEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )

    existing = collection.count()
    if existing > 0 and not force:
        print(f"\nCollection already contains {existing} chunks. Skipping.")
        print("Run with --force to re-index: python init_db.py --force")
        return

    print("\nIndexing knowledge base — calling Ollama for embeddings...")
    print("(This may take a minute on first run)\n")

    from onboarding_agent.tools.rag_tool import _index_knowledge_base as _index
    _index(collection)

    total = collection.count()
    print(f"\nDone. {total} chunks indexed into '{COLLECTION_NAME}'.")
    print("You can now start the server: onboarding_agent")


if __name__ == "__main__":
    init()
