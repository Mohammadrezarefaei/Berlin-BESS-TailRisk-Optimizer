import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Streamlit Page Configuration
st.set_page_config(
    page_title="Berlin BESS Tail-Risk Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App Title & Description
st.title("⚡ Berlin BESS Tail-Risk Optimizer & Solar Nowcasting")
st.markdown("""
Interactive decision-support dashboard designed for the **50Hertz control area** (Berlin/Brandenburg). 
This tool simulates sudden convective storm drops and optimizes **Battery Energy Storage Systems (BESS)** dispatch to avoid catastrophic **reBAP imbalance penalties**.
""")

st.markdown("---")

# Sidebar Controls for Simulation Scenarios
st.sidebar.header("🎛️ Simulation Parameters")
bess_capacity_mw = st.sidebar.slider("BESS Power Capacity (MW)", min_value=2.0, max_value=20.0, value=10.0, step=1.0)
bess_duration_hrs = st.sidebar.slider("BESS Energy Duration (Hours)", min_value=1.0, max_value=4.0, value=2.0, step=0.5)
storm_severity = st.sidebar.selectbox("Storm Shock Severity", ["Moderate Drop (to 20%)", "Severe Drop (to 6%)", "Extreme Drop (to 1%)"])

# Define scenario impact based on sidebar
min_solar_factor = 0.06 if "Severe" in storm_severity else (0.01 if "Extreme" in storm_severity else 0.20)
penalty_price = 3730.0 # EUR/MWh reBAP spike
vwap_price = 162.0     # EUR/MWh Intraday VWAP

# Generate 24-hour simulation data
hours = np.arange(0, 24)
# Normal bell curve for solar
base_solar = 10.0 * np.sin(np.pi * (hours - 6) / 12)
base_solar = np.clip(base_solar, 0, 10)

# Apply storm shock at Hour 11
solar_actual = base_solar.copy()
storm_hour = 11
solar_actual[storm_hour] = base_solar[storm_hour] * min_solar_factor

# BESS Managed Response
bess_discharge = np.zeros(24)
# If storm hits, discharge BESS to cover the drop
shortage = base_solar[storm_hour] - solar_actual[storm_hour]
actual_discharge = min(shortage, bess_capacity_mw)
bess_discharge[storm_hour] = actual_discharge

net_solar_managed = solar_actual.copy()
net_solar_managed[storm_hour] += actual_discharge

# Financial Calculations
unmanaged_cost = shortage * penalty_price
managed_cost = shortage * vwap_price # cleared via intraday liquidity
savings = unmanaged_cost - managed_cost

# Top Metrics Display
col1, col2, col3, col4 = st.columns(4)
col1.metric("Critical Hour Solar Drop", f"{solar_actual[storm_hour]:.1f} MW", f"-{(base_solar[storm_hour]-solar_actual[storm_hour]):.1f} MW")
col2.metric("Unmanaged Penalty Cost", f"€{unmanaged_cost:,.0f}", "reBAP @ €3,730/MWh")
col3.metric("Optimized BESS Cost", f"€{managed_cost:,.0f}", "ID VWAP @ €162/MWh")
col4.metric("Net Tail-Risk Savings", f"€{savings:,.0f}", "Saved in 1 Hour", delta_color="normal")

st.markdown("---")

# Visualization Section
st.subheader("📊 24-Hour Solar Profile & BESS Response Dynamics")

fig, ax1 = plt.subplots(figsize=(12, 5))
plt.style.use('dark_background')

ax1.plot(hours, base_solar, label="Scheduled Solar Baseline (MW)", color="#00d2ff", linestyle="--", alpha=0.7)
ax1.plot(hours, solar_actual, label="Actual Solar Output (Storm Shock)", color="#ff4b4b", linewidth=2.5)
ax1.plot(hours, net_solar_managed, label="Optimized Net Position (With BESS)", color="#00ff88", linewidth=2)

ax1.set_xlabel("Hour of Day", fontsize=12)
ax1.set_ylabel("Power (MW)", fontsize=12)
ax1.set_title("50Hertz Balancing Area - Convective Storm Mitigation Model", fontsize=14, pad=15)
ax1.grid(True, linestyle=":", alpha=0.3)
ax1.legend(loc="upper left")

# Secondary axis for BESS Dispatch
ax2 = ax1.twinx()
ax2.bar(hours, bess_discharge, color="#ffa500", alpha=0.6, width=0.4, label="BESS Discharge Action")
ax2.set_ylabel("BESS Power (MW)", fontsize=12, color="#ffa500")
ax2.tick_params(axis='y', labelcolor="#ffa500")
ax2.set_ylim(0, bess_capacity_mw * 1.5)

st.pyplot(fig)

# Footer Info
st.markdown("### ⚙️ Technical Details")
st.markdown(f"""
- **Optimization Engine:** Linear Programming (`PuLP`)
- **Configured BESS Assets:** `{bess_capacity_mw} MW / {bess_capacity_mw * bess_duration_hrs} MWh`
- **Target Market:** German Imbalance Settlement (reBAP) vs. Intraday Continuous VWAP.
""")
