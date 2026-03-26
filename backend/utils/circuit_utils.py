"""Circuit analysis utility functions."""

from __future__ import annotations
from typing import Any


def identify_topology(components: list[dict]) -> str:
    """주요 부품 구성으로 LED 드라이버 토폴로지를 추정한다."""
    ic_values = [c.get("value", "").lower() for c in components]
    ic_parts = [c.get("part_number", "").lower() for c in components]
    all_text = " ".join(ic_values + ic_parts)

    # Buck topology indicators
    buck_ics = ["ncl30170", "bp2866", "xl4015", "mp2307", "tps5430", "lm2596"]
    if any(ic in all_text for ic in buck_ics):
        return "buck"

    # Boost topology indicators
    boost_ics = ["mt3608", "xl6009", "tps61088"]
    if any(ic in all_text for ic in boost_ics):
        return "boost"

    # Buck-boost
    bb_ics = ["lt3791", "tps63020"]
    if any(ic in all_text for ic in bb_ics):
        return "buck-boost"

    # Flyback (isolated)
    flyback_ics = ["uc3842", "viper22a", "ob2263", "cr6853"]
    if any(ic in all_text for ic in flyback_ics):
        return "flyback"

    # Linear driver
    linear_ics = ["sm2082", "bp9916", "pt4115"]
    if any(ic in all_text for ic in linear_ics):
        return "linear"

    # Check for transformer (indicates isolated topology)
    has_transformer = any(
        c.get("category", "").lower() in ["transformer", "트랜스포머"]
        or "transformer" in c.get("description", "").lower()
        for c in components
    )
    if has_transformer:
        return "flyback"

    return "unknown"


def estimate_power(components: list[dict]) -> dict[str, Any]:
    """부품 구성으로 대략적인 출력 전력을 추정한다."""
    result = {
        "estimated_power_w": None,
        "input_voltage": None,
        "output_voltage": None,
        "confidence": "low",
        "basis": [],
    }

    for c in components:
        desc = (c.get("description", "") + " " + c.get("value", "")).lower()

        # LED current from sense resistor
        if c.get("category") == "resistor" and "sense" in desc:
            try:
                value = float(c.get("value", "0").replace("R", ".").replace("Ω", ""))
                if 0.1 <= value <= 10:
                    current_a = 0.5 / value  # Typical Vsense ≈ 0.5V
                    result["basis"].append(f"Sense resistor {value}Ω → ~{current_a:.2f}A")
            except (ValueError, ZeroDivisionError):
                pass

    return result


def identify_protection_circuits(components: list[dict]) -> list[dict]:
    """보호회로 구성 요소를 식별한다."""
    protections = []

    for c in components:
        category = c.get("category", "").lower()
        value = c.get("value", "").lower()
        desc = c.get("description", "").lower()
        combined = f"{category} {value} {desc}"

        if any(kw in combined for kw in ["mov", "varistor", "배리스터"]):
            protections.append({
                "type": "MOV",
                "component": c.get("ref_designator", "?"),
                "purpose": "서지 보호 (과전압 클램핑)",
            })
        elif any(kw in combined for kw in ["ptc", "fuse", "퓨즈"]):
            protections.append({
                "type": "PTC_fuse",
                "component": c.get("ref_designator", "?"),
                "purpose": "과전류 보호 (자기복구 퓨즈)",
            })
        elif any(kw in combined for kw in ["tvs", "esd", "정전기"]):
            protections.append({
                "type": "TVS",
                "component": c.get("ref_designator", "?"),
                "purpose": "ESD/TVS 보호",
            })
        elif any(kw in combined for kw in ["ntc", "써미스터"]):
            protections.append({
                "type": "NTC",
                "component": c.get("ref_designator", "?"),
                "purpose": "돌입전류 제한",
            })
        elif "zener" in combined:
            protections.append({
                "type": "Zener",
                "component": c.get("ref_designator", "?"),
                "purpose": "과전압 보호 (OVP)",
            })

    return protections


def classify_component(part_number: str, value: str, description: str) -> str:
    """부품을 기능 분류한다."""
    text = f"{part_number} {value} {description}".lower()

    categories = [
        ("led-driver-ic", ["ncl30170", "bp2866", "sm2082", "bp9916", "pt4115", "ob2263"]),
        ("rf-ic", ["nrf24l01", "cc2500", "esp32", "cc2530", "si4432", "esp8266"]),
        ("sensor-ic", ["biss0001", "hlk-ld", "rcwl", "as312", "am312"]),
        ("mcu", ["stm32", "attiny", "atmega", "pic", "esp32", "nrf52"]),
        ("mosfet", ["mosfet", "irf", "ao3400", "si2302"]),
        ("diode", ["diode", "1n4148", "ss34", "es1j", "bridge"]),
        ("capacitor", ["cap", "uf", "nf", "pf", "capacitor", "콘덴서"]),
        ("resistor", ["res", "ohm", "resistor", "저항"]),
        ("inductor", ["inductor", "uh", "mh", "인덕터", "코일"]),
        ("transformer", ["transformer", "트랜스"]),
        ("connector", ["connector", "header", "pin", "커넥터", "단자"]),
        ("led", ["led", "발광"]),
    ]

    for cat, keywords in categories:
        if any(kw in text for kw in keywords):
            return cat

    return "other"


def calculate_thermal_budget(power_w: float, ambient_c: float = 25.0) -> dict[str, Any]:
    """열적 버짓을 계산한다."""
    # Typical LED driver efficiency assumptions
    efficiency = 0.85
    power_loss = power_w * (1 - efficiency) / efficiency

    # PCB thermal resistance estimates (FR4)
    rth_pcb_to_air = 40.0  # °C/W for small PCB
    temp_rise = power_loss * rth_pcb_to_air

    return {
        "input_power_w": round(power_w / efficiency, 2),
        "power_loss_w": round(power_loss, 2),
        "assumed_efficiency": efficiency,
        "ambient_temp_c": ambient_c,
        "estimated_pcb_temp_c": round(ambient_c + temp_rise, 1),
        "rth_pcb_to_air": rth_pcb_to_air,
        "warning": "실측 필요 — 이 값은 추정치입니다" if temp_rise > 30 else None,
        "risk_level": "high" if temp_rise > 50 else "medium" if temp_rise > 30 else "low",
    }
