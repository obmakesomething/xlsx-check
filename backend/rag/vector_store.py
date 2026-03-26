"""ChromaDB vector store wrapper with singleton access and collection management."""

from __future__ import annotations

import logging
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default collections used by the LED AI Copilot
COLLECTION_NAMES = [
    "circuits",
    "bom_patterns",
    "certification",
    "debugging",
    "knowledge",
]


class VectorStore:
    """Singleton wrapper around a ChromaDB persistent client.

    Usage::

        store = VectorStore.get_instance()
        store.initialize()
        store.add_documents("knowledge", documents=[...], metadatas=[...], ids=[...])
        results = store.query("knowledge", "LED driver circuit", n_results=5)
    """

    _instance: Optional["VectorStore"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._client: Any = None
        self._collections: dict[str, Any] = {}
        self._ef: Any = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "VectorStore":
        """Return the singleton *VectorStore* instance (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # -----------------------------------------------------------------
    # Initialisation
    # -----------------------------------------------------------------

    def initialize(self, persist_path: Optional[str] = None) -> None:
        """Initialize ChromaDB client and create default collections.

        Args:
            persist_path: Directory for on-disk storage.  Falls back to
                ``settings.CHROMA_PATH`` when *None*.
        """
        if self._initialized:
            return

        if persist_path is None:
            try:
                from config import settings
                persist_path = settings.CHROMA_PATH
            except Exception:
                persist_path = "./chroma_data"

        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except ImportError:
            logger.error(
                "chromadb is not installed. Install with: pip install chromadb"
            )
            raise

        from .embeddings import get_embedding_function

        self._ef = get_embedding_function()

        logger.info("Initializing ChromaDB at %s", persist_path)
        self._client = chromadb.PersistentClient(
            path=persist_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        for name in COLLECTION_NAMES:
            self._get_or_create(name)

        self._initialized = True
        logger.info(
            "VectorStore initialized with collections: %s", COLLECTION_NAMES
        )

    # -----------------------------------------------------------------
    # Collection access
    # -----------------------------------------------------------------

    @property
    def client(self) -> Any:
        """Raw ChromaDB client (may be *None* before :meth:`initialize`)."""
        return self._client

    def get_collection(self, name: str) -> Any:
        """Get or create a collection by name.

        Args:
            name: Collection name (e.g. ``"knowledge"``).

        Returns:
            A ``chromadb.Collection`` object, or *None* when the store
            is not yet initialised and the name is unknown.
        """
        if name not in self._collections:
            if self._client is not None:
                self._get_or_create(name)
            else:
                return None
        return self._collections.get(name)

    # -----------------------------------------------------------------
    # CRUD helpers
    # -----------------------------------------------------------------

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
        ids: Optional[list[str]] = None,
    ) -> bool:
        """Add (upsert) documents into a collection.

        Args:
            collection_name: Target collection.
            documents: List of text documents to embed and store.
            metadatas: Optional parallel list of metadata dicts.
            ids: Optional parallel list of unique IDs.  Auto-generated
                when not provided.

        Returns:
            ``True`` on success, ``False`` on error.
        """
        self._ensure_initialized()
        col = self.get_collection(collection_name)
        if col is None:
            logger.error("Collection '%s' not found", collection_name)
            return False

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        # Sanitize metadatas -- ChromaDB only accepts str/int/float/bool values
        if metadatas:
            metadatas = [self._sanitize_metadata(m) for m in metadatas]

        try:
            col.upsert(documents=documents, metadatas=metadatas, ids=ids)
            logger.debug(
                "Upserted %d documents into '%s'",
                len(documents),
                collection_name,
            )
            return True
        except Exception as exc:
            logger.error(
                "Failed to add documents to '%s': %s", collection_name, exc
            )
            return False

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Query a collection for documents similar to *query_text*.

        Args:
            collection_name: Collection to search.
            query_text: Natural-language query string.
            n_results: Maximum number of results to return.
            where: Optional ChromaDB metadata filter dict.

        Returns:
            Dict with ``documents``, ``metadatas``, ``distances`` lists
            (flattened from ChromaDB's nested structure for convenience).
        """
        empty: dict[str, Any] = {
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        self._ensure_initialized()
        col = self.get_collection(collection_name)
        if col is None:
            logger.warning("Collection '%s' not found", collection_name)
            return empty

        try:
            count = col.count()
            if count == 0:
                return empty

            effective_n = min(n_results, count)
            kwargs: dict[str, Any] = {
                "query_texts": [query_text],
                "n_results": effective_n,
            }
            if where:
                kwargs["where"] = where

            results = col.query(**kwargs)
            return {
                "documents": results.get("documents", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "distances": results.get("distances", [[]])[0],
            }
        except Exception as exc:
            logger.error("Query failed on '%s': %s", collection_name, exc)
            return empty

    def delete(
        self,
        collection_name: str,
        ids: list[str],
    ) -> bool:
        """Delete documents by their IDs from a collection.

        Args:
            collection_name: Target collection.
            ids: List of document IDs to remove.

        Returns:
            ``True`` on success, ``False`` on error.
        """
        self._ensure_initialized()
        col = self.get_collection(collection_name)
        if col is None:
            logger.error("Collection '%s' not found", collection_name)
            return False
        try:
            col.delete(ids=ids)
            logger.debug(
                "Deleted %d docs from '%s'", len(ids), collection_name
            )
            return True
        except Exception as exc:
            logger.error("Delete failed on '%s': %s", collection_name, exc)
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """Delete an entire collection.

        Args:
            collection_name: Name of the collection to drop.

        Returns:
            ``True`` on success, ``False`` on error.
        """
        if self._client is None:
            return False
        try:
            self._client.delete_collection(collection_name)
            self._collections.pop(collection_name, None)
            return True
        except Exception as exc:
            logger.error(
                "Failed to delete collection '%s': %s", collection_name, exc
            )
            return False

    def count(self, collection_name: str) -> int:
        """Return the number of documents stored in a collection."""
        col = self.get_collection(collection_name)
        if col is None:
            return 0
        try:
            return col.count()
        except Exception:
            return 0

    def list_collections(self) -> list[dict[str, Any]]:
        """List all managed collections with their document counts."""
        info: list[dict[str, Any]] = []
        for name, col in self._collections.items():
            try:
                count = col.count()
            except Exception:
                count = 0
            info.append({"name": name, "count": count})
        return info

    # -----------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------

    def _ensure_initialized(self) -> None:
        """Lazily initialise if not already done."""
        if not self._initialized:
            self.initialize()

    def _get_or_create(self, name: str) -> Any:
        """Get or create a ChromaDB collection and cache the handle."""
        kwargs: dict[str, Any] = {"name": name}
        if self._ef is not None:
            kwargs["embedding_function"] = self._ef
        collection = self._client.get_or_create_collection(**kwargs)
        self._collections[name] = collection
        return collection

    @staticmethod
    def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, Any]:
        """Ensure all metadata values are ChromaDB-compatible primitives."""
        clean: dict[str, Any] = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif v is None:
                clean[k] = ""
            else:
                clean[k] = str(v)
        return clean
