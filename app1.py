import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
from io import BytesIO
import requests

st.set_page_config(page_title="Indicadores de dados", layout="wide")

st.title("📊 Indicadores de casos")

# Configuração do Google Drive
@st.cache_data(ttl=300)  # Cache por 5 minutos

def load_data():
    # URL do seu arquivo (modificada para o formato de download direto)
    file_id = "1SqSOc1xsb1i9hxq2OziyxWHrG3GAs450"
    url = f"https://drive.google.com/uc?id={file_id}"

    responsaveis_outros = [
        "Alexsandro Fernandes Maffei",
        "Ana Caroline Mendes Carvalho",
        "Brenda Bertotti Ribeiro",
        "Bruno Macagnan Do Nascimento",
        "Cleiton Bitencourt De Souza",
        "Cristian Macagnan Reus",
        "Douglas Gonçalves E Barra",
        "Fabiana Bressan",
        "Filipe Dos Santos Batista",
        "Guilherme De Costa Sonego",
        "Guilherme Medeiros Rodrigues",
        "Henrique Da Rosa Josefino",
        "Inaiá Rovaris",
        "João Victor Dagostin Dos Santos",
        "João Vitor Ghellere",
        "Jose Victor Padilha Inacio",
        "Kenny Robert Rodrigues",
        "Lucas Demetrio De Abreu",
        "Lucas Demetrio Pizzoni",
        "Lucas Jacques Costa",
        "Luiz Gustavo Uggioni Savi",
        "Marlon De Bem",
        "Otomar Rocha Speck",
        "Outro",
        "Rafael Dias Rocha (Rafa)",
        "Ramiriz Leal",
        "Susan Carboni"
    ]
    
    def agrupar_responsavel(nome):
        if nome in responsaveis_outros:
            return "Outro"
        return nome

    try:
        # Usando gdown para baixar o arquivo
        output = 'temp_file.xlsx'
        gdown.download(url, output, quiet=True)
        
        df = pd.read_excel(output, parse_dates=["Abertura", "Solução"])       
    
        
        # Processamento dos dados
        df["AnoMes"] = df["Abertura"].dt.strftime('%Y-%m')
        df["AnoMes_Display"] = df["Abertura"].dt.strftime('%b/%Y')
        df["Ano"] = df["Abertura"].dt.year
        df["Conta_Resumida"] = df["Conta"].apply(lambda x: ' '.join(x.split()[:2]) if pd.notnull(x) else x)
        df['Responsável'] = df['Responsável'].apply(agrupar_responsavel)
        df['Data de Abertura'] = pd.to_datetime(df['Abertura'])

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# Botão de refresh
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()

with st.spinner("Carregando dados..."):
    df = load_data()

if df is None:
    st.error("Falha ao carregar os dados.")
else:
    # Só agora que o df existe
    maior_data_abertura = df['Data de Abertura'].max().strftime('%d/%m/%Y')

    with st.container():
        st.success(
            f"Indicador atualizado até: {maior_data_abertura}", icon="✅"
        )

        #atualizar = st.button("Atualizar dados")
        
        #if atualizar:
        #    st.write("Dados atualizados!")     

    # Aqui seguem os filtros e gráficos normalmente


if df is not None:
    # Filtros - Adicionando Tipo
    anos = sorted(df["Ano"].dropna().astype(int).unique())
    origens = sorted(df["Origem"].dropna().unique())
    responsaveis = sorted(df["Responsável"].dropna().unique())
    tipos = sorted(df["Tipo"].dropna().unique())  # Novo filtro para Tipo

    st.sidebar.header("🔍 Filtros")

    ano_sel = st.sidebar.multiselect("Ano:", anos, default=anos)
    origem_sel = st.sidebar.multiselect("Origem:", origens, default=origens)
    resp_sel = st.sidebar.multiselect("Responsável:", responsaveis, default=responsaveis)
    tipo_sel = st.sidebar.multiselect("Tipo:", tipos, default=tipos)  # Novo filtro

    # Aplicar filtros - incluindo Tipo
    df_filtrado = df[
        df["Ano"].isin(ano_sel) &
        df["Origem"].isin(origem_sel) &
        df["Responsável"].isin(resp_sel) &
        df["Tipo"].isin(tipo_sel)  # Aplicando filtro de Tipo
    ]

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado para os filtros selecionados.")
    else:
        # Criar ordenação cronológica
        df_ordenado = df_filtrado.sort_values("AnoMes")
        meses_ordenados = df_ordenado["AnoMes"].unique()
        meses_display_ordenados = df_ordenado["AnoMes_Display"].unique()

        ## 1️⃣ Total de Casos por Mês (versão corrigida)
        st.subheader("1️⃣ Total de casos por mês")

        # 1. Converter ano para string (evita decimais)
        df_filtrado = df_filtrado.copy()
        df_filtrado['Ano'] = df_filtrado['Ano'].astype(int).astype(str)

        # 2. Extrair mês e número do mês para ordenação
        df_filtrado['MesNum'] = df_filtrado['Abertura'].dt.month
        df_filtrado['MesNome'] = df_filtrado['Abertura'].dt.strftime('%b')

        # 3. Agrupar para obter a contagem de casos
        casos_mes = df_filtrado.groupby(['MesNum', 'MesNome', 'Ano']).size().reset_index(name='Total')

        # 4. Ordenar por mês e ano
        casos_mes = casos_mes.sort_values(['MesNum', 'Ano'])

        # 5. Definir cores por ano
        cores_por_ano = {
            '2023': '#ff7f0e',  # Laranja
            '2024': '#aec7e8',  # Azul claro
            '2025': '#1f77b4'   # Azul escuro
        }

        # 6. Criar posições personalizadas considerando apenas anos existentes por mês
        import plotly.graph_objects as go

        # Obter meses únicos ordenados
        meses_unicos = casos_mes[['MesNum', 'MesNome']].drop_duplicates().sort_values('MesNum')
        meses_lista = meses_unicos.to_dict('records')

        # Criar estrutura para armazenar posições
        barras_x = []
        barras_y = []
        barras_cor = []
        barras_texto = []
        tickvals = []
        ticktext = []
        mes_posicoes = {}  # Para armazenar a posição central de cada mês
        contador = 0

        for mes in meses_lista:
            mes_num = mes['MesNum']
            mes_nome = mes['MesNome']
            
            # Filtrar dados apenas para este mês
            dados_mes = casos_mes[casos_mes['MesNum'] == mes_num]
            anos_no_mes = dados_mes['Ano'].unique()
            
            # Posição inicial para este mês
            inicio_mes = contador
            
            # Adicionar barra para cada ano que existe neste mês
            for ano in sorted(anos_no_mes):
                total = dados_mes[dados_mes['Ano'] == ano]['Total'].values[0]
                
                barras_x.append(contador)
                barras_y.append(total)
                barras_cor.append(cores_por_ano.get(ano, '#333333'))
                barras_texto.append(str(total))
                
                tickvals.append(contador)
                ticktext.append(ano)
                
                contador += 1
            
            # Armazenar posição central do mês para a anotação
            mes_posicoes[mes_nome] = (inicio_mes + contador - 1) / 2
            
            # Adicionar espaço extra entre os meses
            contador += 2  # Espaço entre grupos de meses

        # Criar o gráfico
        fig1 = go.Figure()

        # Adicionar as barras
        fig1.add_trace(go.Bar(
            x=barras_x,
            y=barras_y,
            marker_color=barras_cor,
            text=barras_texto,
            textposition='outside',
            width=0.7  # Largura das barras
        ))

        # Adicionar anotações para os meses (centralizadas)
        anotacoes = []
        for mes_nome, pos_central in mes_posicoes.items():
            anotacoes.append(dict(
                x=pos_central,
                y=1.05,  # Posição acima do gráfico
                xref='x',
                yref='paper',
                text=mes_nome,
                showarrow=False,
                font=dict(size=14, color='white'),
                xanchor='center'
            ))

        # Configurar os rótulos do eixo X (anos)
        fig1.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=tickvals,
                ticktext=ticktext,
                title=None,
                showgrid=False
            ),
            yaxis=dict(
                title='Total de Casos',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            annotations=anotacoes,
            plot_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            font=dict(color='white'),
            margin=dict(t=80, b=50, l=50, r=50),
            height=500,
            bargap=0,
            bargroupgap=0,
            title='Total de casos por mês'
        )

        # Exibir o gráfico
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
            barmode='group'
        )
        fig2.update_traces(textposition='outside')
        fig2.update_xaxes(
            type='category', 
            categoryorder='array', 
            categoryarray=meses_display_ordenados,
            title_text="Mês/Ano"
        )
        st.plotly_chart(fig2, use_container_width=True)

        ## 3️⃣ Reaberturas por Mês - Layout agrupado por ano (versão corrigida)
        st.subheader("3️⃣ Reaberturas por mês")

        # 1. Converter ano para string (evita decimais)
        df_filtrado = df_filtrado.copy()
        df_filtrado['Ano'] = df_filtrado['Ano'].astype(int).astype(str)

        # 2. Extrair mês e número do mês para ordenação
        df_filtrado['MesNum'] = df_filtrado['Abertura'].dt.month
        df_filtrado['MesNome'] = df_filtrado['Abertura'].dt.strftime('%b')

        # 3. Agrupar para obter a soma de reaberturas
        reaberturas_mes = df_filtrado.groupby(['MesNum', 'MesNome', 'Ano'])['Qt Reab.'].sum().reset_index(name='Total')
        reaberturas_mes['Total'] = reaberturas_mes['Total'].astype(int)

        # 4. Ordenar por mês e ano
        reaberturas_mes = reaberturas_mes.sort_values(['MesNum', 'Ano'])

        # 5. Definir cores por ano
        cores_por_ano = {
            '2023': '#ff7f0e',  # Laranja
            '2024': '#aec7e8',  # Azul claro
            '2025': '#1f77b4'   # Azul escuro
        }

        # 6. Criar posições personalizadas considerando apenas anos existentes por mês
        import plotly.graph_objects as go

        # Obter meses únicos ordenados
        meses_unicos = reaberturas_mes[['MesNum', 'MesNome']].drop_duplicates().sort_values('MesNum')
        meses_lista = meses_unicos.to_dict('records')

        # Criar estrutura para armazenar posições
        barras_x = []
        barras_y = []
        barras_cor = []
        barras_texto = []
        tickvals = []
        ticktext = []
        mes_posicoes = {}  # Para armazenar a posição central de cada mês
        contador = 0

        for mes in meses_lista:
            mes_num = mes['MesNum']
            mes_nome = mes['MesNome']
            
            # Filtrar dados apenas para este mês
            dados_mes = reaberturas_mes[reaberturas_mes['MesNum'] == mes_num]
            anos_no_mes = dados_mes['Ano'].unique()
            
            # Posição inicial para este mês
            inicio_mes = contador
            
            # Adicionar barra para cada ano que existe neste mês
            for ano in sorted(anos_no_mes):
                total = dados_mes[dados_mes['Ano'] == ano]['Total'].values[0]
                
                barras_x.append(contador)
                barras_y.append(total)
                barras_cor.append(cores_por_ano.get(ano, '#333333'))
                barras_texto.append(str(total))
                
                tickvals.append(contador)
                ticktext.append(ano)
                
                contador += 1
            
            # Armazenar posição central do mês para a anotação
            mes_posicoes[mes_nome] = (inicio_mes + contador - 1) / 2
            
            # Adicionar espaço extra entre os meses
            contador += 2  # Espaço entre grupos de meses

        # Criar o gráfico
        fig3 = go.Figure()

        # Adicionar as barras
        fig3.add_trace(go.Bar(
            x=barras_x,
            y=barras_y,
            marker_color=barras_cor,
            text=barras_texto,
            textposition='outside',
            width=0.7  # Largura das barras
        ))

        # Adicionar anotações para os meses (centralizadas)
        anotacoes = []
        for mes_nome, pos_central in mes_posicoes.items():
            anotacoes.append(dict(
                x=pos_central,
                y=1.05,  # Posição acima do gráfico
                xref='x',
                yref='paper',
                text=mes_nome,
                showarrow=False,
                font=dict(size=14, color='white'),
                xanchor='center'
            ))

        # Configurar os rótulos do eixo X (anos)
        fig3.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=tickvals,
                ticktext=ticktext,
                title=None,
                showgrid=False
            ),
            yaxis=dict(
                title='Total de Reaberturas',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            annotations=anotacoes,
            plot_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            font=dict(color='white'),
            margin=dict(t=80, b=50, l=50, r=50),
            height=500,
            bargap=0,
            bargroupgap=0,
            title='Reaberturas por mês'
        )

        # Exibir o gráfico
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

        ## 5️⃣ Casos por Responsável (Mensal)
        st.subheader("5️⃣ Casos por responsável (Mensal)")
        
        df_filtrado = df_filtrado.copy()
        df_filtrado["Primeiro_Nome"] = df_filtrado["Responsável"].str.split().str[0].fillna("Não informado")

        casos_resp = (df_filtrado.groupby(["AnoMes", "AnoMes_Display", "Primeiro_Nome"])
                    .size()
                    .reset_index(name="Total"))

        casos_resp = casos_resp.sort_values(["AnoMes", "Total"], ascending=[True, False])

        fig5 = px.bar(
            casos_resp,
            x="Primeiro_Nome",
            y="Total",
            color="Primeiro_Nome",
            text="Total",
            title=" ",
            facet_col="AnoMes_Display",
            category_orders={"Primeiro_Nome": casos_resp["Primeiro_Nome"].tolist()}
        )

        fig5.update_traces(
            textposition='outside',
            textangle=0,
            marker_line_width=0.5
        )

        fig5.update_layout(
            xaxis_title=None,
            yaxis_title="Total de casos",
            showlegend=False
        )

        fig5.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig5.update_xaxes(title_text=None)

        st.plotly_chart(fig5, use_container_width=True)

        ## 6️⃣ Casos por Tipo (Mensal) - NOVO GRÁFICO
        st.subheader("6️⃣ Casos por Tipo (Mensal)")
        
        casos_tipo = df_filtrado.groupby(["AnoMes", "AnoMes_Display", "Tipo"]).size().reset_index(name="Total")
        casos_tipo = casos_tipo.sort_values("AnoMes")

        fig6 = px.bar(
            casos_tipo,
            x="AnoMes_Display",
            y="Total",
            color="Tipo",
            text="Total",
            title="Casos por Tipo",
            barmode='group'
        )
        fig6.update_traces(textposition='outside')
        fig6.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=meses_display_ordenados,
            title_text="Mês/Ano"
        )
        st.plotly_chart(fig6, use_container_width=True)

        ## 7️⃣ Índice de Resolubilidade
        st.subheader("7️⃣ Índice de Resolubilidade")

        import calendar
        import plotly.graph_objects as go

        df_filtrado["Resolvido_Mesmo_Dia"] = df_filtrado["Abertura"] == df_filtrado["Solução"]
        df_filtrado["Ano"] = df_filtrado["Abertura"].dt.year
        df_filtrado["Mes"] = df_filtrado["Abertura"].dt.month
        df_filtrado["Mes_Display"] = df_filtrado["Mes"].apply(lambda x: calendar.month_abbr[x]) + "/" + df_filtrado["Ano"].astype(str)
        df_filtrado["Mes_Ano_Ordenacao"] = df_filtrado["Ano"] * 100 + df_filtrado["Mes"]
        df_filtrado["Primeiro_Nome"] = df_filtrado["Responsável"].str.split().str[0].fillna("Não informado")

        meses_ordenados = (
            df_filtrado[["Mes_Display", "Mes_Ano_Ordenacao"]]
            .drop_duplicates()
            .sort_values("Mes_Ano_Ordenacao")
        )

        meses_disponiveis = meses_ordenados["Mes_Display"].tolist()
        mes_escolhido = st.selectbox("Selecione o mês:", meses_disponiveis, index=len(meses_disponiveis)-1)

        df_mes = df_filtrado[df_filtrado["Mes_Display"] == mes_escolhido]

        total_casos = (df_mes
                    .groupby("Primeiro_Nome")
                    .size()
                    .reset_index(name="Total_Casos"))

        resolvidos_mesmo_dia = (df_mes[df_mes["Resolvido_Mesmo_Dia"]]
                                .groupby("Primeiro_Nome")
                                .size()
                                .reset_index(name="Resolvidos_Mesmo_Dia"))

        resumo = pd.merge(total_casos, resolvidos_mesmo_dia,
                        on="Primeiro_Nome", how="left").fillna(0)

        resumo["%_Resolubilidade"] = (resumo["Resolvidos_Mesmo_Dia"] / resumo["Total_Casos"]) * 100

        fig7 = go.Figure()

        x_labels = resumo["Primeiro_Nome"]

        fig7.add_trace(go.Bar(
            x=x_labels,
            y=resumo["Total_Casos"],
            name="Total de casos",
            text=resumo["Total_Casos"],
            textposition="auto"
        ))

        fig7.add_trace(go.Bar(
            x=x_labels,
            y=resumo["Resolvidos_Mesmo_Dia"],
            name="Resolvidos no mesmo dia",
            text=resumo["Resolvidos_Mesmo_Dia"],
            textposition="auto"
        ))

        fig7.add_trace(go.Scatter(
            x=x_labels,
            y=resumo["%_Resolubilidade"],
            name="% Resolubilidade",
            mode="lines+markers+text",
            text=[f"{v:.1f}%" for v in resumo["%_Resolubilidade"]],
            textposition="top center",
            yaxis="y2"
        ))

        fig7.update_layout(
            title=f"Índice de resolubilidade - {mes_escolhido}",
            xaxis_title="Responsável",
            yaxis=dict(title="Quantidade de casos"),
            yaxis2=dict(title="% Resolubilidade", overlaying="y", side="right"),
            barmode="group",
            legend=dict(title="Legenda", x=1.05, y=1),
            margin=dict(r=100)
        )

        st.plotly_chart(fig7, use_container_width=True)

        st.success(f"✅ Indicador carregado com sucesso.")
else:
    st.error("Não foi possível carregar os dados. Verifique a conexão ou tente novamente mais tarde.")