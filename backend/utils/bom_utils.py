"""BoM normalization and analysis utilities."""

from __future__ import annotations

import re
from typing import Any, Optional


# Column name mapping: various Korean/English variants → normalized name
COLUMN_MAPPINGS: dict[str, str] = {
    # Part number
    "부품번호": "part_number",
    "part number": "part_number",
    "part_number": "part_number",
    "p/n": "part_number",
    "pn": "part_number",
    "mpn": "part_number",
    "mfr part": "part_number",
    "manufacturer part": "part_number",
    "제조사 부품번호": "part_number",
    # Quantity
    "수량": "quantity",
    "qty": "quantity",
    "quantity": "quantity",
    "개수": "quantity",
    # Description
    "설명": "description",
    "description": "description",
    "desc": "description",
    "비고": "description",
    "comment": "description",
    # Package
    "패키지": "package",
    "package": "package",
    "pkg": "package",
    "footprint": "package",
    "풋프린트": "package",
    # Price
    "단가": "unit_price",
    "price": "unit_price",
    "unit price": "unit_price",
    "가격": "unit_price",
    # Manufacturer
    "제조사": "manufacturer",
    "manufacturer": "manufacturer",
    "mfr": "manufacturer",
    "mfg": "manufacturer",
    "maker": "manufacturer",
    # LCSC code
    "lcsc": "lcsc_code",
    "lcsc번호": "lcsc_code",
    "lcsc code": "lcsc_code",
    "lcsc part": "lcsc_code",
    # Reference designator
    "레퍼런스": "ref_designator",
    "reference": "ref_designator",
    "ref": "ref_designator",
    "designator": "ref_designator",
    "refdes": "ref_designator",
    "부품 번호": "ref_designator",
    # Value
    "값": "value",
    "value": "value",
    "val": "value",
}


def normalize_column_name(col: str) -> str:
    """컬럼명을 정규화한다."""
    cleaned = col.strip().lower().replace("\n", " ").replace("_", " ")
    return COLUMN_MAPPINGS.get(cleaned, cleaned)


def normalize_bom_columns(columns: list[str]) -> dict[str, str]:
    """BoM 컬럼들을 정규화된 이름으로 매핑한다."""
    mapping = {}
    for col in columns:
        normalized = normalize_column_name(col)
        if normalized != col.strip().lower():
            mapping[col] = normalized
        else:
            # Try partial match
            col_lower = col.strip().lower()
            for pattern, target in COLUMN_MAPPINGS.items():
                if pattern in col_lower:
                    mapping[col] = target
                    break
            else:
                mapping[col] = col_lower.replace(" ", "_")
    return mapping


def normalize_part_number(pn: str) -> str:
    """부품번호를 정규화한다 (공백, 대소문자, 특수문자 정리)."""
    if not pn:
        return ""
    # Remove extra whitespace
    pn = re.sub(r"\s+", "", pn.strip())
    # Uppercase
    pn = pn.upper()
    # Remove common suffixes that don't affect identity
    pn = re.sub(r"[-_]?(TR|CT|DKRND|ND)$", "", pn)
    return pn


def normalize_package(pkg: str) -> str:
    """패키지명을 정규화한다."""
    if not pkg:
        return ""
    pkg = pkg.strip().upper()
    # Common aliases
    aliases = {
        "0402": "0402",
        "0603": "0603",
        "0805": "0805",
        "1206": "1206",
        "SOT-23": "SOT-23",
        "SOT23": "SOT-23",
        "SOT-23-3": "SOT-23",
        "SOP-8": "SOP-8",
        "SOP8": "SOP-8",
        "SOIC-8": "SOP-8",
        "SOIC8": "SOP-8",
        "QFN": "QFN",
        "TQFP": "TQFP",
        "DIP-8": "DIP-8",
        "DIP8": "DIP-8",
    }
    return aliases.get(pkg, pkg)


def extract_component_value(text: str) -> dict[str, Any]:
    """부품 값 텍스트에서 수치와 단위를 추출한다."""
    if not text:
        return {"raw": text, "numeric": None, "unit": None}

    text = text.strip()

    # Resistance patterns
    r_match = re.match(r"^(\d+\.?\d*)\s*(k|m|M|G)?\s*(ohm|Ω|옴|R)?$", text, re.IGNORECASE)
    if r_match:
        value = float(r_match.group(1))
        multiplier = {"k": 1e3, "m": 1e-3, "M": 1e6, "G": 1e9}.get(r_match.group(2), 1)
        return {"raw": text, "numeric": value * multiplier, "unit": "Ω"}

    # Capacitance patterns
    c_match = re.match(r"^(\d+\.?\d*)\s*(p|n|u|μ|m)?\s*(f|F|패럿)?$", text, re.IGNORECASE)
    if c_match:
        value = float(c_match.group(1))
        multiplier = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "μ": 1e-6, "m": 1e-3}.get(c_match.group(2), 1)
        return {"raw": text, "numeric": value * multiplier, "unit": "F"}

    # Inductance patterns
    l_match = re.match(r"^(\d+\.?\d*)\s*(n|u|μ|m)?\s*(h|H|헨리)?$", text, re.IGNORECASE)
    if l_match:
        value = float(l_match.group(1))
        multiplier = {"n": 1e-9, "u": 1e-6, "μ": 1e-6, "m": 1e-3}.get(l_match.group(2), 1)
        return {"raw": text, "numeric": value * multiplier, "unit": "H"}

    # Voltage
    v_match = re.match(r"^(\d+\.?\d*)\s*(V|v|볼트)$", text)
    if v_match:
        return {"raw": text, "numeric": float(v_match.group(1)), "unit": "V"}

    return {"raw": text, "numeric": None, "unit": None}


def detect_bom_risks(bom_items: list[dict]) -> list[dict]:
    """BoM 항목에서 리스크를 감지한다."""
    risks = []

    for i, item in enumerate(bom_items):
        row_id = item.get("ref_designator", f"row_{i}")

        # Missing part number
        if not item.get("part_number"):
            risks.append({
                "row_id": row_id,
                "type": "missing-part",
                "severity": "high",
                "note": "부품번호(MPN)가 누락됨 — 조달 불가",
            })

        # Missing package
        if not item.get("package"):
            risks.append({
                "row_id": row_id,
                "type": "missing-package",
                "severity": "medium",
                "note": "패키지 정보 누락 — footprint 확인 필요",
            })

        # Suspicious quantity
        qty = item.get("quantity")
        if qty is not None:
            try:
                q = int(qty)
                if q <= 0:
                    risks.append({
                        "row_id": row_id,
                        "type": "invalid-quantity",
                        "severity": "high",
                        "note": f"수량이 {q}임 — 확인 필요",
                    })
                elif q > 100:
                    risks.append({
                        "row_id": row_id,
                        "type": "high-quantity",
                        "severity": "low",
                        "note": f"수량이 {q}개로 많음 — LED array 또는 저항 네트워크인지 확인",
                    })
            except (ValueError, TypeError):
                pass

        # Duplicate detection (simple)
        pn = normalize_part_number(item.get("part_number", ""))
        if pn:
            dupes = [
                j for j, other in enumerate(bom_items)
                if j != i and normalize_part_number(other.get("part_number", "")) == pn
                and other.get("ref_designator") != row_id
            ]
            if dupes:
                risks.append({
                    "row_id": row_id,
                    "type": "duplicate-variant",
                    "severity": "low",
                    "note": f"동일 부품번호가 여러 행에 존재 — 통합 가능 여부 확인",
                })

    return risks


def calculate_bom_cost(bom_items: list[dict]) -> dict[str, Any]:
    """BoM 총 원가를 계산한다."""
    total = 0.0
    items_with_price = 0
    items_without_price = 0

    for item in bom_items:
        price = item.get("unit_price")
        qty = item.get("quantity", 1)

        try:
            p = float(price) if price else 0
            q = int(qty) if qty else 1
            if p > 0:
                total += p * q
                items_with_price += 1
            else:
                items_without_price += 1
        except (ValueError, TypeError):
            items_without_price += 1

    return {
        "total_cost": round(total, 2),
        "items_with_price": items_with_price,
        "items_without_price": items_without_price,
        "completeness": round(items_with_price / max(len(bom_items), 1) * 100, 1),
        "warning": "일부 부품 가격 미포함" if items_without_price > 0 else None,
    }
