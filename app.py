import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
from io import BytesIO
import requests
import calendar
import numpy as np
from functools import lru_cache
import pickle
import os
from datetime import datetime, timedelta

def inject_universal_css():
    """Injeta CSS que funciona em dark e light mode"""
    st.markdown("""
    <style>
    /* CSS adaptativo para ambos os temas */
    .stApp {
        color-scheme: light dark;
    }
    
    /* Forçar visibilidade de texto em gráficos */
    .js-plotly-plot .plotly text {
        fill: var(--text-color) !important;
    }
    
    .js-plotly-plot .plotly .textpoint {
        fill: var(--text-color) !important;
        font-weight: bold !important;
    }
    
    /* Variáveis CSS para temas */
    :root {
        --text-color: #000000;
        --bg-color: #ffffff;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --text-color: #ffffff;
            --bg-color: #0e1117;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def formatar_mes_pt(data):
    """Formata data para mês abreviado em português"""
    meses = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    return f"{meses[data.month]}/{data.year}"

def traduzir_mes(mes_nome):
    """Traduz nome do mês em inglês para português abreviado"""
    traducao = {
        'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr',
        'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
        'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
    }
    return traducao.get(mes_nome, mes_nome)  # Retorna o original se não encontrar        

def detect_streamlit_theme():
    """Detecta se está em dark ou light mode"""
    try:
        # Tentar detectar pelo session state do Streamlit
        if hasattr(st, '_config') and hasattr(st._config, 'get_option'):
            theme = st._config.get_option('theme.base')
            if theme == 'dark':
                return 'dark'
            elif theme == 'light':
                return 'light'
    except:
        pass
    
    # Fallback: assumir dark mode como padrão
    return 'dark'

def apply_universal_theme(fig, theme_mode='auto'):
    """Aplica tema universal que funciona em dark e light mode"""
    
    if theme_mode == 'auto':
        theme_mode = detect_streamlit_theme()
    
    if theme_mode == 'dark':
        # Configurações para dark mode
        text_color = 'white'
        bg_color = 'rgba(0,0,0,0)'
        grid_color = 'rgba(255,255,255,0.1)'
    else:
        # Configurações para light mode
        text_color = 'black'
        bg_color = 'rgba(255,255,255,0.9)'
        grid_color = 'rgba(0,0,0,0.1)'
    
    # Aplicar configurações
    fig.update_layout(
        font=dict(color=text_color, family='Arial'),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        xaxis=dict(
            gridcolor=grid_color,
            tickfont=dict(color=text_color)
        ),
        yaxis=dict(
            gridcolor=grid_color,
            tickfont=dict(color=text_color)
        )
    )
    
    # Atualizar texto das barras/traces
    fig.update_traces(
        textfont=dict(color=text_color, size=12, family='Arial')
    )
    
    # Atualizar anotações se existirem
    if hasattr(fig.layout, 'annotations') and fig.layout.annotations:
        for annotation in fig.layout.annotations:
            annotation.font.update(color=text_color, family='Arial')
    
    return fig

st.set_page_config(page_title="Indicadores de dados", layout="wide")
inject_universal_css()
current_theme = detect_streamlit_theme()

st.title("📊 Indicadores de casos")

# ✅ OTIMIZAÇÃO: Cache persistente e otimizado
@st.cache_data(ttl=1800, show_spinner=False)
def load_data_optimized():
    """Carregamento otimizado com cache persistente"""
    
    # Verificar cache local
    cache_file = 'data_cache.pkl'
    cache_time_file = 'cache_time.txt'
    
    if os.path.exists(cache_file) and os.path.exists(cache_time_file):
        try:
            with open(cache_time_file, 'r') as f:
                cache_time = datetime.fromisoformat(f.read().strip())
            
            if datetime.now() - cache_time < timedelta(minutes=30):
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except:
            pass
    
    file_id = "1SqSOc1xsb1i9hxq2OziyxWHrG3GAs450"
    url = f"https://drive.google.com/uc?id={file_id}"
    
    responsaveis_outros_set = {
        "Alexsandro Fernandes Maffei", "Ana Caroline Mendes Carvalho",
        "Brenda Bertotti Ribeiro", "Bruno Macagnan Do Nascimento",
        "Cleiton Bitencourt De Souza", "Cristian Macagnan Reus",
        "Douglas Gonçalves E Barra", "Fabiana Bressan",
        "Filipe Dos Santos Batista", "Guilherme De Costa Sonego",
        "Guilherme Medeiros Rodrigues", "Henrique Da Rosa Josefino",
        "Inaiá Rovaris", "João Victor Dagostin Dos Santos",
        "João Vitor Ghellere", "Jose Victor Padilha Inacio",
        "Kenny Robert Rodrigues", "Lucas Demetrio De Abreu",
        "Lucas Demetrio Pizzoni", "Lucas Jacques Costa",
        "Luiz Gustavo Uggioni Savi", "Marlon De Bem",
        "Otomar Rocha Speck", "Outro", "Rafael Dias Rocha (Rafa)",
        "Ramiriz Leal", "Susan Carboni"
    }
    
    def agrupar_responsavel(nome):
        return "Outro" if nome in responsaveis_outros_set else nome

    try:
        output = 'temp_file.xlsx'
        gdown.download(url, output, quiet=True)
        
        df = pd.read_excel(output, parse_dates=["Abertura", "Solução"])
        
        # Processamento otimizado
        df["AnoMes"] = df["Abertura"].dt.strftime('%Y-%m')
        df["AnoMes_Display"] = df["Abertura"].apply(formatar_mes_pt)
        df["Ano"] = df["Abertura"].dt.year
        df["Conta_Resumida"] = df["Conta"].apply(lambda x: ' '.join(x.split()[:2]) if pd.notnull(x) else x)
        df['Responsável'] = df['Responsável'].apply(agrupar_responsavel)
        df['Data de Abertura'] = pd.to_datetime(df['Abertura'])

        # Salvar cache
        with open(cache_file, 'wb') as f:
            pickle.dump(df, f)
        with open(cache_time_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# ✅ OTIMIZAÇÃO: Cache para filtros
@st.cache_data(show_spinner=False)
def filter_data(df, anos, origens, responsaveis, tipos):
    return df[
        df["Ano"].isin(anos) &
        df["Origem"].isin(origens) &
        df["Responsável"].isin(responsaveis) &
        df["Tipo"].isin(tipos)
    ].copy() 

# ✅ FUNÇÃO CORRIGIDA para criar mini gráfico de barras horizontais
def create_mini_horizontal_bar(data, title, color="#d62728", height=100):
    """Cria mini gráfico de barras horizontais para métricas"""
    fig = go.Figure()
    
    # ✅ CORRIGIDO: Garantir que anos sejam inteiros limpos
    anos_formatados = []
    valores_formatados = []
    
    for year, value in zip(data.index, data.values):
        try:
            # Converter ano para int primeiro, depois para string
            ano_int = int(float(year))
            anos_formatados.append(str(ano_int))
            
            # Converter valor para int
            valor_int = int(float(value))
            valores_formatados.append(valor_int)
        except:
            anos_formatados.append(str(year))
            valores_formatados.append(value)
    
    fig.add_trace(go.Bar(
        y=anos_formatados,  # Anos como strings limpas
        x=valores_formatados,  # Valores como inteiros
        orientation='h',
        marker_color=color,
        text=[str(val) for val in valores_formatados],  # Texto das barras
        textposition='inside',
        textfont=dict(size=12, color='white', family='Arial Bold'),
        width=0.6,
        hovertemplate='<b>%{y}</b>: %{x} casos<extra></extra>'
    ))
    
    fig.update_layout(
        height=height,
        margin=dict(t=5, b=5, l=5, r=5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            showline=False,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color='white', family='Arial Bold'),
            showline=False,
            # ✅ CORRIGIDO: Forçar tipo categoria e ordem
            type='category',
            categoryorder='array',
            categoryarray=anos_formatados[::-1]  # Mais recente no topo
        ),
        font=dict(color='white')
    )
    
    return fig

# ✅ FUNÇÃO MELHORADA: Métricas detalhadas de responsáveis
def calcular_metricas_responsaveis(df_filtrado):
    """Calcula métricas detalhadas dos responsáveis"""
    
    # Responsáveis únicos APÓS o agrupamento
    responsaveis_agrupados = df_filtrado['Responsável'].nunique()
    
    # Casos atribuídos a "Outro"
    casos_outros = len(df_filtrado[df_filtrado['Responsável'] == 'Outro'])
    
    # Responsáveis principais (não "Outro")
    responsaveis_principais = df_filtrado[
        df_filtrado['Responsável'] != 'Outro'
    ]['Responsável'].nunique() if 'Outro' in df_filtrado['Responsável'].values else responsaveis_agrupados
    
    # Percentual de casos "Outro"
    perc_outros = (casos_outros / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    
    return {
        'total_agrupados': responsaveis_agrupados,
        'principais': responsaveis_principais,
        'casos_outros': casos_outros,
        'perc_outros': perc_outros,
        'tem_outros': 'Outro' in df_filtrado['Responsável'].values
    }

# ✅ FUNÇÃO MELHORADA: Mini gráfico de responsáveis
def create_mini_responsaveis_chart_improved(df_filtrado, height=100):
    """Cria mini gráfico MELHORADO mostrando distribuição de responsáveis"""
    
    # Top 4 responsáveis por casos
    top_resp = df_filtrado['Responsável'].value_counts().head(4)
    
    fig = go.Figure()
    
    # ✅ MELHORADO: Extrair apenas primeiro nome
    nomes_curtos = []
    for resp in top_resp.index:
        if resp == 'Outro':
            nomes_curtos.append('Outros')  # Manter "Outros" como está
        else:
            # Extrair apenas o primeiro nome
            primeiro_nome = resp.split()[0] if ' ' in resp else resp
            nomes_curtos.append(primeiro_nome)
    
    # Cores diferentes para "Outros" vs responsáveis principais
    cores = []
    for resp in top_resp.index:
        if resp == 'Outro':
            cores.append('#ff7f0e')  # Laranja para "Outros"
        else:
            cores.append('#2ca02c')  # Verde para principais
    
    fig.add_trace(go.Bar(
        y=nomes_curtos,  # ✅ MELHORADO: Usar nomes curtos
        x=top_resp.values,
        orientation='h',
        marker_color=cores,
        text=[str(val) for val in top_resp.values],
        textposition='outside',  # ✅ MELHORADO: Texto fora da barra
        textfont=dict(size=11, color='white', family='Arial Bold'),
        width=0.6,
        hovertemplate='<b>%{y}</b>: %{x} casos<extra></extra>'
    ))
    
    fig.update_layout(
        height=height,
        margin=dict(t=5, b=5, l=5, r=25),  # ✅ MELHORADO: Mais margem à direita para texto
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            showline=False,
            zeroline=False,
            # ✅ MELHORADO: Expandir range para acomodar texto externo
            range=[0, max(top_resp.values) * 1.3] if len(top_resp) > 0 else [0, 1]
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color='white', family='Arial Bold'),
            showline=False,
            type='category'
        ),
        font=dict(color='white')
    )
    
    return fig

# ✅ OTIMIZAÇÃO: Session state para dados
if 'df' not in st.session_state:
    with st.spinner("🚀 Carregando dados..."):
        st.session_state.df = load_data_optimized()

df = st.session_state.df

if df is None:
    st.error("Falha ao carregar os dados.")
    st.stop()

# ✅ Header com botão de atualização e data - ALINHADOS
col_btn, col_data = st.columns([1, 6])

with col_btn:
    if st.button("🔄 Atualizar", help="Força atualização dos dados"):
        st.cache_data.clear()
        for file in ['data_cache.pkl', 'cache_time.txt']:
            if os.path.exists(file):
                os.remove(file)
        st.rerun()

# ✅ Informações do dataset ao lado do botão
maior_data_abertura = df['Data de Abertura'].max().strftime('%d/%m/%Y')
with col_data:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; height: 38px;">
            <span style="background-color: #d4edda; color: #155724; padding: 6px 12px; border-radius: 4px; font-size: 14px;">
                ✅ Atualizado até: {maior_data_abertura}
            </span>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Filtros otimizados
st.sidebar.header("🔍 Filtros")

anos = sorted(df["Ano"].dropna().astype(int).unique())
origens = sorted(df["Origem"].dropna().unique())
responsaveis = sorted(df["Responsável"].dropna().unique())
tipos = sorted(df["Tipo"].dropna().unique())

ano_sel = st.sidebar.multiselect("Ano:", anos, default=anos)
origem_sel = st.sidebar.multiselect("Origem:", origens, default=origens)
resp_sel = st.sidebar.multiselect("Responsável:", responsaveis, default=responsaveis)
tipo_sel = st.sidebar.multiselect("Tipo:", tipos, default=tipos)

# Aplicar filtros
df_filtrado = filter_data(df, ano_sel, origem_sel, resp_sel, tipo_sel)

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado para os filtros selecionados.")
    st.stop()

# ✅ RESUMO EXECUTIVO MELHORADO
st.markdown("---")
st.subheader("📊 Resumo")

# ✅ CORRIGIDO: Calcular métricas garantindo anos como inteiros
total_casos = len(df_filtrado)

# ✅ CORRIGIDO: Forçar anos como inteiros na agregação
df_work = df_filtrado.copy()
df_work.loc[:, 'Ano_Int'] = df_work['Ano'].astype(int)
casos_por_ano = df_work.groupby('Ano_Int').size().sort_index()

# Mês atual dos dados (último mês disponível)
ultimo_mes_dados = df_filtrado['Abertura'].max()
casos_mes_atual = len(df_filtrado[
    (df_filtrado['Abertura'].dt.month == ultimo_mes_dados.month) & 
    (df_filtrado['Abertura'].dt.year == ultimo_mes_dados.year)
])

mes_atual_nome = formatar_mes_pt(ultimo_mes_dados)

# ✅ CORRIGIDO: Reaberturas garantindo anos como inteiros
total_reaberturas = df_filtrado['Qt Reab.'].sum()
reaberturas_por_ano = df_work.groupby('Ano_Int')['Qt Reab.'].sum().sort_index()

# ✅ NOVO: Métricas detalhadas de responsáveis
metricas_resp = calcular_metricas_responsaveis(df_filtrado)

# Layout das métricas
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Card Total de Casos
    st.markdown(
        f"""
        <div style="text-align: center; padding: 8px; border: 1px solid #333; border-radius: 8px; background: rgba(31, 119, 180, 0.1); height: 80px; display: flex; flex-direction: column; justify-content: center;">
            <h5 style="margin: 0; padding: 0; color: #1f77b4; font-size: 14px;">📊 Total de Casos</h5>
            <h2 style="margin: 2px 0; padding: 0; color: #1f77b4; font-size: 24px;">{total_casos:,}</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Mini gráfico CORRIGIDO
    if len(casos_por_ano) > 1:
        fig_casos = create_mini_horizontal_bar(casos_por_ano, "Casos por Ano", "#1f77b4", 100)
        fig_casos = apply_universal_theme(fig_casos, current_theme)
        st.plotly_chart(fig_casos, use_container_width=True, config={'displayModeBar': False})
    else:
        st.markdown("<div style='height: 100px; display: flex; align-items: center; justify-content: center; color: #666;'><small>Dados de um único ano</small></div>", unsafe_allow_html=True)

with col2:
    # Card Último Mês
    st.markdown(
        f"""
        <div style="text-align: center; padding: 8px; border: 1px solid #333; border-radius: 8px; background: rgba(255, 127, 14, 0.1); height: 80px; display: flex; flex-direction: column; justify-content: center;">
            <h5 style="margin: 0; padding: 0; color: #ff7f0e; font-size: 14px;">📅 Último Mês</h5>
            <h4 style="margin: 2px 0; padding: 0; color: #ff7f0e; font-size: 16px;">{mes_atual_nome}</h4>
            <h3 style="margin: 2px 0; padding: 0; color: #ff7f0e; font-size: 20px;">{casos_mes_atual:,} casos</h3>
        </div>
        """, 
        unsafe_allow_html=True
    )

with col3:
    # Card Reaberturas
    st.markdown(
        f"""
        <div style="text-align: center; padding: 8px; border: 1px solid #333; border-radius: 8px; background: rgba(214, 39, 40, 0.1); height: 80px; display: flex; flex-direction: column; justify-content: center;">
            <h5 style="margin: 0; padding: 0; color: #d62728; font-size: 14px;">🔄 Reaberturas</h5>
            <h2 style="margin: 2px 0; padding: 0; color: #d62728; font-size: 24px;">{total_reaberturas:,}</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Mini gráfico CORRIGIDO
    if len(reaberturas_por_ano) > 1 and reaberturas_por_ano.sum() > 0:
        fig_reab = create_mini_horizontal_bar(reaberturas_por_ano, "Reaberturas por Ano", "#d62728", 100)
        st.plotly_chart(fig_reab, use_container_width=True, config={'displayModeBar': False})
    else:
        st.markdown("<div style='height: 100px; display: flex; align-items: center; justify-content: center; color: #666;'><small>Sem dados suficientes</small></div>", unsafe_allow_html=True)

with col4:
    # ✅ MELHORADO: Card Responsáveis com tooltip
    if metricas_resp['tem_outros']:
        outros_texto = f"""
        <span style="position: relative; display: inline-block;">
            Outros
            <span style="color: #ff7f0e; margin-left: 3px; cursor: help;" 
                  title="Agrupamento aplicado: {metricas_resp['casos_outros']:,} casos ({metricas_resp['perc_outros']:.1f}%) foram agrupados como 'Outros'">
                ℹ️
            </span>
        </span>
        """
    else:
        outros_texto = "0 outros"
    
    st.markdown(
        f"""
        <div style="text-align: center; padding: 8px; border: 1px solid #333; border-radius: 8px; background: rgba(44, 160, 44, 0.1); height: 80px; display: flex; flex-direction: column; justify-content: center;">
            <h5 style="margin: 0; padding: 0; color: #2ca02c; font-size: 14px;">👥 Responsáveis</h5>
            <h2 style="margin: 2px 0; padding: 0; color: #2ca02c; font-size: 24px;">{metricas_resp['total_agrupados']}</h2>
            <p style="margin: 2px 0; padding: 0; color: #2ca02c; font-size: 11px;">
                {metricas_resp['principais']} principais + {outros_texto}
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # ✅ MELHORADO: Mini gráfico de responsáveis
    if metricas_resp['total_agrupados'] > 1:
        fig_resp = create_mini_responsaveis_chart_improved(df_filtrado, 100)
        st.plotly_chart(fig_resp, use_container_width=True, config={'displayModeBar': False})
    else:
        st.markdown("<div style='height: 100px; display: flex; align-items: center; justify-content: center; color: #666;'><small>Apenas 1 responsável</small></div>", unsafe_allow_html=True)

st.markdown("---")

# ✅ ESTRUTURA DE ABAS PARA PERFORMANCE (mantendo gráficos originais)
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Casos/Mês", "🏢 Origem", "🔄 Reaberturas", "🏆 Top Contas", "👤 Responsáveis", "📋 Tipos", "📈 Resolubilidade"
])

with tab1:
    ## 1️⃣ GRÁFICO ORIGINAL - Total de Casos por Mês
    st.subheader("Total de casos por mês")

    # Código original mantido
    df_filtrado_copy = df_filtrado.copy().assign(
        Ano=lambda x: x['Ano'].astype(str),
        MesNum=lambda x: x['Abertura'].dt.month,
        MesNome=lambda x: x['Abertura'].dt.strftime('%b')
    )

    casos_mes = df_filtrado_copy.groupby(['MesNum', 'MesNome', 'Ano']).size().reset_index(name='Total')
    casos_mes = casos_mes.sort_values(['MesNum', 'Ano'])

    cores_por_ano = {
        '2023': '#ff7f0e',
        '2024': '#aec7e8',
        '2025': '#1f77b4'
    }

    meses_unicos = casos_mes[['MesNum', 'MesNome']].drop_duplicates().sort_values('MesNum')
    meses_lista = meses_unicos.to_dict('records')

    barras_x = []
    barras_y = []
    barras_cor = []
    barras_texto = []
    tickvals = []
    ticktext = []
    mes_posicoes = {}
    contador = 0

    for mes in meses_lista:
        mes_num = mes['MesNum']
        mes_nome = mes['MesNome']
        
        dados_mes = casos_mes[casos_mes['MesNum'] == mes_num]
        anos_no_mes = dados_mes['Ano'].unique()
        
        inicio_mes = contador
        
        for ano in sorted(anos_no_mes):
            total = dados_mes[dados_mes['Ano'] == ano]['Total'].values[0]
            
            barras_x.append(contador)
            barras_y.append(total)
            barras_cor.append(cores_por_ano.get(ano, '#333333'))
            barras_texto.append(str(total))
            
            tickvals.append(contador)
            ticktext.append(ano)
            
            contador += 1
        
        mes_posicoes[mes_nome] = (inicio_mes + contador - 1) / 2
        contador += 2

    fig1 = go.Figure()

    fig1.add_trace(go.Bar(
        x=barras_x,
        y=barras_y,
        marker_color=barras_cor,
        text=barras_texto,
        textposition='outside',
        width=0.7
    ))

    anotacoes = []
    for mes_nome, pos_central in mes_posicoes.items():
        anotacoes.append(dict(
            x=pos_central,
            y=1.05,
            xref='x',
            yref='paper',
            text=traduzir_mes(mes_nome),
            showarrow=False,
            font=dict(size=14, color='white'),
            xanchor='center'
        ))

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
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(t=80, b=50, l=50, r=50),
        height=500,
        bargap=0,
        bargroupgap=0
    )

    fig1 = apply_universal_theme(fig1, current_theme)
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    ## 2️⃣ GRÁFICO ORIGINAL - Casos por Origem
    st.subheader("Casos por origem (Mensal)")
    
    df_ordenado = df_filtrado.sort_values("AnoMes")
    meses_display_ordenados = df_ordenado["AnoMes_Display"].unique()
    
    casos_origem = df_filtrado.groupby(["AnoMes", "AnoMes_Display", "Origem"]).size().reset_index(name="Total")
    casos_origem = casos_origem.sort_values("AnoMes")

    fig2 = px.bar(
        casos_origem, 
        x="AnoMes_Display", 
        y="Total", 
        color="Origem", 
        text="Total",
        barmode='group'
    )
    fig2.update_traces(textposition='outside')
    fig2.update_xaxes(
        type='category', 
        categoryorder='array', 
        categoryarray=meses_display_ordenados,
        title_text="Mês/Ano"
    )
    fig2 = apply_universal_theme(fig2, current_theme)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    ## 3️⃣ GRÁFICO ORIGINAL - Reaberturas por Mês
    st.subheader("Reaberturas por mês")

    df_filtrado_copy = df_filtrado.copy().assign(
        Ano=lambda x: x['Ano'].astype(str),
        MesNum=lambda x: x['Abertura'].dt.month,
        MesNome=lambda x: x['Abertura'].dt.strftime('%b')
    )

    reaberturas_mes = df_filtrado_copy.groupby(['MesNum', 'MesNome', 'Ano'])['Qt Reab.'].sum().reset_index(name='Total')
    reaberturas_mes['Total'] = reaberturas_mes['Total'].astype(int)
    reaberturas_mes = reaberturas_mes.sort_values(['MesNum', 'Ano'])

    cores_por_ano = {
        '2023': '#ff7f0e',
        '2024': '#aec7e8',
        '2025': '#1f77b4'
    }

    meses_unicos = reaberturas_mes[['MesNum', 'MesNome']].drop_duplicates().sort_values('MesNum')
    meses_lista = meses_unicos.to_dict('records')

    barras_x = []
    barras_y = []
    barras_cor = []
    barras_texto = []
    tickvals = []
    ticktext = []
    mes_posicoes = {}
    contador = 0

    for mes in meses_lista:
        mes_num = mes['MesNum']
        mes_nome = mes['MesNome']
        
        dados_mes = reaberturas_mes[reaberturas_mes['MesNum'] == mes_num]
        anos_no_mes = dados_mes['Ano'].unique()
        
        inicio_mes = contador
        
        for ano in sorted(anos_no_mes):
            total = dados_mes[dados_mes['Ano'] == ano]['Total'].values[0]
            
            barras_x.append(contador)
            barras_y.append(total)
            barras_cor.append(cores_por_ano.get(ano, '#333333'))
            barras_texto.append(str(total))
            
            tickvals.append(contador)
            ticktext.append(ano)
            
            contador += 1
        
        mes_posicoes[mes_nome] = (inicio_mes + contador - 1) / 2
        contador += 2

    fig3 = go.Figure()

    fig3.add_trace(go.Bar(
        x=barras_x,
        y=barras_y,
        marker_color=barras_cor,
        text=barras_texto,
        textposition='outside',
        width=0.7
    ))

    anotacoes = []
    for mes_nome, pos_central in mes_posicoes.items():
        anotacoes.append(dict(
            x=pos_central,
            y=1.05,
            xref='x',
            yref='paper',
            text=traduzir_mes(mes_nome),
            showarrow=False,
            font=dict(size=14, color='white'),
            xanchor='center'
        ))

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
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(t=80, b=50, l=50, r=50),
        height=500,
        bargap=0,
        bargroupgap=0
    )

    fig3 = apply_universal_theme(fig3, current_theme)
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    ## 4️⃣ GRÁFICO ORIGINAL - Top 10 Contas
    st.subheader("Top 10 contas com mais casos")
    
    top_contas = df_filtrado["Conta_Resumida"].value_counts().nlargest(10).reset_index()
    top_contas.columns = ["Conta", "Total"]

    fig4 = px.bar(
        top_contas, 
        x="Conta", 
        y="Total", 
        text="Total"
    )
    fig4.update_traces(textposition='outside')
    fig4.update_layout(xaxis={'categoryorder':'total descending'})
    fig4 = apply_universal_theme(fig4, current_theme)
    st.plotly_chart(fig4, use_container_width=True)

with tab5:
    ## 5️⃣ GRÁFICO ORIGINAL - Casos por Responsável (COMPLETO)
    st.subheader("Casos por Responsável (Mensal)")
    
    anos_disponiveis = sorted(df_filtrado["Ano"].unique())
    ano_selecionado = st.selectbox("Selecione o ano:", anos_disponiveis, index=len(anos_disponiveis)-1)
    
    df_ano = (df_filtrado[df_filtrado["Ano"] == ano_selecionado]
          .copy()
          .assign(
              Primeiro_Nome=lambda x: x["Responsável"].str.split().str[0].fillna("Não informado")
          ))
    
    casos_resp = (df_ano.groupby(["AnoMes", "AnoMes_Display", "Primeiro_Nome"])
                .size()
                .reset_index(name="Total"))
    
    casos_resp = casos_resp.sort_values(["AnoMes", "Total"], ascending=[True, False])
    
    # MÉTRICAS RESUMO ORIGINAIS - Centralizadas
    col1, col2, col3, col4 = st.columns(4)
    
    total_casos = casos_resp["Total"].sum()
    media_mensal = casos_resp.groupby("AnoMes_Display")["Total"].sum().mean()
    responsavel_top = casos_resp.groupby("Primeiro_Nome")["Total"].sum().idxmax()
    casos_top = casos_resp.groupby("Primeiro_Nome")["Total"].sum().max()
    
    with col1:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h4 style="margin-bottom: 0; padding-bottom: 2px;">📊 Total de casos no ano</h4>
                <h2 style="margin-top: 0px; padding-top: 0; color: #1f77b4;">{total_casos:,}</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h4 style="margin-bottom: 0; padding-bottom: 2px;">📈 Média Mensal</h4>
                <h2 style="margin-top: 0px; padding-top: 0; color: #ff7f0e;">{media_mensal:.1f}</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h4 style="margin-bottom: 0; padding-bottom: 2px;">🏆 Top Responsável</h4>
                <h2 style="margin-top: 0px;padding-top: 0; color: #2ca02c;">{responsavel_top}</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h4 style="margin-bottom: 0; padding-bottom: 2px;">🎯 Total casos do top no ano</h4>
                <h2 style="margin-top: 0px; padding-top: 0; color: #d62728;">{casos_top:,}</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # GRÁFICO PRINCIPAL ORIGINAL
    pivot_data = casos_resp.pivot(index="AnoMes_Display", columns="Primeiro_Nome", values="Total").fillna(0)
    
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e', '#f1c40f', '#95a5a6']
    
    fig5 = go.Figure()
    
    for i, responsavel in enumerate(pivot_data.columns):
        fig5.add_trace(go.Bar(
            name=responsavel,
            x=pivot_data.index,
            y=pivot_data[responsavel],
            text=pivot_data[responsavel].astype(int),
            textposition='outside',
            marker_color=colors[i % len(colors)],
            marker_line_color='white',
            marker_line_width=1,
            hovertemplate=f'<b>{responsavel}</b><br>Mês: %{{x}}<br>Casos: %{{y}}<extra></extra>'
        ))
    
    max_value = pivot_data.values.max()
    
    fig5.update_layout(
        title={
            'text': 'Distribuição de Casos por Responsável ao Longo dos Meses',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': 'white', 'family': 'Arial Black'}
        },
        xaxis_title="Período",
        yaxis_title="Número de Casos",
        barmode='group',
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(255,255,255,0.3)",
            borderwidth=1,
            font=dict(color="white")
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif", size=12, color="white"),
        margin=dict(t=100, b=150, l=60, r=60)
    )
    
    fig5.add_annotation(
        text=f"🔥 Pico: {int(max_value)} casos",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=12, color="#e74c3c", family="Arial Bold"),
        bgcolor="rgba(231, 76, 60, 0.1)",
        bordercolor="#e74c3c",
        borderwidth=1
    )
    
    fig5.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        showline=True,
        linewidth=2,
        linecolor='rgba(128,128,128,0.3)',
        tickangle=0,
        categoryorder='array',
        categoryarray=casos_resp.sort_values("AnoMes")["AnoMes_Display"].unique(),
        tickfont=dict(color="white")
    )
    
    fig5.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        showline=True,
        linewidth=2,
        linecolor='rgba(128,128,128,0.3)',
        tickfont=dict(color="white")
    )
    
    fig5 = apply_universal_theme(fig5, current_theme)
    st.plotly_chart(fig5, use_container_width=True)
    
    # SEÇÕES ORIGINAIS - Análise Detalhada
    with st.expander("📋 Análise Detalhada por Responsável", expanded=False):
        resumo_responsaveis = casos_resp.groupby("Primeiro_Nome").agg({
            "Total": ["sum", "mean", "max", "min"]
        }).round(1)
        
        resumo_responsaveis.columns = ["Total Geral", "Média Mensal", "Máximo", "Mínimo"]
        resumo_responsaveis = resumo_responsaveis.sort_values("Total Geral", ascending=False)
        
        resumo_responsaveis["Variação"] = resumo_responsaveis["Máximo"] - resumo_responsaveis["Mínimo"]
        resumo_responsaveis["% do Total"] = (resumo_responsaveis["Total Geral"] / resumo_responsaveis["Total Geral"].sum() * 100).round(1)
        
        def highlight_max(s):
            is_max = s == s.max()
            return ['background-color: teal' if v else '' for v in is_max]
        
        styled_df = resumo_responsaveis.style.format({
            "Total Geral": "{:.0f}",
            "Média Mensal": "{:.1f}",
            "Máximo": "{:.0f}",
            "Mínimo": "{:.0f}",
            "Variação": "{:.0f}",
            "% do Total": "{:.1f}%"
        }).apply(highlight_max, subset=["Total Geral"])
        
        st.dataframe(styled_df, use_container_width=True)
    
    # Ranking Original
    with st.expander("📊 Ranking de Responsáveis", expanded=False):
        ranking_data = resumo_responsaveis.reset_index()
        
        fig_ranking = px.bar(
            ranking_data.head(10),
            x="Primeiro_Nome",
            y="Total Geral",
            text="Total Geral",
            title=f"Top 10 Responsáveis por Total de Casos em {ano_selecionado}",
            color="Total Geral",
            color_continuous_scale="Blues"
        )
        
        fig_ranking.update_traces(
            textposition='outside',
            textfont=dict(color='white', size=12, family='Arial Bold')
        )
        
        max_value = ranking_data.head(10)["Total Geral"].max()
        
        fig_ranking.update_layout(
            xaxis_title="Responsável",
            yaxis_title="Total de Casos",
            showlegend=False,
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=80, b=60, l=60, r=60),
            yaxis=dict(range=[0, max_value * 1.15]),
            font=dict(color='white'),
            title=dict(
                font=dict(color='white', size=16),
                x=0.5,
                xanchor='center'
            )
        )
        
        fig_ranking.update_xaxes(tickangle=45, tickfont=dict(color='white'))
        fig_ranking.update_yaxes(tickfont=dict(color='white'))

        fig_ranking = apply_universal_theme(fig_ranking, current_theme)       
        st.plotly_chart(fig_ranking, use_container_width=True)

with tab6:
    ## 6️⃣ GRÁFICO ORIGINAL - Casos por Tipo
    st.subheader("Casos por Tipo (Mensal)")
    
    df_ordenado = df_filtrado.sort_values("AnoMes")
    meses_display_ordenados = df_ordenado["AnoMes_Display"].unique()
    
    casos_tipo = df_filtrado.groupby(["AnoMes", "AnoMes_Display", "Tipo"]).size().reset_index(name="Total")
    casos_tipo = casos_tipo.sort_values("AnoMes")

    fig6 = px.bar(
        casos_tipo,
        x="AnoMes_Display",
        y="Total",
        color="Tipo",
        text="Total",
        title=" ",
        barmode='group'
    )
    fig6.update_traces(textposition='outside')
    fig6.update_xaxes(
        type='category',
        categoryorder='array',
        categoryarray=meses_display_ordenados,
        title_text="Mês/Ano"
    )
    fig6 = apply_universal_theme(fig6, current_theme)
    st.plotly_chart(fig6, use_container_width=True)

with tab7:
    ## 7️⃣ GRÁFICO ORIGINAL - Índice de Resolubilidade
    st.subheader("Índice de Resolubilidade")

    # Criar uma cópia independente com todas as transformações necessárias
    df_resolubilidade = (
        df_filtrado
        .copy()
        .assign(
            Resolvido_Mesmo_Dia=lambda x: x["Abertura"] == x["Solução"],
            Ano=lambda x: x["Abertura"].dt.year,
            Mes=lambda x: x["Abertura"].dt.month,
            Mes_Display=lambda x: x["Abertura"].apply(formatar_mes_pt),
            Mes_Ano_Ordenacao=lambda x: x["Ano"] * 100 + x["Mes"],
            Primeiro_Nome=lambda x: x["Responsável"].str.split().str[0].fillna("Não informado")
        )
    )

    # Ordenar os meses de forma segura (sem modificar o DataFrame original)
    meses_ordenados = (
        df_resolubilidade[["Mes_Display", "Mes_Ano_Ordenacao"]]
        .drop_duplicates()
        .sort_values("Mes_Ano_Ordenacao")
    )

    meses_disponiveis = meses_ordenados["Mes_Display"].tolist()
    mes_escolhido = st.selectbox("Selecione o mês:", meses_disponiveis, index=len(meses_disponiveis)-1)

    # Filtrar para o mês escolhido
    df_mes = df_resolubilidade.loc[df_resolubilidade["Mes_Display"] == mes_escolhido].copy()

    # Agregações seguras usando groupby
    total_casos = (
        df_mes
        .groupby("Primeiro_Nome", observed=True)
        .size()
        .reset_index(name="Total_Casos")
    )

    resolvidos_mesmo_dia = (
        df_mes.loc[df_mes["Resolvido_Mesmo_Dia"]]
        .groupby("Primeiro_Nome", observed=True)
        .size()
        .reset_index(name="Resolvidos_Mesmo_Dia")
    )

    # Merge seguro
    resumo = (
        total_casos
        .merge(
            resolvidos_mesmo_dia,
            on="Primeiro_Nome",
            how="left"
        )
        .fillna(0)
        .assign(
            Perc_Resolubilidade=lambda x: (x["Resolvidos_Mesmo_Dia"] / x["Total_Casos"]) * 100
        )
    )

    # Criar o gráfico
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
        y=resumo["Perc_Resolubilidade"],
        name="% Resolubilidade",
        mode="lines+markers+text",
        text=[f"{v:.1f}%" for v in resumo["Perc_Resolubilidade"]],
        textposition="top center",
        yaxis="y2"
    ))

    fig7.update_layout(
        title=f"Índice de resolubilidade - {traduzir_mes(mes_escolhido)}",
        xaxis_title="Responsável",
        yaxis=dict(title="Quantidade de casos"),
        yaxis2=dict(title="% Resolubilidade", overlaying="y", side="right"),
        barmode="group",
        legend=dict(title="Legenda", x=1.05, y=1),
        margin=dict(r=100),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    fig7 = apply_universal_theme(fig7, current_theme)
    st.plotly_chart(fig7, use_container_width=True)
