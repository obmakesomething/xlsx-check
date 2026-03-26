"""RAG retriever for searching similar projects, components, and knowledge."""

from __future__ import annotations
import logging
from typing import Any, Optional

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Search the vector store for relevant context."""

    def __init__(self, store: VectorStore | None = None):
        self.store = store or VectorStore.get_instance()

    def search_circuits(self, query: str, n_results: int = 5,
                        project_id: Optional[int] = None) -> list[dict[str, Any]]:
        """Search circuit designs and project summaries."""
        where = {"project_id": project_id} if project_id else None
        raw = self.store.query("circuits", query, n_results=n_results, where=where)
        return self._format_results(raw)

    def search_components(self, query: str, n_results: int = 10,
                          category: Optional[str] = None) -> list[dict[str, Any]]:
        """Search BoM patterns and component data."""
        where = {"category": category} if category else None
        raw = self.store.query("bom_patterns", query, n_results=n_results, where=where)
        return self._format_results(raw)

    def search_certifications(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search certification and regulatory information."""
        raw = self.store.query("certification", query, n_results=n_results)
        return self._format_results(raw)

    def search_debug_cases(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search debugging cases and known issues."""
        raw = self.store.query("debugging", query, n_results=n_results)
        return self._format_results(raw)

    def search_knowledge(self, query: str, n_results: int = 5,
                         category: Optional[str] = None) -> list[dict[str, Any]]:
        """Search the general knowledge base."""
        where = {"category": category} if category else None
        raw = self.store.query("knowledge", query, n_results=n_results, where=where)
        return self._format_results(raw)

    def search_all(self, query: str, n_results_per_collection: int = 3) -> dict[str, list[dict[str, Any]]]:
        """Search across all collections and return combined results."""
        results = {}
        for collection in ("circuits", "bom_patterns", "certification", "debugging", "knowledge"):
            raw = self.store.query(collection, query, n_results=n_results_per_collection)
            formatted = self._format_results(raw)
            if formatted:
                results[collection] = formatted
        return results

    def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """Get a formatted context string for LLM consumption."""
        all_results = self.search_all(query, n_results_per_collection=3)

        context_parts = []
        total_length = 0

        for collection, items in all_results.items():
            label = {
                "circuits": "회로 설계 참고",
                "bom_patterns": "부품/BOM 참고",
                "certification": "인증 참고",
                "debugging": "디버깅 참고",
                "knowledge": "지식베이스 참고",
            }.get(collection, collection)

            for item in items:
                doc = item.get("document", "")
                chunk = f"[{label}] {doc}"
                if total_length + len(chunk) > max_tokens * 4:  # Rough char estimate
                    break
                context_parts.append(chunk)
                total_length += len(chunk)

        return "\n\n".join(context_parts) if context_parts else ""

    def _format_results(self, raw: dict[str, Any]) -> list[dict[str, Any]]:
        """Format raw ChromaDB results into a cleaner structure."""
        documents = raw.get("documents", [])
        metadatas = raw.get("metadatas", [])
        distances = raw.get("distances", [])

        results = []
        for i, doc in enumerate(documents):
            entry = {
                "document": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            }
            results.append(entry)

        return results
