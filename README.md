# Mercado Imobiliário Regional — Storytelling

## Objetivo

Este módulo apresenta uma análise exploratória do mercado imobiliário regional
em uma aplicação Streamlit, investigando onde estão as oportunidades relativas
na amostra analisada.

## Posição na arquitetura

O Storytelling é o quarto e último módulo do projeto: coleta de dados reais →
batch com PySpark e Parquet → Analytics com Pandas e NumPy → Storytelling com
Streamlit e Plotly. Ele consome os CSVs produzidos pelo Analytics e permanece
desacoplado dos módulos anteriores: não importa seus códigos, não executa
scraping ou PySpark e não recalcula análises ou classificações.

## Dados de entrada

Copie para `data/analytics/` os cinco artefatos CSV produzidos pelo projeto
`mercado-imobiliario-analytics`:

- `neighborhood_analysis.csv`
- `market_by_type.csv`
- `market_by_neighborhood.csv`
- `data_quality_summary.csv`
- `correlations.csv`

O projeto consome somente esses CSVs; não inclui os Parquets nem o código-fonte
do Analytics.

## Amostra e limitações

Os artefatos registram **285 imóveis**. Segundo as informações dos dados de
origem, a amostra é predominantemente de Porto Alegre/RS, com ocorrências
pontuais em outros municípios. Os CSVs agregados deste módulo não identificam
o município de cada imóvel e, portanto, não permitem verificar essa distribuição
geográfica. O período exato de coleta não está documentado neste projeto.

A amostra não representa necessariamente todo o mercado, e o número de imóveis
varia entre bairros. O resumo de qualidade registra 4 áreas inválidas e 35
outliers de área. Os CSVs não incluem pares individuais de área e preço; a
correlação de Pearson apresentada é a calculada pelo Analytics (aproximadamente
0,872, com 285 observações) e não implica causalidade.

As classificações, incluindo **Oportunidade relativa**, são relativas à amostra
e às medianas utilizadas pelo Analytics. Elas não são recomendações financeiras
individuais nem garantias de investimento.

## Narrativa

O Streamlit apresenta a sequência: Contexto → Retrato do mercado → Concentração
→ Relação entre área e preço → Oportunidades relativas → Segmento premium →
Conclusão. A comparação de preços utiliza medianas por bairro.

## Instalação e execução

Crie e ative um ambiente virtual para manter as dependências isoladas. No
PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run src/app.py
```

Para executar os testes, instale o pytest no mesmo ambiente virtual (ele é uma
dependência de desenvolvimento e não faz parte das dependências da aplicação):

```powershell
python -m pip install pytest
pytest -q
```
