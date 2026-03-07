import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import pytz

st.set_page_config(page_title="DESA Dashboard SP500", layout="wide")
st.title("📊 DESA S&P500")

# ================== CONFIG ==================
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]
ALERTA_DIAS = 7
VENTANA_NOTICIAS_DIAS = 7

# ================== Lista de tickers ==================
sp500_tickers = [
# Tu lista completa de tickers aquí
"AAPL","ABBV","ABNB","ABT","ACGL","ACN","ADBE","ADI","ADM","ADP",
# ...
]

# ================== FUNCIONES ==================
def normalize(value, min_val, max_val):
    if value is None:
        return 0.5
    return max(0, min(1, (value - min_val)/(max_val - min_val)))

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

        per = t.info.get('trailingPE', None)
        roe = t.info.get('returnOnEquity', None)
        deuda_equity = t.info.get('debtToEquity', None)
        crecimiento_ingresos = t.info.get('revenueGrowth', None)
        beta = t.info.get('beta', None)

        score_per = 1 - normalize(per, 5, 50)
        score_roe = normalize(roe, 0, 0.3)
        score_deuda = 1 - normalize(deuda_equity, 0, 2)
        score_crec = normalize(crecimiento_ingresos, 0, 0.3)
        score_fund = (score_per*0.25 + score_roe*0.25 + score_deuda*0.25 + score_crec*0.25)

        score_rsi = 1 - normalize(rsi, 30, 70)
        score_sma = sum([1 if c_actual > sma else 0 for sma in [sma20, sma50, sma200]]) / 3
        score_tec = (score_rsi*0.5 + score_sma*0.5)

        score_vol = 1 - normalize(atr_ratio, 0.01, 0.1)
        score_beta = 1 - normalize(beta, 0.5, 2)
        score_riesgo = (score_vol*0.5 + score_beta*0.5)

        score_final = score_fund*0.5 + score_tec*0.3 + score_riesgo*0.2
        score_final_10 = round(score_final*10,1)

        señal = "BUY" if score_final_10 >= 7 else "HOLD" if score_final_10 >= 4 else "SELL"

        stop_loss = max(soporte, c_actual - 1.5*atr)
        take_profit = min(resistencia, c_actual + 2*atr)

        return {
            "Ticker": ticker_symbol,
            "Nombre": nombre_accion,
            "Precio": round(c_actual,2),
            "Score": score_final_10,
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

# ================== GENERAR SCANNER ==================
@st.cache_data(show_spinner=True, ttl=3600, max_entries=3)
def generar_scanner(cache_key):
    resultados = []
    total = len(sp500_tickers)
    progress_bar = st.progress(0)
    progress_text = st.empty()
    for i, tick in enumerate(sp500_tickers):
        res = analizar_SP500_profesional(tick)
        if res:
            resultados.append(res)
        porcentaje = int((i+1)/total*100)
        progress_bar.progress((i+1)/total)
        progress_text.text(f"Procesando acciones... {porcentaje}% completado")
    df = pd.DataFrame(resultados)
    if "Score" in df.columns:
        df = df.sort_values(by="Score", ascending=False)
    progress_text.text("¡Procesamiento completado!")
    return df

# ================== CARGA DE DATOS ==================
tz_madrid = pytz.timezone("Europe/Madrid")
if 'df' not in st.session_state:
    st.session_state['df'] = generar_scanner("scanner_sp500_v1")
    st.session_state['last_refresh'] = datetime.now(tz_madrid)

if st.button("Actualizar datos"):
    generar_scanner.clear()
    st.session_state['df'] = generar_scanner("scanner_sp500_v1")
    st.session_state['last_refresh'] = datetime.now(tz_madrid)

df = st.session_state['df']

# ================== SIDEBAR ==================
st.sidebar.markdown(f"**Dia:** {datetime.now(tz_madrid).strftime('%d/%m/%Y')}")
st.sidebar.markdown(f"**Hora:** {datetime.now(tz_madrid).strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**Actualización:** {st.session_state['last_refresh'].astimezone(tz_madrid).strftime('%d/%m/%Y %H:%M:%S')}")
st.sidebar.header("Filtros")

# ================== TAB 2 – HISTÓRICO ==================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Acciones","📈 Gráfico","📊 Resultados","📰 Noticias","🌍 Other"])
with tab2:
    ticker = "AAPL"  # Ejemplo; reemplaza con tu selección dinámica
    hist = yf.Ticker(ticker).history(period="1y")

    # Convertir timestamps ya tz-aware a hora Madrid
    hist.index = hist.index.tz_convert('Europe/Madrid')

    hist["SMA20"] = hist["Close"].rolling(20).mean()
    hist["SMA50"] = hist["Close"].rolling(50).mean()
    hist["SMA200"] = hist["Close"].rolling(200).mean()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=hist.index,
                                 open=hist["Open"], high=hist["High"],
                                 low=hist["Low"], close=hist["Close"],
                                 name="Precio"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA20"], name="SMA20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA50"], name="SMA50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA200"], name="SMA200"), row=1, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=800)
    st.plotly_chart(fig, use_container_width=True)

# ================== TAB 4 – NOTICIAS ==================
with tab4:
    ticker = "AAPL"  # Ejemplo; reemplaza con tu selección dinámica
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=VENTANA_NOTICIAS_DIAS)
    url_news = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={fecha_inicio}&to={fecha_fin}&token={FINNHUB_API_KEY}"
    noticias = requests.get(url_news).json()

    st.subheader(f"Noticias últimos {VENTANA_NOTICIAS_DIAS} días")
    if noticias:
        for n in noticias[:10]:
            # Convertir timestamp UTC a hora Madrid
            fecha = pd.to_datetime(n.get("datetime"), unit='s', utc=True).tz_convert('Europe/Madrid')
            st.markdown(f"**{n.get('headline')}**")
            st.write(f"{n.get('source')} | {fecha.strftime('%d/%m/%Y %H:%M:%S')}")
            st.write(f"[Leer noticia]({n.get('url')})")
            st.markdown("---")
    else:
        st.info("No hay noticias recientes.")

# ================== TAB 5 ==================
with tab5:

    st.subheader("🌍 Crypto & Commodities")

    activos = {
        "Bitcoin": {"ticker": "BTC-USD", "moneda": "USD"},
        "Bitcoin €": {"ticker": "BTC-EUR", "moneda": "EUR"},
        "Oro": {"ticker": "GC=F", "moneda": "USD"},
        "Plata": {"ticker": "SI=F", "moneda": "USD"}
    }

    tickers = [v["ticker"] for v in activos.values()]

    # Descarga en una sola llamada (más eficiente)
    data = yf.download(tickers, period="1y", group_by="ticker", progress=False)

    datos_tabla = []
    historicos = {}

    for nombre, info in activos.items():

        ticker = info["ticker"]
        moneda = info["moneda"]

        if ticker in data.columns.get_level_values(0):

            hist = data[ticker].dropna()

            if not hist.empty:

                precio_actual = hist["Close"].iloc[-1]

                datos_tabla.append({
                    "Activo": nombre,
                    "Ticker": ticker,
                    "Precio Actual": round(precio_actual, 2),
                    "Moneda": moneda
                })

                historicos[nombre] = hist

    df_activos = pd.DataFrame(datos_tabla)

    st.subheader("📊 Precios actuales")
    st.dataframe(df_activos, use_container_width=True)

    st.subheader("📈 Histórico 1 año")

    for nombre, hist in historicos.items():

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines",
                name=nombre
            )
        )

        fig.update_layout(
            title=f"{nombre} - Histórico 1 año",
            xaxis_title="Fecha",
            yaxis_title="Precio",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
