"""Eagle XML (.sch, .brd) file parser."""

from __future__ import annotations
import xml.etree.ElementTree as ET
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EagleParser:
    """Parse Autodesk Eagle XML schematic and board files."""

    def parse(self, content: str | bytes, filename: str = "") -> dict[str, Any]:
        """Parse Eagle XML file and extract components, nets, and board info."""
        result: dict[str, Any] = {
            "format": "eagle",
            "filename": filename,
            "valid": False,
            "components": [],
            "nets": [],
            "metadata": {},
            "layers": [],
        }

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")

        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            result["error"] = f"XML parse error: {e}"
            return result

        result["valid"] = True

        # Get Eagle version
        eagle_elem = root if root.tag == "eagle" else root.find("eagle")
        if eagle_elem is not None:
            result["metadata"]["version"] = eagle_elem.get("version", "")

        # Detect type: schematic or board
        schematic = root.find(".//schematic")
        board = root.find(".//board")

        if schematic is not None:
            result["subtype"] = "schematic"
            self._parse_schematic(schematic, result)
        elif board is not None:
            result["subtype"] = "board"
            self._parse_board(board, result)

        # Extract libraries info
        self._parse_libraries(root, result)

        # Extract layers
        self._parse_layers(root, result)

        return result

    def _parse_schematic(self, schematic: ET.Element, result: dict):
        """Parse schematic sheets and extract parts and nets."""
        # Parts
        parts = schematic.findall(".//part")
        for part in parts:
            comp = {
                "ref": part.get("name", ""),
                "library": part.get("library", ""),
                "deviceset": part.get("deviceset", ""),
                "device": part.get("device", ""),
                "value": part.get("value", ""),
            }
            # Extract attributes
            for attr in part.findall("attribute"):
                comp[attr.get("name", "").lower()] = attr.get("value", "")
            result["components"].append(comp)

        # Nets
        nets = schematic.findall(".//net")
        for net in nets:
            net_info = {
                "name": net.get("name", ""),
                "class": net.get("class", "0"),
                "pins": [],
            }
            for segment in net.findall("segment"):
                for pinref in segment.findall("pinref"):
                    net_info["pins"].append({
                        "part": pinref.get("part", ""),
                        "gate": pinref.get("gate", ""),
                        "pin": pinref.get("pin", ""),
                    })
            result["nets"].append(net_info)

        # Count sheets
        sheets = schematic.findall(".//sheet")
        result["metadata"]["sheet_count"] = len(sheets)

    def _parse_board(self, board: ET.Element, result: dict):
        """Parse board and extract elements, signals, and dimensions."""
        # Elements (component instances on board)
        elements = board.findall(".//element")
        for elem in elements:
            comp = {
                "ref": elem.get("name", ""),
                "library": elem.get("library", ""),
                "package": elem.get("package", ""),
                "value": elem.get("value", ""),
                "x": elem.get("x", ""),
                "y": elem.get("y", ""),
                "rotation": elem.get("rot", ""),
            }
            result["components"].append(comp)

        # Signals (nets on board)
        signals = board.findall(".//signal")
        for sig in signals:
            result["nets"].append({
                "name": sig.get("name", ""),
                "class": sig.get("class", "0"),
            })

        # Try to get board dimensions from dimension layer wires
        self._extract_board_dimensions(board, result)

    def _extract_board_dimensions(self, board: ET.Element, result: dict):
        """Extract board outline from dimension layer (layer 20)."""
        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")
        found = False

        for wire in board.findall(".//wire"):
            if wire.get("layer") == "20":  # Dimension layer
                try:
                    for attr in ("x1", "x2"):
                        x = float(wire.get(attr, "0"))
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                    for attr in ("y1", "y2"):
                        y = float(wire.get(attr, "0"))
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
                    found = True
                except ValueError:
                    continue

        if found:
            result["metadata"]["board_dimensions"] = {
                "width_mm": round(max_x - min_x, 2),
                "height_mm": round(max_y - min_y, 2),
            }

    def _parse_libraries(self, root: ET.Element, result: dict):
        """Extract library information."""
        libs = root.findall(".//library")
        result["metadata"]["libraries"] = [lib.get("name", "") for lib in libs]

    def _parse_layers(self, root: ET.Element, result: dict):
        """Extract layer definitions."""
        layers = root.findall(".//layer")
        for layer in layers:
            result["layers"].append({
                "number": layer.get("number", ""),
                "name": layer.get("name", ""),
                "color": layer.get("color", ""),
                "visible": layer.get("visible", "yes"),
                "active": layer.get("active", "yes"),
            })
