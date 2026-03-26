"""Document indexer for the RAG pipeline.

Converts structured project, BoM, knowledge-base, and certification data
into natural-language descriptions, then indexes them into the appropriate
ChromaDB collections via :class:`~backend.rag.vector_store.VectorStore`.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


def _make_id(*parts: Any) -> str:
    """Generate a deterministic, short document ID from arbitrary parts."""
    raw = ":".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


class Indexer:
    """Index structured data into the vector store collections.

    Each ``index_*`` method converts its input into one or more text
    documents, attaches metadata, and upserts them into the appropriate
    collection.

    Args:
        store: A :class:`VectorStore` instance.  Defaults to the
            singleton returned by ``VectorStore.get_instance()``.
    """

    def __init__(self, store: Optional[VectorStore] = None) -> None:
        self.store = store or VectorStore.get_instance()

    # -----------------------------------------------------------------
    # Project / circuit indexing  ->  "circuits" collection
    # -----------------------------------------------------------------

    def index_project(self, project_data: dict[str, Any]) -> bool:
        """Index a project summary into the *circuits* collection.

        Expected keys in *project_data*:
            - ``id`` or ``project_id``  (int | str)
            - ``name``                  (str)
            - ``description``           (str, optional)
            - ``spec`` / ``specs``      (dict, optional)
            - ``blocks``                (list[dict], optional -- circuit blocks)

        Returns:
            ``True`` when all documents were indexed successfully.
        """
        pid = project_data.get("id", project_data.get("project_id", "unknown"))
        name = project_data.get("name", "")
        description = project_data.get("description", "")
        spec = project_data.get("spec", project_data.get("specs", {}))

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        # -- Project-level document --
        doc_parts = [f"프로젝트: {name}"]
        if description:
            doc_parts.append(f"설명: {description}")
        if spec:
            doc_parts.append(f"사양: {json.dumps(spec, ensure_ascii=False)}")

        documents.append("\n".join(doc_parts))
        metadatas.append({
            "project_id": str(pid),
            "type": "project",
            "name": name,
        })
        ids.append(_make_id("project", pid))

        # -- Circuit blocks (if present) --
        blocks = project_data.get("blocks", [])
        for i, block in enumerate(blocks):
            block_id = block.get("id", block.get("block_id", i))
            block_name = block.get("name", f"Block {i}")
            block_type = block.get("type", block.get("block_type", ""))
            block_desc = block.get("description", "")

            doc = (
                f"회로 블록: {block_name}\n"
                f"유형: {block_type}\n"
                f"설명: {block_desc}"
            )
            documents.append(doc)
            metadatas.append({
                "project_id": str(pid),
                "block_id": str(block_id),
                "type": "circuit_block",
                "block_type": block_type,
            })
            ids.append(_make_id("block", pid, block_id))

        return self.store.add_documents("circuits", documents, metadatas, ids)

    # -----------------------------------------------------------------
    # BoM / component indexing  ->  "bom_patterns" collection
    # -----------------------------------------------------------------

    def index_bom(self, bom_data: dict[str, Any]) -> bool:
        """Index BoM (Bill of Materials) data into the *bom_patterns* collection.

        Expected keys in *bom_data*:
            - ``project_id`` (int | str, optional)
            - ``components`` (list[dict]) -- each dict should have keys like
              ``ref_designator``, ``part_number``, ``manufacturer``,
              ``description``, ``package``, ``value``, ``quantity``,
              ``lcsc_code``, ``category``.

        Returns:
            ``True`` on success.
        """
        pid = bom_data.get("project_id", "unknown")
        components = bom_data.get("components", [])
        if not components:
            return True

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        field_labels = {
            "ref_designator": "레퍼런스",
            "part_number": "부품번호",
            "manufacturer": "제조사",
            "description": "설명",
            "package": "패키지",
            "value": "값",
            "quantity": "수량",
            "lcsc_code": "LCSC",
            "category": "분류",
        }

        for i, comp in enumerate(components):
            parts: list[str] = []
            for key, label in field_labels.items():
                val = comp.get(key, "")
                if val:
                    parts.append(f"{label}: {val}")
            if not parts:
                continue

            documents.append("\n".join(parts))
            metadatas.append({
                "project_id": str(pid),
                "type": "component",
                "part_number": str(comp.get("part_number", "")),
                "category": str(comp.get("category", "")),
            })
            ids.append(_make_id("comp", pid, i))

        if not documents:
            return True

        return self.store.add_documents("bom_patterns", documents, metadatas, ids)

    def index_components(
        self,
        project_id: int | str,
        components: list[dict[str, Any]],
    ) -> bool:
        """Convenience wrapper -- delegates to :meth:`index_bom`."""
        return self.index_bom({
            "project_id": project_id,
            "components": components,
        })

    # -----------------------------------------------------------------
    # Knowledge base indexing  ->  "knowledge" collection
    # -----------------------------------------------------------------

    def index_knowledge(self, entries: list[dict[str, Any]] | dict[str, Any]) -> bool:
        """Index one or more knowledge-base entries.

        Each entry dict should contain:
            - ``id`` or ``entry_id``  (int | str)
            - ``title``              (str)
            - ``category``           (str, optional)
            - ``content``            (str)
            - ``tags``               (list[str], optional)

        A single dict is also accepted (auto-wrapped in a list).

        Returns:
            ``True`` on success.
        """
        if isinstance(entries, dict):
            entries = [entries]

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        for entry in entries:
            eid = entry.get("id", entry.get("entry_id", ""))
            title = entry.get("title", "")
            category = entry.get("category", "")
            content = entry.get("content", "")
            tags = entry.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]

            doc_parts = [f"제목: {title}"]
            if category:
                doc_parts.append(f"카테고리: {category}")
            if tags:
                doc_parts.append(f"태그: {', '.join(tags)}")
            if content:
                doc_parts.append(f"내용: {content}")

            documents.append("\n".join(doc_parts))
            metadatas.append({
                "entry_id": str(eid),
                "category": category,
                "tags": ",".join(tags),
            })
            ids.append(_make_id("knowledge", eid))

        if not documents:
            return True

        return self.store.add_documents("knowledge", documents, metadatas, ids)

    # -----------------------------------------------------------------
    # Certification / regulatory indexing  ->  "certification" collection
    # -----------------------------------------------------------------

    def index_certification(self, cert_data: list[dict[str, Any]] | dict[str, Any]) -> bool:
        """Index certification / regulatory information.

        Each entry dict should contain:
            - ``id`` or ``cert_id``  (str)
            - ``title``             (str)
            - ``content``           (str)
            - ``standard``          (str, optional)

        A single dict is also accepted (auto-wrapped in a list).

        Returns:
            ``True`` on success.
        """
        if isinstance(cert_data, dict):
            cert_data = [cert_data]

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        for entry in cert_data:
            cid = entry.get("id", entry.get("cert_id", ""))
            title = entry.get("title", "")
            standard = entry.get("standard", "")
            content = entry.get("content", "")

            doc = f"인증: {title}\n규격: {standard}\n내용: {content}"
            documents.append(doc)
            metadatas.append({
                "cert_id": str(cid),
                "standard": standard,
                "type": "certification",
            })
            ids.append(_make_id("cert", cid))

        if not documents:
            return True

        return self.store.add_documents("certification", documents, metadatas, ids)

    # Alias for direct single-item call
    def index_certification_info(
        self,
        cert_id: str,
        title: str,
        content: str,
        standard: str = "",
    ) -> bool:
        """Convenience: index a single certification entry by explicit args."""
        return self.index_certification({
            "cert_id": cert_id,
            "title": title,
            "content": content,
            "standard": standard,
        })

    # -----------------------------------------------------------------
    # Debugging case indexing  ->  "debugging" collection
    # -----------------------------------------------------------------

    def index_debug_case(
        self,
        case_id: str,
        symptom: str,
        cause: str,
        solution: str,
        category: str = "",
    ) -> bool:
        """Index a single debugging case for future reference.

        Args:
            case_id: Unique identifier for the case.
            symptom: Description of the observed problem.
            cause: Root cause analysis.
            solution: How the problem was resolved.
            category: Optional category label.

        Returns:
            ``True`` on success.
        """
        doc = (
            f"증상: {symptom}\n"
            f"원인: {cause}\n"
            f"해결: {solution}\n"
            f"카테고리: {category}"
        )
        metadata = {
            "case_id": case_id,
            "category": category,
            "type": "debug_case",
        }
        doc_id = _make_id("debug", case_id)
        return self.store.add_documents(
            "debugging", [doc], [metadata], [doc_id]
        )
