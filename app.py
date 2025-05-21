import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Casos", layout="wide")

st.title("📊 Dashboard de Casos - Upload Manual de Excel")

uploaded_file = st.file_uploader("Faça upload do arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, parse_dates=["Abertura", "Solução"])

    df["AnoMes"] = df["Abertura"].dt.to_period("M").astype(str)
    df["Ano"] = df["Abertura"].dt.year

    st.subheader("1️⃣ Total de Casos por Mês")
    casos_mes = df.groupby("AnoMes").size().reset_index(name="Total")
    fig1 = px.bar(casos_mes, x="AnoMes", y="Total", title="Total de Casos por Mês")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("2️⃣ Casos por Origem (Mensal)")
    casos_origem = df.groupby(["AnoMes", "Origem"]).size().reset_index(name="Total")
    fig2 = px.bar(casos_origem, x="AnoMes", y="Total", color="Origem")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("3️⃣ Reaberturas por Mês")
    reaberturas = df.groupby("AnoMes")["Qt Reab."].sum().reset_index()
    fig3 = px.line(reaberturas, x="AnoMes", y="Qt Reab.")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("4️⃣ Top 10 Contas com Mais Casos")
    top_contas = df["Conta"].value_counts().nlargest(10).reset_index()
    top_contas.columns = ["Conta", "Total"]
    fig4 = px.bar(top_contas, x="Conta", y="Total")
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("5️⃣ Casos por Responsável (Mensal)")
    casos_resp = df.groupby(["AnoMes", "Responsável"]).size().reset_index(name="Total")
    fig5 = px.line(casos_resp, x="AnoMes", y="Total", color="Responsável")
    st.plotly_chart(fig5, use_container_width=True)

    st.success("✅ Dashboard carregado com sucesso!")
else:
    st.info("Por favor, envie um arquivo Excel para visualizar os dados.")
