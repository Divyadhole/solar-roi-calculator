# Solar Project ROI Calculator

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20App-FF6B35?logo=streamlit)](https://divyadhole.github.io/solar-roi-calculator/)
[![Data](https://img.shields.io/badge/EIA-Commercial%20Rates%202023-orange)](https://www.eia.gov/opendata/)
[![NREL](https://img.shields.io/badge/NREL-Solar%20Resource-yellow)](https://developer.nrel.gov/)

## Live App

**[solar-roi-calculator.streamlit.app](https://divyadhole.github.io/solar-roi-calculator/)**

Select a state → auto-fills the real EIA utility rate and NREL capacity factor → get full financial analysis in seconds.

---

## What It Does

Enter a commercial building's system size and the tool calculates:

- **IRR** — Internal Rate of Return (scipy brentq solver)
- **NPV** — Net Present Value over 25 years
- **Simple and discounted payback period**
- **LCOE** — Levelized Cost of Energy ($/kWh)
- **Year 1 and lifetime savings**
- **25-year cash flow stream** with degradation and rate escalation
- **Excel report** — formatted 3-sheet workbook ready for proposals

All with real utility rate data from EIA and solar resource data from NREL. Not made-up numbers.

---

## The Numbers (100kW commercial, Tucson AZ)

| Metric | Value |
|---|---|
| Installed cost | $280,000 |
| Federal ITC (30%) | -$84,000 |
| Net cost | $196,000 |
| IRR | **12.7%** |
| NPV | **$147,000** |
| Simple payback | **7.3 years** |
| Year 1 savings | $20,157 |
| Lifetime savings | $644,597 |

---

## Incentives Modeled

**Federal ITC (Investment Tax Credit)**
30% through 2032 per the Inflation Reduction Act (IRA 2022).
Scheduled step-down to 26% in 2033, 22% in 2034.

**MACRS 5-Year Accelerated Depreciation**
IRS Publication 946. Half-year convention: 20%, 32%, 19.2%, 11.52%, 11.52%, 5.76%.
ITC reduces MACRS basis by 50%. At 21% corporate tax rate, this adds meaningful NPV.

---

## Data Sources

**EIA Commercial Electricity Rates**
All 50 states — 2023 actuals from EIA Electric Power Monthly, Table 5.6.B.
```
https://api.eia.gov/v2/electricity/retail-sales/data/
```
Live API fetch with embedded fallback for offline use.

**NREL Solar Resource**
State-level annual capacity factors from NREL 10km Solar Resource Database.
```
https://developer.nrel.gov/api/solar/
```

---

## Sensitivity Analysis

The `src/sensitivity.py` module generates:
- 2D IRR table: electricity rate vs cost per watt
- 2D NPV table: electricity rate vs WACC
- Tornado chart: which input has the biggest impact on IRR

On a 100kW Arizona system, electricity rate and capacity factor each swing IRR ±5.6pp. System cost swings it ±5.3pp. O&M matters least (±0.4pp).

---

## Run Locally

```bash
git clone https://github.com/Divyadhole/solar-roi-calculator
cd solar-roi-calculator
pip install -r requirements.txt
streamlit run app.py
```

---

## Project Layout

```
solar-roi-calculator/
├── src/
│   ├── financial_model.py   # IRR, NPV, payback, MACRS, 25yr cashflows
│   ├── eia_rates.py         # EIA commercial rates all 50 states
│   ├── sensitivity.py       # Sensitivity tables + tornado chart
│   └── excel_export.py      # 3-sheet Excel proposal report
├── app.py                   # Streamlit app
├── .streamlit/config.toml   # Theme config
└── outputs/excel/           # Sample report
```

---

*Built by Divya Dhole · MS Data Science @ UArizona · [divyadhole.github.io](https://divyadhole.github.io) · [LinkedIn](https://www.linkedin.com/in/divyadhole/)*
