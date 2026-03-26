"""BoM (Bill of Materials) Excel/CSV parser with Korean+English column normalization."""

from __future__ import annotations
import io
import logging
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Column name normalization mapping (Korean -> English canonical names)
COLUMN_MAP: dict[str, str] = {
    # Reference designator
    "ref": "ref_designator", "reference": "ref_designator", "designator": "ref_designator",
    "부품번호": "ref_designator", "참조기호": "ref_designator", "레퍼런스": "ref_designator",
    "ref designator": "ref_designator", "refdes": "ref_designator",
    # Part number
    "part number": "part_number", "part_number": "part_number", "part no": "part_number",
    "partnumber": "part_number", "p/n": "part_number", "pn": "part_number",
    "부품 번호": "part_number", "파트넘버": "part_number", "모델명": "part_number",
    "부품코드": "part_number", "품번": "part_number",
    # Manufacturer
    "manufacturer": "manufacturer", "mfr": "manufacturer", "mfg": "manufacturer",
    "제조사": "manufacturer", "메이커": "manufacturer", "제조업체": "manufacturer",
    "vendor": "manufacturer",
    # Description
    "description": "description", "desc": "description",
    "설명": "description", "품명": "description", "부품명": "description", "사양": "description",
    "규격": "description", "스펙": "description",
    # Value
    "value": "value", "값": "value", "정격": "value",
    # Package / Footprint
    "package": "package", "footprint": "package", "패키지": "package",
    "풋프린트": "package", "사이즈": "package", "size": "package",
    # Quantity
    "quantity": "quantity", "qty": "quantity", "수량": "quantity",
    "ea": "quantity", "개수": "quantity", "pcs": "quantity",
    # Unit price
    "unit price": "unit_price", "price": "unit_price", "단가": "unit_price",
    "unit_price": "unit_price", "가격": "unit_price",
    # LCSC code
    "lcsc": "lcsc_code", "lcsc_code": "lcsc_code", "lcsc part": "lcsc_code",
    "lcsc code": "lcsc_code", "lcsc번호": "lcsc_code",
    # Category
    "category": "category", "type": "category", "분류": "category",
    "카테고리": "category", "종류": "category", "구분": "category",
    # Notes
    "note": "notes", "notes": "notes", "비고": "notes", "메모": "notes", "참고": "notes",
}


class BomParser:
    """Parse BoM files in Excel or CSV format with smart column detection."""

    def parse(self, data: bytes, filename: str = "") -> dict[str, Any]:
        """Parse BoM file and return normalized component list."""
        result: dict[str, Any] = {
            "format": "bom",
            "filename": filename,
            "valid": False,
            "components": [],
            "raw_columns": [],
            "mapped_columns": {},
            "unmapped_columns": [],
            "summary": {},
        }

        try:
            df = self._read_file(data, filename)
        except Exception as e:
            result["error"] = f"Failed to read file: {e}"
            return result

        if df is None or df.empty:
            result["error"] = "File is empty or unreadable"
            return result

        result["valid"] = True
        result["raw_columns"] = list(df.columns)

        # Find the header row (may not be row 0)
        df = self._find_header_row(df)

        # Normalize column names
        col_mapping = self._map_columns(df.columns.tolist())
        result["mapped_columns"] = col_mapping
        result["unmapped_columns"] = [
            c for c in df.columns if c.lower().strip() not in {k for k in COLUMN_MAP}
            and c.lower().strip() not in col_mapping
        ]

        # Rename columns
        rename_map = {}
        for orig_col in df.columns:
            normalized = col_mapping.get(orig_col.lower().strip())
            if normalized:
                rename_map[orig_col] = normalized
        df = df.rename(columns=rename_map)

        # Convert to component dicts
        components = []
        for _, row in df.iterrows():
            comp = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    val = ""
                else:
                    val = str(val).strip()
                comp[col] = val
            # Skip empty rows
            if any(v for v in comp.values()):
                components.append(comp)

        result["components"] = components

        # Summary
        result["summary"] = {
            "total_rows": len(components),
            "unique_parts": len(set(c.get("part_number", "") for c in components if c.get("part_number"))),
            "categories": list(set(c.get("category", "") for c in components if c.get("category"))),
        }

        return result

    def _read_file(self, data: bytes, filename: str) -> Optional[pd.DataFrame]:
        """Read Excel or CSV file into a DataFrame."""
        lower = filename.lower()
        if lower.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(data), header=None, dtype=str)
        elif lower.endswith(".csv"):
            # Try different encodings
            for encoding in ("utf-8", "cp949", "euc-kr", "latin-1"):
                try:
                    return pd.read_csv(io.BytesIO(data), header=None, dtype=str, encoding=encoding)
                except (UnicodeDecodeError, Exception):
                    continue
        # Try as Excel by default
        try:
            return pd.read_excel(io.BytesIO(data), header=None, dtype=str)
        except Exception:
            return pd.read_csv(io.BytesIO(data), header=None, dtype=str, encoding="utf-8", errors="ignore")

    def _find_header_row(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect which row contains column headers."""
        best_row = 0
        best_score = 0

        for i in range(min(10, len(df))):
            row_values = [str(v).lower().strip() for v in df.iloc[i] if pd.notna(v)]
            score = sum(1 for v in row_values if v in COLUMN_MAP)
            if score > best_score:
                best_score = score
                best_row = i

        if best_score > 0:
            df.columns = [str(v).strip() if pd.notna(v) else f"col_{i}" for i, v in enumerate(df.iloc[best_row])]
            df = df.iloc[best_row + 1:].reset_index(drop=True)
        else:
            df.columns = [str(v).strip() if pd.notna(v) else f"col_{i}" for i, v in enumerate(df.iloc[0])]
            df = df.iloc[1:].reset_index(drop=True)

        return df

    # ------------------------------------------------------------------
    # Convenience file-path helpers
    # ------------------------------------------------------------------

    def parse_excel(self, filepath: str) -> list[dict[str, Any]]:
        """Read an Excel file from disk and return a normalized component list.

        Args:
            filepath: Path to an ``.xlsx`` or ``.xls`` file.

        Returns:
            A list of normalised component dicts (the ``components`` field of
            the full parse result).
        """
        import os

        if not os.path.isfile(filepath):
            logger.error("Excel file not found: %s", filepath)
            return []
        try:
            with open(filepath, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            logger.error("Cannot read Excel file %s: %s", filepath, exc)
            return []
        result = self.parse(data, filename=os.path.basename(filepath))
        return result.get("components", [])

    def parse_csv(self, filepath: str) -> list[dict[str, Any]]:
        """Read a CSV file from disk and return a normalized component list.

        Args:
            filepath: Path to a ``.csv`` file.

        Returns:
            A list of normalised component dicts.
        """
        import os

        if not os.path.isfile(filepath):
            logger.error("CSV file not found: %s", filepath)
            return []
        try:
            with open(filepath, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            logger.error("Cannot read CSV file %s: %s", filepath, exc)
            return []
        result = self.parse(data, filename=os.path.basename(filepath))
        return result.get("components", [])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_columns(self, columns: list[str]) -> dict[str, str]:
        """Map raw column names to canonical names."""
        mapping = {}
        for col in columns:
            key = col.lower().strip()
            if key in COLUMN_MAP:
                mapping[key] = COLUMN_MAP[key]
        return mapping
