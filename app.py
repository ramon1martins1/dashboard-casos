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

        
        ## 5️⃣ Casos por Responsável (Mensal) - Ordenação Independente por Mês
        st.subheader("5️⃣ Casos por responsável (Mensal)")

        # Extrair primeiro nome e tratar dados
        df_filtrado = df_filtrado.copy()
        df_filtrado["Primeiro_Nome"] = df_filtrado["Responsável"].str.split().str[0].fillna("Não informado")

        # Preparar dados com ordenação independente por mês
        casos_resp = (df_filtrado.groupby(["AnoMes", "AnoMes_Display", "Primeiro_Nome"])
                    .size()
                    .reset_index(name="Total"))

        # Criar uma coluna auxiliar para ordenação dentro de cada mês
        casos_resp = casos_resp.sort_values(["AnoMes", "Total"], ascending=[True, False])

        # Criar um campo para eixo x: "Mês - Nome"
        casos_resp["EixoX"] = casos_resp["AnoMes_Display"] + " - " + casos_resp["Primeiro_Nome"]

        # Garantir que o eixo seja tratado como categoria na ordem certa
        category_order = casos_resp["EixoX"].tolist()

        # Criar gráfico
        fig5 = px.bar(
            casos_resp,
            x="Primeiro_Nome",  # Mantemos só o nome simples como eixo X
            y="Total",
            color="Primeiro_Nome",
            text="Total",
            title="Casos por responsável",
            facet_col="AnoMes_Display",
            category_orders={"Primeiro_Nome": casos_resp["Primeiro_Nome"].tolist()}
        )

        # Ajustes visuais das barras
        fig5.update_traces(
            textposition='outside',
            textangle=0,
            marker_line_width=0.5
        )

        # Remover legenda lateral
        fig5.update_layout(
            xaxis_title=None,
            yaxis_title="Total de casos",
            showlegend=False
        )

        # Remove o "AnoMes_Display=" das anotações de facet
        fig5.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

        # Remove títulos automáticos de eixo x
        fig5.update_xaxes(title_text=None)

        st.plotly_chart(fig5, use_container_width=True)

         ## [6] Índice de Resolubilidade
        st.subheader("🎯 Índice de Resolubilidade")

        # Criar coluna: resolvido no mesmo dia?
        df_filtrado["Resolvido_Mesmo_Dia"] = df_filtrado["Data_Abertura"] == df_filtrado["Data_Resolucao"]

        # Extrair mês para agrupamento
        df_filtrado["AnoMes"] = df_filtrado["Data_Abertura"].dt.to_period("M")
        df_filtrado["AnoMes_Display"] = df_filtrado["AnoMes"].astype(str)

        # Primeiro nome
        df_filtrado["Primeiro_Nome"] = df_filtrado["Responsável"].str.split().str[0].fillna("Não informado")

        # Contar casos resolvidos no mesmo dia
        resolucao = (df_filtrado
                    .groupby(["AnoMes", "AnoMes_Display", "Primeiro_Nome", "Resolvido_Mesmo_Dia"])
                    .size()
                    .reset_index(name="Total"))

        # Pivotar para facilitar
        resolucao_pivot = resolucao.pivot_table(
            index=["AnoMes", "AnoMes_Display", "Primeiro_Nome"],
            columns="Resolvido_Mesmo_Dia",
            values="Total",
            fill_value=0
        ).reset_index()

        # Renomear colunas
        resolucao_pivot = resolucao_pivot.rename(columns={
            True: "Mesmo_Dia",
            False: "Dias_Diferentes"
        })

        # Total e percentual
        resolucao_pivot["Total"] = resolucao_pivot["Mesmo_Dia"] + resolucao_pivot["Dias_Diferentes"]
        resolucao_pivot["%_Resolubilidade"] = (resolucao_pivot["Mesmo_Dia"] / resolucao_pivot["Total"]).fillna(0) * 100

        ---

        # Criar gráfico
        import plotly.express as px
        import plotly.graph_objects as go

        fig = go.Figure()

        # Barras: Mesmo Dia
        fig.add_trace(go.Bar(
            x=resolucao_pivot["AnoMes_Display"] + " - " + resolucao_pivot["Primeiro_Nome"],
            y=resolucao_pivot["Mesmo_Dia"],
            name="Resolvido no Mesmo Dia"
        ))

        # Barras: Dias Diferentes
        fig.add_trace(go.Bar(
            x=resolucao_pivot["AnoMes_Display"] + " - " + resolucao_pivot["Primeiro_Nome"],
            y=resolucao_pivot["Dias_Diferentes"],
            name="Resolvido em Dias Diferentes"
        ))

        # Linha: % Resolubilidade
        fig.add_trace(go.Scatter(
            x=resolucao_pivot["AnoMes_Display"] + " - " + resolucao_pivot["Primeiro_Nome"],
            y=resolucao_pivot["%_Resolubilidade"],
            name="% Resolubilidade",
            mode="lines+markers",
            yaxis="y2"
        ))

        # Layout com eixos secundários
        fig.update_layout(
            title="Índice de Resolubilidade por Responsável e Mês",
            xaxis_title="Mês - Responsável",
            yaxis_title="Quantidade de Casos",
            yaxis2=dict(
                title="% Resolubilidade",
                overlaying="y",
                side="right"
            ),
            barmode="group",
            legend_title="Legenda"
        )

        st.plotly_chart(fig, use_container_width=True)


        st.success("✅ Dashboard carregado com sucesso!")
else:
    st.info("Por favor, envie um arquivo Excel para visualizar os dados.")