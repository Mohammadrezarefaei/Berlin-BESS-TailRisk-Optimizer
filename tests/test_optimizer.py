import unittest
import numpy as np
import pandas as pd
import pulp

class TestBESSTailRiskOptimizer(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment and mock data before each test."""
        self.hours = pd.date_range(start="2026-08-28 00:00", periods=24, freq="h")
        self.base_cf = np.array([
            0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.15, 0.30, 0.50, 0.70, 0.85, 0.90,
            0.85, 0.70, 0.50, 0.30, 0.15, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ])
        self.actual_cf = self.base_cf.copy()
        self.actual_cf[11] = 0.06  # Storm shock at hour 11
        
        self.df = pd.DataFrame({
            "Timestamp": self.hours,
            "Scheduled_CF": self.base_cf,
            "Actual_CF": self.actual_cf,
        })
        self.cap_mw = 10.0
        self.df["Scheduled_MW"] = self.df["Scheduled_CF"] * self.cap_mw
        self.df["Actual_MW"] = self.df["Actual_CF"] * self.cap_mw
        self.df["Imbalance_MW"] = self.df["Actual_MW"] - self.df["Scheduled_MW"]
        self.df["Nowcast_Alert"] = False
        self.df.loc[11, "Nowcast_Alert"] = True

    def test_imbalance_calculation(self):
        """Test if the storm shock at hour 11 generates the expected negative imbalance (short position)."""
        expected_imbalance = 0.6 - 9.0  # Actual (0.6 MW) - Scheduled (9.0 MW)
        actual_imbalance = self.df.loc[11, "Imbalance_MW"]
        self.assertAlmostEqual(actual_imbalance, expected_imbalance, places=2)
        self.assertEqual(self.df.loc[11, "Imbalance_MW"], -8.4)

    def test_optimization_dispatch(self):
        """Test if the PuLP optimization successfully mitigates the shortfall at hour 11."""
        prob = pulp.LpProblem("BESS_TailRisk_Optimization", pulp.LpMinimize)
        T = range(24)
        max_p = 10.0
        max_e = 20.0
        initial_soc = 20.0  # Fully charged to force discharge during storm tail-risk
        eta = 0.95

        p_charge = pulp.LpVariable.dicts("P_Charge", T, lowBound=0, upBound=max_p)
        p_discharge = pulp.LpVariable.dicts("P_Discharge", T, lowBound=0, upBound=max_p)
        p_bess = pulp.LpVariable.dicts("P_BESS", T, lowBound=-max_p, upBound=max_p)
        soc = pulp.LpVariable.dicts("SoC", T, lowBound=0, upBound=max_e)

        for t in T:
            prob += p_bess[t] == p_discharge[t] - p_charge[t]

        total_cost = 0
        for t in T:
            net_imb = self.df.loc[t, "Imbalance_MW"] + p_bess[t]
            cost_coeff = 162.0 if self.df.loc[t, "Nowcast_Alert"] else (3730.0 if t == 11 else 50.0)
            total_cost += cost_coeff * net_imb

        prob += total_cost
        prob += soc[0] == initial_soc + (eta * p_charge[0]) - (p_discharge[0] / eta)
        for t in range(1, 24):
            prob += soc[t] == soc[t-1] + (eta * p_charge[t]) - (p_discharge[t] / eta)

        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # Check if optimization solved successfully
        self.assertEqual(pulp.LpStatus[prob.status], "Optimal")
        
        # Check if BESS discharged to cover the 8.4 MW shortfall at hour 11
        bess_action_hour_11 = p_bess[11].varValue
        self.assertGreater(bess_action_hour_11, 8.0, "BESS should discharge to cover the solar drop")

if __name__ == "__main__":
    unittest.main()
