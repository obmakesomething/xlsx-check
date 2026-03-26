"""Document indexer for the RAG pipeline."""

from __future__ import annotations
import json
import logging
from typing import Any

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class Indexer:
    """Index various data sources into the vector store."""

    def __init__(self, store: VectorStore | None = None):
        self.store = store or VectorStore.get_instance()

    def index_project(self, project_id: int, name: str, description: str, spec: dict) -> bool:
        """Index a project summary into the circuits collection."""
        doc = f"프로젝트: {name}\n설명: {description}\n사양: {json.dumps(spec, ensure_ascii=False)}"
        metadata = {"project_id": project_id, "type": "project", "name": name}
        doc_id = f"project-{project_id}"
        return self.store.add_documents("circuits", [doc], [metadata], [doc_id])

    def index_components(self, project_id: int, components: list[dict[str, Any]]) -> bool:
        """Index component/BoM data into the bom_patterns collection."""
        if not components:
            return True

        documents = []
        metadatas = []
        ids = []

        for i, comp in enumerate(components):
            doc_parts = []
            for key in ("ref_designator", "part_number", "manufacturer", "description", "package", "category"):
                val = comp.get(key, "")
                if val:
                    doc_parts.append(f"{key}: {val}")
            doc = "\n".join(doc_parts)
            documents.append(doc)
            metadatas.append({
                "project_id": project_id,
                "type": "component",
                "part_number": comp.get("part_number", ""),
                "category": comp.get("category", ""),
            })
            ids.append(f"comp-{project_id}-{i}")

        return self.store.add_documents("bom_patterns", documents, metadatas, ids)

    def index_circuit_block(self, project_id: int, block_id: int, name: str,
                            block_type: str, description: str) -> bool:
        """Index a circuit block into the circuits collection."""
        doc = f"회로 블록: {name}\n유형: {block_type}\n설명: {description}"
        metadata = {"project_id": project_id, "block_id": block_id, "type": "circuit_block", "block_type": block_type}
        doc_id = f"block-{project_id}-{block_id}"
        return self.store.add_documents("circuits", [doc], [metadata], [doc_id])

    def index_knowledge(self, entry_id: int, category: str, title: str,
                        content: str, tags: list[str]) -> bool:
        """Index a knowledge entry into the knowledge collection."""
        doc = f"제목: {title}\n카테고리: {category}\n태그: {', '.join(tags)}\n내용: {content}"
        metadata = {"entry_id": entry_id, "category": category, "tags": ",".join(tags)}
        doc_id = f"knowledge-{entry_id}"
        return self.store.add_documents("knowledge", [doc], [metadata], [doc_id])

    def index_certification_info(self, cert_id: str, title: str, content: str,
                                 standard: str = "") -> bool:
        """Index certification/regulatory information."""
        doc = f"인증: {title}\n규격: {standard}\n내용: {content}"
        metadata = {"cert_id": cert_id, "standard": standard, "type": "certification"}
        doc_id = f"cert-{cert_id}"
        return self.store.add_documents("certification", [doc], [metadata], [doc_id])

    def index_debug_case(self, case_id: str, symptom: str, cause: str,
                         solution: str, category: str = "") -> bool:
        """Index a debugging case for future reference."""
        doc = f"증상: {symptom}\n원인: {cause}\n해결: {solution}\n카테고리: {category}"
        metadata = {"case_id": case_id, "category": category, "type": "debug_case"}
        doc_id = f"debug-{case_id}"
        return self.store.add_documents("debugging", [doc], [metadata], [doc_id])
