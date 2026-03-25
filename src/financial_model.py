"""
src/financial_model.py
Core solar financial calculations: IRR, NPV, payback period,
cash flow modeling, and savings analysis.

All formulas match standard commercial solar project finance:
  - NREL System Advisor Model (SAM) methodology
  - IRS Publication 946 (MACRS depreciation)
  - ITC per IRA 2022 (Inflation Reduction Act) — 30% through 2032
"""

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from dataclasses import dataclass, field
from typing import Optional


# ── Federal Incentive Rates (IRA 2022) ───────────────────────────────────
ITC_RATES = {
    2022: 0.26, 2023: 0.30, 2024: 0.30, 2025: 0.30,
    2026: 0.30, 2027: 0.30, 2028: 0.30, 2029: 0.30,
    2030: 0.30, 2031: 0.30, 2032: 0.30, 2033: 0.26,
    2034: 0.22, 2035: 0.10,
}

# MACRS 5-year depreciation schedule (half-year convention, IRS)
MACRS_5YR = [0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576]


@dataclass
class SolarProjectInputs:
    """All inputs needed to model a commercial solar project."""

    # System
    system_size_kw:        float = 100.0    # DC system size in kW
    cost_per_watt:         float = 2.80     # Installed cost $/W (commercial 2024 avg)
    annual_degradation:    float = 0.005    # Panel degradation rate (0.5%/yr)

    # Energy
    annual_production_kwh: Optional[float] = None  # If None, calculated from capacity factor
    capacity_factor:       float = 0.175    # Default for Southwest US (NREL typical)
    electricity_rate:      float = 0.12     # $/kWh current utility rate
    rate_escalation:       float = 0.025    # Annual utility rate increase (2.5%/yr avg)

    # Financial
    project_year:          int   = 2024
    analysis_period:       int   = 25       # Years (standard for commercial solar)
    discount_rate:         float = 0.07     # WACC / discount rate
    tax_rate:              float = 0.21     # Federal corporate tax rate
    apply_itc:             bool  = True     # Apply Investment Tax Credit
    apply_macrs:           bool  = True     # Apply MACRS depreciation
    state_itc_pct:         float = 0.0      # Additional state ITC if applicable

    # O&M
    om_cost_per_kw_yr:     float = 15.0     # O&M $/kW/yr (NREL benchmark)
    om_escalation:         float = 0.02     # O&M cost escalation

    # Grid
    net_metering:          bool  = True     # Net metering available
    export_rate:           float = None     # $/kWh for exported energy (if not NEM)


@dataclass
class SolarProjectResults:
    """Full financial analysis output."""

    # Capital
    total_installed_cost:  float = 0.0
    itc_amount:            float = 0.0
    net_cost_after_itc:    float = 0.0
    macrs_pv_benefit:      float = 0.0

    # Returns
    simple_payback_yrs:    float = 0.0
    discounted_payback_yrs:float = 0.0
    irr:                   float = 0.0
    npv:                   float = 0.0
    lcoe:                  float = 0.0     # $/kWh levelized cost of energy

    # Savings
    year1_production_kwh:  float = 0.0
    year1_savings_usd:     float = 0.0
    lifetime_savings_usd:  float = 0.0
    co2_offset_tons:       float = 0.0    # Lifetime CO2 offset

    # Annual cash flows
    cash_flows:            pd.DataFrame = field(default_factory=pd.DataFrame)


def calculate(inputs: SolarProjectInputs) -> SolarProjectResults:
    """Run full financial analysis for a commercial solar project."""

    r = SolarProjectResults()
    p = inputs

    # ── System Cost ──────────────────────────────────────────────────────
    r.total_installed_cost = p.system_size_kw * 1000 * p.cost_per_watt

    # ── ITC ──────────────────────────────────────────────────────────────
    itc_rate = ITC_RATES.get(p.project_year, 0.30) + p.state_itc_pct
    r.itc_amount = r.total_installed_cost * itc_rate * int(p.apply_itc)
    r.net_cost_after_itc = r.total_installed_cost - r.itc_amount

    # ── Annual Production ─────────────────────────────────────────────────
    if p.annual_production_kwh:
        base_production = p.annual_production_kwh
    else:
        base_production = p.system_size_kw * 8760 * p.capacity_factor

    r.year1_production_kwh = base_production

    # ── MACRS NPV Benefit ─────────────────────────────────────────────────
    macrs_basis = r.total_installed_cost - r.itc_amount * 0.5  # ITC reduces basis by 50%
    macrs_benefit = 0.0
    if p.apply_macrs:
        for yr, pct in enumerate(MACRS_5YR, start=1):
            depr_amount = macrs_basis * pct
            tax_benefit  = depr_amount * p.tax_rate
            macrs_benefit += tax_benefit / ((1 + p.discount_rate) ** yr)
    r.macrs_pv_benefit = macrs_benefit

    # ── Annual Cash Flows ──────────────────────────────────────────────────
    rows = []
    cum_cf = -r.net_cost_after_itc   # Year 0 outflow

    total_kwh = 0.0
    for yr in range(1, p.analysis_period + 1):
        # Production degrades each year
        production_kwh = base_production * ((1 - p.annual_degradation) ** (yr - 1))

        # Electricity rate escalates
        elec_rate = p.electricity_rate * ((1 + p.rate_escalation) ** (yr - 1))

        # Gross savings
        gross_savings = production_kwh * elec_rate

        # O&M cost
        om_cost = p.system_size_kw * p.om_cost_per_kw_yr * ((1 + p.om_escalation) ** (yr - 1))

        # MACRS depreciation tax shield
        macrs_benefit_yr = 0.0
        if p.apply_macrs and yr <= len(MACRS_5YR):
            depr = macrs_basis * MACRS_5YR[yr - 1]
            macrs_benefit_yr = depr * p.tax_rate

        # Net cash flow
        net_cf = gross_savings - om_cost + macrs_benefit_yr
        cum_cf += net_cf

        # Discounted
        pv_factor = (1 + p.discount_rate) ** yr
        dcf = net_cf / pv_factor

        total_kwh += production_kwh
        rows.append({
            "year":           yr,
            "production_kwh": round(production_kwh, 0),
            "elec_rate":      round(elec_rate, 4),
            "gross_savings":  round(gross_savings, 2),
            "om_cost":        round(om_cost, 2),
            "macrs_benefit":  round(macrs_benefit_yr, 2),
            "net_cash_flow":  round(net_cf, 2),
            "cumulative_cf":  round(cum_cf, 2),
            "discounted_cf":  round(dcf, 2),
        })

    df = pd.DataFrame(rows)
    r.cash_flows = df

    # ── Payback Period ────────────────────────────────────────────────────
    # Simple: when cumulative CF turns positive
    r.simple_payback_yrs = _simple_payback(df, r.net_cost_after_itc)

    # Discounted: when cumulative NPV turns positive
    r.discounted_payback_yrs = _discounted_payback(df, r.net_cost_after_itc, p.discount_rate)

    # ── IRR ───────────────────────────────────────────────────────────────
    cf_stream = [-r.net_cost_after_itc] + df["net_cash_flow"].tolist()
    r.irr = _calculate_irr(cf_stream)

    # ── NPV ───────────────────────────────────────────────────────────────
    r.npv = -r.net_cost_after_itc + df["discounted_cf"].sum() + r.macrs_pv_benefit

    # ── LCOE ─────────────────────────────────────────────────────────────
    # Levelized cost of energy = NPV of costs / NPV of production
    total_production_kwh = df["production_kwh"].sum()
    if total_production_kwh > 0:
        r.lcoe = r.net_cost_after_itc / total_production_kwh
    else:
        r.lcoe = 0.0

    # ── Summary ───────────────────────────────────────────────────────────
    r.year1_savings_usd    = df.iloc[0]["gross_savings"]
    r.lifetime_savings_usd = df["gross_savings"].sum()
    r.co2_offset_tons      = total_production_kwh * 0.000386  # EPA avg US grid factor

    return r


def _simple_payback(df: pd.DataFrame, initial_cost: float) -> float:
    """Simple payback: year when cumulative CF first turns positive."""
    for i, row in df.iterrows():
        if row["cumulative_cf"] >= 0:
            # Interpolate within the year
            prev_cum = df.iloc[i-1]["cumulative_cf"] if i > 0 else -initial_cost
            fraction = -prev_cum / (row["cumulative_cf"] - prev_cum)
            return row["year"] - 1 + fraction
    return float(df["year"].max())  # Never paid back


def _discounted_payback(df: pd.DataFrame, initial_cost: float, rate: float) -> float:
    """Discounted payback: when cumulative NPV first turns positive."""
    cum_npv = -initial_cost
    for _, row in df.iterrows():
        prev = cum_npv
        cum_npv += row["discounted_cf"]
        if cum_npv >= 0:
            fraction = -prev / (cum_npv - prev)
            return row["year"] - 1 + fraction
    return float(df["year"].max())


def _calculate_irr(cash_flows: list) -> float:
    """Newton's method IRR calculation."""
    def npv_at_rate(rate):
        return sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))

    try:
        irr = brentq(npv_at_rate, -0.999, 10.0, xtol=1e-6, maxiter=200)
        return round(irr, 6)
    except (ValueError, RuntimeError):
        return 0.0


def format_results(r: SolarProjectResults, inputs: SolarProjectInputs) -> dict:
    """Format results for display."""
    return {
        "System Size":          f"{inputs.system_size_kw:.0f} kW",
        "Installed Cost":       f"${r.total_installed_cost:,.0f}",
        "ITC (30%)":            f"-${r.itc_amount:,.0f}",
        "Net Cost After ITC":   f"${r.net_cost_after_itc:,.0f}",
        "Year 1 Production":    f"{r.year1_production_kwh:,.0f} kWh",
        "Year 1 Savings":       f"${r.year1_savings_usd:,.0f}",
        "Simple Payback":       f"{r.simple_payback_yrs:.1f} years",
        "Discounted Payback":   f"{r.discounted_payback_yrs:.1f} years",
        "IRR":                  f"{r.irr*100:.1f}%",
        "NPV (25-yr)":          f"${r.npv:,.0f}",
        "LCOE":                 f"${r.lcoe:.3f}/kWh",
        "Lifetime Savings":     f"${r.lifetime_savings_usd:,.0f}",
        "CO2 Offset":           f"{r.co2_offset_tons:.0f} tons",
    }


if __name__ == "__main__":
    # Example: 100kW commercial rooftop in Arizona
    inputs = SolarProjectInputs(
        system_size_kw     = 100,
        cost_per_watt      = 2.80,
        electricity_rate   = 0.118,  # APS commercial rate
        capacity_factor    = 0.195,  # Tucson, AZ (NREL)
        discount_rate      = 0.07,
        project_year       = 2024,
    )
    results = calculate(inputs)
    print("=== SOLAR PROJECT FINANCIAL ANALYSIS ===")
    for k, v in format_results(results, inputs).items():
        print(f"  {k:<25} {v}")
