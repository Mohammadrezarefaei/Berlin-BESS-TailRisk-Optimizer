import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pulp

print("⚡ Starting Berlin BESS Tail-Risk Optimizer Pipeline...")

# --- 1. DATA & SIMULATION PIPELINE ---
hours = pd.date_range(start="2026-08-28 00:00", periods=24, freq="H")
base_cf = np.array(
    [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.2,
        0.15,
        0.30,
        0.50,
        0.70,
        0.85,
        0.90,
        0.85,
        0.70,
        0.50,
        0.30,
        0.15,
        0.05,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ]
)
actual_cf = base_cf.copy()
actual_cf[11] = 0.06  # Storm shock at hour 11 (Berlin 50Hertz Zone)

df = pd.DataFrame(
    {
        "Timestamp": hours,
        "Scheduled_CF": base_cf,
        "Actual_CF": actual_cf,
    }
)

cap_mw = 10.0
df["Scheduled_MW"] = df["Scheduled_CF"] * cap_mw
df["Actual_MW"] = df["Actual_CF"] * cap_mw
df["Imbalance_MW"] = df["Actual_MW"] - df["Scheduled_MW"]
df["Nowcast_Alert"] = False
df.loc[11, "Nowcast_Alert"] = True

id_vwap = 162.0  # EUR/MWh (Mitigated via Nowcasting)
rebap_spike = 3730.0  # EUR/MWh (Penalty without Nowcasting)

print("[INFO] Solar generation data & storm shock injected successfully.")

# --- 2. OPTIMIZATION MODEL (PuLP) ---
print("[INFO] Running PuLP Linear Programming Optimization...")
prob = pulp.LpProblem("BESS_TailRisk_Optimization", pulp.LpMinimize)
T = range(24)
max_p = 10.0
max_e = 20.0
initial_soc = 10.0
eta = 0.95

p_charge = pulp.LpVariable.dicts("P_Charge", T, lowBound=0, upBound=max_p)
p_discharge = pulp.LpVariable.dicts("P_Discharge", T, lowBound=0, upBound=max_p)
p_bess = pulp.LpVariable.dicts("P_BESS", T, lowBound=-max_p, upBound=max_p)
soc = pulp.LpVariable.dicts("SoC", T, lowBound=0, upBound=max_e)

for t in T:
  prob += p_bess[t] == p_discharge[t] - p_charge[t]

total_cost = 0
for t in T:
  net_imb = df.loc[t, "Imbalance_MW"] + p_bess[t]
  cost_coeff = (
      id_vwap if df.loc[t, "Nowcast_Alert"] else (rebap_spike if t == 11 else 50.0)
  )
  total_cost += cost_coeff * net_imb

prob += total_cost
prob += soc[0] == initial_soc + (eta * p_charge[0]) - (p_discharge[0] / eta)
for t in range(1, 24):
  prob += soc[t] == soc[t - 1] + (eta * p_charge[t]) - (p_discharge[t] / eta)

prob.solve(pulp.PULP_CBC_CMD(msg=0))

df["BESS_Action_MW"] = [p_bess[t].varValue for t in T]
df["Net_Imbalance_MW"] = df["Imbalance_MW"] + df["BESS_Action_MW"]
df["BESS_SoC_MWh"] = [soc[t].varValue for t in T]

# Financial summary
cost_no_bess = abs(df.loc[11, "Imbalance_MW"]) * rebap_spike
cost_with_bess = abs(df.loc[11, "Net_Imbalance_MW"]) * id_vwap
savings = cost_no_bess - cost_with_bess

print(f"[SUCCESS] Optimization Status: {pulp.LpStatus[prob.status]}")
print(f"[FINANCIAL] Hour 11 Net Savings achieved: €{savings:,.2f}")

# --- 3. DARK THEME VISUALIZATION ---
print("[INFO] Generating dark-theme output visualization...")
plt.style.use("dark_background")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

hours_str = [ts.strftime("%H:00") for ts in df["Timestamp"]]

# Plot 1: Power & Imbalance Mitigation
ax1.plot(
    hours_str,
    df["Actual_MW"],
    label="Actual Solar (MW)",
    color="#2ecc71",
    linewidth=2.5,
)
ax1.plot(
    hours_str,
    df["Scheduled_MW"],
    label="Scheduled Solar (MW)",
    color="#3498db",
    linestyle="--",
    linewidth=2,
)
ax1.bar(
    hours_str,
    df["Imbalance_MW"],
    label="Raw Imbalance (Storm Drop)",
    color="#e74c3c",
    alpha=0.6,
)
ax1.bar(
    hours_str,
    df["BESS_Action_MW"],
    label="BESS Response Action",
    color="#f1c40f",
    alpha=0.8,
)
ax1.plot(
    hours_str,
    df["Net_Imbalance_MW"],
    label="Net Imbalance (Managed)",
    color="#e67e22",
    linewidth=3,
)

ax1.set_title(
    "Berlin 50Hertz Zone: Solar Tail-Risk Mitigation & BESS Dispatch",
    fontsize=14,
    fontweight="bold",
    pad=15,
)
ax1.set_ylabel("Power (MW)", fontsize=12)
ax1.grid(True, linestyle=":", alpha=0.3)
ax1.legend(loc="upper right", framealpha=0.8)

# Plot 2: State of Charge (SoC)
ax2.plot(
    hours_str,
    df["BESS_SoC_MWh"],
    label="BESS SoC (MWh)",
    color="#9b59b6",
    linewidth=3,
)
ax2.fill_between(
    hours_str, df["BESS_SoC_MWh"], color="#9b59b6", alpha=0.2
)
ax2.set_title("Battery State of Charge (SoC) Profile", fontsize=12, pad=10)
ax2.set_xlabel("Time of Day (Aug 28, 2026)", fontsize=12)
ax2.set_ylabel("Energy (MWh)", fontsize=12)
ax2.set_ylim(0, 22)
ax2.grid(True, linestyle=":", alpha=0.3)
ax2.legend(loc="upper right", framealpha=0.8)

plt.xticks(rotation=45)
plt.tight_layout()

# Save output
output_filename = "bess_tail_risk_optimizer.png"
plt.savefig(output_filename, dpi=300)
print(f"[SUCCESS] High-resolution chart saved as '{output_filename}'")
plt.show()
