import os
from pathlib import Path

import pandas as pd


ANALYTICS_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "analytics"


def _load_csv(file_name: str) -> pd.DataFrame:
    configured_dir = os.environ.get("ANALYTICS_DATA_DIR")
    if configured_dir is not None and not configured_dir.strip():
        raise ValueError("ANALYTICS_DATA_DIR não pode estar vazia.")
    data_dir = Path(configured_dir) if configured_dir is not None else ANALYTICS_DATA_DIR
    file_path = data_dir / file_name
    if not file_path.is_file():
        raise FileNotFoundError(
            f"Arquivo obrigatório não encontrado: {file_path}"
        )
    return pd.read_csv(file_path)


def load_neighborhood_analysis() -> pd.DataFrame:
    return _load_csv("neighborhood_analysis.csv")


def load_market_by_type() -> pd.DataFrame:
    return _load_csv("market_by_type.csv")


def load_market_by_neighborhood() -> pd.DataFrame:
    return _load_csv("market_by_neighborhood.csv")


def load_data_quality_summary() -> pd.DataFrame:
    return _load_csv("data_quality_summary.csv")


def load_correlations() -> pd.DataFrame:
    return _load_csv("correlations.csv")


def load_all_data() -> dict[str, pd.DataFrame]:
    return {
        "neighborhood_analysis": load_neighborhood_analysis(),
        "market_by_type": load_market_by_type(),
        "market_by_neighborhood": load_market_by_neighborhood(),
        "data_quality_summary": load_data_quality_summary(),
        "correlations": load_correlations(),
    }
