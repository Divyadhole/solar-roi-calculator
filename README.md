# Solar Project ROI Calculator

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20App-FF6B35?logo=streamlit&logoColor=white)](https://solar-roi-calcu-kvtumqm7wwyyd6hnr4zfoc.streamlit.app)
[![Dashboard](https://img.shields.io/badge/🌐%20Live%20Dashboard-divyadhole.github.io-FF6B35)](https://divyadhole.github.io/solar-roi-calculator/)
[![EIA](https://img.shields.io/badge/Data-EIA%20Commercial%20Rates-orange)](https://www.eia.gov/opendata/)
[![NREL](https://img.shields.io/badge/Data-NREL%20Solar%20Resource-yellow)](https://developer.nrel.gov/)
[![CI](https://github.com/Divyadhole/solar-roi-calculator/workflows/Solar%20ROI%20Validation/badge.svg)](https://github.com/Divyadhole/solar-roi-calculator/actions)

## Live Links

| | Link |
|---|---|
| 🌐 **Dashboard** | [divyadhole.github.io/solar-roi-calculator](https://divyadhole.github.io/solar-roi-calculator/) |
| ▶ **Interactive App** | [Launch App ↗](https://solar-roi-calcu-kvtumqm7wwyyd6hnr4zfoc.streamlit.app) |

The dashboard shows the financial model output and charts as a static site.
The Streamlit app is fully interactive — select any US state, adjust system size and cost, and get IRR/NPV/payback instantly with a downloadable Excel report.

---

## What It Does

A commercial solar financial analysis tool built to the exact methodology used by solar EPC companies. Enter a system size and location, get the full picture:

- **IRR** — Internal Rate of Return via scipy brentq solver
- **NPV** — Net Present Value at your specified WACC over 25 years
- **Simple payback** — years to recover net investment
- **Discounted payback** — payback accounting for time value of money
- **LCOE** — Levelized Cost of Energy in $/kWh
- **25-year cash flow stream** — year-by-year with panel degradation and utility rate escalation
- **Sensitivity tables** — IRR vs electricity rate vs cost per watt (2D matrix)
- **Tornado chart** — which input drives IRR the most
- **Excel report** — formatted 3-sheet workbook ready for client proposals

---

## Example Output — 100kW Commercial Rooftop, Tucson AZ

| Metric | Value |
|---|---|
| System size | 100 kW DC |
| Installed cost | $280,000 |
| Federal ITC (30%) | −$84,000 |
| Net cost after ITC | **$196,000** |
| Year 1 production | 170,820 kWh |
| Year 1 savings | $20,157 |
| **IRR** | **12.7%** |
| **NPV (25yr, 7% WACC)** | **$147,136** |
| **Simple payback** | **7.3 years** |
| LCOE | $0.049/kWh |
| Lifetime savings | $644,597 |
| CO₂ offset (25yr) | 1,553 tons |

Numbers use real EIA rate for Arizona (11.66¢/kWh) and NREL capacity factor (19.5%).

---

## Incentives Modeled

**Federal Investment Tax Credit (ITC)**
Locked at 30% through 2032 per the Inflation Reduction Act (IRA 2022). Steps down to 26% in 2033, 22% in 2034. The model applies the correct rate automatically based on project year.

**MACRS 5-Year Accelerated Depreciation**
IRS Publication 946, half-year convention: 20% / 32% / 19.2% / 11.52% / 11.52% / 5.76%. ITC reduces the depreciable basis by 50%. At 21% corporate tax rate this adds roughly $32K NPV to a 100kW system.

Without ITC + MACRS, the same Arizona project drops from **12.7% to 8.1% IRR**. The incentive stack is the difference between above and below most commercial hurdle rates.

---

## Data Sources

**EIA Open Data — Commercial Electricity Rates**
All 50 states, 2023 actuals from EIA Electric Power Monthly Table 5.6.B.
```python
# Live API endpoint
url = "https://api.eia.gov/v2/electricity/retail-sales/data/"
# Free registration: https://www.eia.gov/opendata/register.php
# Fallback: embedded 2023 verified rates for offline use
```

**NREL Solar Resource Database**
State-level annual capacity factors from NREL 10km resolution data.
```python
url = "https://developer.nrel.gov/api/solar/"
# Free registration: https://developer.nrel.gov/signup/
```

---

## Sensitivity Analysis

From `src/sensitivity.py`, on a 100kW Arizona system (±20% variation):

| Input | IRR Swing |
|---|---|
| Electricity rate | ±5.6pp |
| Capacity factor | ±5.6pp |
| System cost ($/W) | ±5.3pp |
| Rate escalation | ±1.0pp |
| O&M cost | ±0.4pp |

Electricity rate and solar resource are equally important. O&M barely matters.

The IRR sensitivity table (rate vs cost/W):

| Rate | $2.40/W | $2.80/W | $3.20/W |
|---|---|---|---|
| $0.09/kWh | 11.4% | 9.6% | 8.2% |
| $0.13/kWh | 16.8% | 14.5% | 12.7% |
| $0.17/kWh | 21.7% | 18.9% | 16.7% |
| $0.23/kWh | 28.7% | 25.1% | 22.3% |

---

## Project Layout

```
solar-roi-calculator/
├── src/
│   ├── financial_model.py   # Core: IRR, NPV, payback, MACRS, 25yr cashflows
│   ├── eia_rates.py         # EIA commercial rates all 50 states + NREL CFs
│   ├── sensitivity.py       # 2D sensitivity tables + tornado chart
│   └── excel_export.py      # 3-sheet formatted Excel proposal report
├── app.py                   # Streamlit interactive app
├── docs/                    # GitHub Pages static dashboard
├── .streamlit/config.toml   # Theme: SOLON orange + dark blue
├── .github/workflows/       # CI — validates IRR, ITC, EIA rates, Excel
├── FINDINGS.md              # Key findings and model caveats
└── outputs/excel/           # Sample report
```

---

## Run Locally

```bash
git clone https://github.com/Divyadhole/solar-roi-calculator
cd solar-roi-calculator
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py

# Or run the financial model directly
python src/financial_model.py
```
