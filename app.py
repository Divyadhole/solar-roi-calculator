"""
app.py — Solar Project ROI Calculator
Streamlit app for commercial solar financial analysis.

Matches SOLON JD requirements:
  - IRR, NPV, payback period calculations
  - Excel export for proposal development
  - EIA utility rate data by state
  - NREL solar resource data
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.financial_model import SolarProjectInputs, calculate, format_results
from src.eia_rates import (get_rate_for_state, get_capacity_factor,
                            get_all_states_df, STATE_NAMES, EIA_STATE_RATES_2023)
from src.excel_export import generate_report

st.set_page_config(
    page_title="Solar ROI Calculator",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { background:#f8f9fa; }
    .metric-card {
        background:white;border:1px solid #e0e0e0;border-radius:10px;
        padding:16px 20px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06);
    }
    .metric-val  { font-size:1.9rem;font-weight:700;color:#1B3A5C;font-family:monospace; }
    .metric-lbl  { font-size:11px;color:#666;text-transform:uppercase;letter-spacing:.05em;margin-top:2px; }
    .metric-good { color:#27AE60; }
    .metric-warn { color:#E67E22; }
    .section-hdr { font-size:13px;font-weight:700;color:#1B3A5C;text-transform:uppercase;
                   letter-spacing:.08em;padding:12px 0 6px; }
    #MainMenu{visibility:hidden}footer{visibility:hidden}header{visibility:hidden}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Inputs ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ☀ Solar ROI Calculator")
    st.markdown("*Commercial solar financial analysis*")
    st.markdown("---")

    st.markdown('<div class="section-hdr">📍 Project Location</div>', unsafe_allow_html=True)
    state_options = sorted(STATE_NAMES.items(), key=lambda x: x[1])
    state_labels  = [f"{name} ({code})" for code, name in state_options]
    state_codes   = [code for code, _ in state_options]

    default_idx = state_codes.index("AZ")
    selected_state_label = st.selectbox("State", state_labels, index=default_idx)
    state_code = state_codes[state_labels.index(selected_state_label)]

    eia_rate = get_rate_for_state(state_code)
    nrel_cf  = get_capacity_factor(state_code)

    st.markdown('<div class="section-hdr">⚡ System Parameters</div>', unsafe_allow_html=True)
    system_size = st.number_input("System Size (kW DC)", min_value=10.0,
                                   max_value=5000.0, value=100.0, step=10.0)
    cost_per_w  = st.number_input("Installed Cost ($/W)", min_value=1.50,
                                   max_value=5.00, value=2.80, step=0.05,
                                   help="2024 commercial benchmark: $2.50-$3.20/W (NREL)")

    st.markdown('<div class="section-hdr">💡 Utility Rate</div>', unsafe_allow_html=True)
    st.caption(f"EIA 2023 rate for {state_code}: ${eia_rate:.4f}/kWh")
    elec_rate = st.number_input("Electricity Rate ($/kWh)", min_value=0.05,
                                 max_value=0.60, value=eia_rate, step=0.005,
                                 format="%.4f")
    rate_esc  = st.slider("Annual Rate Escalation (%)", 0.0, 6.0, 2.5, 0.1) / 100

    st.markdown('<div class="section-hdr">☀ Solar Resource</div>', unsafe_allow_html=True)
    st.caption(f"NREL capacity factor for {state_code}: {nrel_cf*100:.1f}%")
    cap_factor = st.slider("Capacity Factor (%)", 10.0, 25.0,
                            nrel_cf * 100, 0.1) / 100

    st.markdown('<div class="section-hdr">💰 Financial</div>', unsafe_allow_html=True)
    discount_rate = st.slider("Discount Rate / WACC (%)", 3.0, 15.0, 7.0, 0.5) / 100
    tax_rate      = st.slider("Corporate Tax Rate (%)", 0.0, 37.0, 21.0, 1.0) / 100
    apply_itc     = st.checkbox("Apply Federal ITC (30%)", value=True)
    apply_macrs   = st.checkbox("Apply MACRS Depreciation", value=True)

    project_year = st.selectbox("Project Year", [2024, 2025, 2026, 2027], index=0)

    st.markdown("---")
    st.caption("Data: EIA Electric Power Monthly · NREL Solar Resource Database · IRS Publication 946")

# ── Run Model ─────────────────────────────────────────────────────────────
inputs = SolarProjectInputs(
    system_size_kw   = system_size,
    cost_per_watt    = cost_per_w,
    capacity_factor  = cap_factor,
    electricity_rate = elec_rate,
    rate_escalation  = rate_esc,
    discount_rate    = discount_rate,
    tax_rate         = tax_rate,
    apply_itc        = apply_itc,
    apply_macrs      = apply_macrs,
    project_year     = project_year,
)
results = calculate(inputs)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown(f"## ☀ Solar ROI — {system_size:.0f} kW Commercial System · {STATE_NAMES.get(state_code, state_code)}")
st.markdown(f"*Installed cost ${inputs.system_size_kw*1000*cost_per_w:,.0f} · EIA rate ${elec_rate:.4f}/kWh · NREL CF {cap_factor*100:.1f}%*")

# ── Headline Metrics ──────────────────────────────────────────────────────
st.markdown("---")
c1,c2,c3,c4,c5,c6 = st.columns(6)

irr_color   = "metric-good" if results.irr > 0.08 else "metric-warn"
npv_color   = "metric-good" if results.npv > 0    else "metric-warn"
pb_color    = "metric-good" if results.simple_payback_yrs < 10 else "metric-warn"

cards = [
    ("IRR",              f"{results.irr*100:.1f}%",         irr_color),
    ("NPV (25-yr)",      f"${results.npv/1000:.0f}K",       npv_color),
    ("Simple Payback",   f"{results.simple_payback_yrs:.1f} yrs", pb_color),
    ("Discounted PBP",   f"{results.discounted_payback_yrs:.1f} yrs", ""),
    ("Year 1 Savings",   f"${results.year1_savings_usd:,.0f}",    "metric-good"),
    ("LCOE",             f"${results.lcoe:.3f}/kWh",              ""),
]
for col, (label, value, color) in zip([c1,c2,c3,c4,c5,c6], cards):
    col.markdown(f"""
    <div class='metric-card'>
        <div class='metric-val {color}'>{value}</div>
        <div class='metric-lbl'>{label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── Main Charts ───────────────────────────────────────────────────────────
col_left, col_right = st.columns([1,1])

with col_left:
    st.markdown("#### 📈 Cumulative Cash Flow")
    df = results.cash_flows
    payback_yr = results.simple_payback_yrs

    fig = go.Figure()
    # Shaded area: before payback (negative)
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["cumulative_cf"],
        fill="tozeroy", fillcolor="rgba(231,76,60,0.1)",
        line=dict(color="#E74C3C", width=2.5),
        name="Cumulative CF",
    ))
    # Payback line
    fig.add_vline(x=payback_yr, line_dash="dash", line_color="#27AE60",
                  annotation_text=f"Payback {payback_yr:.1f}yr",
                  annotation_font_color="#27AE60")
    fig.add_hline(y=0, line_color="#888", line_width=0.8)
    fig.update_layout(
        height=340, margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="white", plot_bgcolor="#fafafa",
        yaxis=dict(tickprefix="$", tickformat=",.0f",
                   showgrid=True, gridcolor="#e8e8e8"),
        xaxis=dict(title="Year", showgrid=False),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("#### 💵 Annual Cash Flows")
    colors = ["#27AE60" if v >= 0 else "#E74C3C"
              for v in df["net_cash_flow"]]
    fig2 = go.Figure(go.Bar(
        x=df["year"], y=df["net_cash_flow"],
        marker_color=colors, opacity=0.85,
    ))
    fig2.update_layout(
        height=340, margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="white", plot_bgcolor="#fafafa",
        yaxis=dict(tickprefix="$", tickformat=",.0f",
                   showgrid=True, gridcolor="#e8e8e8"),
        xaxis=dict(title="Year", showgrid=False),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Cost Breakdown ────────────────────────────────────────────────────────
st.markdown("---")
col3, col4 = st.columns([1,1])

with col3:
    st.markdown("#### 💰 Investment Breakdown")
    labels = ["Net Cost After ITC", "ITC Benefit (30%)", "MACRS Tax Benefit"]
    values = [results.net_cost_after_itc,
              results.itc_amount,
              results.macrs_pv_benefit]
    fig3 = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=["#1B3A5C", "#FF6B35", "#27AE60"],
        hole=0.45, textinfo="label+percent",
        textfont_size=11,
    ))
    fig3.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10),
                        paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("#### ⚡ Annual Savings vs O&M")
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(name="Gross Savings", x=df["year"][::3],
                           y=df["gross_savings"][::3],
                           marker_color="#FF6B35"))
    fig4.add_trace(go.Bar(name="O&M Cost", x=df["year"][::3],
                           y=df["om_cost"][::3],
                           marker_color="#1B3A5C"))
    fig4.update_layout(
        barmode="group", height=300,
        margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="white", plot_bgcolor="#fafafa",
        yaxis=dict(tickprefix="$", tickformat=",.0f",
                   showgrid=True, gridcolor="#e8e8e8"),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── 25-Year Cash Flow Table ───────────────────────────────────────────────
st.markdown("---")
with st.expander("📋 Full 25-Year Cash Flow Table"):
    display = df.copy()
    display["elec_rate"]     = display["elec_rate"].apply(lambda x: f"${x:.4f}")
    display["gross_savings"] = display["gross_savings"].apply(lambda x: f"${x:,.0f}")
    display["om_cost"]       = display["om_cost"].apply(lambda x: f"${x:,.0f}")
    display["net_cash_flow"] = display["net_cash_flow"].apply(lambda x: f"${x:,.0f}")
    display["cumulative_cf"] = display["cumulative_cf"].apply(lambda x: f"${x:,.0f}")
    display["discounted_cf"] = display["discounted_cf"].apply(lambda x: f"${x:,.0f}")
    display["production_kwh"]= display["production_kwh"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(display, use_container_width=True, hide_index=True)

# ── State Comparison ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 🗺️ How Your State Compares — EIA Commercial Rates 2023")
states_df = get_all_states_df()
fig5 = px.choropleth(
    states_df,
    locations="state_code", locationmode="USA-states",
    color="rate_cents_kwh",
    color_continuous_scale=["#27AE60","#F39C12","#E74C3C"],
    scope="usa",
    labels={"rate_cents_kwh":"¢/kWh"},
    hover_data={"state_name":True, "rate_cents_kwh":":.1f", "capacity_factor":":.3f"},
)
fig5.update_layout(
    height=380, margin=dict(t=0,b=0,l=0,r=0),
    paper_bgcolor="white",
    geo=dict(bgcolor="white", showlakes=True, lakecolor="white"),
    coloraxis_colorbar=dict(title="¢/kWh"),
)
# Highlight selected state
highlight = states_df[states_df["state_code"] == state_code]
if len(highlight) > 0:
    st.caption(f"**{STATE_NAMES.get(state_code,'')}:** ${eia_rate:.4f}/kWh "
               f"({eia_rate*100:.1f}¢/kWh) · NREL capacity factor: {nrel_cf*100:.1f}%")
st.plotly_chart(fig5, use_container_width=True)

# ── Excel Export ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 📥 Export Financial Report")
col_dl1, col_dl2 = st.columns([2,3])
with col_dl1:
    if st.button("📊 Generate Excel Report", type="primary", use_container_width=True):
        with st.spinner("Building report..."):
            path = generate_report(inputs, results,
                                   "outputs/excel/solar_analysis.xlsx")
            with open(path, "rb") as f:
                data = f.read()
        st.download_button(
            "⬇️ Download Excel Report",
            data=data,
            file_name=f"solar_roi_{state_code}_{system_size:.0f}kW.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
with col_dl2:
    st.markdown("""
    <div style='background:#EBF5FB;border-left:3px solid #4A90C4;
                padding:10px 14px;border-radius:0 6px 6px 0;font-size:12px;color:#555'>
    Excel report includes: Executive Summary · 25-Year Cash Flow Table · Input Assumptions<br>
    Data sources: <strong>EIA</strong> Electric Power Monthly ·
    <strong>NREL</strong> Solar Resource Database · <strong>IRS</strong> Pub 946
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Built by Divya Dhole · MS Data Science @ UArizona · "
           "[Portfolio](https://divyadhole.github.io) · "
           "[LinkedIn](https://www.linkedin.com/in/divyadhole/)")
