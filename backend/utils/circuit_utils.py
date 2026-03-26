"""Circuit analysis helper utilities for LED product design."""

from __future__ import annotations
import math
from typing import Any


class CircuitUtils:
    """Static utility methods for LED circuit calculations."""

    @staticmethod
    def led_resistor(v_supply: float, v_led: float, i_led_ma: float, n_series: int = 1) -> dict[str, Any]:
        """Calculate current-limiting resistor for LED string.

        Args:
            v_supply: Supply voltage (V)
            v_led: Forward voltage per LED (V)
            i_led_ma: Desired LED current (mA)
            n_series: Number of LEDs in series

        Returns:
            Dict with resistance, power dissipation, and E24 nearest value.
        """
        v_drop = v_supply - (v_led * n_series)
        if v_drop <= 0:
            return {"error": "Supply voltage too low for LED string", "v_drop": v_drop}

        i_led_a = i_led_ma / 1000.0
        r_exact = v_drop / i_led_a
        p_resistor = v_drop * i_led_a
        r_nearest = CircuitUtils.nearest_e24(r_exact)

        return {
            "r_exact_ohm": round(r_exact, 2),
            "r_nearest_e24_ohm": r_nearest,
            "power_dissipation_w": round(p_resistor, 4),
            "recommended_power_rating_w": CircuitUtils._next_power_rating(p_resistor),
            "actual_current_ma": round((v_drop / r_nearest) * 1000, 2) if r_nearest > 0 else 0,
            "v_drop_resistor": round(v_drop, 2),
        }

    @staticmethod
    def buck_converter(v_in: float, v_out: float, i_out_a: float,
                       f_sw_khz: float = 500, ripple_pct: float = 30) -> dict[str, Any]:
        """Calculate Buck converter inductor and capacitor values.

        Args:
            v_in: Input voltage (V)
            v_out: Output voltage (V)
            i_out_a: Output current (A)
            f_sw_khz: Switching frequency (kHz)
            ripple_pct: Inductor current ripple percentage
        """
        if v_in <= v_out:
            return {"error": "V_in must be greater than V_out for buck converter"}

        duty = v_out / v_in
        f_sw = f_sw_khz * 1000
        delta_il = i_out_a * (ripple_pct / 100.0)

        # Inductor: L = (V_out * (1 - D)) / (f_sw * delta_IL)
        l_henry = (v_out * (1 - duty)) / (f_sw * delta_il) if delta_il > 0 else 0
        l_uh = l_henry * 1e6

        # Output capacitor: C = delta_IL / (8 * f_sw * delta_V_out)
        # Assuming 1% output voltage ripple
        delta_v_out = v_out * 0.01
        c_farad = delta_il / (8 * f_sw * delta_v_out) if delta_v_out > 0 else 0
        c_uf = c_farad * 1e6

        return {
            "duty_cycle": round(duty, 4),
            "inductor_uh": round(l_uh, 1),
            "output_capacitor_uf": round(c_uf, 1),
            "ripple_current_a": round(delta_il, 3),
            "peak_current_a": round(i_out_a + delta_il / 2, 3),
            "power_out_w": round(v_out * i_out_a, 2),
            "efficiency_estimate": "85-92%",
        }

    @staticmethod
    def thermal_resistance(
        p_total_w: float,
        t_ambient_c: float = 25,
        tj_max_c: float = 125,
        rth_jc: float = 5.0,
        rth_cs: float = 0.5,
    ) -> dict[str, Any]:
        """Calculate required heatsink thermal resistance.

        Args:
            p_total_w: Total power dissipation (W)
            t_ambient_c: Ambient temperature (C)
            tj_max_c: Maximum junction temperature (C)
            rth_jc: Junction-to-case thermal resistance (C/W)
            rth_cs: Case-to-sink thermal resistance (C/W)
        """
        rth_total = (tj_max_c - t_ambient_c) / p_total_w if p_total_w > 0 else float("inf")
        rth_sa_required = rth_total - rth_jc - rth_cs

        return {
            "rth_total_cw": round(rth_total, 2),
            "rth_sa_required_cw": round(rth_sa_required, 2),
            "heatsink_needed": rth_sa_required < 50,
            "tj_estimated_c": round(t_ambient_c + p_total_w * (rth_jc + rth_cs + max(rth_sa_required, 0)), 1),
            "margin_c": round(tj_max_c - (t_ambient_c + p_total_w * rth_total), 1),
        }

    @staticmethod
    def nearest_e24(value: float) -> float:
        """Find nearest E24 standard resistor value."""
        if value <= 0:
            return 0

        e24 = [
            1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
            3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1,
        ]

        decade = 10 ** math.floor(math.log10(value))
        normalized = value / decade

        nearest = min(e24, key=lambda x: abs(x - normalized))
        return round(nearest * decade, 2)

    @staticmethod
    def _next_power_rating(power_w: float) -> float:
        """Select the next standard power rating above the dissipation."""
        ratings = [0.0625, 0.1, 0.125, 0.25, 0.5, 1.0, 2.0, 5.0]
        for r in ratings:
            if r >= power_w * 2:  # 2x derating
                return r
        return power_w * 3

    @staticmethod
    def led_string_config(
        v_supply: float,
        v_led: float,
        n_total: int,
        i_per_string_ma: float,
    ) -> dict[str, Any]:
        """Calculate optimal series/parallel LED configuration.

        Args:
            v_supply: Available supply voltage
            v_led: Forward voltage per LED
            n_total: Total number of LEDs
            i_per_string_ma: Current per series string
        """
        max_series = int(v_supply / v_led) if v_led > 0 else 1
        max_series = max(1, max_series)

        # Find best configuration
        best = None
        for n_s in range(1, max_series + 1):
            n_p = math.ceil(n_total / n_s)
            used = n_s * n_p
            waste = used - n_total
            v_string = v_led * n_s
            v_headroom = v_supply - v_string
            total_current = n_p * i_per_string_ma
            total_power = v_supply * total_current / 1000.0

            if v_headroom < 0.5:
                continue

            config = {
                "series": n_s,
                "parallel": n_p,
                "total_leds_used": used,
                "wasted_positions": waste,
                "v_string": round(v_string, 2),
                "v_headroom": round(v_headroom, 2),
                "total_current_ma": round(total_current, 1),
                "total_power_w": round(total_power, 2),
            }

            if best is None or (waste < best["wasted_positions"] and v_headroom >= 0.5):
                best = config

        return best or {"error": "No valid configuration found"}
