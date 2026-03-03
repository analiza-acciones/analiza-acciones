import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import subprocess
import yfinance as yf
import requests
from datetime import datetime, timedelta

# ================= CONFIG APIs =================
FINNHUB_API_KEY = "d6itlc9r01qleu95hcf0d6itlc9r01qleu95hcfg"
ALERTA_DIAS = 7
VENTANA_NOTICIAS_DIAS = 7  # Ventana de días para noticias
VENTANA_NOTICIAS_DIAS = 7

st.set_page_config(page_title="Dashboard SP500", layout="wide")
st.title("📊 Dashboard Profesional IBEX / S&P500")

# ==========================================================
# 🔄 ACTUALIZAR SCANNER
# ==========================================================
if st.button("🔄 Actualizar datos del Scanner"):
    with st.spinner("Ejecutando scanner_engine_sp500.py..."):
        subprocess.run(["python3", "scanner_engine_sp500.py"])
    st.success("Datos actualizados correctamente")

# ==========================================================
# 📂 CARGAR CSV
# ==========================================================
try:
    df = pd.read_csv("Scanner_SP500_Profesional.csv")
except FileNotFoundError:
    st.error("❌ No se encontró el CSV.")
    st.stop()

# ==========================================================
# 🎛 FILTROS
# ==========================================================
st.sidebar.header("Filtros")
score_min = st.sidebar.slider("Score mínimo", 0, 10, 4)
score_max = st.sidebar.slider("Score máximo", 0, 10, 10)
señales = df["Señal"].unique()
señal_filtrada = st.sidebar.multiselect("Filtrar por Señal", señales, default=señales)

df_filtrado = df[
    (df["Score"] >= score_min) &
    (df["Score"] <= score_max) &
    (df["Señal"].isin(señal_filtrada))
]

st.dataframe(df_filtrado, use_container_width=True)
if df_filtrado.empty:
    st.stop()

# ==========================================================
# 📌 SELECTOR
# ==========================================================
accion = st.selectbox("Selecciona una acción",
                      df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"])

ticker = accion.split(" - ")[0]
fila = df_filtrado[df_filtrado["Ticker"] == ticker].iloc[0]

# ==========================================================
# 📈 HISTÓRICO
# ==========================================================
hist = yf.Ticker(ticker).history(period="1y")
if hist.empty:
    st.error("No se pudieron descargar datos históricos")
    st.stop()

hist["SMA20"] = hist["Close"].rolling(20).mean()
hist["SMA50"] = hist["Close"].rolling(50).mean()
hist["SMA200"] = hist["Close"].rolling(200).mean()

# ==========================================================
# 📅 FINNHUB DATA
# ==========================================================

def obtener_earnings_futuros(ticker):
    from_date = datetime.now().date()
    to_date = (datetime.now() + timedelta(days=60)).date()
    url = f"https://finnhub.io/api/v1/calendar/earnings?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
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

# ==========================================================
# 📊 GRÁFICO (SIN EARNINGS FUTUROS)
# ==========================================================
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

# ==========================================================
# 📅 PRÓXIMOS RESULTADOS (EN FECHA)
# ==========================================================
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

# ==========================================================
# 📊 RESULTADOS ANTERIORES (CON INFO)
# ==========================================================
st.subheader("📊 Resultados anteriores")

if past_earnings:
    for e in past_earnings[:6]:
        st.write(
            f"{e.get('period')} | Actual: {e.get('actual')} | Estimado: {e.get('estimate')} | Surprise: {e.get('surprisePercent')}%"
        )
else:
    st.info("No hay resultados anteriores disponibles.")

# ==========================================================
# 📰 NOTICIAS ÚLTIMOS 7 DÍAS (FINNHUB)
# ==========================================================
st.subheader("📰 Noticias últimos 7 días")

if noticias:
    for n in noticias:
        fecha = datetime.fromtimestamp(n.get("datetime"))
        st.markdown(f"**{n.get('headline')}**")
        st.write(f"{n.get('source')} | {fecha.strftime('%d/%m/%Y')}")
        st.write(f"[Leer noticia]({n.get('url')})")
        st.markdown("---")
else:
    st.info("No hay noticias disponibles en los últimos 7 días.")

