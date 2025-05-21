import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Casos", layout="wide")

st.title("📊 Dashboard de Casos")

uploaded_file = st.file_uploader("Faça upload do arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, parse_dates=["Abertura", "Solução"])

    # Colunas auxiliares
    df["AnoMes"] = df["Abertura"].dt.strftime('%Y-%m')  # Para ordenação
    df["AnoMes_Display"] = df["Abertura"].dt.strftime('%m/%Y')  # Alterado para Mês/Ano
    df["Ano"] = df["Abertura"].dt.year
    
    # Extrair primeiro nome do responsável
    df["Primeiro_Nome"] = df["Responsável"].str.split().str[0]
    
    # Pré-processamento para o Top 10 Contas
    df["Conta_Resumida"] = df["Conta"].apply(lambda x: ' '.join(x.split()[:2]) if pd.notnull(x) else x)

    # Filtros
    anos = sorted(df["Ano"].dropna().astype(int).unique())
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
        # Criar ordenação cronológica
        df_ordenado = df_filtrado.sort_values("AnoMes")
        meses_ordenados = df_ordenado["AnoMes"].unique()
        meses_display_ordenados = df_ordenado["AnoMes_Display"].unique()

        ## 1️⃣ Total de Casos por Mês
        st.subheader("1️⃣ Total de Casos por Mês")
        casos_mes = df_filtrado.groupby(["AnoMes", "AnoMes_Display"]).size().reset_index(name="Total")
        casos_mes = casos_mes.sort_values("AnoMes")

        fig1 = px.bar(
            casos_mes, 
            x="AnoMes_Display", 
            y="Total", 
            text="Total", 
            title="Total de Casos por Mês"
        )
        fig1.update_traces(textposition='outside')
        fig1.update_xaxes(
            type='category', 
            categoryorder='array', 
            categoryarray=meses_display_ordenados,
            title_text="Mês/Ano"  # Alterado para Mês/Ano
        )
        st.plotly_chart(fig1, use_container_width=True)

        ## 2️⃣ Casos por Origem (Mensal) - Barras lado a lado
        st.subheader("2️⃣ Casos por Origem (Mensal)")
        casos_origem = df_filtrado.groupby(["AnoMes", "AnoMes_Display", "Origem"]).size().reset_index(name="Total")
        casos_origem = casos_origem.sort_values("AnoMes")

        fig2 = px.bar(
            casos_origem, 
            x="AnoMes_Display", 
            y="Total", 
            color="Origem", 
            text="Total", 
            title="Casos por Origem",
            barmode='group'  # Barras lado a lado
        )
        fig2.update_traces(textposition='outside')
        fig2.update_xaxes(
            type='category', 
            categoryorder='array', 
            categoryarray=meses_display_ordenados,
            title_text="Mês/Ano"  # Alterado para Mês/Ano
        )
        st.plotly_chart(fig2, use_container_width=True)

        ## 3️⃣ Reaberturas por Mês - Barras
        st.subheader("3️⃣ Reaberturas por Mês")
        reaberturas = df_filtrado.groupby(["AnoMes", "AnoMes_Display"])["Qt Reab."].sum().reset_index()
        reaberturas = reaberturas.sort_values("AnoMes")

        fig3 = px.bar(
            reaberturas, 
            x="AnoMes_Display", 
            y="Qt Reab.", 
            text="Qt Reab.", 
            title="Reaberturas por Mês"
        )
        fig3.update_traces(textposition='outside')
        fig3.update_xaxes(
            type='category', 
            categoryorder='array', 
            categoryarray=meses_display_ordenados,
            title_text="Mês/Ano"  # Alterado para Mês/Ano
        )
        st.plotly_chart(fig3, use_container_width=True)

        ## 4️⃣ Top 10 Contas com Mais Casos - Nomes resumidos
        st.subheader("4️⃣ Top 10 Contas com Mais Casos")
        top_contas = df_filtrado["Conta_Resumida"].value_counts().nlargest(10).reset_index()
        top_contas.columns = ["Conta", "Total"]

        fig4 = px.bar(
            top_contas, 
            x="Conta", 
            y="Total", 
            text="Total", 
            title="Top 10 Contas (2 primeiras palavras)"
        )
        fig4.update_traces(textposition='outside')
        fig4.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig4, use_container_width=True)

        ## 5️⃣ Casos por Responsável (Mensal) - Barras com primeiro nome
        st.subheader("5️⃣ Casos por Responsável (Mensal)")
        casos_resp = df_filtrado.groupby(["AnoMes", "AnoMes_Display", "Responsável", "Primeiro_Nome"]).size().reset_index(name="Total")
        casos_resp = casos_resp.sort_values("AnoMes")

        fig5 = px.bar(
            casos_resp, 
            x="AnoMes_Display", 
            y="Total", 
            color="Responsável", 
            text="Primeiro_Nome",  # Mostra primeiro nome na base da barra
            title="Casos por Responsável",
            barmode='group'
        )
        
        # Adicionar linhas verticais para separar meses
        for mes in meses_display_ordenados[1:]:
            fig5.add_vline(
                x=meses_display_ordenados.index(mes)-0.5, 
                line_width=1, 
                line_dash="dash", 
                line_color="gray"
            )
            
        fig5.update_traces(textposition='inside', textangle=0)
        fig5.update_xaxes(
            type='category', 
            categoryorder='array', 
            categoryarray=meses_display_ordenados,
            title_text="Mês/Ano"  # Alterado para Mês/Ano
        )
        st.plotly_chart(fig5, use_container_width=True)

        st.success("✅ Dashboard carregado com sucesso!")
else:
    st.info("Por favor, envie um arquivo Excel para visualizar os dados.")