import pandas as pd
import pytest

import data_loader
from data_loader import (
    load_all_data,
    load_correlations,
    load_data_quality_summary,
    load_market_by_neighborhood,
    load_market_by_type,
    load_neighborhood_analysis,
)


CSV_FIXTURES = {
    "neighborhood_analysis.csv": (
        "bairro,quantidade_imoveis,preco_mediano,area_mediana,"
        "quantidade_imoveis_validos,preco_m2_mediano,"
        "participacao_amostra,classificacao\n"
        "Centro,2,190000,47.5,2,3370.78,50,Oportunidade relativa\n"
    ),
    "market_by_type.csv": (
        "tipo_imovel,quantidade_imoveis\nApto,2\n"
    ),
    "market_by_neighborhood.csv": (
        "bairro,quantidade_imoveis\nCentro,2\n"
    ),
    "data_quality_summary.csv": "registros_totais\n2\n",
    "correlations.csv": (
        "variavel_a,variavel_b,correlacao,metodo,registros_utilizados\n"
        "area_m2,preco,0.87,Pearson,2\n"
    ),
}

LOADERS = {
    "neighborhood_analysis.csv": load_neighborhood_analysis,
    "market_by_type.csv": load_market_by_type,
    "market_by_neighborhood.csv": load_market_by_neighborhood,
    "data_quality_summary.csv": load_data_quality_summary,
    "correlations.csv": load_correlations,
}

MAIN_COLUMNS = {
    "neighborhood_analysis.csv": {"bairro", "quantidade_imoveis", "classificacao"},
    "market_by_type.csv": {"tipo_imovel"},
    "market_by_neighborhood.csv": {"bairro"},
    "data_quality_summary.csv": {"registros_totais"},
    "correlations.csv": {"variavel_a", "variavel_b", "correlacao"},
}


@pytest.fixture
def analytics_data_dir(tmp_path, monkeypatch):
    for file_name, contents in CSV_FIXTURES.items():
        (tmp_path / file_name).write_text(contents, encoding="utf-8")
    monkeypatch.setattr(data_loader, "ANALYTICS_DATA_DIR", tmp_path)
    return tmp_path


def test_load_all_data_returns_five_dataframes_with_main_columns(
    analytics_data_dir,
):
    data = load_all_data()

    assert len(data) == 5
    for file_name in CSV_FIXTURES:
        key = file_name.removesuffix(".csv")
        assert isinstance(data[key], pd.DataFrame)
        assert MAIN_COLUMNS[file_name].issubset(data[key].columns)


@pytest.mark.parametrize("file_name,loader", LOADERS.items())
def test_each_loader_reads_its_csv(analytics_data_dir, file_name, loader):
    result = loader()

    assert isinstance(result, pd.DataFrame)
    assert MAIN_COLUMNS[file_name].issubset(result.columns)


def test_load_all_data_raises_when_a_required_file_is_missing(
    analytics_data_dir,
):
    (analytics_data_dir / "correlations.csv").unlink()

    with pytest.raises(FileNotFoundError, match="correlations.csv"):
        load_all_data()
