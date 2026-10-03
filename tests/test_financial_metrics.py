"""
Automated Unit Tests: Financial Analytics & Risk Engine
"""

import pytest
import pandas as pd
import numpy as np
from src.analytics.returns import (
    calculate_daily_returns,
    calculate_cumulative_returns,
    calculate_cagr
)
from src.analytics.volatility import (
    calculate_annualized_volatility,
    calculate_parkinson_volatility
)
from src.analytics.drawdown import (
    compute_drawdown_series,
    analyze_maximum_drawdown
)
from src.analytics.risk import (
    calculate_sharpe_ratio,
    calculate_downside_deviation,
    calculate_sortino_ratio,
    calculate_var_historical,
    calculate_var_parametric,
    calculate_cvar,
    calculate_portfolio_performance
)
from src.analytics.momentum import compute_asset_momentum
from src.analytics.correlation import compute_correlation_matrix

def test_daily_and_cumulative_returns():
    """Verify daily return calculation and cumulative compounding."""
    prices = pd.Series([100.0, 110.0, 99.0, 108.9])
    daily_ret = calculate_daily_returns(prices)
    
    assert np.isnan(daily_ret.iloc[0])
    assert abs(daily_ret.iloc[1] - 0.10) < 1e-5
    assert abs(daily_ret.iloc[2] - (-0.10)) < 1e-5
    assert abs(daily_ret.iloc[3] - 0.10) < 1e-5
    
    cum_ret = calculate_cumulative_returns(daily_ret)
    assert abs(cum_ret.iloc[-1] - 0.089) < 1e-4

def test_cagr():
    """Verify CAGR calculation over exact periods."""
    # Doubling price over 252 days = 100% CAGR
    prices = pd.Series([100.0] + [150.0] * 250 + [200.0])
    cagr = calculate_cagr(prices, periods_per_year=252)
    assert abs(cagr - 1.0) < 1e-2

def test_annualized_volatility():
    """Verify annualized standard deviation scaling."""
    daily_std = 0.01
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, daily_std, 10000))
    ann_vol = calculate_annualized_volatility(returns, trading_days=252)
    expected_vol = daily_std * np.sqrt(252)
    assert abs(ann_vol - expected_vol) < 0.01

def test_maximum_drawdown_exact():
    """Verify exact peak, trough, and MDD identification."""
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    prices = pd.Series([100.0, 120.0, 90.0, 110.0, 80.0], index=dates)
    
    dd_result = analyze_maximum_drawdown(prices)
    # Trough is 80.0 from peak 120.0 => (80 - 120) / 120 = -40 / 120 = -0.3333
    assert abs(dd_result["max_drawdown"] - (-0.3333)) < 1e-3
    assert dd_result["peak_date"] == str(dates[1])
    assert dd_result["trough_date"] == str(dates[4])

def test_sharpe_ratio():
    """Verify Sharpe ratio behavior."""
    # Consistent positive returns with low vol -> high Sharpe
    returns = pd.Series([0.005] * 252)
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.03)
    # Series with zero std returns 0.0 defensively
    assert sharpe == 0.0
    
    np.random.seed(42)
    varying_returns = pd.Series(np.random.normal(0.001, 0.01, 252))
    sharpe_varying = calculate_sharpe_ratio(varying_returns, risk_free_rate=0.035)
    assert isinstance(sharpe_varying, float)

def test_var_and_cvar():
    """Verify VaR and CVaR order and tail expectations."""
    np.random.seed(42)
    # Gaussian returns
    returns = pd.Series(np.random.normal(0.0005, 0.015, 1000))
    
    var_95 = calculate_var_historical(returns, confidence_level=0.95)
    var_99 = calculate_var_historical(returns, confidence_level=0.99)
    cvar_95 = calculate_cvar(returns, confidence_level=0.95)
    
    assert var_99 > var_95, "99% VaR must exceed 95% VaR"
    assert cvar_95 >= var_95, "CVaR (expected shortfall) must exceed or equal VaR"

def test_multi_asset_portfolio_and_euler_risk():
    """Verify multi-asset portfolio performance and risk decomposition summation."""
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    np.random.seed(42)
    df_returns = pd.DataFrame({
        "A": np.random.normal(0.0008, 0.01, 100),
        "B": np.random.normal(0.0005, 0.02, 100)
    }, index=dates)
    
    weights = {"A": 0.6, "B": 0.4}
    results = calculate_portfolio_performance(df_returns, weights, risk_free_rate=0.035)
    
    assert "portfolio_cagr" in results
    assert "annualized_volatility" in results
    assert "risk_decomposition" in results
    
    risk_shares = [
        results["risk_decomposition"][s]["percentage_risk_share"]
        for s in ["A", "B"]
    ]
    # Euler's theorem: sum of component percentage risk shares equals 100%
    assert abs(sum(risk_shares) - 100.0) < 0.5, f"Risk shares must sum to 100%, got {sum(risk_shares)}"
