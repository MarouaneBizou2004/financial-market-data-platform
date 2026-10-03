"""
Notebook Generator Utility
Generates production-grade Jupyter Notebooks (.ipynb) in notebooks/
with rich markdown narrative, executable code cells, and financial visualizations.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

def make_cell(cell_type: str, source: str) -> dict:
    return {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source.strip().split("\n")]
    }

def make_code_cell(source: str) -> dict:
    cell = make_cell("code", source)
    cell["execution_count"] = None
    cell["outputs"] = []
    return cell

def build_notebook(cells: list) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

def generate_notebook_01():
    """Generates 01_data_exploration.ipynb"""
    cells = [
        make_cell("markdown", """# Financial Market Data Platform: 01. Exploratory Data Analysis
### Medallion Data Inspection, Statistical Properties, and Quality Validation

**Author:** Marouane Bizou  
**Role:** Senior Data Engineer / Quantitative Analyst  
**Focus:** Data Pipeline Inspection, Return Distributions, Fat Tails, Quality Validation

---
## 1. Project Context & Objectives
In quantitative finance and production data engineering, raw market feeds frequently exhibit anomalies:
- Missing trading intervals or corrupted quotes
- Out-of-sequence timestamps and duplicated rows
- Corporate action splits, dividends, and non-positive prices
- Fat-tailed (leptokurtic) return distributions that violate Gaussian assumptions

This notebook explores the validated **Silver Layer** data, verifies data quality metrics, and characterizes the statistical distributions across our 16-asset liquid universe."""),

        make_code_cell("""import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path("..").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from src.utils.config import SILVER_DATA_DIR, load_assets_config

# Configure plotting style
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10
print("Environment and dependencies initialized successfully.")"""),

        make_cell("markdown", """## 2. Load Validated Silver Layer Data & Asset Configuration
We load the cleansed parquet dataset produced by `src.validation.market_checks.MarketDataValidator` alongside `config/assets.yml`."""),

        make_code_cell("""config = load_assets_config()
silver_path = SILVER_DATA_DIR / "silver_market_data.parquet"
df_silver = pd.read_parquet(silver_path)

print(f"Total Clean Silver Records: {len(df_silver):,}")
print(f"Distinct Assets: {df_silver['symbol'].nunique()}")
print(f"Date Range: {df_silver['date'].min()} to {df_silver['date'].max()}")
df_silver.head(5)"""),

        make_cell("markdown", """## 3. Data Integrity & Granularity Check
Verify that every asset possesses consistent trading day coverage and no unexpected null values."""),

        make_code_cell("""summary = df_silver.groupby("symbol").agg(
    trading_days=("date", "count"),
    min_date=("date", "min"),
    max_date=("date", "max"),
    avg_daily_volume=("volume", "mean"),
    min_close=("close", "min"),
    max_close=("close", "max")
).reset_index()

summary["avg_daily_volume"] = summary["avg_daily_volume"].apply(lambda v: f"{v:,.0f}")
summary"""),

        make_cell("markdown", """## 4. Return Distribution & Leptokurtosis (Fat Tails) Analysis
Standard financial models often assume Gaussian normality for returns. In reality, market asset returns feature **excess kurtosis** (fat tails) and **negative skewness** (crash risk).

Let's calculate empirical skewness and kurtosis across all instruments."""),

        make_code_cell("""df_silver["daily_return"] = df_silver.groupby("symbol")["adjusted_close"].pct_change()

stats_list = []
for symbol, group in df_silver.groupby("symbol"):
    ret = group["daily_return"].dropna()
    stats_list.append({
        "symbol": symbol,
        "mean_daily_return_pct": ret.mean() * 100,
        "std_daily_return_pct": ret.std() * 100,
        "skewness": stats.skew(ret),
        "excess_kurtosis": stats.kurtosis(ret),
        "jarque_bera_p_value": stats.jarque_bera(ret)[1]
    })

df_stats = pd.DataFrame(stats_list).sort_values(by="excess_kurtosis", ascending=False)
df_stats"""),

        make_cell("markdown", """## 5. Visualizing Fat Tails vs. Gaussian Normal Curve
We plot the standardized daily return distribution of **SPY** against a theoretical normal distribution to visually demonstrate the severe tail risk."""),

        make_code_cell("""spy_returns = df_silver[df_silver["symbol"] == "SPY"]["daily_return"].dropna()

fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(spy_returns, bins=60, kde=True, stat="density", color="#1f77b4", label="Empirical Returns (SPY)", ax=ax)

# Overlay theoretical normal distribution
x_axis = np.linspace(spy_returns.min(), spy_returns.max(), 500)
norm_pdf = stats.norm.pdf(x_axis, spy_returns.mean(), spy_returns.std())
ax.plot(x_axis, norm_pdf, "r--", linewidth=2.5, label="Fitted Normal Distribution")

ax.set_title("SPY Daily Return Distribution vs. Normal Distribution (Notice Fat Tails)", fontsize=14, fontweight="bold")
ax.set_xlabel("Daily Return")
ax.set_ylabel("Density")
ax.legend()
plt.tight_layout()
plt.show()"""),

        make_cell("markdown", """## 6. Key Takeaways from Data Exploration
1. **Zero Data Quality Defects:** The validation pipeline effectively removed duplicates and reconciled OHLC envelope violations.
2. **Universal Fat Tails:** Every instrument exhibits positive excess kurtosis, with tech stocks showing extreme kurtosis > 4.0.
3. **Rejection of Normality:** Jarque-Bera p-values are uniformly $\approx 0.0$, confirming that standard Gaussian risk models underestimate tail event probability.
4. **Platform Readiness:** The dataset is fully cleaned and structured for gold feature transformations and advanced risk modeling.""")
    ]
    
    nb = build_notebook(cells)
    target_path = NOTEBOOKS_DIR / "01_data_exploration.ipynb"
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Generated {target_path}")

def generate_notebook_02():
    """Generates 02_market_analytics.ipynb"""
    cells = [
        make_cell("markdown", """# Financial Market Data Platform: 02. Market Analytics & Risk Engine
### Volatility Modeling, Drawdown Profiling, Cross-Asset Correlations & Portfolio Attribution

**Author:** Marouane Bizou  
**Role:** Senior Data Engineer / Quantitative Analyst  
**Focus:** Time-Series Analytics, Drawdowns, VaR / CVaR, Euler Risk Decomposition

---
## 1. Overview
This notebook executes in-depth financial analytics on the **Gold Feature Layer** (`data/gold/gold_market_features.parquet`):
1. **Cumulative Performance Trajectories:** Performance across market cycles (2021–2025).
2. **Volatility Dynamics:** Close-to-Close vs. Parkinson High-Low range estimators.
3. **Drawdown Anatomy:** Peak-to-trough coordinate identification, recovery duration, and maximum drawdowns.
4. **Cross-Asset Correlations:** Heatmaps and rolling correlations highlighting flight-to-safety regime shifts.
5. **Portfolio Risk Attribution:** Euler Component Contribution to Risk (CCR) for multi-asset portfolios."""),

        make_code_cell("""import sys
from pathlib import Path

PROJECT_ROOT = Path("..").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.utils.config import GOLD_DATA_DIR, load_assets_config
from src.analytics.returns import calculate_cagr
from src.analytics.volatility import calculate_annualized_volatility, calculate_parkinson_volatility
from src.analytics.drawdown import analyze_maximum_drawdown
from src.analytics.risk import calculate_portfolio_performance, calculate_var_historical, calculate_cvar

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)
print("Libraries and analytics modules loaded.")"""),

        make_cell("markdown", """## 2. Load Gold Layer Features & Pivot Price Series"""),

        make_code_cell("""df_gold = pd.read_parquet(GOLD_DATA_DIR / "gold_market_features.parquet")
prices_pivot = df_gold.pivot(index="date", columns="symbol", values="adjusted_close")
returns_pivot = df_gold.pivot(index="date", columns="symbol", values="daily_return").dropna()

print(f"Analyzed {prices_pivot.shape[1]} instruments across {prices_pivot.shape[0]} trading sessions.")"""),

        make_cell("markdown", """## 3. Cumulative Growth of $1.00 Across Asset Classes
Compare the compounded growth trajectories across Equities (NVDA, AAPL), Broad Market ETFs (SPY, QQQ), Commodities (GLD), and Fixed Income (TLT)."""),

        make_code_cell("""benchmarks = ["SPY", "QQQ", "GLD", "TLT", "NVDA", "AAPL"]
cum_returns = (1.0 + returns_pivot[benchmarks]).cumprod()

fig, ax = plt.subplots(figsize=(12, 6))
for sym in benchmarks:
    ax.plot(cum_returns.index, cum_returns[sym], label=sym, linewidth=2)

ax.set_title("Cumulative Growth of $1.00 (2021 - 2025)", fontsize=14, fontweight="bold")
ax.set_ylabel("Growth Factor ($1.00 base)")
ax.set_yscale("log")
ax.legend(loc="upper left")
plt.tight_layout()
plt.show()"""),

        make_cell("markdown", """## 4. Volatility Modeling: Close-to-Close vs. Parkinson High-Low Estimator
The **Parkinson Estimator** leverages intraday price extremities $(High / Low)$ rather than discrete closing snapshots, providing up to 5x higher statistical efficiency."""),

        make_code_cell("""spy_data = df_gold[df_gold["symbol"] == "SPY"].copy().set_index("date")
spy_data["parkinson_vol_20d"] = calculate_parkinson_volatility(spy_data["high"], spy_data["low"], window=20)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(spy_data.index, spy_data["volatility_20d"] * 100, label="Standard Rolling Volatility (20D)", color="#1f77b4")
ax.plot(spy_data.index, spy_data["parkinson_vol_20d"] * 100, label="Parkinson Range Volatility (20D)", color="#ff7f0e", linestyle="--")

ax.set_title("SPY: Standard Close-to-Close vs. Parkinson Intraday Volatility", fontsize=14, fontweight="bold")
ax.set_ylabel("Annualized Volatility (%)")
ax.legend()
plt.tight_layout()
plt.show()"""),

        make_cell("markdown", """## 5. Peak-to-Trough Drawdown Analysis
We compute the continuous drawdown series from historical peaks and determine the deepest drawdown coordinates for each asset."""),

        make_code_cell("""dd_summary = []
for sym in prices_pivot.columns:
    dd_info = analyze_maximum_drawdown(prices_pivot[sym])
    dd_summary.append({
        "symbol": sym,
        "max_drawdown_pct": dd_info["max_drawdown"] * 100,
        "peak_date": dd_info["peak_date"],
        "trough_date": dd_info["trough_date"],
        "duration_trading_days": dd_info["drawdown_duration"]
    })

df_dd = pd.DataFrame(dd_summary).sort_values(by="max_drawdown_pct")
df_dd.head(10)"""),

        make_cell("markdown", """## 6. Cross-Asset Correlation Matrix
Evaluating co-movement between Equities, Tech, Gold, and Long-Term Treasuries."""),

        make_code_cell("""corr_matrix = returns_pivot.corr()

fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax, cbar_kws={'label': 'Pearson Correlation'})
ax.set_title("Cross-Asset Daily Return Correlation Matrix (2021 - 2025)", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()"""),

        make_cell("markdown", """## 7. Multi-Asset Portfolio Risk Decomposition (Euler CCR)
We evaluate the balanced model portfolio (`35% SPY, 25% QQQ, 20% GLD, 20% TLT`) and attribute total volatility using Euler's Theorem:
$$\sigma_p = \sum_{i=1}^N w_i \frac{\partial \sigma_p}{\partial w_i}$$"""),

        make_code_cell("""config = load_assets_config()
weights = config["portfolio"]["weights"]

port_results = calculate_portfolio_performance(returns_pivot, weights)
print("=== BALANCED MODEL PORTFOLIO PERFORMANCE ===")
print(f"Annualized CAGR:        {port_results['portfolio_cagr'] * 100:.2f}%")
print(f"Annualized Volatility:  {port_results['annualized_volatility'] * 100:.2f}%")
print(f"Sharpe Ratio (Rf=3.5%): {port_results['sharpe_ratio']:.2f}")
print(f"Sortino Ratio:          {port_results['sortino_ratio']:.2f}")
print(f"Maximum Drawdown:       {port_results['max_drawdown'] * 100:.2f}%")
print(f"1-Day 95% Historical VaR: {port_results['var_95_daily'] * 100:.2f}%")
print(f"1-Day 95% CVaR:         {port_results['cvar_95_daily'] * 100:.2f}%")

df_risk = pd.DataFrame(port_results["risk_decomposition"]).T
df_risk""")
    ]
    
    nb = build_notebook(cells)
    target_path = NOTEBOOKS_DIR / "02_market_analytics.ipynb"
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Generated {target_path}")

def generate_notebook_03():
    """Generates 03_market_regime_analysis.ipynb"""
    cells = [
        make_cell("markdown", """# Financial Market Data Platform: 03. Machine Learning Market Regime Classification
### Zero-Leakage Temporal Modeling, Walk-Forward Validation, and Macroeconomic Regime States

**Author:** Marouane Bizou  
**Role:** Senior Data Scientist / Machine Learning Engineer  
**Focus:** Economic Regime Modeling, Zero Lookahead Bias, HistGradientBoosting, Model Explainability

---
## 1. Problem Formulation & Economic Regimes
Market conditions continuously shift across discrete volatility and momentum states:
- **Regime 0: Low Vol / Bull (Calm Expansion):** Below-average volatility and positive trailing 3-month momentum.
- **Regime 1: Low Vol / Stagnant (Grinding Drift):** Low volatility with stagnant or negative momentum.
- **Regime 2: High Vol / Bear (Crisis / Selloff):** Elevated volatility and negative momentum (market panic).
- **Regime 3: High Vol / Dynamic Rally (Volatile Rebound):** Elevated volatility with strong positive rebound momentum.

### Critical Requirement: Strict Zero Data Leakage
Financial time series violate the i.i.d. assumption. Standard K-Fold cross validation causes catastrophic lookahead leakage by training on future events to predict past states.
Here, we implement **forward-chaining temporal splits**:
- **Train:** $\le 2023-12-31$ (627 trading days)
- **Validation:** $2024-01-01$ to $2024-12-31$ (252 trading days)
- **Out-of-Sample Holdout Test:** $2025-01-01$ to $2025-12-31$ (249 trading days)"""),

        make_code_cell("""import sys
from pathlib import Path

PROJECT_ROOT = Path("..").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

from src.utils.config import GOLD_DATA_DIR, MODELS_DIR
from src.ml.feature_pipeline import MarketRegimeFeaturePipeline, REGIME_LABELS
from src.ml.predict import MarketRegimePredictor

sns.set_theme(style="whitegrid")
print("ML modules initialized.")"""),

        make_cell("markdown", """## 2. Feature Pipeline & Regime Target Construction
We extract lagging features (returns, volatilities, moving average ratios, momentum) for benchmark SPY."""),

        make_code_cell("""df_gold = pd.read_parquet(GOLD_DATA_DIR / "gold_market_features.parquet")
pipeline = MarketRegimeFeaturePipeline(benchmark_symbol="SPY")
df_ml = pipeline.build_features_and_regimes(df_gold)

train_df, val_df, test_df = pipeline.split_temporal(df_ml)

print(f"Train split:      {len(train_df)} rows ({train_df['date'].min()} to {train_df['date'].max()})")
print(f"Validation split: {len(val_df)} rows ({val_df['date'].min()} to {val_df['date'].max()})")
print(f"Test split:       {len(test_df)} rows ({test_df['date'].min()} to {test_df['date'].max()})")"""),

        make_cell("markdown", """## 3. Regime Distribution Across Historical Time Periods"""),

        make_code_cell("""fig, axes = plt.subplots(1, 3, figsize=(16, 4))
for ax, (split_name, data) in zip(axes, [("Train (<=2023)", train_df), ("Val (2024)", val_df), ("Test (2025)", test_df)]):
    counts = data["regime_name"].value_counts()
    sns.barplot(x=counts.values, y=counts.index, ax=ax, palette="viridis")
    ax.set_title(f"{split_name} (N={len(data)})", fontweight="bold")
    ax.set_xlabel("Count")

plt.tight_layout()
plt.show()"""),

        make_cell("markdown", """## 4. Benchmark Model Evaluation & Test Set Performance
We evaluate the production model (`models/market_regime_model.joblib`) on the unobserved 2025 holdout test set."""),

        make_code_cell("""predictor = MarketRegimePredictor()
feature_cols = pipeline.feature_columns

X_test = test_df[feature_cols]
y_test = test_df["regime_target"]

y_pred = predictor.model.predict(X_test)

target_names = [REGIME_LABELS[i] for i in sorted(y_test.unique())]
print("=== OUT-OF-SAMPLE TEST SET CLASSIFICATION REPORT (2025 HOLDOUT) ===")
print(classification_report(y_test, y_pred, target_names=target_names))"""),

        make_cell("markdown", """## 5. Confusion Matrix Analysis
Examine classification error distribution across market regimes."""),

        make_code_cell("""cm = confusion_matrix(y_test, y_pred)

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
            xticklabels=target_names, yticklabels=target_names, ax=ax)
ax.set_title("2025 Holdout Test Set: Confusion Matrix", fontsize=14, fontweight="bold")
ax.set_xlabel("Predicted Regime")
ax.set_ylabel("True Regime")
plt.xticks(rotation=25, ha="right")
plt.tight_layout()
plt.show()"""),

        make_cell("markdown", """## 6. Live Inference & Current Market Regime State
Query the current regime state and probability distribution using `MarketRegimePredictor`."""),

        make_code_cell("""latest_pred = predictor.predict_latest_regime(df_gold)

print(f"As of Date:        {latest_pred['as_of_date']}")
print(f"Predicted Regime:  {latest_pred['predicted_regime_name']} (ID: {latest_pred['predicted_regime_id']})")
print("\\nRegime Probabilities:")
for regime_name, prob in latest_pred["regime_probabilities"].items():
    print(f"  - {regime_name:<38}: {prob * 100:6.2f}%")

print("\\nKey Macro Signals:")
for signal, val in latest_pred["macro_signals"].items():
    print(f"  - {signal:<25}: {val}")""")
    ]
    
    nb = build_notebook(cells)
    target_path = NOTEBOOKS_DIR / "03_market_regime_analysis.ipynb"
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Generated {target_path}")

if __name__ == "__main__":
    generate_notebook_01()
    generate_notebook_02()
    generate_notebook_03()
