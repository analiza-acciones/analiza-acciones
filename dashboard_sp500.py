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

# ================== TICKERS ==================
sp500_tickers = [
"AAPL","ABBV","ABNB","ABT","ACGL","ACN","ADBE","ADI","ADM","ADP",
"ADSK","AEE","AEP","AES","AFL","AIG","AIZ","AJG","AKAM","ALB",
"ALGN","ALLE","ALL","AMAT","AMD","AME","AMGN","AMP","AMT",
"AMZN","ANET","ANSS","AON","APA","APD","APH","APTV","ARE","ATO",
"AVB","AVGO","AVY","AXP","AZO","BA","BAC","BALL","BAX","BBWI",
"BBY","BDX","BEN","BF.B","BG","BIIB","BK","BKNG","BKR","BLK",
"BMY","BR","BRK.B","BSX","BWA","C","CAG","CAH","CARR","CAT",
"CB","CBRE","CCI","CCL","CDNS","CEG","CF","CFG","CHD",
"CHRW","CHTR","CI","CINF","CL","CLX","CMA","CMCSA","CME","CMG",
"COF","COO","COP","COST","CPRT","CRM","CSCO","CSX",
"CTAS","CTSH","CTVA","CVS","CVX","DD","DE","DFS",
"DG","DGX","DHI","DHR","DIS","DOW","DPZ",
"DRI","DTE","DUK","DVA","DVN","EA","EBAY","ECL",
"ED","EFX","EIX","EL","EMN","EMR","ENPH","EOG","EQIX",
"ESS","ETN","ETR","EW","EXC","EXPD","EXPE","F","FAST",
"FCX","FDX","FE","FIS","FISV","FITB","FLT",
"FMC","FOXA","FOX","FTNT","FTV","GD",
"GE","GILD","GIS","GL","GLW","GM","GOOG","GOOGL",
"GS","GWW","HAL","HAS","HBAN","HCA",
"HD","HES","HIG","HLT","HON","HPQ","HRL",
"HSY","HUM","IBM","ICE","IFF","ILMN",
"INTC","INTU","IP","IQV","IRM","ISRG","ITW",
"JCI","JNJ","JPM","K","KEY","KHC",
"KLAC","KO","KR","LEN","LH","LIN",
"LLY","LMT","LOW","LRCX","LUV","MA","MCD",
"MCHP","MCK","MCO","MDLZ","MDT","MET","MGM",
"MKC","MLM","MMC","MMM","MNST","MO","MOS",
"MPC","MRK","MS","MSFT","MSI","MTB","MTD",
"MU","NFLX","NI","NKE","NRG","NSC",
"NTRS","NUE","NVDA","NXPI","O","ODFL",
"OKE","OMC","ORCL","ORLY","OTIS","OXY",
"PAYX","PCAR","PFG","PG","PGR","PH",
"PLD","PM","PNC","PPG","PRU","PSA",
"PSX","PYPL","QCOM","RCL","REGN","RF",
"RJF","RMD","ROK","ROP","ROST","RTX",
"SBUX","SCHW","SHW","SLB","SNPS","SO",
"SPG","SPGI","SRE","STE","STT","STZ",
"SYK","SYY","T","TFC","TGT","TJX",
"TMO","TMUS","TRV","TSCO","TSLA","TSN",
"TT","TXN","UAL","UDR","ULTA","UNH",
"UNP","UPS","USB","V","VLO","VRTX",
"VZ","WAB","WAT","WBA","WDC","WEC",
"WELL","WFC","WM","WMT","WRB",
"XEL","XOM","XYL","YUM","ZBH","ZBRA","ZION","ZTS"
]

# ================== FUNCIÓN ANALÍTICA ==================
def analizar_SP500_profesional(ticker_symbol):
    try:
        yf_ticker = ticker_symbol.replace('.', '-')
        t = yf.Ticker(yf_ticker)
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

        return {
            "Ticker": ticker_symbol,
            "Nombre": nombre_accion,
            "Precio": round(c_actual, 2),
            "Score": score,
            "Señal": señal
        }

    except:
        return None

# ================== SCANNER ==================
@st.cache_data(show_spinner=True)
def generar_scanner():
    resultados = []
    for tick in sp500_tickers:
        res = analizar_SP500_profesional(tick)
        if res:
            resultados.append(res)

    df = pd.DataFrame(resultados)
    if not df.empty:
        df = df.sort_values(by="Score", ascending=False)

    return df

# ================== BOTÓN ==================
if st.button("🔄 Actualizar datos del Scanner"):
    with st.spinner("Ejecutando scanner..."):
        df = generar_scanner()
    st.success("Datos actualizados correctamente")

# ================== CARGA INICIAL ==================
try:
    df
except:
    df = generar_scanner()

if df.empty:
    st.error("No se generaron datos")
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

# ================== INFO DEBUG ==================
st.write("Total acciones escaneadas:", len(df))
st.write("Total después de filtros:", len(df_filtrado))

# ================== TABLA ==================
st.dataframe(df_filtrado, use_container_width=True)

if df_filtrado.empty:
    st.stop()

# ================== SELECTOR ==================
accion = st.selectbox(
    "Selecciona una acción",
    df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"]
)

ticker = accion.split(" - ")[0]

# ================== GRÁFICO ==================
hist = yf.Ticker(ticker).history(period="1y")

hist["SMA20"] = hist["Close"].rolling(20).mean()
hist["SMA50"] = hist["Close"].rolling(50).mean()
hist["SMA200"] = hist["Close"].rolling(200).mean()

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.7, 0.3]
)

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

fig.add_trace(go.Bar(
    x=hist.index,
    y=hist["Volume"],
    name="Volumen"
), row=2, col=1)

fig.update_layout(xaxis_rangeslider_visible=False, height=800)
st.plotly_chart(fig, use_container_width=True)
