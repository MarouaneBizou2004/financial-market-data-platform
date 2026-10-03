"""
Market Regime Model Training & Evaluation Engine
Benchmarks multiple ML architectures across chronological train/val/test splits,
evaluates out-of-sample performance, and serializes the champion model artifact.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import (
    GOLD_DATA_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    FIGURES_DIR
)
from src.utils.logging import get_logger
from src.ml.feature_pipeline import MarketRegimeFeaturePipeline, REGIME_LABELS

logger = get_logger("MLTrainingEngine")

class MarketRegimeTrainer:
    def __init__(self, gold_path: Path = GOLD_DATA_DIR / "gold_market_features.parquet"):
        self.gold_path = gold_path
        self.models_dir = MODELS_DIR
        self.reports_dir = REPORTS_DIR
        self.figures_dir = FIGURES_DIR
        self.pipeline_builder = MarketRegimeFeaturePipeline(benchmark_symbol="SPY")

    def run_training_pipeline(self) -> Dict[str, Any]:
        """Executes full ML training, benchmarking, test evaluation, and artifact serialization."""
        logger.info("Starting Market Regime ML Pipeline...")
        df_gold = pd.read_parquet(self.gold_path)
        
        # 1. Feature & Target Generation
        df_ml = self.pipeline_builder.build_features_and_regimes(df_gold)
        logger.info(f"Built {len(df_ml)} feature records for regime classification.")
        
        # 2. Strict Chronological Train/Val/Test Split
        train_df, val_df, test_df = self.pipeline_builder.split_temporal(df_ml)
        logger.info(f"Temporal Split: Train={len(train_df)} | Val={len(val_df)} | Test={len(test_df)}")
        
        feature_cols = self.pipeline_builder.feature_columns
        X_train, y_train = train_df[feature_cols], train_df["regime_target"]
        X_val, y_val = val_df[feature_cols], val_df["regime_target"]
        X_test, y_test = test_df[feature_cols], test_df["regime_target"]
        
        # 3. Model Candidates
        candidates = {
            "Baseline (Majority Class)": DummyClassifier(strategy="most_frequent"),
            "Multinomial Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_leaf=5, random_state=42),
            "Gradient Boosting": HistGradientBoostingClassifier(max_iter=100, max_depth=3, learning_rate=0.05, random_state=42)
        }
        
        val_results = {}
        fitted_pipelines = {}
        
        # Benchmark on Validation set
        for name, model in candidates.items():
            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("classifier", model)
            ])
            pipe.fit(X_train, y_train)
            fitted_pipelines[name] = pipe
            
            y_val_pred = pipe.predict(X_val)
            acc = float(accuracy_score(y_val, y_val_pred))
            f1 = float(f1_score(y_val, y_val_pred, average="macro", zero_division=0))
            prec = float(precision_score(y_val, y_val_pred, average="macro", zero_division=0))
            rec = float(recall_score(y_val, y_val_pred, average="macro", zero_division=0))
            
            val_results[name] = {
                "val_accuracy": round(acc, 4),
                "val_macro_f1": round(f1, 4),
                "val_macro_precision": round(prec, 4),
                "val_macro_recall": round(rec, 4)
            }
            logger.info(f"[{name}] Val Accuracy: {acc:.4f} | Val Macro F1: {f1:.4f}")
            
        # Select Champion based on Validation Macro F1
        champion_name = max(
            [k for k in val_results.keys() if "Baseline" not in k],
            key=lambda k: val_results[k]["val_macro_f1"]
        )
        logger.info(f"Champion Architecture Selected: {champion_name}")
        champion_pipe = fitted_pipelines[champion_name]
        
        # 4. Out-of-Sample Holdout Evaluation on Test Set (2025)
        y_test_pred = champion_pipe.predict(X_test)
        test_acc = float(accuracy_score(y_test, y_test_pred))
        test_f1 = float(f1_score(y_test, y_test_pred, average="macro", zero_division=0))
        test_prec = float(precision_score(y_test, y_test_pred, average="macro", zero_division=0))
        test_rec = float(recall_score(y_test, y_test_pred, average="macro", zero_division=0))
        cm = confusion_matrix(y_test, y_test_pred).tolist()
        
        logger.info(f"Test Set Evaluation ({champion_name}): Accuracy: {test_acc:.4f} | Macro F1: {test_f1:.4f}")
        
        # 5. Serialize Champion Model
        model_out = self.models_dir / "market_regime_model.joblib"
        joblib.dump(champion_pipe, model_out)
        logger.info(f"Champion pipeline saved to: {model_out}")
        
        # 6. Save Consolidated Metrics JSON
        metrics_payload = {
            "model_metadata": {
                "champion_architecture": champion_name,
                "benchmark_symbol": self.pipeline_builder.benchmark_symbol,
                "features_used": feature_cols,
                "regime_labels": REGIME_LABELS
            },
            "split_chronology": {
                "train_period": f"<= {train_df['date'].max().strftime('%Y-%m-%d')} ({len(train_df)} days)",
                "val_period": f"{val_df['date'].min().strftime('%Y-%m-%d')} to {val_df['date'].max().strftime('%Y-%m-%d')} ({len(val_df)} days)",
                "test_period": f"{test_df['date'].min().strftime('%Y-%m-%d')} to {test_df['date'].max().strftime('%Y-%m-%d')} ({len(test_df)} days)"
            },
            "validation_benchmark": val_results,
            "test_set_performance": {
                "test_accuracy": round(test_acc, 4),
                "test_macro_f1": round(test_f1, 4),
                "test_macro_precision": round(test_prec, 4),
                "test_macro_recall": round(test_rec, 4),
                "confusion_matrix": cm
            }
        }
        
        metrics_file = self.reports_dir / "model_metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics_payload, f, indent=4)
        logger.info(f"Model metrics saved to: {metrics_file}")
        
        # 7. Plot Confusion Matrix
        plt.figure(figsize=(7, 6))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=[REGIME_LABELS.get(i, str(i)) for i in range(len(cm))],
                    yticklabels=[REGIME_LABELS.get(i, str(i)) for i in range(len(cm))])
        plt.title(f"Market Regime Confusion Matrix (Holdout Test 2025)\n{champion_name}", pad=12, fontweight="bold")
        plt.xlabel("Predicted Regime", fontweight="bold")
        plt.ylabel("Actual Regime", fontweight="bold")
        plt.xticks(rotation=20, ha="right", fontsize=9)
        plt.yticks(rotation=0, fontsize=9)
        plt.tight_layout()
        cm_path = self.figures_dir / "regime_confusion_matrix.png"
        plt.savefig(cm_path, dpi=300)
        plt.close()
        logger.info(f"Saved confusion matrix plot to: {cm_path}")
        
        return metrics_payload

if __name__ == "__main__":
    trainer = MarketRegimeTrainer()
    trainer.run_training_pipeline()
