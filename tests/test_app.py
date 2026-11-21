import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import data_loader


APP_PATH = Path(__file__).resolve().parents[1] / "src" / "app.py"


@pytest.fixture
def story_data():
    return {
        "neighborhood_analysis": pd.DataFrame([
            {
                "bairro": "Alfa", "quantidade_imoveis": 8, "preco_mediano": 100000,
                "area_mediana": 50, "preco_m2_mediano": 2000,
                "participacao_amostra": 80.0, "classificacao": "Oportunidade relativa",
            },
            {
                "bairro": "Beta", "quantidade_imoveis": 2, "preco_mediano": 400000,
                "area_mediana": 80, "preco_m2_mediano": 5000,
                "participacao_amostra": 20.0, "classificacao": "Segmento premium",
            },
        ]),
        "market_by_type": pd.DataFrame([
            {"tipo_imovel": "Casa", "quantidade_imoveis": 10},
        ]),
        "market_by_neighborhood": pd.DataFrame([
            {"bairro": "Alfa", "quantidade_imoveis": 8, "participacao_amostra": 80.0},
            {"bairro": "Beta", "quantidade_imoveis": 2, "participacao_amostra": 20.0},
        ]),
        "data_quality_summary": pd.DataFrame([
            {"registros_totais": 10, "areas_invalidas": 1, "outliers_area_m2": 2},
        ]),
        "correlations": pd.DataFrame([
            {"variavel_a": "area_m2", "variavel_b": "preco", "correlacao": 0.42, "metodo": "Pearson", "registros_utilizados": 9},
        ]),
    }


def test_story_uses_precomputed_values_and_classifications(monkeypatch, story_data):
    monkeypatch.setattr(data_loader, "load_all_data", lambda: story_data)

    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert [metric.value for metric in app.metric] == ["10", "2", "1", "0,420"]
    assert "Alfa reúne 8 imóveis (80,0%" in app.markdown[2].value
    assert "correlação não implica causalidade" in app.markdown[3].value
    assert "**9 observações**" in app.markdown[3].value
    assert "áreas inválidas: 1; outliers de área: 2" in app.caption[0].value
    assert "Alfa" in app.markdown[-3].value
    assert "Beta" in app.markdown[-2].value
    table = app.dataframe[0].value
    assert table["bairro"].tolist() == ["Alfa"]
    assert table["preco_m2_mediano"].tolist() == [2000]

    charts = app.get("plotly_chart")
    assert len(charts) == 4
    traces = json.loads(charts[-1].proto.spec)["data"]
    assert {trace["name"] for trace in traces} == {
        "Oportunidade relativa", "Segmento premium"
    }
    for chart in (charts[2], charts[3]):
        spec = json.loads(chart.proto.spec)
        assert spec["layout"]["separators"] == ",."
        assert "R$ %{x:,.2f}" in spec["data"][0]["hovertemplate"]


def test_missing_classification_is_explained(monkeypatch, story_data):
    story_data["neighborhood_analysis"] = story_data["neighborhood_analysis"].iloc[:1]
    monkeypatch.setattr(data_loader, "load_all_data", lambda: story_data)

    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert any("contraste está incompleto" in message.value for message in app.info)
    assert "nenhum bairro classificado" in app.markdown[-2].value


def test_missing_pearson_correlation_is_reported(monkeypatch, story_data):
    story_data["correlations"]["metodo"] = "Spearman"
    monkeypatch.setattr(data_loader, "load_all_data", lambda: story_data)

    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert "correlação Pearson" in app.error[0].value
