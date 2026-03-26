"""Gerber RS-274X file parser for board dimensions and layer information."""

from __future__ import annotations
import re
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Common Gerber layer file extensions and their meanings
LAYER_MAP: dict[str, str] = {
    ".gtl": "Top Copper",
    ".gbl": "Bottom Copper",
    ".gts": "Top Solder Mask",
    ".gbs": "Bottom Solder Mask",
    ".gto": "Top Silkscreen",
    ".gbo": "Bottom Silkscreen",
    ".gko": "Board Outline (Keep-Out)",
    ".gtp": "Top Paste",
    ".gbp": "Bottom Paste",
    ".g1": "Inner Layer 1",
    ".g2": "Inner Layer 2",
    ".g3": "Inner Layer 3",
    ".g4": "Inner Layer 4",
    ".drl": "Drill File",
    ".gbr": "Gerber (generic)",
}


class GerberParser:
    """Parse Gerber RS-274X files for board info and layer analysis."""

    def parse(self, content: str | bytes, filename: str = "") -> dict[str, Any]:
        """Parse a Gerber file and extract metadata, apertures, and dimensions."""
        result: dict[str, Any] = {
            "format": "gerber",
            "filename": filename,
            "valid": False,
            "layer_type": self._detect_layer_type(filename),
            "apertures": [],
            "metadata": {},
            "bounds": None,
            "units": "mm",
            "polarity": "dark",
        }

        if isinstance(content, bytes):
            content = content.decode("ascii", errors="ignore")

        lines = content.strip().split("\n")
        if not lines:
            result["error"] = "Empty file"
            return result

        result["valid"] = True

        # Parse header commands
        self._parse_header(lines, result)

        # Extract aperture definitions
        self._parse_apertures(lines, result)

        # Calculate bounding box from coordinates
        self._calculate_bounds(lines, result)

        # Count draw commands
        result["metadata"]["total_commands"] = len(lines)
        result["metadata"]["draw_commands"] = sum(
            1 for line in lines if line.strip().endswith(("D01*", "D02*", "D03*"))
        )

        return result

    def _detect_layer_type(self, filename: str) -> str:
        """Detect Gerber layer type from filename extension."""
        import os
        _, ext = os.path.splitext(filename.lower())
        return LAYER_MAP.get(ext, "Unknown")

    def _parse_header(self, lines: list[str], result: dict):
        """Parse Gerber header for format specifiers and metadata."""
        for line in lines:
            line = line.strip()

            # Format specification: %FSLAX34Y34*%
            match = re.match(r"%FS([LT])([AI])X(\d)(\d)Y(\d)(\d)\*%", line)
            if match:
                result["metadata"]["format_spec"] = {
                    "zero_omission": "leading" if match.group(1) == "L" else "trailing",
                    "coordinate_mode": "absolute" if match.group(2) == "A" else "incremental",
                    "x_integer": int(match.group(3)),
                    "x_decimal": int(match.group(4)),
                    "y_integer": int(match.group(5)),
                    "y_decimal": int(match.group(6)),
                }

            # Units: %MOIN*% or %MOMM*%
            if "%MOIN*%" in line:
                result["units"] = "inch"
            elif "%MOMM*%" in line:
                result["units"] = "mm"

            # Image polarity
            if "%IPPOS*%" in line:
                result["polarity"] = "positive"
            elif "%IPNEG*%" in line:
                result["polarity"] = "negative"

            # Comment
            if line.startswith("G04"):
                comment = line[3:].rstrip("*").strip()
                if comment:
                    result["metadata"].setdefault("comments", []).append(comment)

    def _parse_apertures(self, lines: list[str], result: dict):
        """Extract aperture definitions (AD commands)."""
        for line in lines:
            line = line.strip()
            # Aperture definition: %ADD10C,0.100*%  or  %ADD11R,0.060X0.060*%
            match = re.match(r"%ADD(\d+)([A-Z]+),?([^*]*)\*%", line)
            if match:
                aperture = {
                    "code": f"D{match.group(1)}",
                    "shape": match.group(2),
                    "parameters": match.group(3),
                }
                result["apertures"].append(aperture)

    def _calculate_bounds(self, lines: list[str], result: dict):
        """Calculate bounding box from coordinate data."""
        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")
        found = False

        format_spec = result["metadata"].get("format_spec", {})
        x_dec = format_spec.get("x_decimal", 4)
        y_dec = format_spec.get("y_decimal", 4)

        for line in lines:
            line = line.strip()
            # Match coordinate commands like X123456Y789012D01*
            match = re.match(r"X(-?\d+)Y(-?\d+)D\d+\*", line)
            if match:
                try:
                    x = int(match.group(1)) / (10 ** x_dec)
                    y = int(match.group(2)) / (10 ** y_dec)
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    found = True
                except (ValueError, OverflowError):
                    continue

        if found:
            result["bounds"] = {
                "min_x": round(min_x, 4),
                "min_y": round(min_y, 4),
                "max_x": round(max_x, 4),
                "max_y": round(max_y, 4),
                "width": round(max_x - min_x, 4),
                "height": round(max_y - min_y, 4),
                "units": result["units"],
            }
