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

# ================== Tickers ==================
ibex35_tickers = [
    "ACS.MC","ACX.MC","AENA.MC","AMS.MC","ANA.MC","BBVA.MC","BKT.MC",
    "CABK.MC","CLNX.MC","COL.MC","ENG.MC","ELE.MC","FER.MC","FDR.MC",
    "GRF.MC","IAG.MC","IBE.MC","IDR.MC","ITX.MC","LOG.MC","MAP.MC",
    "MEL.MC","MRL.MC","NTGY.MC","PUIG.MC","RED.MC","REP.MC","ROVI.MC",
    "SAB.MC","SAN.MC","SCYR.MC","SLR.MC","TEF.MC","UNI.MC"
]

# ================== FUNCIONES ==================
def analizar_ibex35_profesional(ticker_symbol):
    try:
        yf_ticker = ticker_symbol.replace('.', '-')
        t = yf.Ticker(yf_ticker)
        hist = t.history(period="15mo")
        if hist.empty:
            print(f"❌ Histórico vacío: {ticker_symbol}")
            return {
                "Ticker": ticker_symbol,
                "Nombre": ticker_symbol,
                "Precio": None,
                "Score": 0,
                "Señal": "N/A",
                "RSI": None,
                "SMA20": None,
                "SMA50": None,
                "SMA200": None,
                "ATR": None,
                "ATR Ratio": None,
                "Volatilidad Anual": None,
                "Volumen Actual": None,
                "Volumen Medio (Mes)": None,
                "Volumen Relativo": None,
                "Soporte": None,
                "Resistencia": None,
                "Stop Loss": None,
                "Take Profit": None
            }

        nombre_accion = t.info.get('longName', ticker_symbol)
        hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]

        c_actual = hist['Close'].iloc[-1]

        # Calcular indicadores solo si hay suficientes datos
        rsi = ta.momentum.RSIIndicator(hist['Close'], window=14).rsi().iloc[-1] if len(hist) >= 14 else None
        sma20 = ta.trend.sma_indicator(hist['Close'], window=20).iloc[-1] if len(hist) >= 20 else None
        sma50 = ta.trend.sma_indicator(hist['Close'], window=50).iloc[-1] if len(hist) >= 50 else None
        sma200 = ta.trend.sma_indicator(hist['Close'], window=200).iloc[-1] if len(hist) >= 200 else None
        atr = ta.volatility.AverageTrueRange(hist['High'], hist['Low'], hist['Close'], window=14).average_true_range().iloc[-1] if len(hist) >= 14 else None
        atr_ratio = atr / c_actual if atr else None
        volatilidad = hist['Close'].pct_change().rolling(252).std().iloc[-1] * (252**0.5) if len(hist) >= 252 else None
        vol_actual = hist['Volume'].iloc[-1] if 'Volume' in hist else None
        vol_medio_mes = hist['Volume'].tail(21).mean() if 'Volume' in hist and len(hist) >= 21 else None
        vol_relativo = vol_actual / vol_medio_mes if vol_actual and vol_medio_mes else None

        h_5d = hist['High'].tail(5).max() if len(hist) >= 5 else c_actual
        l_5d = hist['Low'].tail(5).min() if len(hist) >= 5 else c_actual

        pivot = (h_5d + l_5d + c_actual) / 3
        resistencia = (2 * pivot) - l_5d
        soporte = (2 * pivot) - h_5d

        # Calcular Score
        score = 0
        if rsi is not None:
            if rsi < 40: score += 2
            elif rsi > 70: score -= 2
        if sma20 is not None and c_actual > sma20: score += 2
        if sma50 is not None and c_actual > sma50: score += 1
        if sma200 is not None and c_actual > sma200: score += 1
        if vol_relativo is not None and vol_relativo > 1.2: score += 1

        # Señal
        if score >= 7:
            señal = "BUY"
        elif score >= 4:
            señal = "HOLD"
        else:
            señal = "SELL"

        # Stop loss y Take profit
        stop_loss = max(soporte, c_actual - 1.5*atr) if atr else None
        take_profit = min(resistencia, c_actual + 2*atr) if atr else None

        return {
            "Ticker": ticker_symbol,
            "Nombre": nombre_accion,
            "Precio": round(c_actual,2) if c_actual else None,
            "Score": score,
            "Señal": señal,
            "RSI": round(rsi,2) if rsi else None,
            "SMA20": round(sma20,2) if sma20 else None,
            "SMA50": round(sma50,2) if sma50 else None,
            "SMA200": round(sma200,2) if sma200 else None,
            "ATR": round(atr,2) if atr else None,
            "ATR Ratio": round(atr_ratio,4) if atr_ratio else None,
            "Volatilidad Anual": round(volatilidad,4) if volatilidad else None,
            "Volumen Actual": int(vol_actual) if vol_actual else None,
            "Volumen Medio (Mes)": int(vol_medio_mes) if vol_medio_mes else None,
            "Volumen Relativo": round(vol_relativo,2) if vol_relativo else None,
            "Soporte": round(soporte,2) if soporte else None,
            "Resistencia": round(resistencia,2) if resistencia else None,
            "Stop Loss": round(stop_loss,2) if stop_loss else None,
            "Take Profit": round(take_profit,2) if take_profit else None
        }

    except Exception as e:
        print(f"❌ Error en {ticker_symbol}: {e}")
        return {
            "Ticker": ticker_symbol,
            "Nombre": ticker_symbol,
            "Precio": None,
            "Score": 0,
            "Señal": "N/A",
            "RSI": None,
            "SMA20": None,
            "SMA50": None,
            "SMA200": None,
            "ATR": None,
            "ATR Ratio": None,
            "Volatilidad Anual": None,
            "Volumen Actual": None,
            "Volumen Medio (Mes)": None,
            "Volumen Relativo": None,
            "Soporte": None,
            "Resistencia": None,
            "Stop Loss": None,
            "Take Profit": None
        }

# ================== GENERAR CSV EN MEMORIA ==================
@st.cache_data(show_spinner=True)
def generar_scanner_ibex35():
    resultados = []
    for tick in ibex35_tickers:
        res = analizar_ibex35_profesional(tick)
        if res:
            resultados.append(res)
    df = pd.DataFrame(resultados).sort_values(by="Score", ascending=False)
    return df

# ================== BOTÓN ACTUALIZAR ==================
if st.button("🔄 Actualizar datos del Scanner"):
    with st.spinner("Ejecutando scanner..."):
        df_ibex35 = generar_scanner_ibex35()
    st.success("Datos actualizados correctamente")

# ================== CARGAR DATAFRAME ==================
try:
    df_ibex35
except NameError:
    try:
        df_ibex35 = generar_scanner_ibex35()
    except Exception as e:
        st.error(f"No se pudieron generar datos del IBEX35: {e}")
        st.stop()

# ================== FILTROS ==================
st.sidebar.header("Filtros")
score_min = st.sidebar.slider("Score mínimo", 0, 10, 0)
score_max = st.sidebar.slider("Score máximo", 0, 10, 10)
señales = df_ibex35["Señal"].unique()
señal_filtrada = st.sidebar.multiselect("Filtrar por Señal", señales, default=señales)

df_filtrado = df_ibex35[
    (df_ibex35["Score"] >= score_min) &
    (df_ibex35["Score"] <= score_max) &
    (df_ibex35["Señal"].isin(señal_filtrada))
]

st.dataframe(df_filtrado, use_container_width=True)
if df_filtrado.empty:
    st.info("No hay resultados que cumplan los filtros.")
    st.stop()

# ================== SELECTOR ==================
accion = st.selectbox("Selecciona una acción",
                      df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"])
ticker = accion.split(" - ")[0]
fila = df_filtrado[df_filtrado["Ticker"] == ticker].iloc[0]

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

# ================== FINNHUB ==================
def obtener_earnings_futuros(ticker):
    url = f"https://finnhub.io/api/v1/calendar/earnings?symbol={ticker}&from={datetime.now().date()}&to={(datetime.now() + timedelta(days=60)).date()}&token={FINNHUB_API_KEY}"
    r = requests.get(url).json()
    return r.get("earningsCalendar", []) if isinstance(r, dict) else []

def obtener_earnings_pasados(ticker):
    url = f"https://finnhub.io/api/v1/stock/earnings?symbol={ticker}&token={FINNHUB_API_KEY}"
    r = requests.get(url).json()
    return r if isinstance(r, list) else []

def obtener_noticias(ticker):
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=VENTANA_NOTICIAS_DIAS)
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={fecha_inicio}&to={fecha_fin}&token={FINNHUB_API_KEY}"
    r = requests.get(url).json()
    return r if isinstance(r, list) else []

future_earnings = obtener_earnings_futuros(ticker)
past_earnings = obtener_earnings_pasados(ticker)
noticias = obtener_noticias(ticker)

# ================== PRÓXIMOS RESULTADOS ==================
st.subheader("📅 Próximos resultados")
if future_earnings:
    for e in future_earnings:
        fecha = e.get("date")
        hora = e.get("hour", "")
        st.write(f"📌 {fecha} {hora}")
    fecha_resultado = pd.to_datetime(future_earnings[0].get("date"))
    dias_restantes = (fecha_resultado.date() - datetime.now().date()).days
    if dias_restantes <= ALERTA_DIAS:
        st.warning(f"🚨 Resultados en {dias_restantes} días")
else:
    st.info("No hay próximos resultados disponibles.")

# ================== RESULTADOS ANTERIORES ==================
st.subheader("📊 Resultados anteriores")
if past_earnings:
    for e in past_earnings[:6]:
        st.write(
            f"{e.get('period')} | Actual: {e.get('actual')} | Estimado: {e.get('estimate')} | Surprise: {e.get('surprisePercent')}%"
        )
else:
    st.info("No hay resultados anteriores disponibles.")

# ================== NOTICIAS ==================
st.subheader(f"📰 Noticias últimos {VENTANA_NOTICIAS_DIAS} días")
if noticias:
    for n in noticias:
        fecha = datetime.fromtimestamp(n.get("datetime"))
        st.markdown(f"**{n.get('headline')}**")
        st.write(f"{n.get('source')} | {fecha.strftime('%d/%m/%Y')}")
        st.write(f"[Leer noticia]({n.get('url')})")
        st.markdown("---")
else:
    st.info("No hay noticias disponibles en los últimos días.")
