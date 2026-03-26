"""BoM normalization and analysis helpers."""

from __future__ import annotations
import re
from typing import Any


class BomUtils:
    """Utility methods for BoM data processing."""

    # Common component category patterns
    CATEGORY_PATTERNS: dict[str, list[str]] = {
        "Resistor": [r"^\d+[\.\d]*\s*[kKmMΩ]?\s*[oO]?[hH]?[mM]?$", r"res", r"저항"],
        "Capacitor": [r"^\d+[\.\d]*\s*[pPnNuUμ][fF]$", r"cap", r"커패시터", r"콘덴서"],
        "Inductor": [r"^\d+[\.\d]*\s*[nNuUμm][hH]$", r"ind", r"인덕터", r"코일"],
        "LED": [r"led", r"엘이디", r"발광"],
        "IC": [r"^[A-Z]{2,}\d+", r"ic\b", r"집적회로"],
        "Diode": [r"diode", r"다이오드", r"^[1-9]N\d+", r"^SS\d+", r"^BAT\d+"],
        "Transistor": [r"mosfet", r"bjt", r"트랜지스터", r"^2N\d+", r"^BC\d+", r"^IRF"],
        "Connector": [r"conn", r"header", r"커넥터", r"핀헤더", r"^JST"],
        "Crystal": [r"crystal", r"osc", r"크리스탈", r"수정"],
        "Fuse": [r"fuse", r"퓨즈"],
        "Transformer": [r"transformer", r"트랜스"],
    }

    @staticmethod
    def detect_category(description: str, value: str = "", part_number: str = "") -> str:
        """Detect component category from description, value, and part number."""
        combined = f"{description} {value} {part_number}".lower()

        for category, patterns in BomUtils.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return category

        return "Other"

    @staticmethod
    def normalize_value(raw_value: str) -> dict[str, Any]:
        """Normalize a component value string to structured data.

        e.g., "10kΩ" -> {"value": 10000, "unit": "ohm", "display": "10kΩ"}
        """
        raw = raw_value.strip()
        if not raw:
            return {"value": 0, "unit": "", "display": raw_value}

        # Resistance
        match = re.match(r"^([\d\.]+)\s*([kKmM]?)\s*[ΩΩoO]?[hH]?[mM]?\s*$", raw)
        if match:
            num = float(match.group(1))
            mult = {"k": 1e3, "K": 1e3, "m": 1e-3, "M": 1e6}.get(match.group(2), 1)
            return {"value": num * mult, "unit": "ohm", "display": raw}

        # Capacitance
        match = re.match(r"^([\d\.]+)\s*([pPnNuUμm])[fF]\s*$", raw)
        if match:
            num = float(match.group(1))
            mult = {"p": 1e-12, "P": 1e-12, "n": 1e-9, "N": 1e-9,
                     "u": 1e-6, "U": 1e-6, "μ": 1e-6, "m": 1e-3}.get(match.group(2), 1)
            return {"value": num * mult, "unit": "farad", "display": raw}

        # Inductance
        match = re.match(r"^([\d\.]+)\s*([nNuUμm])[hH]\s*$", raw)
        if match:
            num = float(match.group(1))
            mult = {"n": 1e-9, "N": 1e-9, "u": 1e-6, "U": 1e-6,
                     "μ": 1e-6, "m": 1e-3}.get(match.group(2), 1)
            return {"value": num * mult, "unit": "henry", "display": raw}

        return {"value": 0, "unit": "", "display": raw}

    @staticmethod
    def normalize_package(raw_package: str) -> str:
        """Normalize package/footprint name."""
        pkg = raw_package.strip().upper()

        # Common normalizations
        pkg_map = {
            "0402": "0402 (1005 Metric)",
            "0603": "0603 (1608 Metric)",
            "0805": "0805 (2012 Metric)",
            "1206": "1206 (3216 Metric)",
            "1210": "1210 (3225 Metric)",
            "2010": "2010 (5025 Metric)",
            "2512": "2512 (6332 Metric)",
            "SOT23": "SOT-23",
            "SOT-23": "SOT-23",
            "SOT23-3": "SOT-23-3",
            "SOT23-5": "SOT-23-5",
            "SOT23-6": "SOT-23-6",
            "SOT223": "SOT-223",
            "SOT-223": "SOT-223",
            "SOP8": "SOP-8",
            "SOP-8": "SOP-8",
            "SOIC8": "SOIC-8",
            "SOIC-8": "SOIC-8",
            "TSSOP": "TSSOP",
            "QFN": "QFN",
            "QFP": "QFP",
            "BGA": "BGA",
            "DIP": "DIP",
        }

        for key, normalized in pkg_map.items():
            if pkg == key or pkg.startswith(key):
                return normalized

        return raw_package.strip()

    @staticmethod
    def calculate_bom_cost(components: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate total BoM cost summary."""
        total_cost = 0.0
        total_parts = 0
        by_category: dict[str, float] = {}

        for comp in components:
            qty = int(comp.get("quantity", 1) or 1)
            price = float(comp.get("unit_price", 0) or 0)
            cat = comp.get("category", "Other")

            line_cost = qty * price
            total_cost += line_cost
            total_parts += qty
            by_category[cat] = by_category.get(cat, 0) + line_cost

        return {
            "total_cost": round(total_cost, 4),
            "total_unique_parts": len(components),
            "total_quantity": total_parts,
            "cost_by_category": {k: round(v, 4) for k, v in sorted(by_category.items(), key=lambda x: -x[1])},
            "currency": "USD",
        }

    @staticmethod
    def find_duplicates(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find potential duplicate components in the BoM."""
        seen: dict[str, list[int]] = {}
        for i, comp in enumerate(components):
            key = f"{comp.get('part_number', '').strip().lower()}|{comp.get('value', '').strip().lower()}"
            if key and key != "|":
                seen.setdefault(key, []).append(i)

        duplicates = []
        for key, indices in seen.items():
            if len(indices) > 1:
                pn, val = key.split("|")
                duplicates.append({
                    "part_number": pn,
                    "value": val,
                    "row_indices": indices,
                    "count": len(indices),
                })

        return duplicates

    @staticmethod
    def validate_bom(components: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Validate BoM data and return list of issues."""
        issues = []
        for i, comp in enumerate(components):
            ref = comp.get("ref_designator", "")
            pn = comp.get("part_number", "")

            if not ref:
                issues.append({"row": str(i), "severity": "warning", "message": "레퍼런스 디자이네이터 누락"})

            if not pn:
                issues.append({"row": str(i), "severity": "warning",
                               "message": f"{ref}: 파트넘버 누락"})

            qty = comp.get("quantity", 0)
            try:
                if int(qty) <= 0:
                    issues.append({"row": str(i), "severity": "error",
                                   "message": f"{ref}: 수량이 0 이하"})
            except (ValueError, TypeError):
                issues.append({"row": str(i), "severity": "error",
                               "message": f"{ref}: 수량 값이 유효하지 않음"})

        return issues
