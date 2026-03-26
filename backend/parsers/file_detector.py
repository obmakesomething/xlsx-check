"""Auto-detect EDA file format by extension and magic bytes."""

from __future__ import annotations

import os
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Extension-to-format mapping
EXTENSION_MAP: dict[str, str] = {
    ".kicad_sch": "kicad_sch",
    ".kicad_pcb": "kicad_pcb",
    ".kicad_pro": "kicad_project",
    ".schdoc": "altium_sch",
    ".pcbdoc": "altium_pcb",
    ".prjpcb": "altium_project",
    ".sch": "eagle_sch",
    ".brd": "eagle_brd",
    ".json": "easyeda",
    ".gbr": "gerber",
    ".gtl": "gerber",
    ".gbl": "gerber",
    ".gts": "gerber",
    ".gbs": "gerber",
    ".gto": "gerber",
    ".gbo": "gerber",
    ".gko": "gerber",
    ".drl": "gerber",
    ".csv": "bom_csv",
    ".xlsx": "bom_excel",
    ".xls": "bom_excel",
    ".pdf": "pdf",
}

# Magic bytes for binary formats
MAGIC_BYTES: dict[bytes, str] = {
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "ole2",  # Altium OLE2
    b"%PDF": "pdf",
    b"PK": "zip",  # Could be KiCad 7+ or EasyEDA
}

# Human-readable descriptions
FORMAT_DESCRIPTIONS: dict[str, str] = {
    "kicad_sch": "KiCad Schematic (.kicad_sch)",
    "kicad_pcb": "KiCad PCB Layout (.kicad_pcb)",
    "altium_sch": "Altium Schematic (.SchDoc)",
    "altium_pcb": "Altium PCB (.PcbDoc)",
    "eagle_sch": "Eagle Schematic (.sch)",
    "eagle_brd": "Eagle Board (.brd)",
    "easyeda": "EasyEDA JSON Project (.json)",
    "gerber": "Gerber RS-274X (.gbr, .gtl, .gbl, etc.)",
    "bom_excel": "BoM Excel (.xlsx, .xls)",
    "bom_csv": "BoM CSV (.csv)",
    "pdf": "PDF Document (.pdf)",
}


class FileDetector:
    """Detect EDA file format from a file path or bytes."""

    @staticmethod
    def detect_by_extension(filename: str) -> Optional[str]:
        """Detect format from filename extension."""
        _, ext = os.path.splitext(filename.lower())
        return EXTENSION_MAP.get(ext)

    @staticmethod
    def detect_by_content(data: bytes) -> Optional[str]:
        """Detect format from file magic bytes."""
        for magic, fmt in MAGIC_BYTES.items():
            if data[: len(magic)] == magic:
                if fmt == "ole2":
                    return "altium_sch"  # Most likely Altium OLE2
                return fmt

        # Check for text-based formats
        try:
            text_start = data[:500].decode("utf-8", errors="ignore")
        except Exception:
            return None

        if text_start.strip().startswith("(kicad_sch"):
            return "kicad_sch"
        if text_start.strip().startswith("(kicad_pcb"):
            return "kicad_pcb"
        if text_start.strip().startswith("<?xml"):
            if "<eagle" in text_start:
                if "<schematic" in text_start:
                    return "eagle_sch"
                return "eagle_brd"
            return "xml"
        if text_start.strip().startswith("{"):
            return "easyeda"
        if text_start.strip().startswith("%") or "G04" in text_start[:80]:
            return "gerber"

        return None

    @staticmethod
    def detect(filename: str, data: Optional[bytes] = None) -> str:
        """Detect format using both extension and content analysis."""
        ext_fmt = FileDetector.detect_by_extension(filename)
        if ext_fmt:
            return ext_fmt

        if data:
            content_fmt = FileDetector.detect_by_content(data)
            if content_fmt:
                return content_fmt

        return "unknown"

    @staticmethod
    def supported_formats() -> list[dict[str, str]]:
        """Return list of supported formats with descriptions."""
        return [
            {"format": k, "description": v}
            for k, v in FORMAT_DESCRIPTIONS.items()
        ]


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def detect_format(filepath: str) -> str:
    """Detect the format of a file by its path (extension + content peek).

    Args:
        filepath: Absolute or relative path to the file.

    Returns:
        A format string such as ``kicad_sch``, ``bom_excel``, ``pdf``, etc.
        Returns ``"unknown"`` when detection fails.
    """
    data: Optional[bytes] = None
    if os.path.isfile(filepath):
        try:
            with open(filepath, "rb") as fh:
                data = fh.read(1024)
        except OSError:
            pass
    return FileDetector.detect(filepath, data)


def get_parser(format_string: str):
    """Return an appropriate parser **instance** for the given format string.

    Lazy-imports parsers to avoid circular-import issues and to keep startup
    lightweight.

    Returns:
        A parser instance (e.g. ``KiCadParser()``) or ``None`` when no parser
        is available for the format.
    """
    fmt = format_string.lower()

    if fmt in ("kicad_sch", "kicad_pcb"):
        from .kicad_parser import KiCadParser
        return KiCadParser()
    if fmt in ("altium_sch", "altium_pcb"):
        from .altium_parser import AltiumParser
        return AltiumParser()
    if fmt == "easyeda":
        from .easyeda_parser import EasyEDAParser
        return EasyEDAParser()
    if fmt in ("eagle_sch", "eagle_brd"):
        from .eagle_parser import EagleParser
        return EagleParser()
    if fmt == "gerber":
        from .gerber_parser import GerberParser
        return GerberParser()
    if fmt in ("bom_excel", "bom_csv"):
        from .bom_parser import BomParser
        return BomParser()
    if fmt == "pdf":
        from .pdf_parser import PdfParser
        return PdfParser()

    return None


def list_supported_formats() -> list[dict[str, str]]:
    """Return all supported formats with human-readable descriptions."""
    return FileDetector.supported_formats()
