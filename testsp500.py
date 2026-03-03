import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

st.set_page_config(page_title="Dashboard SP500 Mejorado", layout="wide")
st.title("📊 S&P500 Dashboard Mejorado")

# ================== CONFIG ==================
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]
ALERTA_DIAS = 7
VENTANA_NOTICIAS_DIAS = 7

# ================== Lista de tickers ==================
sp500_tickers = [
    "AAPL","MSFT","GOOGL","AMZN","TSLA","NVDA","META","BRK.B","JNJ","V",
    # (agrega el resto de tickers aquí o usa tu lista completa)
]

# ================== FUNCIONES ==================
@st.cache_data(show_spinner=True)
def descargar_datos(tickers):
    """Descarga histórica de todos los tickers de una vez."""
    try:
        data = yf.download(tickers, period="15mo", group_by='ticker', threads=True)
        return data
    except Exception as e:
        st.error(f"Error descargando datos: {e}")
        return None

def analizar_ticker(ticker, df_hist):
    """Calcula indicadores técnicos y score para un ticker."""
    try:
        hist = df_hist[ticker].dropna()
        if hist.empty or len(hist) < 200:
            return None

        c_actual = hist['Close'].iloc[-1]
        h_5d = hist['High'].tail(5).max()
        l_5d = hist['Low'].tail(5).min()
        pivot = (h_5d + l_5d + c_actual) / 3
        resistencia = (2*pivot - l_5d)
        soporte = (2*pivot - h_5d)

        rsi = ta.momentum.RSIIndicator(hist['Close'], window=14).rsi().iloc[-1]
        sma20 = ta.trend.sma_indicator(hist['Close'], window=20).iloc[-1]
        sma50 = ta.trend.sma_indicator(hist['Close'], window=50).iloc[-1]
        sma200 = ta.trend.sma_indicator(hist['Close'], window=200).iloc[-1]
        atr = ta.volatility.AverageTrueRange(hist['High'], hist['Low'], hist['Close'], window=14).average_true_range().iloc[-1]
        atr_ratio = atr / c_actual
        volatilidad = hist['Close'].pct_change().rolling(252).std().iloc[-1] * (252**0.5)
        vol_actual = hist['Volume'].iloc[-1]
        vol_medio_mes = hist['Volume'].tail(21).mean()
        vol_relativo = vol_actual / vol_medio_mes

        score = 0
        if rsi < 40: score += 2
        elif rsi > 70: score -= 2
        if c_actual > sma20: score += 2
        if c_actual > sma50: score += 1
        if c_actual > sma200: score += 1
        if vol_relativo > 1.2: score += 1

        if score >= 7:
            señal = "BUY"
        elif score >= 4:
            señal = "HOLD"
        else:
            señal = "SELL"

        stop_loss = max(soporte, c_actual - 1.5*atr)
        take_profit = min(resistencia, c_actual + 2*atr)

        return {
            "Ticker": ticker,
            "Precio": round(c_actual,2),
            "Score": score,
            "Señal": señal,
            "RSI": round(rsi,2),
            "SMA20": round(sma20,2),
            "SMA50": round(sma50,2),
            "SMA200": round(sma200,2),
            "ATR": round(atr,2),
            "ATR Ratio": round(atr_ratio,4),
            "Volatilidad Anual": round(volatilidad,4),
            "Volumen Actual": int(vol_actual),
            "Volumen Medio (Mes)": int(vol_medio_mes),
            "Volumen Relativo": round(vol_relativo,2),
            "Soporte": round(soporte,2),
            "Resistencia": round(resistencia,2),
            "Stop Loss": round(stop_loss,2),
            "Take Profit": round(take_profit,2)
        }
    except:
        return None

@st.cache_data(show_spinner=True)
def generar_scanner(tickers):
    df_hist = descargar_datos(tickers)
    resultados = []
    for tick in tickers:
        r = analizar_ticker(tick, df_hist)
        if r:
            resultados.append(r)
    df_result = pd.DataFrame(resultados).sort_values(by="Score", ascending=False)
    return df_result, df_hist

# ================== Finnhub ==================
def obtener_earnings_futuros(ticker):
    try:
        url = f"https://finnhub.io/api/v1/calendar/earnings?symbol={ticker}&from={datetime.now().date()}&to={(datetime.now()+timedelta(days=60)).date()}&token={FINNHUB_API_KEY}"
        r = requests.get(url).json()
        return r.get("earningsCalendar",[]) if isinstance(r, dict) else []
    except:
        return []

def obtener_earnings_pasados(ticker):
    try:
        url = f"https://finnhub.io/api/v1/stock/earnings?symbol={ticker}&token={FINNHUB_API_KEY}"
        r = requests.get(url).json()
        return r if isinstance(r,list) else []
    except:
        return []

def obtener_noticias(ticker):
    try:
        fecha_fin = datetime.now().date()
        fecha_inicio = fecha_fin - timedelta(days=VENTANA_NOTICIAS_DIAS)
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={fecha_inicio}&to={fecha_fin}&token={FINNHUB_API_KEY}"
        r = requests.get(url).json()
        return r if isinstance(r,list) else []
    except:
        return []

# ================== Generar scanner ==================
with st.spinner("Generando scanner..."):
    df, df_hist = generar_scanner(sp500_tickers)

# ================== Sidebar filtros ==================
st.sidebar.header("Filtros avanzados")
score_min, score_max = st.sidebar.slider("Score", 0, 10, (0,10))
rsi_min, rsi_max = st.sidebar.slider("RSI", 0, 100, (0,100))
sma200_min = st.sidebar.number_input("Precio > SMA200", 0.0, 10000.0, 0.0)
vol_min = st.sidebar.number_input("Volumen Relativo Min", 0.0, 5.0, 0.0)
señales = df["Señal"].unique()
señal_filtrada = st.sidebar.multiselect("Señal", señales, default=señales)

df_filtrado = df[
    (df["Score"]>=score_min) & (df["Score"]<=score_max) &
    (df["RSI"]>=rsi_min) & (df["RSI"]<=rsi_max) &
    (df["SMA200"]<=df["Precio"]) &
    (df["Volumen Relativo"]>=vol_min) &
    (df["Señal"].isin(señal_filtrada))
]

# ================== Tabs ==================
tab1, tab2, tab3, tab4 = st.tabs(["📋 Scanner","📈 Gráfico","📅 Earnings","📰 Noticias"])

with tab1:
    st.subheader("Scanner S&P500")
    def color_signal(val):
        if val=="BUY": return 'background-color: #b6f0b6'
        elif val=="HOLD": return 'background-color: #fff2b3'
        else: return 'background-color: #f0b6b6'
    st.dataframe(df_filtrado.style.applymap(color_signal, subset=["Señal"]), use_container_width=True)

with tab2:
    accion = st.selectbox("Selecciona acción", df_filtrado["Ticker"])
    hist = df_hist[accion].dropna()
    hist["SMA20"] = hist["Close"].rolling(20).mean()
    hist["SMA50"] = hist["Close"].rolling(50).mean()
    hist["SMA200"] = hist["Close"].rolling(200).mean()
    last_row = df_filtrado[df_filtrado["Ticker"]==accion].iloc[0]
    soporte = last_row["Soporte"]
    resistencia = last_row["Resistencia"]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7,0.3])
    fig.add_trace(go.Candlestick(x=hist.index, open=hist["Open"], high=hist["High"],
                                 low=hist["Low"], close=hist["Close"], name="Precio"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA20"], name="SMA20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA50"], name="SMA50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA200"], name="SMA200"), row=1, col=1)
    fig.add_trace(go.Scatter(x=[hist.index[0], hist.index[-1]], y=[soporte, soporte], name="Soporte", line=dict(dash='dash', color='green')), row=1, col=1)
    fig.add_trace(go.Scatter(x=[hist.index[0], hist.index[-1]], y=[resistencia,resistencia], name="Resistencia", line=dict(dash='dash', color='red')), row=1, col=1)
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volumen"), row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=700)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Próximos resultados")
    future_earnings = obtener_earnings_futuros(accion)
    past_earnings = obtener_earnings_pasados(accion)
    if future_earnings:
        for e in future_earnings:
            st.write(f"{e.get('date')} {e.get('hour','')}")
            dias_restantes = (pd.to_datetime(e.get("date")).date() - datetime.now().date()).days
            if dias_restantes <= ALERTA_DIAS:
                st.warning(f"🚨 Resultados en {dias_restantes} días")
    else:
        st.info("No hay próximos resultados disponibles.")

    st.subheader("Resultados anteriores")
    if past_earnings:
        for e in past_earnings[:6]:
            st.write(f"{e.get('period')} | Actual: {e.get('actual')} | Estimado: {e.get('estimate')} | Surprise: {e.get('surprisePercent')}%")
    else:
        st.info("No hay resultados anteriores disponibles.")

with tab4:
    st.subheader(f"Noticias últimos {VENTANA_NOTICIAS_DIAS} días")
    noticias = obtener_noticias(accion)
    if noticias:
        for n in noticias[:10]:
            fecha = datetime.fromtimestamp(n.get("datetime"))
            st.markdown(f"**{n.get('headline')}**")
            st.write(f"{n.get('source')} | {fecha.strftime('%d/%m/%Y')}")
            st.write(f"[Leer noticia]({n.get('url')})")
            st.markdown("---")
    else:
        st.info("No hay noticias recientes.")
