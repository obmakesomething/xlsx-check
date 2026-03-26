"""KiCad S-expression file parser for .kicad_sch and .kicad_pcb files."""

from __future__ import annotations
import re
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SExpressionParser:
    """Parse S-expression format used by KiCad."""

    def parse(self, text: str) -> list:
        """Parse S-expression string into nested list structure."""
        tokens = self._tokenize(text)
        result, _ = self._parse_tokens(tokens, 0)
        return result

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize S-expression text."""
        tokens = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch in (" ", "\t", "\n", "\r"):
                i += 1
            elif ch == "(":
                tokens.append("(")
                i += 1
            elif ch == ")":
                tokens.append(")")
                i += 1
            elif ch == '"':
                j = i + 1
                while j < len(text) and text[j] != '"':
                    if text[j] == "\\":
                        j += 1
                    j += 1
                tokens.append(text[i + 1:j])
                i = j + 1
            else:
                j = i
                while j < len(text) and text[j] not in (" ", "\t", "\n", "\r", "(", ")"):
                    j += 1
                tokens.append(text[i:j])
                i = j
        return tokens

    def _parse_tokens(self, tokens: list[str], pos: int) -> tuple[Any, int]:
        """Recursively parse tokens into nested lists."""
        if pos >= len(tokens):
            return [], pos

        if tokens[pos] == "(":
            lst = []
            pos += 1
            while pos < len(tokens) and tokens[pos] != ")":
                if tokens[pos] == "(":
                    child, pos = self._parse_tokens(tokens, pos)
                    lst.append(child)
                else:
                    lst.append(tokens[pos])
                    pos += 1
            return lst, pos + 1  # skip closing )
        else:
            return tokens[pos], pos + 1


class KiCadParser:
    """Parse KiCad schematic and PCB files."""

    def __init__(self):
        self.sexpr_parser = SExpressionParser()

    def parse_schematic(self, content: str) -> dict[str, Any]:
        """Parse a .kicad_sch file and extract components, nets, and metadata."""
        try:
            tree = self.sexpr_parser.parse(content)
        except Exception as e:
            logger.error(f"S-expression parse error: {e}")
            return {"error": str(e), "components": [], "nets": []}

        if not tree or not isinstance(tree, list):
            return {"error": "Empty or invalid schematic", "components": [], "nets": []}

        result = {
            "format": "kicad_schematic",
            "version": self._find_value(tree, "version"),
            "generator": self._find_value(tree, "generator"),
            "components": [],
            "nets": [],
            "wires": 0,
            "labels": [],
        }

        self._extract_symbols(tree, result)
        self._extract_labels(tree, result)
        result["wires"] = self._count_elements(tree, "wire")

        return result

    def parse_pcb(self, content: str) -> dict[str, Any]:
        """Parse a .kicad_pcb file and extract footprints, layers, and board outline."""
        try:
            tree = self.sexpr_parser.parse(content)
        except Exception as e:
            logger.error(f"S-expression parse error: {e}")
            return {"error": str(e), "footprints": [], "layers": []}

        result = {
            "format": "kicad_pcb",
            "version": self._find_value(tree, "version"),
            "generator": self._find_value(tree, "generator"),
            "footprints": [],
            "layers": [],
            "nets": [],
            "board_dimensions": None,
        }

        self._extract_footprints(tree, result)
        self._extract_layers(tree, result)
        self._extract_nets_pcb(tree, result)
        self._extract_board_dimensions(tree, result)

        return result

    def parse(self, content: str, filename: str = "") -> dict[str, Any]:
        """Auto-detect and parse KiCad file."""
        if filename.endswith(".kicad_pcb") or content.strip().startswith("(kicad_pcb"):
            return self.parse_pcb(content)
        return self.parse_schematic(content)

    def _find_value(self, tree: list, key: str) -> Optional[str]:
        """Find a simple key-value in the S-expression tree."""
        if not isinstance(tree, list):
            return None
        for item in tree:
            if isinstance(item, list) and len(item) >= 2 and item[0] == key:
                return str(item[1])
        return None

    def _extract_symbols(self, tree: list, result: dict):
        """Extract symbol instances (components) from schematic."""
        if not isinstance(tree, list):
            return
        for item in tree:
            if isinstance(item, list) and len(item) > 0 and item[0] == "symbol":
                comp = self._parse_symbol(item)
                if comp:
                    result["components"].append(comp)
            elif isinstance(item, list):
                self._extract_symbols(item, result)

    def _parse_symbol(self, node: list) -> Optional[dict]:
        """Parse a symbol node into component dict."""
        if len(node) < 2:
            return None

        comp: dict[str, Any] = {"lib_id": "", "ref": "", "value": "", "footprint": ""}

        for child in node:
            if not isinstance(child, list):
                continue
            if child[0] == "lib_id" and len(child) > 1:
                comp["lib_id"] = str(child[1])
            elif child[0] == "property":
                prop_name = str(child[1]) if len(child) > 1 else ""
                prop_val = str(child[2]) if len(child) > 2 else ""
                if prop_name == "Reference":
                    comp["ref"] = prop_val
                elif prop_name == "Value":
                    comp["value"] = prop_val
                elif prop_name == "Footprint":
                    comp["footprint"] = prop_val

        if comp["ref"] and not comp["ref"].startswith("#"):
            return comp
        return None

    def _extract_labels(self, tree: list, result: dict):
        """Extract net labels from schematic."""
        if not isinstance(tree, list):
            return
        for item in tree:
            if isinstance(item, list) and len(item) > 0:
                if item[0] in ("label", "global_label", "hierarchical_label"):
                    name = str(item[1]) if len(item) > 1 else ""
                    if name:
                        result["labels"].append({"type": item[0], "name": name})
                else:
                    self._extract_labels(item, result)

    def _count_elements(self, tree: list, element_type: str) -> int:
        """Count occurrences of an element type in the tree."""
        count = 0
        if not isinstance(tree, list):
            return 0
        for item in tree:
            if isinstance(item, list) and len(item) > 0 and item[0] == element_type:
                count += 1
            elif isinstance(item, list):
                count += self._count_elements(item, element_type)
        return count

    def _extract_footprints(self, tree: list, result: dict):
        """Extract footprint instances from PCB."""
        if not isinstance(tree, list):
            return
        for item in tree:
            if isinstance(item, list) and len(item) > 0 and item[0] == "footprint":
                fp = {"lib": str(item[1]) if len(item) > 1 else "", "ref": "", "value": "", "layer": ""}
                for child in item:
                    if isinstance(child, list) and len(child) > 0:
                        if child[0] == "layer" and len(child) > 1:
                            fp["layer"] = str(child[1])
                        elif child[0] == "fp_text" and len(child) > 2:
                            if str(child[1]) == "reference":
                                fp["ref"] = str(child[2])
                            elif str(child[1]) == "value":
                                fp["value"] = str(child[2])
                        elif child[0] == "property" and len(child) > 2:
                            if str(child[1]) == "Reference":
                                fp["ref"] = str(child[2])
                            elif str(child[1]) == "Value":
                                fp["value"] = str(child[2])
                result["footprints"].append(fp)

    def _extract_layers(self, tree: list, result: dict):
        """Extract layer definitions from PCB."""
        if not isinstance(tree, list):
            return
        for item in tree:
            if isinstance(item, list) and len(item) > 0 and item[0] == "layers":
                for child in item[1:]:
                    if isinstance(child, list) and len(child) >= 3:
                        result["layers"].append({
                            "number": str(child[0]),
                            "name": str(child[1]),
                            "type": str(child[2]),
                        })

    def _extract_nets_pcb(self, tree: list, result: dict):
        """Extract net definitions from PCB."""
        if not isinstance(tree, list):
            return
        for item in tree:
            if isinstance(item, list) and len(item) >= 3 and item[0] == "net":
                result["nets"].append({"number": str(item[1]), "name": str(item[2])})

    def _extract_board_dimensions(self, tree: list, result: dict):
        """Try to extract board outline dimensions from edge cuts."""
        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")
        found = False

        def walk(node):
            nonlocal min_x, min_y, max_x, max_y, found
            if not isinstance(node, list):
                return
            if len(node) > 0 and node[0] == "gr_line":
                layer = ""
                for child in node:
                    if isinstance(child, list) and child[0] == "layer" and len(child) > 1:
                        layer = str(child[1])
                if layer in ("Edge.Cuts", "edge.cuts"):
                    for child in node:
                        if isinstance(child, list) and child[0] in ("start", "end") and len(child) >= 3:
                            try:
                                x, y = float(child[1]), float(child[2])
                                min_x = min(min_x, x)
                                min_y = min(min_y, y)
                                max_x = max(max_x, x)
                                max_y = max(max_y, y)
                                found = True
                            except (ValueError, IndexError):
                                pass
            for child in node:
                if isinstance(child, list):
                    walk(child)

        walk(tree)
        if found:
            result["board_dimensions"] = {
                "width_mm": round(max_x - min_x, 2),
                "height_mm": round(max_y - min_y, 2),
            }
