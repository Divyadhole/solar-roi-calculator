"""
src/sensitivity.py
Sensitivity analysis — how IRR and NPV change when
key inputs vary. Used by SOLON to stress-test project economics
before presenting to clients.

Standard commercial solar sensitivities:
  - Electricity rate (primary driver)
  - System cost per watt
  - Discount rate / WACC
  - Capacity factor (solar resource)
  - Rate escalation assumption
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.financial_model import SolarProjectInputs, calculate


def irr_sensitivity_table(base_inputs: SolarProjectInputs) -> pd.DataFrame:
    """
    2D sensitivity table: IRR vs (electricity rate, cost per watt).
    The two most important variables for commercial solar feasibility.
    """
    rates     = [0.07, 0.09, 0.11, 0.13, 0.15, 0.17, 0.20, 0.23]
    costs_w   = [2.20, 2.40, 2.60, 2.80, 3.00, 3.20, 3.40]

    rows = []
    for rate in rates:
        row = {"Elec Rate ($/kWh)": f"${rate:.2f}"}
        for cost in costs_w:
            inputs = SolarProjectInputs(
                **{**base_inputs.__dict__,
                   "electricity_rate": rate,
                   "cost_per_watt":    cost}
            )
            r = calculate(inputs)
            row[f"${cost:.2f}/W"] = f"{r.irr*100:.1f}%"
        rows.append(row)

    return pd.DataFrame(rows).set_index("Elec Rate ($/kWh)")


def npv_sensitivity_table(base_inputs: SolarProjectInputs) -> pd.DataFrame:
    """NPV sensitivity vs discount rate and electricity rate."""
    rates    = [0.07, 0.09, 0.11, 0.13, 0.15, 0.17, 0.20]
    discounts = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12]

    rows = []
    for rate in rates:
        row = {"Elec Rate ($/kWh)": f"${rate:.2f}"}
        for disc in discounts:
            inputs = SolarProjectInputs(
                **{**base_inputs.__dict__,
                   "electricity_rate": rate,
                   "discount_rate":    disc}
            )
            r = calculate(inputs)
            row[f"{disc*100:.0f}% WACC"] = f"${r.npv/1000:.0f}K"
        rows.append(row)

    return pd.DataFrame(rows).set_index("Elec Rate ($/kWh)")


def payback_sensitivity(base_inputs: SolarProjectInputs) -> pd.DataFrame:
    """Payback period sensitivity matrix."""
    sizes     = [50, 100, 150, 200, 250, 500]
    cost_w    = [2.40, 2.60, 2.80, 3.00, 3.20]

    rows = []
    for size in sizes:
        row = {"System Size (kW)": f"{size} kW"}
        for cost in cost_w:
            inputs = SolarProjectInputs(
                **{**base_inputs.__dict__,
                   "system_size_kw": size,
                   "cost_per_watt":  cost}
            )
            r = calculate(inputs)
            row[f"${cost:.2f}/W"] = f"{r.simple_payback_yrs:.1f} yr"
        rows.append(row)

    return pd.DataFrame(rows).set_index("System Size (kW)")


def tornado_chart_data(base_inputs: SolarProjectInputs,
                        variation_pct: float = 0.20) -> pd.DataFrame:
    """
    Tornado chart data — how much IRR changes when each input
    varies +/- 20% while others stay constant.
    Shows which inputs have the biggest impact on project economics.
    """
    base = calculate(base_inputs)
    base_irr = base.irr

    variables = {
        "Electricity Rate":   "electricity_rate",
        "System Cost ($/W)":  "cost_per_watt",
        "Capacity Factor":    "capacity_factor",
        "Discount Rate":      "discount_rate",
        "Rate Escalation":    "rate_escalation",
        "O&M Cost":           "om_cost_per_kw_yr",
    }

    rows = []
    for label, field in variables.items():
        base_val = getattr(base_inputs, field)
        low_val  = base_val * (1 - variation_pct)
        high_val = base_val * (1 + variation_pct)

        low_inputs  = SolarProjectInputs(**{**base_inputs.__dict__, field: low_val})
        high_inputs = SolarProjectInputs(**{**base_inputs.__dict__, field: high_val})

        irr_low  = calculate(low_inputs).irr
        irr_high = calculate(high_inputs).irr

        rows.append({
            "Variable":  label,
            "IRR_Low":   irr_low,
            "IRR_High":  irr_high,
            "IRR_Base":  base_irr,
            "Swing":     abs(irr_high - irr_low),
        })

    df = pd.DataFrame(rows).sort_values("Swing", ascending=True)
    return df


if __name__ == "__main__":
    from src.eia_rates import get_rate_for_state, get_capacity_factor
    inputs = SolarProjectInputs(
        system_size_kw   = 100,
        electricity_rate = get_rate_for_state("AZ"),
        capacity_factor  = get_capacity_factor("AZ"),
    )
    print("IRR Sensitivity Table (rate vs cost/W):")
    print(irr_sensitivity_table(inputs).to_string())
    print("\nTornado chart (what matters most for IRR):")
    t = tornado_chart_data(inputs)
    for _, r in t.iterrows():
        print(f"  {r['Variable']:<25} swing = {r['Swing']*100:.1f}pp")
