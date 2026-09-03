# ⚡ Berlin BESS Tail-Risk Optimizer & Solar Nowcasting

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Optimization: PuLP](https://img.shields.io/badge/Optimization-Linear%20Programming-orange.svg)](https://coin-or.github.io/pulp/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20Demo-red.svg)](TBD_STREAMLIT_LINK_HERE)

## 🎯 Project Overview
This repository contains a professional-grade Python pipeline designed to optimize **Battery Energy Storage Systems (BESS)** dispatch within the German **50Hertz control area** (Berlin/Brandenburg region). 

Inspired by real-world market tail-risk events (such as sudden convective storm drops causing reBAP imbalance prices to spike up to **€3,730/MWh**), this project demonstrates how integrating a **15-minute Solar Nowcasting** warning signal with a linear programming optimization engine (`PuLP`) protects solar-plus-storage portfolios from catastrophic imbalance penalties.

---

## 🌐 Live Web Application
Explore the interactive simulation and real-time BESS optimization dashboard:
👉 **[Launch Streamlit Dashboard](TBD_STREAMLIT_LINK_HERE)** *(Coming Soon)*

---

## 📂 Repository Structure
```text
Berlin-BESS-TailRisk-Optimizer/
│
├── data/                    # Historical and scenario solar datasets
│   └── 2026-08-28_berlin_solar.csv
│
├── notebooks/               # Jupyter notebook for interactive exploration
│   └── berlin_bess_tail_risk_optimizer.ipynb
│
├── src/                     # Modular source code
│   └── optimizer.py
│
├── tests/                   # Automated unit tests for pipeline validation
│   └── test_optimizer.py
│
├── outputs/                 # Visual outputs and animated demonstration
│   └── bess_optimization_animated.gif
│
├── app.py                   # Main standalone execution script
├── requirements.txt         # Project dependencies
└── README.md
