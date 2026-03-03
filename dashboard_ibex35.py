import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

st.set_page_config(page_title="Dashboard IBEX35", layout="wide")
st.title("📊 IBEX35")

# ================== CONFIG ==================
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]
ALERTA_DIAS = 7
VENTANA_NOTICIAS_DIAS = 7

# ================== TICKERS ==================
ibex35_tickers = [
    "ACS.MC","ACX.MC","AENA.MC","AMS.MC","ANA.MC","BBVA.MC","BKT.MC",
    "CABK.MC","CLNX.MC","COL.MC","ENG.MC","ELE.MC","FER.MC","FDR.MC",
    "GRF.MC","IAG.MC","IBE.MC","IDR.MC","ITX.MC","LOG.MC","MAP.MC",
    "MEL.MC","MRL.MC","NTGY.MC","PUIG.MC","RED.MC","REP.MC","ROVI.MC",
    "SAB.MC","SAN.MC","SCYR.MC","SLR.MC","TEF.MC","UNI.MC"
]

# ================== FUNCIÓN ANALÍTICA ==================
def analizar_ibex35_profesional(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period="15mo")

        if hist.empty or len(hist) < 200:
            return None

        nombre_accion = t.info.get('longName', ticker_symbol)

        c_actual = hist['Close'].iloc[-1]
        h_5d = hist['High'].tail(5).max()
        l_5d = hist['Low'].tail(5).min()

        pivot = (h_5d + l_5d + c_actual) / 3
        resistencia = (2 * pivot) - l_5d
        soporte = (2 * pivot) - h_5d

        rsi = ta.momentum.RSIIndicator(hist['Close'], 14).rsi().iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        sma50 = hist['Close'].rolling(50).mean().iloc[-1]
        sma200 = hist['Close'].rolling(200).mean().iloc[-1]

        atr = ta.volatility.AverageTrueRange(
            hist['High'], hist['Low'], hist['Close'], 14
        ).average_true_range().iloc[-1]

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

        stop_loss = max(soporte, c_actual - 1.5 * atr)
        take_profit = min(resistencia, c_actual + 2 * atr)

        return {
            "Ticker": ticker_symbol,
            "Nombre": nombre_accion,
            "Precio": round(c_actual, 2),
            "Score": score,
            "Señal": señal,
            "RSI": round(rsi, 2),
            "SMA20": round(sma20, 2),
            "SMA50": round(sma50, 2),
            "SMA200": round(sma200, 2),
            "Stop Loss": round(stop_loss, 2),
            "Take Profit": round(take_profit, 2)
        }

    except Exception:
        return None


# ================== SCANNER ROBUSTO ==================
@st.cache_data(show_spinner=True)
def generar_scanner():
    resultados = []

    for tick in ibex35_tickers:
        res = analizar_ibex35_profesional(tick)
        if res is not None:
            resultados.append(res)

    if not resultados:
        return pd.DataFrame()

    df = pd.DataFrame(resultados)

    if "Score" in df.columns:
        df = df.sort_values(by="Score", ascending=False)

    return df


# ================== BOTÓN ACTUALIZAR ==================
if st.button("🔄 Actualizar datos del Scanner"):
    with st.spinner("Ejecutando scanner..."):
        df = generar_scanner()
    st.success("Datos actualizados correctamente")

# ================== CARGA INICIAL SEGURA ==================
try:
    df
except NameError:
    df = generar_scanner()

if df.empty:
    st.error("El scanner no generó resultados. Posible fallo en descarga de datos.")
    st.stop()

# ================== FILTROS ==================
st.sidebar.header("Filtros")

score_min, score_max = st.sidebar.slider(
    "Rango de Score",
    min_value=0,
    max_value=10,
    value=(0, 10)
)

señales = df["Señal"].unique()
señal_filtrada = st.sidebar.multiselect(
    "Filtrar por Señal",
    señales,
    default=señales
)

df_filtrado = df[
    (df["Score"] >= score_min) &
    (df["Score"] <= score_max) &
    (df["Señal"].isin(señal_filtrada))
]

# ================== INFO DIAGNÓSTICO ==================
st.write("Total acciones escaneadas:", len(df))
st.write("Total después de filtros:", len(df_filtrado))

st.dataframe(df_filtrado, use_container_width=True)

if df_filtrado.empty:
    st.warning("No hay acciones con los filtros actuales.")
    st.stop()

# ================== SELECTOR ==================
accion = st.selectbox(
    "Selecciona una acción",
    df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"]
)

ticker = accion.split(" - ")[0]

# ================== HISTÓRICO ==================
hist = yf.Ticker(ticker).history(period="1y")

if hist.empty:
    st.error("No se pudieron descargar datos históricos")
    st.stop()

hist["SMA20"] = hist["Close"].rolling(20).mean()
hist["SMA50"] = hist["Close"].rolling(50).mean()
hist["SMA200"] = hist["Close"].rolling(200).mean()

fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.05, row_heights=[0.7, 0.3])

fig.add_trace(go.Candlestick(
    x=hist.index,
    open=hist["Open"],
    high=hist["High"],
    low=hist["Low"],
    close=hist["Close"],
    name="Precio"
), row=1, col=1)

fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA20"], name="SMA20"), row=1, col=1)
fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA50"], name="SMA50"), row=1, col=1)
fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA200"], name="SMA200"), row=1, col=1)

fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volumen"), row=2, col=1)

fig.update_layout(xaxis_rangeslider_visible=False, height=800)
st.plotly_chart(fig, use_container_width=True)
