"""EasyEDA JSON project parser."""

from __future__ import annotations
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EasyEDAParser:
    """Parse EasyEDA JSON project exports."""

    def parse(self, content: str | bytes, filename: str = "") -> dict[str, Any]:
        """Parse EasyEDA JSON and extract schematic/PCB data."""
        result: dict[str, Any] = {
            "format": "easyeda",
            "filename": filename,
            "valid": False,
            "components": [],
            "nets": [],
            "metadata": {},
        }

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            result["error"] = f"Invalid JSON: {e}"
            return result

        result["valid"] = True

        if isinstance(data, dict):
            self._parse_project(data, result)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    self._parse_project(item, result)

        return result

    def _parse_project(self, data: dict, result: dict):
        """Parse a project-level JSON object."""
        # EasyEDA Pro format
        if "docType" in data:
            result["metadata"]["doc_type"] = data["docType"]
        if "title" in data:
            result["metadata"]["title"] = data["title"]
        if "description" in data:
            result["metadata"]["description"] = data["description"]

        # Extract components from various EasyEDA structures
        if "dataStr" in data:
            self._parse_data_str(data["dataStr"], result)
        elif "schematics" in data:
            for sch in data["schematics"]:
                if isinstance(sch, dict) and "dataStr" in sch:
                    self._parse_data_str(sch["dataStr"], result)
        elif "components" in data:
            for comp in data["components"]:
                if isinstance(comp, dict):
                    result["components"].append(self._normalize_component(comp))

        # EasyEDA standard format
        if "canvas" in data or "shape" in data:
            self._parse_standard_format(data, result)

    def _parse_data_str(self, data_str: Any, result: dict):
        """Parse the dataStr field which may be a JSON string or dict."""
        if isinstance(data_str, str):
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                # May be EasyEDA's custom format (line-delimited)
                self._parse_easyeda_shapes(data_str, result)
                return
            if isinstance(data, dict):
                self._parse_data_str(data, result)
            return

        if isinstance(data_str, dict):
            if "shape" in data_str:
                self._parse_easyeda_shapes(data_str["shape"], result)
            if "BBox" in data_str:
                result["metadata"]["bbox"] = data_str["BBox"]

    def _parse_easyeda_shapes(self, shapes: Any, result: dict):
        """Parse EasyEDA shape strings to extract component info."""
        if isinstance(shapes, str):
            lines = shapes.split("\n")
        elif isinstance(shapes, list):
            lines = shapes
        else:
            return

        for line in lines:
            if not isinstance(line, str):
                continue
            parts = line.split("~")
            if not parts:
                continue

            shape_type = parts[0].strip()
            if shape_type == "LIB":
                comp = self._parse_lib_shape(parts)
                if comp:
                    result["components"].append(comp)
            elif shape_type == "N":
                # Net
                if len(parts) > 1:
                    result["nets"].append({"name": parts[1] if len(parts) > 5 else ""})

    def _parse_lib_shape(self, parts: list[str]) -> dict[str, str] | None:
        """Parse a LIB shape (component instance) from EasyEDA format."""
        if len(parts) < 10:
            return None
        comp = {
            "ref": "",
            "value": "",
            "package": "",
            "lib_id": "",
        }
        # EasyEDA LIB format positions vary, try common positions
        for i, part in enumerate(parts):
            part = part.strip()
            if part.startswith("R") and len(part) <= 5 and part[1:].isdigit():
                comp["ref"] = part
            elif part.startswith("C") and len(part) <= 5 and part[1:].isdigit():
                comp["ref"] = part
            elif part.startswith("U") and len(part) <= 5 and part[1:].isdigit():
                comp["ref"] = part
            elif part.startswith("L") and len(part) <= 5 and part[1:].isdigit():
                comp["ref"] = part

        return comp if comp["ref"] else None

    def _parse_standard_format(self, data: dict, result: dict):
        """Parse EasyEDA standard JSON format."""
        if "shape" in data and isinstance(data["shape"], list):
            for shape in data["shape"]:
                if isinstance(shape, str):
                    self._parse_easyeda_shapes(shape, result)

    def _normalize_component(self, comp: dict) -> dict[str, str]:
        """Normalize component dict from various formats."""
        return {
            "ref": comp.get("ref", comp.get("designator", comp.get("name", ""))),
            "value": comp.get("value", comp.get("val", "")),
            "package": comp.get("package", comp.get("footprint", "")),
            "lib_id": comp.get("lib_id", comp.get("id", "")),
            "description": comp.get("description", comp.get("desc", "")),
        }
