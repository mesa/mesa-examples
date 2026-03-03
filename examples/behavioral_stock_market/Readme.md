# 📈 Behavioral Stock Market Model (Mesa)

An Agent-Based Model (ABM) of a behavioral financial market built using Mesa.

This model simulates a stock market composed of heterogeneous trader types:

- Fundamentalist traders
- Trend-following traders (ML-based)
- Risk-averse traders

The model explores how different behavioral strategies affect:

- Price dynamics
- Market volatility
- Wealth distribution
- Strategy dominance

---

## 🧠 Model Description

The market consists of N traders initialized with random capital and share holdings.

Each trader belongs to one of three behavioral classes:

### 1️⃣ Fundamentalist
Trades based on intrinsic value comparison.

### 2️⃣ TrendFollower
Uses a trained machine learning model to predict price movement.

### 3️⃣ RiskAverse
Sells quickly during price drops and buys conservatively.

Market price evolves based on total demand and supply imbalance.

---

## 📊 Features

- Real-time price visualization
- Auto-run simulation
- Strategy wealth comparison
- Highest & lowest wealth tracking per strategy
- ML-integrated trading behavior

---

## 🚀 How to Run

Install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
solara run app.py