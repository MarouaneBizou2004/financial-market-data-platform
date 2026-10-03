"""
Structured Logging Module
Provides uniform, contextual logging for ingestion, ETL, Spark, ML, and quality checks.
Safeguards against Python 3.13 stdlib module shadowing.
"""

import sys

# Ensure stdlib logging is loaded rather than local module shadowing
_clean_sys_path = [p for p in sys.path if not p.endswith(r"\utils") and not p.endswith("/utils")]
_saved_sys_path = sys.path[:]
sys.path = _clean_sys_path
import logging as std_logging
sys.path = _saved_sys_path

def get_logger(name: str, level: int = std_logging.INFO) -> std_logging.Logger:
    """Returns a structured logger with standardized console output."""
    logger = std_logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = std_logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = std_logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
