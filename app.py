import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Casos", layout="wide")

st.title("📊 Dashboard de Casos")

uploaded_file = st.file_uploader("Faça upload do arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, parse_dates=["Abertura", "Solução"])

    # Colunas auxiliares
    df["AnoMes_Ord"] = df["Abertura"].dt.to_period("M").dt.to_timestamp()
    df["AnoMes"] = df["AnoMes_Ord"].dt.strftime('%Y-%m')
    df["Ano"] = df["Abertura"].dt.year.astype(int)  # Corrige 2025.0

    # Filtros
    anos = sorted(df["Ano"].dropna().unique())
    origens = sorted(df["Origem"].dropna().unique())
    responsaveis = sorted(df["Responsável"].dropna().unique())

    st.sidebar.header("🔍 Filtros")

    ano_sel = st.sidebar.multiselect("Ano:", anos, default=anos)
    origem_sel = st.sidebar.multiselect("Origem:", origens, default=origens)
    resp_sel = st.sidebar.multiselect("Responsável:", responsaveis, default=responsaveis)

    # Aplicar filtros
    df_filtrado = df[
        df["Ano"].isin(ano_sel) &
        df["Origem"].isin(origem_sel) &
        df["Responsável"].isin(resp_sel)
    ]

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado para os filtros selecionados.")
    else:
        # Base para ordenação
        ordem_mes = (df_filtrado[["AnoMes", "AnoMes_Ord"]]
                     .drop_duplicates()
                     .sort_values("AnoMes_Ord"))["AnoMes"].tolist()

        # Função auxiliar para transformar em categoria ordenada
        def categorizar(df_plot):
            df_plot["AnoMes"] = pd.Categorical(df_plot["AnoMes"], categories=ordem_mes, ordered=True)
            return df_plot

        ## 1️⃣ Total de Casos por Mês
        st.subheader("1️⃣ Total de Casos por Mês")
        casos_mes = df_filtrado.groupby(["AnoMes", "AnoMes_Ord"]).size().reset_index(name="Total")
        casos_mes = categorizar(casos_mes)

        fig1 = px.bar(casos_mes, x="AnoMes", y="Total", text="Total", title="Total de Casos por Mês")
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)

        ## 2️⃣ Casos por Origem (Mensal)
        st.subheader("2️⃣ Casos por Origem (Mensal)")
        casos_origem = df_filtrado.groupby(["AnoMes", "AnoMes_Ord", "Origem"]).size().reset_index(name="Total")
        casos_origem = categorizar(casos_origem)

        fig2 = px.bar(casos_origem, x="AnoMes", y="Total", color="Origem", text="Total", title="Casos por Origem")
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

        ## 3️⃣ Reaberturas por Mês
        st.subheader("3️⃣ Reaberturas por Mês")
        reaberturas = df_filtrado.groupby(["AnoMes", "AnoMes_Ord"])["Qt Reab."].sum().reset_index()
        reaberturas = categorizar(reaberturas)

        fig3 = px.line(reaberturas, x="AnoMes", y="Qt Reab.", title="Reaberturas por Mês")
        st.plotly_chart(fig3, use_container_width=True)

        ## 4️⃣ Top 10 Contas com Mais Casos
        st.subheader("4️⃣ Top 10 Contas com Mais Casos")
        top_contas = df_filtrado["Conta"].value_counts().nlargest(10).reset_index()
        top_contas.columns = ["Conta", "Total"]

        fig4 = px.bar(top_contas, x="Conta", y="Total", text="Total", title="Top 10 Contas")
        fig4.update_traces(textposition='outside')
        st.plotly_chart(fig4, use_container_width=True)

        ## 5️⃣ Casos por Responsável (Mensal)
        st.subheader("5️⃣ Casos por Responsável (Mensal)")
        casos_resp = df_filtrado.groupby(["AnoMes", "AnoMes_Ord", "Responsável"]).size().reset_index(name="Total")
        casos_resp = categorizar(casos_resp)

        fig5 = px.line(casos_resp, x="AnoMes", y="Total", color="Responsável", title="Casos por Responsável")
        st.plotly_chart(fig5, use_container_width=True)

        st.success("✅ Dashboard carregado com sucesso!")
else:
    st.info("Por favor, envie um arquivo Excel para visualizar os dados.")
