"""PDF file parser for schematics and datasheets using PyMuPDF (fitz).

Extracts text content page-by-page (suitable for RAG chunking), tables,
image counts, and document metadata.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)


class PdfParser:
    """Parse PDF files to extract text, tables, images, and metadata."""

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def parse(self, data: bytes, filename: str = "") -> dict[str, Any]:
        """Parse a PDF from raw bytes.

        Args:
            data: Raw PDF file content.
            filename: Original filename (used only for metadata).

        Returns:
            Dict with keys: format, filename, valid, text_content,
            page_count, pages, tables, images_count, metadata,
            component_hints.
        """
        result = self._empty_result(filename)

        try:
            import fitz  # PyMuPDF
        except ImportError:
            result["error"] = (
                "PyMuPDF (fitz) is not installed. "
                "Install with: pip install pymupdf"
            )
            return result

        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:
            result["error"] = f"Failed to open PDF: {exc}"
            return result

        result["valid"] = True
        result["page_count"] = len(doc)

        # Document-level metadata
        meta = doc.metadata or {}
        result["metadata"] = {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "creation_date": meta.get("creationDate", ""),
            "modification_date": meta.get("modDate", ""),
        }

        all_text_parts: list[str] = []
        total_images = 0

        for page_num in range(len(doc)):
            page = doc[page_num]

            # --- Text ---
            page_text = ""
            try:
                page_text = page.get_text("text")
            except Exception as exc:
                logger.warning(
                    "Text extraction failed on page %d: %s", page_num + 1, exc
                )

            all_text_parts.append(page_text)

            page_entry: dict[str, Any] = {
                "page_number": page_num + 1,
                "text": page_text,
                "char_count": len(page_text),
                "width": page.rect.width,
                "height": page.rect.height,
            }

            # --- Images ---
            try:
                image_list = page.get_images(full=True)
                page_entry["images"] = len(image_list)
                total_images += len(image_list)
            except Exception:
                page_entry["images"] = 0

            # --- Tables ---
            page_tables = self._extract_tables_from_page(page)
            if page_tables:
                page_entry["tables"] = page_tables
                result["tables"].extend(page_tables)

            result["pages"].append(page_entry)

        doc.close()

        result["text_content"] = "\n\n".join(all_text_parts)
        result["images_count"] = total_images

        # Bonus: extract component reference hints from the full text
        result["component_hints"] = self._extract_component_hints(
            result["text_content"]
        )

        return result

    def parse_file(self, filepath: str) -> dict[str, Any]:
        """Convenience: read a PDF from *filepath* on disk and parse it.

        Args:
            filepath: Absolute or relative path to a PDF file.

        Returns:
            Same dict structure as :meth:`parse`.
        """
        if not os.path.isfile(filepath):
            result = self._empty_result(filepath)
            result["error"] = f"File not found: {filepath}"
            return result

        try:
            with open(filepath, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            result = self._empty_result(filepath)
            result["error"] = f"Cannot read file: {exc}"
            return result

        return self.parse(data, filename=os.path.basename(filepath))

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _empty_result(filename: str = "") -> dict[str, Any]:
        """Return an empty/default result dict."""
        return {
            "format": "pdf",
            "filename": filename,
            "valid": False,
            "text_content": "",
            "page_count": 0,
            "pages": [],
            "tables": [],
            "images_count": 0,
            "metadata": {},
            "component_hints": [],
        }

    def _extract_tables_from_page(self, page: Any) -> list[dict[str, Any]]:
        """Heuristic table extraction from a single PDF page.

        Tries the built-in ``find_tables`` API available in PyMuPDF >= 1.23.
        Falls back to a lightweight text-block clustering heuristic.
        """
        tables: list[dict[str, Any]] = []

        # --- Strategy 1: built-in find_tables (PyMuPDF >= 1.23) ----------
        try:
            if hasattr(page, "find_tables"):
                found = page.find_tables()
                tab_list = getattr(found, "tables", found) if found else []
                for tbl in tab_list:
                    try:
                        extracted = tbl.extract()
                        if extracted and len(extracted) > 1:
                            tables.append({
                                "rows": len(extracted),
                                "cols": len(extracted[0]) if extracted else 0,
                                "data": extracted[:50],
                            })
                    except Exception:
                        continue
                if tables:
                    return tables
        except Exception:
            pass

        # --- Strategy 2: cluster text blocks by y-coordinate -------------
        try:
            blocks = page.get_text("blocks")
            if not blocks:
                return tables

            rows_map: dict[int, list[tuple]] = {}
            for b in blocks:
                if b[6] != 0:  # skip image blocks
                    continue
                y_key = round(b[1] / 3) * 3
                rows_map.setdefault(y_key, []).append(b)

            sorted_keys = sorted(rows_map.keys())
            run: list[list[str]] = []
            for key in sorted_keys:
                cells = rows_map[key]
                if len(cells) >= 2:
                    cells.sort(key=lambda c: c[0])
                    row_texts = [
                        c[4].strip().replace("\n", " ") for c in cells
                    ]
                    run.append(row_texts)
                else:
                    if len(run) >= 2:
                        tables.append({
                            "rows": len(run),
                            "cols": max(len(r) for r in run),
                            "data": run[:50],
                        })
                    run = []

            if len(run) >= 2:
                tables.append({
                    "rows": len(run),
                    "cols": max(len(r) for r in run),
                    "data": run[:50],
                })

        except Exception as exc:
            logger.debug("Fallback table extraction failed: %s", exc)

        return tables

    @staticmethod
    def _extract_component_hints(text: str) -> list[dict[str, str]]:
        """Find component reference designators (R1, C2, U3 ...) in text."""
        pattern = r"\b([RCULDJQMTFKYW]\d{1,4}[A-Z]?)\b"
        matches = re.findall(pattern, text)

        seen: set[str] = set()
        hints: list[dict[str, str]] = []
        category_map = {
            "R": "Resistor",
            "C": "Capacitor",
            "U": "IC",
            "L": "Inductor",
            "D": "Diode",
            "J": "Connector",
            "Q": "Transistor",
            "M": "Motor/MOSFET",
            "T": "Transformer",
            "F": "Fuse",
            "K": "Relay",
            "Y": "Crystal",
            "W": "Wire/Jumper",
        }
        for m in matches:
            if m not in seen:
                seen.add(m)
                hints.append({
                    "ref": m,
                    "category": category_map.get(m[0], "Unknown"),
                })
        return hints[:200]
