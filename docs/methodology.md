# Financial & Quantitative Methodology
## Mathematical Formulations & Analytical Framework

### 1. Returns Analytics

#### 1.1 Daily Arithmetic Return
$$R_t = \frac{P_t - P_{t-1}}{P_{t-1}} = \frac{P_t}{P_{t-1}} - 1$$
Where $P_t$ is the adjusted closing price on trading day $t$.

#### 1.2 Multi-Period Compounded Cumulative Return
$$R_{0, T} = \prod_{t=1}^T (1 + R_t) - 1$$

#### 1.3 Compound Annual Growth Rate (CAGR)
$$\text{CAGR} = \left(\frac{P_T}{P_0}\right)^{\frac{252}{N}} - 1$$
Where $N$ represents the total number of elapsed trading days and 252 represents standard annual trading sessions.

---

### 2. Volatility Modeling

#### 2.1 Sample Annualized Volatility (Close-to-Close)
$$\sigma_{\text{ann}} = \sqrt{252} \cdot \sqrt{\frac{1}{N-1} \sum_{t=1}^N (R_t - \bar{R})^2}$$

#### 2.2 Parkinson Extreme-Value Volatility Estimator
The Parkinson estimator utilizes daily High ($H_t$) and Low ($L_t$) prices, providing up to 5x greater statistical efficiency than close-to-close measures by capturing intraday price dispersion:
$$\sigma_{\text{Parkinson}} = \sqrt{\frac{252}{4 \ln(2) \cdot N} \sum_{t=1}^N \left(\ln\frac{H_t}{L_t}\right)^2}$$

---

### 3. Drawdown & Downside Risk

#### 3.1 Running Peak & Continuous Drawdown
$$\text{Peak}_t = \max_{\tau \le t} P_\tau$$
$$\text{DD}_t = \frac{P_t - \text{Peak}_t}{\text{Peak}_t} \in [-1.0, 0.0]$$

#### 3.2 Maximum Drawdown (MDD)
$$\text{MDD} = \min_{t \in [0, T]} \text{DD}_t$$
The recovery date $t_{\text{rec}}$ is the earliest timestamp subsequent to the trough $t_{\text{trough}}$ such that $P_{t_{\text{rec}}} \ge P_{t_{\text{peak}}}$.

---

### 4. Risk-Adjusted Performance Ratios

#### 4.1 Sharpe Ratio
Measures excess return over the risk-free rate ($R_f$) per unit of total risk:
$$\text{Sharpe} = \frac{\bar{R}_{\text{ann}} - R_f}{\sigma_{\text{ann}}} = \frac{\bar{R}_{\text{daily}} \cdot 252 - R_f}{\sigma_{\text{daily}} \cdot \sqrt{252}}$$
Where $R_f = 3.5\%$ default risk-free rate.

#### 4.2 Downside Deviation & Sortino Ratio
The Sortino ratio replaces total volatility with downside semi-deviation below a Minimum Acceptable Return ($\text{MAR} = R_f / 252$), penalizing only harmful downside volatility:
$$\sigma_d = \sqrt{252 \cdot \frac{1}{N} \sum_{t=1}^N \min(0, R_t - \text{MAR})^2}$$
$$\text{Sortino} = \frac{\bar{R}_{\text{ann}} - R_f}{\sigma_d}$$

---

### 5. Tail Risk: Value at Risk (VaR) & Expected Shortfall (CVaR)

#### 5.1 Historical Value at Risk ($\text{VaR}_\alpha$)
Expressed as a positive percentage loss at confidence level $\alpha \in \{0.95, 0.99\}$:
$$\text{VaR}_\alpha = - \text{Percentile}(R, 1 - \alpha)$$

#### 5.2 Parametric Gaussian Value at Risk
$$\text{VaR}_\alpha^{\text{param}} = - (\mu - z_\alpha \cdot \sigma)$$
Where $z_{0.95} \approx 1.645$ and $z_{0.99} \approx 2.326$.

#### 5.3 Conditional Value at Risk ($\text{CVaR}_\alpha$ / Expected Shortfall)
Quantifies the conditional expected loss in the worst $(1 - \alpha)\%$ tail scenarios:
$$\text{CVaR}_\alpha = - \mathbb{E}\left[ R \mid R \le -\text{VaR}_\alpha \right]$$

---

### 6. Multi-Asset Portfolio Mathematics & Euler Risk Attribution

#### 6.1 Portfolio Return & Covariance
For weight vector $\mathbf{w} \in \mathbb{R}^K$ where $\sum_{i=1}^K w_i = 1$ and annualized covariance matrix $\mathbf{\Sigma} \in \mathbb{R}^{K \times K}$:
$$R_p = \mathbf{w}^T \mathbf{R}$$
$$\sigma_p = \sqrt{\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}}$$

#### 6.2 Marginal Contribution to Risk (MCR)
The partial derivative of portfolio volatility with respect to the weight of asset $i$:
$$\text{MCR}_i = \frac{\partial \sigma_p}{\partial w_i} = \frac{(\mathbf{\Sigma} \mathbf{w})_i}{\sigma_p}$$

#### 6.3 Euler's Component Contribution to Risk (CCR)
By Euler's homogeneous function theorem:
$$\sigma_p = \sum_{i=1}^K w_i \cdot \text{MCR}_i = \sum_{i=1}^K \text{CCR}_i$$
$$\text{Percentage Risk Share}_i = \frac{\text{CCR}_i}{\sigma_p} \times 100\%$$
Guarantees exact $100\%$ additive risk attribution across portfolio constituents.

---

### 7. Machine Learning Market Regime Classification

#### 7.1 Economic Regime States
1. **Regime 0 (Low Vol / Bull):** Trailing 20D Volatility $\le$ trailing 252D median volatility AND trailing 3-Month Momentum $> 0$.
2. **Regime 1 (Low Vol / Stagnant):** Trailing 20D Volatility $\le$ trailing 252D median volatility AND trailing 3-Month Momentum $\le 0$.
3. **Regime 2 (High Vol / Bear):** Trailing 20D Volatility $>$ trailing 252D median volatility AND trailing 3-Month Momentum $\le 0$.
4. **Regime 3 (High Vol / Dynamic Rally):** Trailing 20D Volatility $>$ trailing 252D median volatility AND trailing 3-Month Momentum $> 0$.

#### 7.2 Strict Zero Lookahead Bias Guarantee
- **No Shuffle:** Never apply random $K$-Fold cross-validation on time series.
- **Forward-Chaining Splits:**
  - Training Set: Historical sessions up to 2023-12-31.
  - Validation Set: Historical sessions throughout 2024.
  - Out-of-Sample Holdout Test Set: 2025 calendar year.
- **Trailing Baseline:** Median volatility thresholds are computed strictly on backward-looking 252-day rolling windows.
