import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import load_all_data


OPPORTUNITY = "Oportunidade relativa"
PREMIUM = "Segmento premium"
COLORS = {OPPORTUNITY: "#28776b", PREMIUM: "#b47b42"}

REQUIRED_COLUMNS = {
    "neighborhood_analysis": {
        "bairro", "quantidade_imoveis", "preco_mediano", "area_mediana",
        "preco_m2_mediano", "participacao_amostra", "classificacao",
    },
    "market_by_type": {"tipo_imovel", "quantidade_imoveis"},
    "market_by_neighborhood": {
        "bairro", "quantidade_imoveis", "participacao_amostra",
    },
    "data_quality_summary": {"registros_totais", "areas_invalidas", "outliers_area_m2"},
    "correlations": {
        "variavel_a", "variavel_b", "correlacao", "metodo", "registros_utilizados",
    },
}


def load_story_data() -> tuple[dict[str, pd.DataFrame], pd.Series]:
    try:
        data = load_all_data()
    except FileNotFoundError as error:
        st.error(f"Não foi possível carregar os dados: {error}")
        st.stop()

    missing_columns = {
        name: sorted(columns - set(data[name].columns))
        for name, columns in REQUIRED_COLUMNS.items()
        if columns - set(data[name].columns)
    }
    if missing_columns:
        details = "; ".join(
            f"{name}: {', '.join(columns)}"
            for name, columns in missing_columns.items()
        )
        st.error(f"Os CSVs não têm todas as colunas esperadas: {details}.")
        st.stop()

    if data["data_quality_summary"].empty:
        st.error("O resumo de qualidade não contém o total de imóveis analisados.")
        st.stop()

    correlations = data["correlations"]
    area_price = correlations[
        (
            ((correlations["variavel_a"] == "area_m2") & (correlations["variavel_b"] == "preco"))
            | ((correlations["variavel_a"] == "preco") & (correlations["variavel_b"] == "area_m2"))
        )
        & (correlations["metodo"].str.casefold() == "pearson")
    ]
    if area_price.empty or pd.isna(area_price.iloc[0]["correlacao"]):
        st.error("O CSV de correlações não contém a correlação Pearson entre área e preço.")
        st.stop()
    return data, area_price.iloc[0]


def render_header(data: dict[str, pd.DataFrame], correlation: pd.Series) -> None:
    total = int(data["data_quality_summary"].iloc[0]["registros_totais"])
    formatted_total = f"{total:,}".replace(",", ".")
    st.title("Mercado Imobiliário Regional")
    st.write(
        f"Uma análise exploratória construída a partir de {formatted_total} imóveis "
        "coletados e processados no pipeline de dados."
    )
    st.subheader("Onde estão as oportunidades relativas no mercado analisado?")
    metrics = st.columns(4)
    metrics[0].metric("Imóveis analisados", formatted_total)
    metrics[1].metric("Bairros", len(data["neighborhood_analysis"]))
    metrics[2].metric("Tipos de imóvel", len(data["market_by_type"]))
    metrics[3].metric(
        "Correlação área × preço", f"{correlation['correlacao']:.3f}".replace(".", ",")
    )


def render_market_overview(market_by_type: pd.DataFrame) -> None:
    st.header("1. Retrato do mercado")
    st.write(
        "A amostra reúne diferentes tipos de imóvel. A distribuição por bairros "
        "é apresentada na próxima seção para evidenciar sua concentração."
    )
    types = market_by_type.sort_values("quantidade_imoveis")
    chart = px.bar(
        types,
        x="quantidade_imoveis",
        y="tipo_imovel",
        orientation="h",
        labels={"quantidade_imoveis": "Imóveis", "tipo_imovel": "Tipo"},
        title="Imóveis por tipo",
        color_discrete_sequence=["#28776b"],
    )
    st.plotly_chart(chart, width="stretch")


def render_concentration(market_by_neighborhood: pd.DataFrame) -> None:
    st.header("2. Concentração por bairro")
    if market_by_neighborhood.empty:
        st.info("Não há bairros disponíveis para apresentar a concentração.")
        return
    leaders = market_by_neighborhood.nlargest(10, "quantidade_imoveis")
    leader = leaders.iloc[0]
    participation = f"{leader['participacao_amostra']:.1f}".replace(".", ",")
    st.write(
        f"Na amostra, {leader['bairro']} reúne {int(leader['quantidade_imoveis'])} "
        f"imóveis ({participation}% do total). "
        "O gráfico apresenta os bairros com mais imóveis, não o mercado inteiro."
    )
    chart = px.bar(
        leaders.sort_values("quantidade_imoveis"),
        x="quantidade_imoveis",
        y="bairro",
        orientation="h",
        custom_data=["participacao_amostra"],
        labels={"quantidade_imoveis": "Imóveis", "bairro": "Bairro"},
        title="Até 10 bairros com mais imóveis na amostra",
        color_discrete_sequence=["#496c88"],
    )
    chart.update_layout(separators=",.")
    chart.update_traces(
        hovertemplate="%{y}<br>Imóveis: %{x}<br>Participação: %{customdata[0]:.1f}%<extra></extra>"
    )
    st.plotly_chart(chart, width="stretch")


def render_area_price_relationship(correlation: pd.Series, quality: pd.Series) -> None:
    st.header("3. Relação entre área e preço")
    coefficient = f"{correlation['correlacao']:.3f}".replace(".", ",")
    observations = f"{int(correlation['registros_utilizados']):,}".replace(",", ".")
    st.write(
        f"A correlação de Pearson entre área e preço calculada pelo Analytics "
        f"é **{coefficient}**, com **{observations} observações**. "
        "Ela é uma evidência descritiva "
        "desta amostra; correlação não implica causalidade."
    )
    st.caption(
        "Resumo de qualidade — áreas inválidas: "
        f"{int(quality['areas_invalidas'])}; "
        f"outliers de área: {int(quality['outliers_area_m2'])}."
    )
    st.caption(
        "Os CSVs disponíveis não contêm os pares individuais de área e preço; "
        "por isso, não é exibido um gráfico de dispersão por imóvel."
    )


def render_relative_opportunities(neighborhoods: pd.DataFrame) -> None:
    st.header("4. Oportunidades relativas")
    st.write(
        "Os bairros abaixo recebem a classificação **Oportunidade relativa** "
        "no Analytics. Os valores são medianas e participações da própria amostra."
    )
    opportunities = neighborhoods[neighborhoods["classificacao"] == OPPORTUNITY]
    if opportunities.empty:
        st.info("Não há bairros classificados como Oportunidade relativa nesta amostra.")
        return
    chart = px.bar(
        opportunities.sort_values("preco_m2_mediano"),
        x="preco_m2_mediano",
        y="bairro",
        orientation="h",
        labels={"preco_m2_mediano": "Preço/m² mediano (R$)", "bairro": "Bairro"},
        title="Preço/m² mediano nos bairros de Oportunidade relativa",
        color_discrete_sequence=[COLORS[OPPORTUNITY]],
    )
    chart.update_layout(separators=",.")
    chart.update_xaxes(tickprefix="R$ ", tickformat=",.0f")
    chart.update_traces(
        hovertemplate="%{y}<br>Preço/m² mediano: R$ %{x:,.2f}<extra></extra>"
    )
    st.plotly_chart(chart, width="stretch")
    table = opportunities[
        [
            "bairro", "quantidade_imoveis", "preco_mediano", "area_mediana",
            "preco_m2_mediano", "participacao_amostra",
        ]
    ]
    st.dataframe(
        table.style.format(
            {
                "preco_mediano": lambda value: f"R$ {value:,.2f}".translate(str.maketrans(",.", ".,")),
                "preco_m2_mediano": lambda value: f"R$ {value:,.2f}".translate(str.maketrans(",.", ".,")),
                "area_mediana": lambda value: f"{value:.2f}".replace(".", ","),
                "participacao_amostra": lambda value: f"{value:.2f}%".replace(".", ","),
            },
            na_rep="—",
        ),
        column_config={
            "bairro": "Bairro",
            "quantidade_imoveis": "Imóveis",
            "preco_mediano": st.column_config.NumberColumn("Preço mediano (R$)"),
            "area_mediana": st.column_config.NumberColumn("Área mediana (m²)"),
            "preco_m2_mediano": st.column_config.NumberColumn("Preço/m² mediano (R$)"),
            "participacao_amostra": st.column_config.NumberColumn("Participação na amostra (%)"),
        },
        hide_index=True,
        width="stretch",
    )


def render_premium_segment(neighborhoods: pd.DataFrame) -> None:
    st.header("5. Contraste com Segmento premium")
    comparison = neighborhoods[neighborhoods["classificacao"].isin([OPPORTUNITY, PREMIUM])]
    if comparison.empty:
        st.info("Não há bairros nessas duas classificações para comparar.")
        return
    present = set(comparison["classificacao"])
    if OPPORTUNITY not in present or PREMIUM not in present:
        st.info("Uma das classificações não está presente nesta amostra; o contraste está incompleto.")
    st.write(
        "Cada ponto representa um bairro, não um imóvel. A posição combina "
        "o preço mediano e o preço/m² mediano já calculados pelo Analytics."
    )
    chart = px.scatter(
        comparison,
        x="preco_mediano",
        y="preco_m2_mediano",
        color="classificacao",
        hover_name="bairro",
        hover_data={"quantidade_imoveis": True, "classificacao": False},
        color_discrete_map=COLORS,
        category_orders={"classificacao": [OPPORTUNITY, PREMIUM]},
        labels={
            "preco_mediano": "Preço mediano (R$)",
            "preco_m2_mediano": "Preço/m² mediano (R$)",
            "classificacao": "Classificação",
            "quantidade_imoveis": "Imóveis",
        },
        title="Posicionamento de preço por bairro",
    )
    chart.update_layout(separators=",.")
    chart.update_xaxes(tickprefix="R$ ", tickformat=",.0f")
    chart.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
    chart.update_traces(
        marker={"size": 11, "opacity": 0.85},
        hovertemplate=(
            "<b>%{hovertext}</b><br>Preço mediano: R$ %{x:,.2f}"
            "<br>Preço/m² mediano: R$ %{y:,.2f}"
            "<br>Imóveis: %{customdata[0]}<extra>%{fullData.name}</extra>"
        ),
    )
    st.plotly_chart(chart, width="stretch")


def render_conclusion(neighborhoods: pd.DataFrame) -> None:
    st.header("Conclusão")
    for label in (OPPORTUNITY, PREMIUM):
        names = neighborhoods.loc[
            neighborhoods["classificacao"] == label, "bairro"
        ].sort_values().tolist()
        if names:
            st.write(f"**{label}:** {', '.join(names)}.")
        else:
            st.write(f"**{label}:** nenhum bairro classificado nesta amostra.")
    st.write(
        "Essas classificações são relativas à amostra e às medianas utilizadas "
        "pelo Analytics. A quantidade de imóveis varia entre bairros, de modo "
        "que a evidência disponível também varia. Os resultados não constituem "
        "recomendação financeira individual."
    )


def main() -> None:
    st.set_page_config(page_title="Mercado Imobiliário Regional", layout="wide")
    data, correlation = load_story_data()
    render_header(data, correlation)
    render_market_overview(data["market_by_type"])
    render_concentration(data["market_by_neighborhood"])
    render_area_price_relationship(correlation, data["data_quality_summary"].iloc[0])
    render_relative_opportunities(data["neighborhood_analysis"])
    render_premium_segment(data["neighborhood_analysis"])
    render_conclusion(data["neighborhood_analysis"])


if __name__ == "__main__":
    main()
