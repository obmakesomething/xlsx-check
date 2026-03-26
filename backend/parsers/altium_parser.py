"""Altium Designer file parser (OLE2 container - basic metadata extraction)."""

from __future__ import annotations
import struct
import logging
from typing import Any

logger = logging.getLogger(__name__)

OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


class AltiumParser:
    """Parse Altium Designer binary files (OLE2 compound document format)."""

    def parse(self, data: bytes, filename: str = "") -> dict[str, Any]:
        """Extract metadata from an Altium OLE2 file."""
        result: dict[str, Any] = {
            "format": "altium",
            "filename": filename,
            "valid": False,
            "streams": [],
            "components": [],
            "metadata": {},
        }

        if len(data) < 512:
            result["error"] = "File too small to be a valid OLE2 container"
            return result

        # Verify OLE2 magic bytes
        if data[:8] != OLE2_MAGIC:
            result["error"] = "Not a valid OLE2/Altium file (bad magic bytes)"
            return result

        result["valid"] = True

        # Parse OLE2 header
        try:
            result["metadata"] = self._parse_ole2_header(data)
        except Exception as e:
            logger.warning(f"OLE2 header parse error: {e}")
            result["metadata"] = {"error": str(e)}

        # Try to find stream names by scanning for ASCII strings
        result["streams"] = self._find_stream_names(data)

        # Try to extract component records from known Altium patterns
        result["components"] = self._extract_component_hints(data)

        # Detect file subtype
        if filename.lower().endswith(".schdoc"):
            result["subtype"] = "schematic"
        elif filename.lower().endswith(".pcbdoc"):
            result["subtype"] = "pcb"
        elif filename.lower().endswith(".prjpcb"):
            result["subtype"] = "project"
        else:
            result["subtype"] = "unknown"

        return result

    def _parse_ole2_header(self, data: bytes) -> dict[str, Any]:
        """Parse OLE2 compound document header."""
        header = {}
        header["minor_version"] = struct.unpack_from("<H", data, 24)[0]
        header["major_version"] = struct.unpack_from("<H", data, 26)[0]
        header["byte_order"] = "little-endian" if struct.unpack_from("<H", data, 28)[0] == 0xFFFE else "big-endian"
        header["sector_size"] = 2 ** struct.unpack_from("<H", data, 30)[0]
        header["mini_sector_size"] = 2 ** struct.unpack_from("<H", data, 32)[0]
        header["total_fat_sectors"] = struct.unpack_from("<I", data, 44)[0]
        header["first_dir_sector"] = struct.unpack_from("<I", data, 48)[0]
        return header

    def _find_stream_names(self, data: bytes) -> list[str]:
        """Scan binary data for embedded stream/storage names."""
        names = set()
        known_patterns = [
            b"FileHeader", b"Storage", b"Data", b"Additional",
            b"Models", b"ComponentBody", b"Pin", b"Record",
            b"SchDoc", b"PcbDoc", b"Board", b"Net",
        ]
        for pat in known_patterns:
            if pat in data:
                names.add(pat.decode("ascii", errors="ignore"))
        return sorted(names)

    def _extract_component_hints(self, data: bytes) -> list[dict[str, str]]:
        """Try to extract component references from binary data using heuristics."""
        components = []
        text = data.decode("ascii", errors="ignore")

        # Look for Altium record patterns (key=value pairs separated by |)
        import re
        # Pattern: |DESIGNITEMID=xxx| or |LIBREFERENCE=xxx|
        ref_matches = re.findall(r"\|DESIGNITEMID=([^|]+)\|", text)
        lib_matches = re.findall(r"\|LIBREFERENCE=([^|]+)\|", text)
        desc_matches = re.findall(r"\|COMPONENTDESCRIPTION=([^|]+)\|", text)

        seen = set()
        for i, ref in enumerate(ref_matches):
            ref = ref.strip()
            if ref and ref not in seen:
                seen.add(ref)
                comp = {"designator": ref}
                if i < len(lib_matches):
                    comp["lib_reference"] = lib_matches[i].strip()
                if i < len(desc_matches):
                    comp["description"] = desc_matches[i].strip()
                components.append(comp)

        return components[:200]  # Cap at 200
