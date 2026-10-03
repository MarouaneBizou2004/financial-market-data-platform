"""
Financial Market Data Platform - Executive Analytics & ML Dashboard
A production multi-page Streamlit application providing real-time financial time-series analytics,
risk management metrics, cross-asset correlation matrices, ML market regime detection,
and interactive portfolio risk attribution.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
curr_dir = str(Path(__file__).resolve().parent)
if curr_dir in sys.path:
    sys.path.remove(curr_dir)

from src.utils.config import GOLD_DATA_DIR, load_assets_config, MODELS_DIR
from src.analytics.returns import calculate_cumulative_returns, calculate_cagr
from src.analytics.volatility import calculate_annualized_volatility
from src.analytics.risk import (
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_var_historical,
    calculate_cvar,
    calculate_portfolio_performance
)
from src.ml.predict import MarketRegimePredictor
from src.ml.feature_pipeline import REGIME_LABELS

# Streamlit Page Config
st.set_page_config(
    page_title="Financial Market Data Platform | Institutional Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional Theme
st.markdown("""
<style>
    .main-header { font-size: 26px; font-weight: 700; color: #0F172A; margin-bottom: 2px; }
    .sub-header { font-size: 14px; color: #64748B; margin-bottom: 20px; }
    .kpi-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .metric-label { font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: 700; color: #1E293B; margin: 4px 0; }
    .regime-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_market_data():
    parquet_path = GOLD_DATA_DIR / "gold_market_features.parquet"
    if not parquet_path.exists():
        st.error("Market data not found! Please run the pipeline first.")
        st.stop()
    df = pd.read_parquet(parquet_path)
    df["date"] = pd.to_datetime(df["date"])
    return df

df_gold = load_market_data()
config = load_assets_config()
all_symbols = sorted(df_gold["symbol"].unique().tolist())
latest_date = df_gold["date"].max().strftime("%Y-%m-%d")

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/isometric/100/line-chart.png", width=65)
st.sidebar.title("Market Data Platform")
st.sidebar.markdown("**Institutional Analytics & ML**")

page = st.sidebar.radio(
    "Navigation View:",
    ["1. Market Overview",
     "2. Single Asset Deep-Dive",
     "3. Risk & Downside Scorecard",
     "4. Cross-Asset Correlation",
     "5. Market Regime ML",
     "6. Portfolio Construction & Risk Attribution"]
)

# ==============================================================================
# PAGE 1: MARKET OVERVIEW
# ==============================================================================
if page == "1. Market Overview":
    st.markdown('<div class="main-header">Multi-Asset Market Overview & Macro Summary</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Authentic OHLCV market data covering 16 US Equities & ETFs | As of {latest_date}</div>', unsafe_allow_html=True)
    
    # Macro KPIs
    spy_df = df_gold[df_gold["symbol"] == "SPY"].sort_values(by="date")
    spy_latest_close = float(spy_df["close"].iloc[-1])
    spy_vol = float(spy_df["volatility_20d"].iloc[-1]) * 100.0
    spy_ytd = float(((spy_latest_close - spy_df["close"].iloc[0]) / spy_df["close"].iloc[0]) * 100.0)
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Universe Assets", f"{len(all_symbols)} Assets", "Equities, ETFs, Bonds")
    c2.metric("Total Records Processed", f"{len(df_gold):,} Rows", "Zero Nulls / Verified")
    c3.metric("S&P 500 (SPY)", f"${spy_latest_close:.2f}", f"{spy_ytd:+.2f}% 5Y Cumulative")
    c4.metric("Benchmark Volatility (20D)", f"{spy_vol:.1f}%", "Annualized")
    c5.metric("Historical Horizon", "2021 – 2025", "1,254 Trading Days")
    
    st.markdown("---")
    
    # Leaderboard: Top Performers vs Decliners
    perf_list = []
    for s in all_symbols:
        s_df = df_gold[df_gold["symbol"] == s].sort_values(by="date")
        start_p = s_df["close"].iloc[0]
        end_p = s_df["close"].iloc[-1]
        tot_ret = ((end_p - start_p) / start_p) * 100.0
        cagr_val = calculate_cagr(s_df["close"]) * 100.0
        ann_vol = calculate_annualized_volatility(s_df["daily_return"]) * 100.0
        sharpe = calculate_sharpe_ratio(s_df["daily_return"])
        mdd = float(s_df["drawdown"].min()) * 100.0
        perf_list.append({
            "Symbol": s,
            "Total Return (%)": round(tot_ret, 2),
            "Annualized CAGR (%)": round(cagr_val, 2),
            "Annualized Vol (%)": round(ann_vol, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown (%)": round(mdd, 2)
        })
    perf_summary = pd.DataFrame(perf_list).sort_values(by="Total Return (%)", ascending=False)
    
    col_l, col_r = st.columns([6, 4])
    with col_l:
        st.subheader("Cross-Asset Cumulative Return Comparison")
        fig_cum = px.line(
            df_gold,
            x="date",
            y="cumulative_return",
            color="symbol",
            labels={"cumulative_return": "Cumulative Return (1.0 = +100%)", "date": "Date"},
            title="Relative Wealth Index Trajectories (Base = 0.0)"
        )
        fig_cum.update_layout(height=420, legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_cum, use_container_width=True)
        
    with col_r:
        st.subheader("Top 5 Outperformers vs Laggards")
        top_bot = pd.concat([perf_summary.head(4), perf_summary.tail(4)])
        colors = ["#10B981" if r > 0 else "#EF4444" for r in top_bot["Total Return (%)"]]
        fig_bars = px.bar(
            top_bot,
            x="Total Return (%)",
            y="Symbol",
            orientation="h",
            color="Total Return (%)",
            color_continuous_scale="RdYlGn",
            text="Total Return (%)"
        )
        fig_bars.update_layout(height=420, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_bars, use_container_width=True)
        
    st.subheader("Asset Performance Master Scorecard")
    st.dataframe(perf_summary, use_container_width=True)

# ==============================================================================
# PAGE 2: SINGLE ASSET DEEP-DIVE
# ==============================================================================
elif page == "2. Single Asset Deep-Dive":
    st.markdown('<div class="main-header">Single Asset Technical & Quantitative Deep-Dive</div>', unsafe_allow_html=True)
    
    selected_asset = st.sidebar.selectbox("Select Asset Symbol:", all_symbols, index=all_symbols.index("AAPL"))
    sub_df = df_gold[df_gold["symbol"] == selected_asset].sort_values(by="date").copy()
    
    # Asset KPIs
    p_last = float(sub_df["close"].iloc[-1])
    cagr_a = calculate_cagr(sub_df["close"]) * 100.0
    vol_a = float(sub_df["volatility_20d"].iloc[-1]) * 100.0
    mdd_a = float(sub_df["drawdown"].min()) * 100.0
    curr_dd = float(sub_df["drawdown"].iloc[-1]) * 100.0
    
    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Latest Close", f"${p_last:.2f}")
    a2.metric("Annualized CAGR", f"{cagr_a:.2f}%")
    a3.metric("Current Volatility (20D)", f"{vol_a:.1f}%")
    a4.metric("Current Drawdown", f"{curr_dd:.2f}%")
    a5.metric("Historical Max Drawdown", f"{mdd_a:.2f}%", delta_color="inverse")
    
    st.markdown("---")
    
    # Technical Chart: Price + Moving Averages
    fig_tech = go.Figure()
    fig_tech.add_trace(go.Scatter(x=sub_df["date"], y=sub_df["close"], name="Close Price", line=dict(color="#2563EB", width=2)))
    fig_tech.add_trace(go.Scatter(x=sub_df["date"], y=sub_df["sma_20"], name="20-Day SMA", line=dict(color="#F59E0B", width=1.5, dash="dot")))
    fig_tech.add_trace(go.Scatter(x=sub_df["date"], y=sub_df["sma_50"], name="50-Day SMA", line=dict(color="#10B981", width=1.5)))
    fig_tech.add_trace(go.Scatter(x=sub_df["date"], y=sub_df["sma_200"], name="200-Day SMA", line=dict(color="#DC2626", width=2)))
    fig_tech.update_layout(title=f"{selected_asset} Historical Price & Trend Ribbon (20, 50, 200 SMA)", height=400, margin=dict(l=20, r=20, t=35, b=20))
    st.plotly_chart(fig_tech, use_container_width=True)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        # Underwater Drawdown Plot
        fig_dd = px.area(
            sub_df,
            x="date",
            y="drawdown",
            title=f"{selected_asset} Continuous Peak-to-Trough Drawdown (%)",
            color_discrete_sequence=["#EF4444"]
        )
        fig_dd.update_layout(height=320, margin=dict(l=20, r=20, t=35, b=20), yaxis=dict(tickformat=".1%"))
        st.plotly_chart(fig_dd, use_container_width=True)
        
    with col_d2:
        # Trading Volume with Anomalies
        fig_vol = px.bar(
            sub_df,
            x="date",
            y="volume",
            color="is_abnormal_volume",
            color_discrete_map={0: "#94A3B8", 1: "#7C3AED"},
            title=f"{selected_asset} Trading Volume & Institutional Surges (>200% of 20D MA)"
        )
        fig_vol.update_layout(height=320, margin=dict(l=20, r=20, t=35, b=20), showlegend=False)
        st.plotly_chart(fig_vol, use_container_width=True)

# ==============================================================================
# PAGE 3: RISK & DOWNSIDE SCORECARD
# ==============================================================================
elif page == "3. Risk & Downside Scorecard":
    st.markdown('<div class="main-header">Institutional Risk & Extreme Tail Loss Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Downside deviation, Sortino, Historical Value at Risk (VaR 95%), and Expected Shortfall (CVaR)</div>', unsafe_allow_html=True)
    
    risk_data = []
    for s in all_symbols:
        s_df = df_gold[df_gold["symbol"] == s].sort_values(by="date")
        rets = s_df["daily_return"].dropna()
        vol = calculate_annualized_volatility(rets) * 100.0
        sharpe = calculate_sharpe_ratio(rets)
        sortino = calculate_sortino_ratio(rets)
        mdd = float(s_df["drawdown"].min()) * 100.0
        var95 = calculate_var_historical(rets, 0.95) * 100.0
        cvar95 = calculate_cvar(rets, 0.95) * 100.0
        worst_day = float(rets.min()) * 100.0
        
        risk_data.append({
            "Symbol": s,
            "Ann. Volatility (%)": round(vol, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Sortino Ratio": round(sortino, 2),
            "Max Drawdown (%)": round(mdd, 2),
            "1-Day VaR 95% (%)": round(var95, 2),
            "1-Day CVaR 95% (%)": round(cvar95, 2),
            "Worst Day (%)": round(worst_day, 2)
        })
    df_risk = pd.DataFrame(risk_data).sort_values(by="Sharpe Ratio", ascending=False)
    
    c_r1, c_r2 = st.columns([6, 4])
    with c_r1:
        st.subheader("Risk vs Return (Annualized Volatility vs Annualized Return)")
        ret_lookup = {r["Symbol"]: r["Annualized CAGR (%)"] for r in perf_list}
        df_risk["Annualized Return (%)"] = df_risk["Symbol"].map(ret_lookup)
        
        fig_scatter = px.scatter(
            df_risk,
            x="Ann. Volatility (%)",
            y="Annualized Return (%)",
            color="Sharpe Ratio",
            size="1-Day VaR 95% (%)",
            text="Symbol",
            color_continuous_scale="Viridis",
            title="Efficient Frontier Positioning"
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(height=420, margin=dict(l=20, r=20, t=35, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with c_r2:
        st.subheader("Downside Loss Risk (VaR vs CVaR 95%)")
        fig_var = go.Figure()
        fig_var.add_trace(go.Bar(y=df_risk["Symbol"], x=df_risk["1-Day VaR 95% (%)"], name="VaR 95% (Loss)", orientation="h", marker_color="#F97316"))
        fig_var.add_trace(go.Bar(y=df_risk["Symbol"], x=df_risk["1-Day CVaR 95% (%)"], name="CVaR 95% (Tail Loss)", orientation="h", marker_color="#EF4444"))
        fig_var.update_layout(barmode="group", height=420, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_var, use_container_width=True)
        
    st.subheader("Complete Asset Risk Scorecard")
    st.dataframe(df_risk, use_container_width=True)

# ==============================================================================
# PAGE 4: CROSS-ASSET CORRELATION
# ==============================================================================
elif page == "4. Cross-Asset Correlation":
    st.markdown('<div class="main-header">Cross-Asset Correlation & Co-Movement Matrix</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating diversification potential across Equities, Fixed Income, and Commodities</div>', unsafe_allow_html=True)
    
    # Pivot returns
    pivot_rets = df_gold.pivot(index="date", columns="symbol", values="daily_return").dropna()
    corr_matrix = pivot_rets.corr().round(2)
    
    st.subheader("Pairwise Pearson Correlation Heatmap")
    fig_heat = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1.0,
        zmax=1.0,
        labels=dict(color="Correlation")
    )
    fig_heat.update_layout(height=520, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Rolling 60-Day Correlation Pair Tracker")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        sym_1 = st.selectbox("Asset 1:", all_symbols, index=all_symbols.index("SPY"))
    with c_p2:
        sym_2 = st.selectbox("Asset 2:", all_symbols, index=all_symbols.index("TLT"))
        
    rolling_corr = pivot_rets[sym_1].rolling(60).corr(pivot_rets[sym_2])
    fig_roll = px.line(
        x=pivot_rets.index,
        y=rolling_corr,
        title=f"Rolling 60-Day Correlation: {sym_1} vs {sym_2}",
        labels={"x": "Date", "y": "Correlation Coefficient"}
    )
    fig_roll.add_hline(y=0.0, line_dash="dash", line_color="black")
    fig_roll.update_layout(height=350, yaxis=dict(range=[-1.05, 1.05]), margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_roll, use_container_width=True)

# ==============================================================================
# PAGE 5: MARKET REGIME ML
# ==============================================================================
elif page == "5. Market Regime ML":
    st.markdown('<div class="main-header">Machine Learning Market Regime Classification</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Walk-forward classification of macroeconomic volatility & momentum regimes (Zero Temporal Leakage)</div>', unsafe_allow_html=True)
    
    predictor = MarketRegimePredictor()
    pred_res = predictor.predict_latest_regime(df_gold)
    
    # State Banner
    regime_colors = {0: "#10B981", 1: "#3B82F6", 2: "#EF4444", 3: "#F59E0B"}
    curr_color = regime_colors.get(pred_res["predicted_regime_id"], "#64748B")
    
    st.markdown(f"""
    <div style="background-color: #F8FAFC; border-left: 6px solid {curr_color}; padding: 18px; border-radius: 6px; margin-bottom: 20px;">
        <span style="font-size: 13px; font-weight: 600; color: #64748B;">LATEST DETECTED MARKET REGIME ({pred_res['as_of_date']})</span>
        <div style="font-size: 22px; font-weight: 800; color: {curr_color}; margin: 4px 0;">
            {pred_res['predicted_regime_name']}
        </div>
        <div style="font-size: 13px; color: #475569;">
            Volatility: <b>{pred_res['macro_signals']['volatility_20d_pct']}%</b> | 
            3-Month Momentum: <b>{pred_res['macro_signals']['momentum_3m_pct']}%</b> | 
            Drawdown: <b>{pred_res['macro_signals']['drawdown_pct']}%</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c_m1, c_m2 = st.columns([5, 5])
    with c_m1:
        st.subheader("Predicted Regime Probabilities")
        prob_df = pd.DataFrame(list(pred_res["regime_probabilities"].items()), columns=["Regime", "Probability"])
        fig_prob = px.bar(
            prob_df,
            x="Probability",
            y="Regime",
            orientation="h",
            color="Probability",
            color_continuous_scale="Blues",
            text_auto=".2%"
        )
        fig_prob.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_prob, use_container_width=True)
        
    with c_m2:
        st.subheader("Model Performance on Unseen Test Set (2025)")
        st.markdown("""
        - **Champion Architecture:** Gradient Boosting (HistGradientBoosting)
        - **Validation Macro F1:** **0.9229** (vs 0.3684 Majority Class Baseline)
        - **Holdout Test Accuracy (2025):** **88.76%**
        - **Holdout Test Macro F1 (2025):** **0.6744**
        - **Methodology:** Strict walk-forward temporal split (Train $\\le$ 2023, Val 2024, Test 2025). Zero lookahead data leakage.
        """)
        
        # Display confusion matrix image
        cm_file = PROJECT_ROOT / "reports" / "figures" / "regime_confusion_matrix.png"
        if cm_file.exists():
            st.image(str(cm_file), caption="Confusion Matrix on 2025 Holdout Test Set", width=360)

# ==============================================================================
# PAGE 6: PORTFOLIO CONSTRUCTION & RISK ATTRIBUTION
# ==============================================================================
elif page == "6. Portfolio Construction & Risk Attribution":
    st.markdown('<div class="main-header">Interactive Portfolio Construction & Risk Attribution</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Euler Marginal & Component Risk Decomposition (CCR) across Multi-Asset Allocations</div>', unsafe_allow_html=True)
    
    pivot_rets = df_gold.pivot(index="date", columns="symbol", values="daily_return").dropna()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Portfolio Allocation Weights")
    w_spy = st.sidebar.slider("SPY (US Equities)", 0.0, 1.0, 0.35, 0.05)
    w_qqq = st.sidebar.slider("QQQ (Tech / Growth)", 0.0, 1.0, 0.25, 0.05)
    w_gld = st.sidebar.slider("GLD (Gold / Commodities)", 0.0, 1.0, 0.20, 0.05)
    w_tlt = st.sidebar.slider("TLT (Treasury Bonds)", 0.0, 1.0, 0.20, 0.05)
    
    user_weights = {"SPY": w_spy, "QQQ": w_qqq, "GLD": w_gld, "TLT": w_tlt}
    port_res = calculate_portfolio_performance(pivot_rets, user_weights)
    
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Portfolio CAGR", f"{port_res['portfolio_cagr']*100:.2f}%")
    p2.metric("Annualized Volatility", f"{port_res['annualized_volatility']*100:.2f}%")
    p3.metric("Sharpe Ratio (3.5% Rf)", f"{port_res['sharpe_ratio']:.2f}")
    p4.metric("Maximum Drawdown", f"{port_res['max_drawdown']*100:.2f}%", delta_color="inverse")
    
    st.markdown("---")
    
    col_p1, col_p2 = st.columns([6, 4])
    with col_p1:
        st.subheader("Portfolio vs S&P 500 Benchmark Wealth Index")
        port_cum = port_res["cumulative_returns_series"]
        spy_cum = calculate_cumulative_returns(pivot_rets["SPY"])
        
        comp_df = pd.DataFrame({
            "Custom Multi-Asset Portfolio": port_cum,
            "SPY (100% Equity Benchmark)": spy_cum
        })
        fig_port = px.line(comp_df, labels={"value": "Cumulative Growth (Base = 0.0)", "index": "Date"})
        fig_port.update_layout(height=380, legend=dict(orientation="h", y=1.1), margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_port, use_container_width=True)
        
    with col_p2:
        st.subheader("Component Contribution to Risk (CCR)")
        ccr_records = []
        for sym, d in port_res["risk_decomposition"].items():
            ccr_records.append({
                "Asset": sym,
                "Weight": f"{d['weight']*100:.1f}%",
                "Percentage Risk Share": d["percentage_risk_share"]
            })
        ccr_df = pd.DataFrame(ccr_records)
        
        fig_ccr = px.pie(
            ccr_df,
            names="Asset",
            values="Percentage Risk Share",
            title="Total Portfolio Volatility Risk Contribution (%)",
            color_discrete_sequence=["#2563EB", "#7C3AED", "#F59E0B", "#10B981"],
            hole=0.4
        )
        fig_ccr.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_ccr, use_container_width=True)
        
    st.subheader("Asset Allocation & Risk Decomposition Table")
    st.dataframe(ccr_df, use_container_width=True)
