import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

st.set_page_config(page_title="Dashboard SP500", layout="wide")
st.title("📊 S&P500")

# ================== CONFIG ==================
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]
ALERTA_DIAS = 7
VENTANA_NOTICIAS_DIAS = 7

# ================== Lista de tickers ==================
sp500_tickers = [
    "AAPL"
]

# ================== FUNCIONES ==================
def analizar_SP500_profesional(ticker_symbol):
    try:
        yf_ticker = ticker_symbol.replace('.', '-')
        t = yf.Ticker(yf_ticker)
        hist = t.history(period="15mo")
        if hist.empty or len(hist) < 200:
            return None

        nombre_accion = t.info.get('longName', ticker_symbol)
        hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]

        c_actual = hist['Close'].iloc[-1]
        h_5d = hist['High'].tail(5).max()
        l_5d = hist['Low'].tail(5).min()
        pivot = (h_5d + l_5d + c_actual) / 3
        resistencia = (2 * pivot) - l_5d
        soporte = (2 * pivot) - h_5d

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
            "Ticker": ticker_symbol,
            "Nombre": nombre_accion,
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

# ================== Cache nominal ==================
@st.cache_data(show_spinner=True, ttl=3600, max_entries=3)
def generar_scanner(cache_key):
    resultados = []
    for tick in sp500_tickers:
        res = analizar_SP500_profesional(tick)
        if res:
            resultados.append(res)
    df = pd.DataFrame(resultados)
    if "Score" in df.columns:
        df = df.sort_values(by="Score", ascending=False)
    return df

# ================== Botón refrescar datos ==================
if st.button("🔄 Actualizar datos del Scanner"):
    df = generar_scanner("scanner_sp500_v1")
    st.session_state['last_refresh'] = datetime.now()
    st.success("Datos actualizados correctamente")

# ================== Última actualización ==================
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = datetime.now()
st.sidebar.markdown(f"**Última actualización:** {st.session_state['last_refresh'].strftime('%d/%m/%Y %H:%M:%S')}")

# ================== Cargar datos iniciales ==================
try:
    df
except NameError:
    df = generar_scanner("scanner_sp500_v1")

if df.empty:
    st.error("No se pudieron generar datos del scanner.")
    st.stop()

# ================== Filtros sidebar ==================
st.sidebar.header("Filtros")
score_min, score_max = st.sidebar.slider("Score mínimo y máximo", 0, 10, (0,10))
señales = df["Señal"].unique()
señal_filtrada = st.sidebar.multiselect("Filtrar por Señal", señales, default=señales)
df_filtrado = df[
    (df["Score"] >= score_min) &
    (df["Score"] <= score_max) &
    (df["Señal"].isin(señal_filtrada))
]

if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# ================== Tabs ==================
tab1, tab2, tab3, tab4 = st.tabs(["📋 Scanner","📈 Gráfico","📅 Earnings","📰 Noticias"])

# ------------------ TAB 1: Scanner ------------------
with tab1:
    accion_scanner = st.selectbox("Selecciona acción", df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"], key="scanner_select")
    st.dataframe(df_filtrado, use_container_width=True)

# ------------------ TAB 2: Gráfico ------------------
with tab2:
    accion_graf = st.selectbox("Selecciona acción para gráfico", df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"], key="grafico_select")
    ticker = accion_graf.split(" - ")[0]
    hist = yf.Ticker(ticker).history(period="1y")
    hist["SMA20"] = hist["Close"].rolling(20).mean()
    hist["SMA50"] = hist["Close"].rolling(50).mean()
    hist["SMA200"] = hist["Close"].rolling(200).mean()
    fila = df_filtrado[df_filtrado["Ticker"] == ticker].iloc[0]
    soporte = fila["Soporte"]
    resistencia = fila["Resistencia"]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=hist.index,
                                 open=hist["Open"], high=hist["High"],
                                 low=hist["Low"], close=hist["Close"],
                                 name="Precio"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA20"], name="SMA20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA50"], name="SMA50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA200"], name="SMA200"), row=1, col=1)
    fig.add_trace(go.Scatter(x=[hist.index[0], hist.index[-1]], y=[soporte, soporte], name="Soporte", line=dict(dash='dash', color='green')), row=1, col=1)
    fig.add_trace(go.Scatter(x=[hist.index[0], hist.index[-1]], y=[resistencia,resistencia], name="Resistencia", line=dict(dash='dash', color='red')), row=1, col=1)
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volumen"), row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=800)
    st.plotly_chart(fig, use_container_width=True)

# ------------------ TAB 3: Earnings ------------------
with tab3:
    accion_earn = st.selectbox("Selecciona acción para Earnings", df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"], key="earnings_select")
    ticker = accion_earn.split(" - ")[0]

    url_fut = f"https://finnhub.io/api/v1/calendar/earnings?symbol={ticker}&from={datetime.now().date()}&to={(datetime.now() + timedelta(days=60)).date()}&token={FINNHUB_API_KEY}"
    future_earnings = requests.get(url_fut).json().get("earningsCalendar", [])

    url_pas = f"https://finnhub.io/api/v1/stock/earnings?symbol={ticker}&token={FINNHUB_API_KEY}"
    past_earnings = requests.get(url_pas).json()

    st.subheader("Próximos resultados")
    if future_earnings:
        for e in future_earnings:
            fecha = e.get("date")
            hora = e.get("hour","")
            st.write(f"📌 {fecha} {hora}")
            dias_restantes = (pd.to_datetime(fecha).date() - datetime.now().date()).days
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

# ------------------ TAB 4: Noticias ------------------
with tab4:
    accion_news = st.selectbox("Selecciona acción para Noticias", df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"], key="news_select")
    ticker = accion_news.split(" - ")[0]
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=VENTANA_NOTICIAS_DIAS)
    url_news = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={fecha_inicio}&to={fecha_fin}&token={FINNHUB_API_KEY}"
    noticias = requests.get(url_news).json()

    st.subheader(f"Noticias últimos {VENTANA_NOTICIAS_DIAS} días")
    if noticias:
        for n in noticias[:10]:
            fecha = datetime.fromtimestamp(n.get("datetime"))
            st.markdown(f"**{n.get('headline')}**")
            st.write(f"{n.get('source')} | {fecha.strftime('%d/%m/%Y')}")
            st.write(f"[Leer noticia]({n.get('url')})")
            st.markdown("---")
    else:
        st.info("No hay noticias recientes.")
