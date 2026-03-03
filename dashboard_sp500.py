import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ta
import requests

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="Dashboard IBEX/SP500 Profesional", layout="wide")
st.title("📊 Dashboard de Acciones - Profesional")

FINNHUB_API_KEY = "d6itlc9r01qleu95hcf0d6itlc9r01qleu95hcfg"
VENTANA_NOTICIAS_DIAS = 7

# ==========================================
# LISTA DE TICKERS
# ==========================================
ibex_tickers = [
    "ANA.MC", "ACX.MC", "ACS.MC", "AENA.MC", "AMS.MC", "BBVA.MC", "SAB.MC", 
    "SAN.MC", "BKT.MC", "CABK.MC", "CLNX.MC", "ENG.MC", "ELE.MC", "FER.MC", 
    "GRF.MC", "IBE.MC", "IDR.MC", "ITX.MC", "IAG.MC", "MAP.MC", "MEL.MC", 
    "MRL.MC", "NTGY.MC", "RED.MC", "REP.MC", "SCYR.MC", "SLR.MC", "TEF.MC", 
    "COL.MC", "ROVI.MC", "FDR.MC", "MTS.MC", "LOG.MC", "UNI.MC", "PUIG.MC"
]

# ==========================================
# SCANNER FUNCION
# ==========================================
def generar_scanner(tickers):
    resultados = []
    for ticker_symbol in tickers:
        try:
            t = yf.Ticker(ticker_symbol)
            hist = t.history(period="15mo")
            if hist.empty or len(hist) < 200:
                continue

            nombre_accion = t.info.get('longName', ticker_symbol)
            hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]

            # Precio y niveles
            c_actual = hist['Close'].iloc[-1]
            h_5d = hist['High'].tail(5).max()
            l_5d = hist['Low'].tail(5).min()
            pivot = (h_5d + l_5d + c_actual) / 3
            resistencia = (2*pivot) - l_5d
            soporte = (2*pivot) - h_5d

            # Técnicos
            rsi = ta.momentum.RSIIndicator(hist['Close']).rsi().iloc[-1]
            sma_200 = ta.trend.sma_indicator(hist['Close'], window=200).iloc[-1]
            atr = ta.volatility.AverageTrueRange(hist['High'], hist['Low'], hist['Close']).average_true_range().iloc[-1]
            vol_actual = hist['Volume'].iloc[-1]
            vol_medio_mes = hist['Volume'].tail(21).mean()
            
            # Señal
            score = 0
            if rsi < 40: score += 3
            if c_actual > sma_200: score += 2
            if c_actual > soporte and c_actual < (soporte*1.025): score += 5

            if score >= 7: señal = "BUY"
            elif score >= 4: señal = "HOLD"
            else: señal = "SELL"

            resultados.append({
                "Ticker": ticker_symbol,
                "Nombre": nombre_accion,
                "Precio": round(c_actual,2),
                "Score": score,
                "Señal": señal,
                "RSI": round(rsi,2),
                "SMA200": round(sma_200,2),
                "ATR": round(atr,2),
                "Volumen Actual": int(vol_actual),
                "Volumen Medio (Mes)": int(vol_medio_mes),
                "Soporte": round(soporte,2),
                "Resistencia": round(resistencia,2),
                "Stop Loss": round(soporte,2),
                "Take Profit": round(resistencia,2)
            })
        except:
            continue
    return pd.DataFrame(resultados)

# ==========================================
# BOTÓN ACTUALIZAR
# ==========================================
if st.button("🔄 Actualizar Scanner"):
    with st.spinner("Actualizando datos..."):
        df = generar_scanner(ibex_tickers)
        st.session_state['df'] = df
    st.success("Scanner actualizado.")

# ==========================================
# CARGAR DATOS (MEMORIA O INICIAL)
# ==========================================
if 'df' not in st.session_state:
    df = generar_scanner(ibex_tickers)
    st.session_state['df'] = df
else:
    df = st.session_state['df']

# ==========================================
# FILTROS
# ==========================================
st.sidebar.header("Filtros")
score_min = st.sidebar.slider("Score mínimo",0,10,4)
score_max = st.sidebar.slider("Score máximo",0,10,10)
señales = df["Señal"].unique()
señal_filtrada = st.sidebar.multiselect("Señal", señales, default=señales)

df_filtrado = df[
    (df["Score"] >= score_min) &
    (df["Score"] <= score_max) &
    (df["Señal"].isin(señal_filtrada))
]

st.subheader(f"📋 Acciones filtradas ({len(df_filtrado)})")
st.dataframe(df_filtrado,use_container_width=True)

if df_filtrado.empty:
    st.warning("No hay acciones con esos filtros.")
    st.stop()

# ==========================================
# SELECTOR DE ACCIÓN
# ==========================================
accion = st.selectbox(
    "Selecciona acción",
    df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"]
)
ticker = accion.split(" - ")[0]
fila = df_filtrado[df_filtrado["Ticker"]==ticker].iloc[0]

# ==========================================
# HISTÓRICO
# ==========================================
hist = yf.Ticker(ticker).history(period="1y")
if hist.empty:
    st.error("No se pudieron descargar datos históricos.")
    st.stop()
hist["SMA20"] = hist["Close"].rolling(20).mean()
hist["SMA50"] = hist["Close"].rolling(50).mean()
hist["SMA200"] = hist["Close"].rolling(200).mean()

# ==========================================
# GRÁFICO
# ==========================================
fig = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.05,row_heights=[0.7,0.3])

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

fig.add_hline(y=fila["Soporte"], line_dash="dash", annotation_text="Soporte")
fig.add_hline(y=fila["Resistencia"], line_dash="dash", annotation_text="Resistencia")
fig.add_hline(y=fila["Stop Loss"], line_dash="dot", annotation_text="Stop Loss")
fig.add_hline(y=fila["Take Profit"], line_dash="dot", annotation_text="Take Profit")

fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volumen"), row=2, col=1)

fig.update_layout(
    title=f"{fila['Nombre']} ({ticker}) | Señal: {fila['Señal']} | Score: {fila['Score']}",
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
    height=800
)

st.plotly_chart(fig,use_container_width=True)

# ==========================================
# RESUMEN TÉCNICO
# ==========================================
st.subheader("📊 Resumen Técnico")
col1, col2, col3 = st.columns(3)
col1.metric("Precio", fila["Precio"])
col1.metric("Score", fila["Score"])
col1.metric("Señal", fila["Señal"])
col2.metric("RSI", fila["RSI"])
col2.metric("ATR", fila["ATR"])
col2.metric("Volumen Anual", fila["Volumen Medio (Mes)"])
col3.metric("Soporte", fila["Soporte"])
col3.metric("Resistencia", fila["Resistencia"])
col3.metric("Take Profit", fila["Take Profit"])

# ==========================================
# FINNHUB NOTICIAS Y EARNINGS
# ==========================================
st.subheader("📰 Noticias recientes y próximas")

def obtener_noticias_y_earnings(ticker):
    noticias = []
    earnings = []
    # Noticias últimos 7 días
    try:
        hoy = datetime.today()
        fecha_inicio = hoy - timedelta(days=VENTANA_NOTICIAS_DIAS)
        url_news = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={fecha_inicio.date()}&to={hoy.date()}&token={FINNHUB_API_KEY}"
        r = requests.get(url_news)
        data = r.json()
        for n in data[:5]:
            noticias.append({
                "titulo": n.get("headline","Sin título"),
                "fecha": n.get("datetime",0),
                "url": n.get("url","#"),
                "source": n.get("source","Desconocido")
            })
    except:
        noticias.append({"titulo":"No se pudieron cargar noticias","fecha":0,"url":"#","source":"-"})

    # Próximos earnings (30 días)
    try:
        fecha_hoy = datetime.today().date()
        fecha_fin = fecha_hoy + timedelta(days=30)
        url_earn = f"https://finnhub.io/api/v1/calendar/earnings?from={fecha_hoy}&to={fecha_fin}&symbol={ticker}&token={FINNHUB_API_KEY}"
        r2 = requests.get(url_earn)
        data2 = r2.json()
        for e in data2.get("earningsCalendar",[]):
            earnings.append({
                "fecha": e.get("date"),
                "epsActual": e.get("epsActual"),
                "epsEstimate": e.get("epsEstimate")
            })
    except:
        earnings.append({"fecha":"No disponible"})
    return noticias, earnings

noticias, earnings = obtener_noticias_y_earnings(ticker)

# Mostrar noticias
if noticias:
    for n in noticias:
        fecha = datetime.fromtimestamp(n["fecha"]).strftime("%d/%m/%Y") if n["fecha"] else "Fecha desconocida"
        st.markdown(f"**{n['titulo']}**")
        st.write(f"{n['source']} | {fecha}")
        st.write(f"[Leer noticia]({n['url']})")
        st.markdown("---")
else:
    st.info("No hay noticias disponibles")

# Mostrar próximos earnings
if earnings:
    st.subheader("📅 Próximos resultados (30 días)")
    for e in earnings:
        st.write(f"- Fecha: {e.get('fecha','Desconocida')} | EPS Estimado: {e.get('epsEstimate','-')} | EPS Actual: {e.get('epsActual','-')}")
else:
    st.info("No se pudo obtener información de próximos resultados en Finnhub.")

# ==========================================
# DESCARGA CSV
# ==========================================
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Descargar CSV", csv, "Scanner_IBEX_Profesional.csv", "text/csv")
