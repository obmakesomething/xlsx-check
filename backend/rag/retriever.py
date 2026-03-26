"""RAG retriever for searching similar projects, components, and knowledge.

Provides high-level search methods over the vector store collections and
a :meth:`build_context` helper that assembles a combined context string
suitable for passing to LLM agents.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .vector_store import VectorStore

logger = logging.getLogger(__name__)

# Human-readable labels for each collection (Korean)
_COLLECTION_LABELS: dict[str, str] = {
    "circuits": "회로 설계 참고",
    "bom_patterns": "부품/BOM 참고",
    "certification": "인증 참고",
    "debugging": "디버깅 참고",
    "knowledge": "지식베이스 참고",
}


class Retriever:
    """Search the vector store and build context for LLM agents.

    Args:
        store: A :class:`VectorStore` instance.  Defaults to the
            singleton returned by ``VectorStore.get_instance()``.
    """

    def __init__(self, store: Optional[VectorStore] = None) -> None:
        self.store = store or VectorStore.get_instance()

    # -----------------------------------------------------------------
    # Typed search helpers
    # -----------------------------------------------------------------

    def retrieve_similar_projects(
        self,
        query: str,
        n: int = 5,
        project_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Find past projects and circuit blocks similar to *query*.

        Args:
            query: Natural-language description of the desired circuit.
            n: Maximum number of results.
            project_id: Restrict to a specific project.

        Returns:
            Flat list of result dicts (``document``, ``metadata``, ``distance``).
        """
        where = {"project_id": str(project_id)} if project_id is not None else None
        raw = self.store.query("circuits", query, n_results=n, where=where)
        return self._format(raw)

    def retrieve_components(
        self,
        query: str,
        n: int = 5,
        category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Find relevant components / BoM entries.

        Args:
            query: Part description, value, or reference.
            n: Maximum number of results.
            category: Optional category filter (e.g. ``"Resistor"``).
        """
        where = {"category": category} if category else None
        raw = self.store.query("bom_patterns", query, n_results=n, where=where)
        return self._format(raw)

    def retrieve_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        n: int = 5,
    ) -> list[dict[str, Any]]:
        """Search the general knowledge base.

        Args:
            query: Free-text query.
            category: Optional category filter.
            n: Maximum results.
        """
        where = {"category": category} if category else None
        raw = self.store.query("knowledge", query, n_results=n, where=where)
        return self._format(raw)

    def retrieve_certification_info(
        self,
        query: str,
        n: int = 5,
    ) -> list[dict[str, Any]]:
        """Find certification and regulatory information."""
        raw = self.store.query("certification", query, n_results=n)
        return self._format(raw)

    def retrieve_debug_cases(
        self,
        query: str,
        n: int = 5,
    ) -> list[dict[str, Any]]:
        """Find debugging cases matching *query*."""
        raw = self.store.query("debugging", query, n_results=n)
        return self._format(raw)

    # -----------------------------------------------------------------
    # Cross-collection search
    # -----------------------------------------------------------------

    def search_all(
        self,
        query: str,
        n_per_collection: int = 3,
    ) -> dict[str, list[dict[str, Any]]]:
        """Search across **all** collections and return grouped results.

        Args:
            query: Natural-language query.
            n_per_collection: Max results per collection.

        Returns:
            Dict mapping collection names to result lists. Only
            collections with results are included.
        """
        results: dict[str, list[dict[str, Any]]] = {}
        for col_name in _COLLECTION_LABELS:
            raw = self.store.query(col_name, query, n_results=n_per_collection)
            formatted = self._format(raw)
            if formatted:
                results[col_name] = formatted
        return results

    # -----------------------------------------------------------------
    # Context builder for agents
    # -----------------------------------------------------------------

    def build_context(
        self,
        query: str,
        collections: Optional[list[str]] = None,
        n_per_collection: int = 3,
        max_chars: int = 8000,
    ) -> str:
        """Build a combined context string suitable for LLM consumption.

        Searches the requested (or all) collections and concatenates the
        top results into a single string, prefixed with Korean section
        headings.

        Args:
            query: The user or agent query.
            collections: List of collection names to search (defaults to
                all five collections).
            n_per_collection: Maximum results per collection.
            max_chars: Approximate character budget for the context.

        Returns:
            A formatted multi-section string, or empty string when no
            relevant documents are found.
        """
        target_collections = collections or list(_COLLECTION_LABELS.keys())

        context_parts: list[str] = []
        total_len = 0

        for col_name in target_collections:
            if col_name not in _COLLECTION_LABELS:
                continue
            label = _COLLECTION_LABELS[col_name]
            raw = self.store.query(col_name, query, n_results=n_per_collection)
            items = self._format(raw)

            for item in items:
                doc = item.get("document", "")
                if not doc:
                    continue
                chunk = f"[{label}]\n{doc}"
                if total_len + len(chunk) > max_chars:
                    break
                context_parts.append(chunk)
                total_len += len(chunk)

            if total_len >= max_chars:
                break

        return "\n\n---\n\n".join(context_parts) if context_parts else ""

    # Alias used by older call sites
    get_context_for_query = build_context

    # -----------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _format(raw: dict[str, Any]) -> list[dict[str, Any]]:
        """Flatten ChromaDB result dict into a list of result dicts."""
        documents = raw.get("documents", [])
        metadatas = raw.get("metadatas", [])
        distances = raw.get("distances", [])

        results: list[dict[str, Any]] = []
        for i, doc in enumerate(documents):
            results.append({
                "document": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            })
        return results
