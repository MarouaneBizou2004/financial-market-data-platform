"""
Market Regime Inference & State Detection Service
Loads trained champion model to infer current market regimes and class probabilities.
"""

from pathlib import Path
from typing import Dict, Any, List
import joblib
import pandas as pd
import numpy as np

from src.utils.config import MODELS_DIR, GOLD_DATA_DIR
from src.ml.feature_pipeline import MarketRegimeFeaturePipeline, REGIME_LABELS
from src.utils.logging import get_logger

logger = get_logger("MarketRegimeInference")

class MarketRegimePredictor:
    def __init__(self, model_path: Path = MODELS_DIR / "market_regime_model.joblib"):
        self.model_path = model_path
        if not self.model_path.exists():
            raise FileNotFoundError(f"Trained model artifact not found at {self.model_path}. Run train.py first.")
        self.model = joblib.load(self.model_path)
        self.pipeline_builder = MarketRegimeFeaturePipeline(benchmark_symbol="SPY")

    def predict_latest_regime(self, df_gold: pd.DataFrame) -> Dict[str, Any]:
        """Infers the most recent market regime from the latest market data."""
        df_ml = self.pipeline_builder.build_features_and_regimes(df_gold)
        latest_row = df_ml.iloc[[-1]]
        
        feature_cols = self.pipeline_builder.feature_columns
        X_latest = latest_row[feature_cols]
        
        pred_class = int(self.model.predict(X_latest)[0])
        probabilities = self.model.predict_proba(X_latest)[0].tolist()
        
        latest_date = str(pd.to_datetime(latest_row["date"].values[0]).strftime("%Y-%m-%d"))
        
        result = {
            "as_of_date": latest_date,
            "predicted_regime_id": pred_class,
            "predicted_regime_name": REGIME_LABELS.get(pred_class, "Unknown"),
            "regime_probabilities": {
                REGIME_LABELS.get(i, str(i)): round(prob, 4)
                for i, prob in enumerate(probabilities)
            },
            "macro_signals": {
                "benchmark_symbol": self.pipeline_builder.benchmark_symbol,
                "latest_close": round(float(latest_row["close"].values[0]), 2),
                "volatility_20d_pct": round(float(latest_row["volatility_20d"].values[0]) * 100.0, 2),
                "momentum_3m_pct": round(float(latest_row["momentum_3m"].values[0]) * 100.0, 2),
                "drawdown_pct": round(float(latest_row["drawdown"].values[0]) * 100.0, 2),
                "sma_200_ratio": round(float(latest_row["sma_200_ratio"].values[0]), 4)
            }
        }
        return result

if __name__ == "__main__":
    df_gold = pd.read_parquet(GOLD_DATA_DIR / "gold_market_features.parquet")
    predictor = MarketRegimePredictor()
    prediction = predictor.predict_latest_regime(df_gold)
    print("Latest Market Regime State:")
    print(prediction)
