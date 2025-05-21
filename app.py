import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Casos", layout="wide")

st.title("📊 Dashboard de Casos")

uploaded_file = st.file_uploader("Faça upload do arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, parse_dates=["Abertura", "Solução"])

    # Colunas auxiliares
    df["AnoMes_Ord"] = df["Abertura"].dt.to_period("M").dt.to_timestamp()  # Para ordenar
    df["AnoMes"] = df["Abertura"].dt.strftime('%b/%y')  # Para exibir

    st.subheader("1️⃣ Total de Casos por Mês")
    casos_mes = df.groupby(["AnoMes", "AnoMes_Ord"]).size().reset_index(name="Total")
    casos_mes = casos_mes.sort_values("AnoMes_Ord")
    fig1 = px.bar(
        casos_mes, 
        x="AnoMes", 
        y="Total", 
        text='Total', 
        title="Total de Casos por Mês",
        category_orders={"AnoMes": casos_mes["AnoMes"].tolist()}  # Ordenação correta
    )
    fig1.update_traces(textposition='outside')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("2️⃣ Casos por Origem (Mensal)")
    casos_origem = df.groupby(["AnoMes", "AnoMes_Ord", "Origem"]).size().reset_index(name="Total")
    casos_origem = casos_origem.sort_values("AnoMes_Ord")
    fig2 = px.bar(
        casos_origem, 
        x="AnoMes", 
        y="Total", 
        color="Origem", 
        text='Total',
        category_orders={"AnoMes": casos_mes["AnoMes"].tolist()}
    )
    fig2.update_traces(textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("3️⃣ Reaberturas por Mês")
    reaberturas = df.groupby(["AnoMes", "AnoMes_Ord"])["Qt Reab."].sum().reset_index()
    reaberturas = reaberturas.sort_values("AnoMes_Ord")
    fig3 = px.line(
        reaberturas, 
        x="AnoMes", 
        y="Qt Reab.", 
        title="Reaberturas por Mês",
        category_orders={"AnoMes": casos_mes["AnoMes"].tolist()}
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("4️⃣ Top 10 Contas com Mais Casos")
    top_contas = df["Conta"].value_counts().nlargest(10).reset_index()
    top_contas.columns = ["Conta", "Total"]
    fig4 = px.bar(
        top_contas, 
        x="Conta", 
        y="Total", 
        text='Total', 
        title="Top 10 Contas com Mais Casos"
    )
    fig4.update_traces(textposition='outside')
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("5️⃣ Casos por Responsável (Mensal)")
    casos_resp = df.groupby(["AnoMes", "AnoMes_Ord", "Responsável"]).size().reset_index(name="Total")
    casos_resp = casos_resp.sort_values("AnoMes_Ord")
    fig5 = px.line(
        casos_resp, 
        x="AnoMes", 
        y="Total", 
        color="Responsável", 
        title="Casos por Responsável (Mensal)",
        category_orders={"AnoMes": casos_mes["AnoMes"].tolist()}
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.success("✅ Dashboard carregado com sucesso!")
else:
    st.info("Por favor, envie um arquivo Excel para visualizar os dados.")
