"""Export service for generating KiCad, Excel, and PDF outputs."""

from __future__ import annotations
import io
import json
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class ExportService:
    """Generate export files from project data."""

    @staticmethod
    def export_bom_excel(components: list[dict[str, Any]], project_name: str = "Project") -> bytes:
        """Export BoM as Excel file."""
        columns = [
            "ref_designator", "part_number", "manufacturer", "description",
            "package", "quantity", "unit_price", "lcsc_code", "category",
        ]

        rows = []
        for comp in components:
            row = {col: comp.get(col, "") for col in columns}
            rows.append(row)

        df = pd.DataFrame(rows, columns=columns)

        # Rename to friendlier headers
        header_map = {
            "ref_designator": "Reference",
            "part_number": "Part Number",
            "manufacturer": "Manufacturer",
            "description": "Description",
            "package": "Package",
            "quantity": "Qty",
            "unit_price": "Unit Price ($)",
            "lcsc_code": "LCSC Code",
            "category": "Category",
        }
        df = df.rename(columns=header_map)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="BOM", index=False)

            # Auto-adjust column widths
            ws = writer.sheets["BOM"]
            for i, col in enumerate(df.columns, 1):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                ws.column_dimensions[chr(64 + i) if i <= 26 else "A"].width = min(max_len, 50)

        return buffer.getvalue()

    @staticmethod
    def export_bom_csv(components: list[dict[str, Any]]) -> str:
        """Export BoM as CSV string."""
        columns = [
            "ref_designator", "part_number", "manufacturer", "description",
            "package", "quantity", "unit_price", "lcsc_code", "category",
        ]

        rows = []
        for comp in components:
            row = {col: comp.get(col, "") for col in columns}
            rows.append(row)

        df = pd.DataFrame(rows, columns=columns)
        return df.to_csv(index=False)

    @staticmethod
    def export_kicad_symbol_lib(components: list[dict[str, Any]], lib_name: str = "project") -> str:
        """Generate a basic KiCad symbol library file (.kicad_sym) from component list."""
        lines = [
            f'(kicad_symbol_lib (version 20211014) (generator led_copilot)',
        ]

        for comp in components:
            ref = comp.get("ref_designator", "U?")
            value = comp.get("part_number", comp.get("description", "Unknown"))
            prefix = ref.rstrip("0123456789") if ref else "U"

            symbol_name = f"{lib_name}:{value}".replace(" ", "_")
            lines.append(f'  (symbol "{symbol_name}" (in_bom yes) (on_board yes)')
            lines.append(f'    (property "Reference" "{prefix}" (at 0 1.27 0)')
            lines.append(f'      (effects (font (size 1.27 1.27))))')
            lines.append(f'    (property "Value" "{value}" (at 0 -1.27 0)')
            lines.append(f'      (effects (font (size 1.27 1.27))))')
            lines.append(f'    (property "Footprint" "{comp.get("package", "")}" (at 0 -3.81 0)')
            lines.append(f'      (effects (font (size 1.27 1.27)) hide))')
            lines.append(f'    (property "Datasheet" "" (at 0 0 0)')
            lines.append(f'      (effects (font (size 1.27 1.27)) hide))')
            lines.append(f'    (property "LCSC" "{comp.get("lcsc_code", "")}" (at 0 0 0)')
            lines.append(f'      (effects (font (size 1.27 1.27)) hide))')
            lines.append(f'    (symbol "{symbol_name}_0_1"')
            lines.append(f'      (rectangle (start -2.54 2.54) (end 2.54 -2.54)')
            lines.append(f'        (stroke (width 0) (type default))')
            lines.append(f'        (fill (type background))))')
            lines.append(f'  )')

        lines.append(")")
        return "\n".join(lines)

    @staticmethod
    def export_project_json(project: dict[str, Any]) -> str:
        """Export full project data as JSON."""
        return json.dumps(project, ensure_ascii=False, indent=2, default=str)
