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
    df["AnoMes_Display"] = df["Abertura"].dt.strftime('%b/%Y')  # Para exibição
    df["Ano"] = df["Abertura"].dt.year
    #df["Responsavel_Primeiro_Nome"] = df["Responsável"].apply(lambda x: ' '.join(x.split()[:2]) if pd.notnull(x) else x)
        
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
        st.subheader("1️⃣ Total de casos por mês")
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
            title_text="Mês/Ano"  # Adicionado título do eixo X
        )
        st.plotly_chart(fig1, use_container_width=True)

        ## 2️⃣ Casos por Origem (Mensal) - Barras lado a lado
        st.subheader("2️⃣ Casos por origem (Mensal)")
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
            title_text="Mês/Ano"  # Adicionado título do eixo X
        )
        st.plotly_chart(fig2, use_container_width=True)

        ## 3️⃣ Reaberturas por Mês - Agora com barras
        st.subheader("3️⃣ Reaberturas por mês")
        reaberturas = df_filtrado.groupby(["AnoMes", "AnoMes_Display"])["Qt Reab."].sum().reset_index()
        reaberturas = reaberturas.sort_values("AnoMes")

        fig3 = px.bar(
            reaberturas, 
            x="AnoMes_Display", 
            y="Qt Reab.", 
            text="Qt Reab.", 
            title="Reaberturas por mês"
        )
        fig3.update_traces(textposition='outside')
        fig3.update_xaxes(
            type='category', 
            categoryorder='array', 
            categoryarray=meses_display_ordenados,
            title_text="Mês/Ano"  # Adicionado título do eixo X
        )
        st.plotly_chart(fig3, use_container_width=True)

        ## 4️⃣ Top 10 Contas com Mais Casos - Nomes resumidos
        st.subheader("4️⃣ Top 10 contas com mais casos")
        top_contas = df_filtrado["Conta_Resumida"].value_counts().nlargest(10).reset_index()
        top_contas.columns = ["Conta", "Total"]

        fig4 = px.bar(
            top_contas, 
            x="Conta", 
            y="Total", 
            text="Total", 
            title="Top 10 contas"
        )
        fig4.update_traces(textposition='outside')
        fig4.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig4, use_container_width=True)

        ## 5️⃣ Casos por Responsável (Mensal) - Versão Final
        st.subheader("5️⃣ Casos por responsável (Mensal)")

        # 1. Tratar valores vazios/nulos
        df_filtrado["Responsável"] = df_filtrado["Responsável"].fillna("Não informado")

        # 2. Preparar dados com ordenação correta
        casos_resp = (df_filtrado.groupby(["AnoMes", "AnoMes_Display", "Responsável"])
                    .size()
                    .reset_index(name="Total")
                    .sort_values(["AnoMes", "Total"], ascending=[True, False]))

        # 3. Definir top 5 responsáveis por volume total (não por mês)
        top_responsaveis = casos_resp.groupby("Responsável")["Total"].sum().nlargest(5).index.tolist()

        # 4. Criar categoria consolidada
        casos_resp["Categoria"] = casos_resp["Responsável"].apply(
            lambda x: x if x in top_responsaveis else "Outros")

        # 5. Ordenação final
        casos_resp = casos_resp.sort_values(["AnoMes", "Categoria", "Total"], 
                                        ascending=[True, False, False])

        # 6. Criar gráfico
        fig5 = px.bar(
            casos_resp,
            x="AnoMes_Display",
            y="Total",
            color="Categoria",
            text="Total",
            title="Casos por responsável (Top 5 + Outros)",
            category_orders={
                "AnoMes_Display": meses_display_ordenados,
                "Categoria": top_responsaveis + ["Outros", "Não informado"]
            },
            color_discrete_sequence=px.colors.qualitative.Plotly + ["#CCCCCC", "#999999"]
        )

        # 7. Ajustes finos
        fig5.update_traces(
            texttemplate='%{text:.0f}',
            textposition='outside',
            textfont_size=10,
            marker_line_width=0
        )

        fig5.update_layout(
            barmode='group',
            xaxis_title="Mês/Ano",
            yaxis_title="Total de Casos",
            legend_title_text="Responsáveis",
            uniformtext_minsize=8,
            hovermode="x unified",
            xaxis={
                'type': 'category',
                'categoryorder': 'array',
                'categoryarray': meses_display_ordenados
            }
        )

        # 8. Alternativa para valores sobrepostos
        if len(casos_resp["Categoria"].unique()) > 6:
            fig5.update_traces(textposition='auto')

        st.plotly_chart(fig5, use_container_width=True)

        st.success("✅ Dashboard carregado com sucesso!")
else:
    st.info("Por favor, envie um arquivo Excel para visualizar os dados.")