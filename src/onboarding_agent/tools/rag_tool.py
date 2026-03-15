"""
RAG tool using ChromaDB (persistent) + Ollama embeddings (nomic-embed-text).

Requires:
  ollama pull nomic-embed-text

ChromaDB data is persisted to <project_root>/.chromadb so the knowledge base
survives server restarts and does not need to be re-indexed each time.
"""

import os
from pathlib import Path
from typing import List

import requests
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Resolve paths relative to this file:
#   src/onboarding_agent/tools/rag_tool.py  →  project root
_PROJECT_ROOT = Path(__file__).parents[4]
KNOWLEDGE_DIR = _PROJECT_ROOT / "knowledge"
CHROMA_PERSIST_DIR = _PROJECT_ROOT / ".chromadb"

COLLECTION_NAME = "onboarding_policies"

# Module-level singletons — initialised once per process
_client: chromadb.PersistentClient | None = None
_collection = None


# --------------------------------------------------------------------------- #
# Ollama embedding function (chromadb EmbeddingFunction interface)
# --------------------------------------------------------------------------- #

class OllamaEmbeddingFunction(EmbeddingFunction[Documents]):
    """Delegates embedding to Ollama's REST API using nomic-embed-text."""

    def __call__(self, input: Documents) -> Embeddings:
        api_base = os.getenv("API_BASE", "http://localhost:11434")
        embeddings: Embeddings = []
        for text in input:
            resp = requests.post(
                f"{api_base}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=30,
            )
            resp.raise_for_status()
            embeddings.append(resp.json()["embedding"])
        return embeddings


# --------------------------------------------------------------------------- #
# ChromaDB initialisation & knowledge base loading
# --------------------------------------------------------------------------- #

def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is not None:
        return _collection

    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    _client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=OllamaEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )

    if _collection.count() == 0:
        _index_knowledge_base(_collection)

    return _collection


def _index_knowledge_base(collection: chromadb.Collection) -> None:
    """Chunk all .md files in knowledge/ and insert into ChromaDB."""
    docs: List[str] = []
    ids: List[str] = []
    metadatas: List[dict] = []

    for kb_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = kb_file.read_text(encoding="utf-8")
        # Split on blank lines; drop very short fragments
        chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 30]
        for idx, chunk in enumerate(chunks):
            doc_id = f"{kb_file.stem}__{idx}"
            docs.append(chunk)
            ids.append(doc_id)
            metadatas.append({"source": kb_file.name, "chunk": idx})

    if docs:
        collection.add(documents=docs, ids=ids, metadatas=metadatas)


def reindex() -> int:
    """
    Drop the existing collection and re-index the knowledge base.
    Useful after editing files in knowledge/.
    Returns the number of chunks indexed.
    """
    global _collection
    if _client is not None:
        _client.delete_collection(COLLECTION_NAME)
    _collection = None
    coll = _get_collection()
    return coll.count()


# --------------------------------------------------------------------------- #
# CrewAI tool
# --------------------------------------------------------------------------- #

class RAGQueryInput(BaseModel):
    query: str = Field(
        description=(
            "Question or topic to search for in onboarding policies. "
            "Example: 'which GitHub team for a Product Manager?' or "
            "'what access does a Senior Software Engineer get?'"
        )
    )


class OnboardingRAGTool(BaseTool):
    name: str = "Onboarding Policy Search"
    description: str = (
        "Search the company onboarding knowledge base stored in ChromaDB. "
        "Returns the most relevant policy excerpts for role-to-GitHub-team mapping. "
        "Always call this tool before deciding whether a role belongs to the "
        "'developer' or 'readonly' GitHub team."
    )
    args_schema: type[BaseModel] = RAGQueryInput

    def _run(self, query: str) -> str:
        collection = _get_collection()
        results = collection.query(query_texts=[query], n_results=3)
        docs = results.get("documents", [[]])[0]
        if not docs:
            return "No relevant policies found in the knowledge base."
        return "\n\n---\n\n".join(docs)
