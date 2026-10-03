"""
Risk & Portfolio Analytics Engine
Implements rigorous financial risk metrics and multi-asset portfolio analytics:
- Annualized Volatility
- Sharpe Ratio (excess return over risk-free rate per unit total risk)
- Downside Deviation & Sortino Ratio (excess return per unit downside risk)
- Value at Risk (VaR): Historical & Parametric Gaussian models (95%, 99%)
- Conditional Value at Risk (CVaR / Expected Shortfall)
- Multi-Asset Portfolio Analytics: Portfolio Return, Volatility, Sharpe, Max Drawdown
- Risk Decomposition: Marginal & Percentage Component Contribution to Risk (CCR)
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from scipy import stats

from src.utils.config import TRADING_DAYS_PER_YEAR, ANNUAL_RISK_FREE_RATE

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = ANNUAL_RISK_FREE_RATE,
    trading_days: int = TRADING_DAYS_PER_YEAR
) -> float:
    """
    Computes annualized Sharpe Ratio:
    Sharpe = (mean(R) * 252 - R_f) / (std(R) * sqrt(252))
    """
    clean_r = returns.dropna()
    if len(clean_r) < 2:
        return 0.0
    daily_rf = risk_free_rate / trading_days
    excess_returns = clean_r - daily_rf
    std = clean_r.std()
    if std <= 0 or np.isnan(std):
        return 0.0
    return float(np.sqrt(trading_days) * (excess_returns.mean() / std))

def calculate_downside_deviation(
    returns: pd.Series,
    mar: float = 0.0,
    trading_days: int = TRADING_DAYS_PER_YEAR
) -> float:
    """
    Computes annualized Downside Deviation below Minimum Acceptable Return (MAR):
    sigma_d = sqrt( 252 / N * sum( min(0, R_t - MAR)^2 ) )
    """
    clean_r = returns.dropna()
    if len(clean_r) < 2:
        return 0.0
    downside_diff = np.minimum(clean_r - mar, 0.0)
    downside_variance = np.mean(downside_diff ** 2)
    return float(np.sqrt(downside_variance * trading_days))

def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = ANNUAL_RISK_FREE_RATE,
    trading_days: int = TRADING_DAYS_PER_YEAR
) -> float:
    """
    Computes annualized Sortino Ratio:
    Sortino = (mean(R) * 252 - R_f) / Downside_Deviation
    """
    clean_r = returns.dropna()
    if len(clean_r) < 2:
        return 0.0
    daily_rf = risk_free_rate / trading_days
    annual_excess = (clean_r.mean() * trading_days) - risk_free_rate
    downside_dev = calculate_downside_deviation(clean_r, mar=daily_rf, trading_days=trading_days)
    if downside_dev <= 0 or np.isnan(downside_dev):
        return 0.0
    return float(annual_excess / downside_dev)

def calculate_var_historical(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Computes 1-day Historical Value at Risk (VaR) as a positive loss percentage.
    VaR_{alpha} = - percentile(R, 1 - alpha)
    """
    clean_r = returns.dropna()
    if len(clean_r) < 10:
        return 0.0
    percentile = (1.0 - confidence_level) * 100.0
    cutoff = np.percentile(clean_r, percentile)
    return float(abs(cutoff))

def calculate_var_parametric(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Computes 1-day Parametric Gaussian Value at Risk (VaR):
    VaR_{alpha} = - (mu - z_{alpha} * sigma)
    """
    clean_r = returns.dropna()
    if len(clean_r) < 10:
        return 0.0
    mu = clean_r.mean()
    sigma = clean_r.std()
    z = stats.norm.ppf(confidence_level)
    return float(abs(mu - z * sigma))

def calculate_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Computes Conditional Value at Risk (CVaR / Expected Shortfall):
    CVaR_{alpha} = - E[ R | R <= - VaR_{alpha} ]
    Represents the expected loss in the worst (1 - alpha)% tail events.
    """
    clean_r = returns.dropna()
    if len(clean_r) < 10:
        return 0.0
    percentile = (1.0 - confidence_level) * 100.0
    cutoff = np.percentile(clean_r, percentile)
    tail_losses = clean_r[clean_r <= cutoff]
    if tail_losses.empty:
        return float(abs(cutoff))
    return float(abs(tail_losses.mean()))

# ==============================================================================
# Multi-Asset Portfolio Analytics
# ==============================================================================

def calculate_portfolio_performance(
    returns_df: pd.DataFrame,
    weights: Dict[str, float],
    risk_free_rate: float = ANNUAL_RISK_FREE_RATE
) -> Dict[str, Any]:
    """
    Calculates comprehensive multi-asset portfolio risk and performance metrics.
    Ensures weights are normalized to sum to 1.0.
    """
    # Filter to matching columns
    active_symbols = [s for s in weights.keys() if s in returns_df.columns]
    raw_weights = np.array([weights[s] for s in active_symbols])
    normalized_weights = raw_weights / np.sum(raw_weights)
    
    sub_returns = returns_df[active_symbols].dropna()
    
    # Portfolio daily returns series
    port_daily_ret = sub_returns.dot(normalized_weights)
    
    # Cumulative return
    port_cum_ret = (1.0 + port_daily_ret).cumprod() - 1.0
    total_return = float(port_cum_ret.iloc[-1]) if not port_cum_ret.empty else 0.0
    
    # Annualized CAGR
    cagr = float(((1.0 + total_return) ** (TRADING_DAYS_PER_YEAR / len(port_daily_ret))) - 1.0) if len(port_daily_ret) > 1 else 0.0
    
    # Annualized Volatility
    port_vol = float(port_daily_ret.std() * np.sqrt(TRADING_DAYS_PER_YEAR))
    
    # Sharpe & Sortino
    sharpe = calculate_sharpe_ratio(port_daily_ret, risk_free_rate)
    sortino = calculate_sortino_ratio(port_daily_ret, risk_free_rate)
    
    # Maximum Drawdown
    running_max = (1.0 + port_cum_ret).cummax()
    dd_series = ((1.0 + port_cum_ret) - running_max) / running_max
    max_dd = float(dd_series.min())
    
    # VaR & CVaR (95%)
    var_95 = calculate_var_historical(port_daily_ret, 0.95)
    cvar_95 = calculate_cvar(port_daily_ret, 0.95)
    
    # Risk Decomposition: Component Contribution to Risk (CCR)
    cov_matrix = sub_returns.cov() * TRADING_DAYS_PER_YEAR
    port_variance = normalized_weights.T.dot(cov_matrix).dot(normalized_weights)
    port_sd = np.sqrt(port_variance)
    
    # Marginal Contribution to Risk: d(sigma_p)/dw_i = (Cov * w) / sigma_p
    marginal_contrib = cov_matrix.dot(normalized_weights) / port_sd
    
    # Component Contribution to Risk: CCR_i = w_i * MCR_i
    component_contrib = normalized_weights * marginal_contrib
    percentage_contrib = (component_contrib / port_sd) * 100.0
    
    risk_breakdown = {}
    for i, sym in enumerate(active_symbols):
        risk_breakdown[sym] = {
            "weight": round(float(normalized_weights[i]), 4),
            "marginal_risk": round(float(marginal_contrib.iloc[i]), 4),
            "component_risk": round(float(component_contrib.iloc[i]), 4),
            "percentage_risk_share": round(float(percentage_contrib.iloc[i]), 2)
        }
        
    return {
        "portfolio_cagr": round(cagr, 4),
        "total_cumulative_return": round(total_return, 4),
        "annualized_volatility": round(port_vol, 4),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "max_drawdown": round(max_dd, 4),
        "var_95_daily": round(var_95, 4),
        "cvar_95_daily": round(cvar_95, 4),
        "risk_decomposition": risk_breakdown,
        "daily_returns_series": port_daily_ret,
        "cumulative_returns_series": port_cum_ret
    }
