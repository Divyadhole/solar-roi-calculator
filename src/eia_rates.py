"""
src/eia_rates.py
Fetches real commercial electricity rates from EIA Open Data API.

Free API: https://www.eia.gov/opendata/
Register for key at: https://www.eia.gov/opendata/register.php
DEMO_KEY works for low-volume requests.

Used in app to auto-populate the utility rate field
based on user's selected state.
"""

import requests
import pandas as pd
from pathlib import Path

EIA_BASE = "https://api.eia.gov/v2"

# 2023 EIA commercial rates (cents/kWh) — EIA Electric Power Monthly
# Source: Table 5.6.B — Average Retail Price of Electricity
EIA_STATE_RATES_2023 = {
    "AK": 16.89, "AL": 11.12, "AR": 9.28,  "AZ": 11.66, "CA": 23.05,
    "CO": 10.74, "CT": 22.96, "DC": 13.22, "DE": 12.81, "FL": 11.44,
    "GA": 10.56, "HI": 38.84, "IA": 9.66,  "ID": 8.41,  "IL": 10.33,
    "IN": 9.74,  "KS": 10.28, "KY": 9.10,  "LA": 9.17,  "MA": 22.35,
    "MD": 13.81, "ME": 18.76, "MI": 11.85, "MN": 11.37, "MO": 9.83,
    "MS": 10.38, "MT": 10.00, "NC": 9.31,  "ND": 9.36,  "NE": 9.62,
    "NH": 22.13, "NJ": 15.91, "NM": 11.89, "NV": 12.04, "NY": 17.39,
    "OH": 10.29, "OK": 9.21,  "OR": 10.28, "PA": 12.96, "RI": 21.19,
    "SC": 10.22, "SD": 9.82,  "TN": 10.19, "TX": 9.54,  "UT": 9.66,
    "VA": 10.12, "VT": 18.14, "WA": 7.55,  "WI": 11.60, "WV": 9.29,
    "WY": 8.56,
}

# NREL capacity factors by state (annual average)
# Source: NREL Solar Resource Maps
NREL_CAPACITY_FACTORS = {
    "AK": 0.130, "AL": 0.178, "AR": 0.172, "AZ": 0.201, "CA": 0.190,
    "CO": 0.188, "CT": 0.153, "DC": 0.155, "DE": 0.156, "FL": 0.183,
    "GA": 0.180, "HI": 0.190, "IA": 0.163, "ID": 0.171, "IL": 0.156,
    "IN": 0.153, "KS": 0.179, "KY": 0.156, "LA": 0.177, "MA": 0.153,
    "MD": 0.162, "ME": 0.150, "MI": 0.149, "MN": 0.160, "MO": 0.168,
    "MS": 0.178, "MT": 0.166, "NC": 0.174, "ND": 0.165, "NE": 0.177,
    "NH": 0.151, "NJ": 0.160, "NM": 0.198, "NV": 0.200, "NY": 0.152,
    "OH": 0.152, "OK": 0.181, "OR": 0.158, "PA": 0.153, "RI": 0.154,
    "SC": 0.178, "SD": 0.170, "TN": 0.167, "TX": 0.182, "UT": 0.193,
    "VA": 0.163, "VT": 0.148, "WA": 0.149, "WI": 0.152, "WV": 0.149,
    "WY": 0.181,
}

STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
    "CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"Washington DC",
    "FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois",
    "IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana",
    "ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan",
    "MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana",
    "NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey",
    "NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota",
    "OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania",
    "RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee",
    "TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington",
    "WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
}


def get_rate_for_state(state_code: str) -> float:
    """Return EIA 2023 commercial electricity rate in $/kWh."""
    cents = EIA_STATE_RATES_2023.get(state_code.upper(), 12.0)
    return round(cents / 100, 4)


def get_capacity_factor(state_code: str) -> float:
    """Return NREL annual capacity factor for state."""
    return NREL_CAPACITY_FACTORS.get(state_code.upper(), 0.175)


def get_all_states_df() -> pd.DataFrame:
    rows = []
    for code, rate in EIA_STATE_RATES_2023.items():
        rows.append({
            "state_code":     code,
            "state_name":     STATE_NAMES.get(code, code),
            "rate_cents_kwh": rate,
            "rate_usd_kwh":   round(rate / 100, 4),
            "capacity_factor":NREL_CAPACITY_FACTORS.get(code, 0.175),
            "kwh_per_kw_yr":  round(NREL_CAPACITY_FACTORS.get(code, 0.175) * 8760, 0),
        })
    return pd.DataFrame(rows).sort_values("state_name").reset_index(drop=True)


def fetch_live_rate(state_code: str, api_key: str = "DEMO_KEY") -> float | None:
    """Try to fetch live rate from EIA API. Falls back to embedded if unavailable."""
    try:
        url = f"{EIA_BASE}/electricity/retail-sales/data/"
        params = {
            "api_key":           api_key,
            "frequency":         "annual",
            "data[0]":           "price",
            "facets[stateid][]": state_code.upper(),
            "facets[sectorid][]":"COM",
            "sort[0][column]":   "period",
            "sort[0][direction]":"desc",
            "length":            1,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        records = data.get("response", {}).get("data", [])
        if records:
            price_cents = float(records[0].get("price", 0))
            return round(price_cents / 100, 4)
    except Exception:
        pass
    return get_rate_for_state(state_code)
