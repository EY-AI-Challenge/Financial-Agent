import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# ==========================================
# 1. CONFIGURAÇÃO BASE E ESTILOS
# ==========================================
st.set_page_config(page_title="EY AI Portfolio Copilot", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 0rem;}
    .stMetric {background-color: #1E1E1E; padding: 15px; border-radius: 5px; border: 1px solid #333;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GESTÃO DE ESTADO (SESSION STATE)
# ==========================================
if 'system_logs' not in st.session_state:
    st.session_state.system_logs = ["[SISTEMA] Inicialização do Motor de IA e LangChain concluída."]
if 'mensagens_langchain' not in st.session_state:
    st.session_state.mensagens_langchain = [{"role": "assistant", "content": "Olá. Sou o EY AI Copilot. Analisei a sua distribuição do Donut Chart e os indicadores de risco. O que deseja otimizar hoje?"}]

def add_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.system_logs.insert(0, f"[{timestamp}] {message}")

# ==========================================
# 3. MOTOR DE DADOS E SIMULAÇÃO
# ==========================================
@st.cache_data(ttl=600)
def generate_enterprise_mock_data():
    np.random.seed(42)
    datas = pd.date_range(end=datetime.today(), periods=365)
    ativos = ["AMZN", "AAPL", "GOOGL", "MSFT", "UDMY", "NXE", "SPY", "CDR.WA", "EH", "BTC-USD", "ETH-USD"]
    df = pd.DataFrame(index=datas)
    for ativo in ativos:
        vol = 0.04 if "USD" in ativo else 0.012 
        retornos = np.random.normal(0.0005, vol, len(datas))
        if "USD" in ativo: retornos[-30] = -0.15 
        df[ativo] = np.cumprod(1 + retornos) * 100
    return df, ativos

df_mercado, lista_ativos = generate_enterprise_mock_data()

portfolio = {
    "Ações Tech (AAPL, MSFT)": 45,
    "Criptomoedas (BTC, ETH)": 35,
    "Ativos Seguros (SPY)": 15,
    "Liquidez (Dinheiro)": 5
}

# ==========================================
# 4. BARRA LATERAL (SEGURANÇA & PARÂMETROS)
# ==========================================
with st.sidebar:
    st.image("https://github.com/EYAIChallenge/Overview/raw/main/EY_Logo_Beam_RGB_White_Yellow.png", width=80)
    st.title("Painel de Controlo")

    st.markdown("### 🔑 Ligação OpenAI (LangChain)")
    api_key = st.text_input("Chave da API (sk-...)", type="password", help="Cole aqui a sua chave durante a demo.")
    if api_key:
        st.success("API Ligada")
    else:
        st.error("API Desligada")

    st.markdown("### ⚙️ Parâmetros Base")
    capital_inicial = st.number_input("AUM (Capital) $", value=5000000, step=500000)
    perfil_risco = st.selectbox("Mandato de Risco:", ["Conservador", "Moderado", "Agressivo"])
    ativo_alvo = st.selectbox("Foco Analítico:", lista_ativos, index=1)

# ==========================================
# 5. HEADER E KPIS DE TOPO
# ==========================================
st.title("📊 EY Sentinel — Plataforma de Inteligência Financeira")

retorno_anual = (df_mercado[ativo_alvo].iloc[-1] / df_mercado[ativo_alvo].iloc[-252]) - 1
volatilidade_anual = df_mercado[ativo_alvo].pct_change().std() * np.sqrt(252)
sharpe = (retorno_anual - 0.03) / volatilidade_anual if volatilidade_anual > 0 else 0
max_drawdown = (df_mercado[ativo_alvo] / df_mercado[ativo_alvo].cummax() - 1).min()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Capital Atualizado", f"${capital_inicial * (1 + retorno_anual):,.0f}", f"{retorno_anual*100:.2f}% YTD")
col2.metric("Volatilidade (Risco)", f"{volatilidade_anual*100:.2f}%", "- Detetada Anomalia", delta_color="inverse")
col3.metric("Sharpe Ratio", f"{sharpe:.2f}", "Ajuste Premium")
col4.metric("Max Drawdown", f"{max_drawdown*100:.2f}%", "Risco Histórico", delta_color="inverse")
col5.metric("Status do LangChain", "🟢 ONLINE" if api_key else "🔴 S/ CHAVE", "A aguardar Prompt")

st.markdown("---")

# ==========================================
# 6. MOTOR DE INTERFACE (SEPARADORES)
# ==========================================
tab_dash, tab_tech, tab_risk, tab_ai, tab_logs = st.tabs([
    "📈 Visão Global (Donut)", "🔬 Análise Técnica", "🕸️ Mapa de Risco", "🤖 Agente LangChain", "🖥️ Logs"
])

with tab_dash:
    st.markdown("### Distribuição Atual do Fundo")
    c1, c2 = st.columns([1, 1])
    with c1:
        fig_donut = go.Figure(data=[go.Pie(
            labels=list(portfolio.keys()),
            values=list(portfolio.values()),
            hole=0.4,
            marker_colors=["#1f77b4", "#ff9900", "#2ca02c", "#d62728"]
        )])
        fig_donut.update_layout(height=400, template="plotly_dark", margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("💡 **Aviso Estratégico:** A exposição a Criptomoedas está em 35%. Consulte o Agente LangChain para estratégias de mitigação.")
        st.write(f"**Ativo em Foco:** {ativo_alvo} apresenta um Sharpe Ratio de {sharpe:.2f}.")

with tab_tech:
    st.markdown(f"### Inspeção Profunda: {ativo_alvo}")
    df_ohlc = pd.DataFrame(index=df_mercado.index[-90:])
    df_ohlc['Close'] = df_mercado[ativo_alvo].iloc[-90:]
    df_ohlc['Open'] = df_ohlc['Close'].shift(1).fillna(df_ohlc['Close'])
    df_ohlc['High'] = df_ohlc[['Open', 'Close']].max(axis=1) * 1.02
    df_ohlc['Low'] = df_ohlc[['Open', 'Close']].min(axis=1) * 0.98
    df_ohlc['MA20'] = df_ohlc['Close'].rolling(window=20).mean()
    df_ohlc['Upper'] = df_ohlc['MA20'] + 2 * df_ohlc['Close'].rolling(window=20).std()
    df_ohlc['Lower'] = df_ohlc['MA20'] - 2 * df_ohlc['Close'].rolling(window=20).std()

    fig_tech = go.Figure()
    fig_tech.add_trace(go.Candlestick(x=df_ohlc.index, open=df_ohlc['Open'], high=df_ohlc['High'], low=df_ohlc['Low'], close=df_ohlc['Close'], name='Preço'))
    fig_tech.add_trace(go.Scatter(x=df_ohlc.index, y=df_ohlc['Upper'], line=dict(color='gray', dash='dot'), name='Banda Superior'))
    fig_tech.add_trace(go.Scatter(x=df_ohlc.index, y=df_ohlc['Lower'], line=dict(color='gray', dash='dot'), name='Banda Inferior', fill='tonexty', fillcolor='rgba(128,128,128,0.1)'))
    fig_tech.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig_tech, use_container_width=True)

with tab_risk:
    st.markdown("### Deteção de Risco Oculto (Correlação)")
    corr = df_mercado.pct_change().corr()
    fig_corr = px.imshow(corr, text_auto=".1f", aspect="auto", color_continuous_scale="RdBu_r")
    fig_corr.update_layout(height=450, template="plotly_dark")
    st.plotly_chart(fig_corr, use_container_width=True)

with tab_ai:
    st.markdown("### 🧠 Conselheiro Estratégico (Powered by LangChain & OpenAI)")
    chat_container = st.container(height=350)
    with chat_container:
        for msg in st.session_state.mensagens_langchain:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Ex: Como devo proteger os meus 35% de Cripto no fim de semana?"):
        st.session_state.mensagens_langchain.append({"role": "user", "content": prompt})
        add_log(f"Chamada LangChain iniciada: '{prompt[:20]}...'")

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if not api_key:
                    erro_msg = "⚠️ ERRO: Insira a Chave OpenAI na barra lateral."
                    st.error(erro_msg)
                    st.session_state.mensagens_langchain.append({"role": "assistant", "content": erro_msg})
                else:
                    with st.spinner("A consultar o modelo preditivo OpenAI..."):
                        try:
                            chat_ia = ChatOpenAI(temperature=0.3, openai_api_key=api_key, model_name="gpt-3.5-turbo")
                            texto_contexto = f"A alocação do fundo é: {portfolio}. Perfil Risco: {perfil_risco}. Ativo Alvo: {ativo_alvo}. Responde como um consultor da EY."
                            system_prompt = SystemMessage(content=texto_contexto)
                            user_prompt = HumanMessage(content=prompt)

                            resposta = chat_ia.invoke([system_prompt, user_prompt])
                            st.markdown(resposta.content)
                            st.session_state.mensagens_langchain.append({"role": "assistant", "content": resposta.content})
                            add_log("Resposta LangChain recebida com sucesso.")

                        except Exception as e:
                            st.error(f"Falha na API: {e}")
                            add_log(f"Erro LangChain: {e}")

with tab_logs:
    st.markdown("### 🖥️ Terminal de Atividade")
    st.code("\n".join(st.session_state.system_logs), language="bash")
