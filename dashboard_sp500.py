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
"AAPL","ABBV","ABNB","ABT","ACGL","ACN","ADBE","ADI","ADM","ADP",
"ADSK","AEE","AEP","AES","AFL","AIG","AIZ","AJG","AKAM","ALB",
"ALGN","ALLE","ALL","AMAT","AMD","AME","AMGN","AMP","AMT",
"AMZN","ANET","ANSS","AON","APA","APD","APH","APTV","ARE","ATO",
"AVB","AVGO","AVY","AXP","AZO","BA","BAC","BALL","BAX","BBWI",
"BBY","BDX","BEN","BF.B","BG","BIIB","BK","BKNG","BKR","BLK",
"BMY","BR","BRK.B","BSX","BWA","C","CAG","CAH","CARR","CAT",
"CB","CBRE","CCI","CCL","CDNS","CEG","CERN","CF","CFG","CHD",
"CHRW","CHTR","CI","CINF","CL","CLX","CMA","CMCSA","CME","CMG",
"COF","COG","COO","COP","COST","CPB","CPRT","CRM","CSCO","CSX",
"CTAS","CTL","CTSH","CTVA","CVS","CVX","CZR","DD","DE","DFS",
"DG","DGX","DHI","DHR","DIS","DISCA","DISCK","DOW","DOX","DPZ",
"DRE","DRI","DTE","DUK","DVA","DVN","DXC","EA","EBAY","ECL",
"ED","EFX","EIX","EL","EME","EMN","EMR","ENPH","EOG","EQIX","EQT",
"ESS","ETN","ETR","EVRG","EW","EXC","EXPD","EXPE","F","FAST",
"FBHS","FCX","FDX","FE","FIS","FISV","FITB","FL","FLS","FLT",
"FMC","FOXA","FOX","FPH","FRC","FRT","FTI","FTNT","FTV","GD",
"GE","GILD","GIS","GL","GLW","GM","GOOG","GOOGL","GPC","GPN",
"GPS","GRMN","GS","GT","GWW","HAL","HAS","HBAN","HCA","HCP",
"HD","HES","HIG","HII","HLT","HOG","HOLX","HON","HPQ","HRL",
"HSIC","HST","HSY","HTZ","HUM","IBM","ICE","IFF","ILMN","INCY",
"INFO","INTC","INTU","IP","IPG","IQV","IR","IRM","ISRG","IT",
"ITW","IVZ","J","JBHT","JCI","JKHY","JNJ","JPM","JWN","K",
"KEY","KEYS","KHC","KIM","KMI","KLAC","KMX","KO","KR","KSU",
"L","LAD","LB","LDOS","LDL","LEG","LEN","LH","LHX","LIN",
"LKQ","LLY","LMT","LNC","LNT","LOW","LRCX","LUV","LYB","M",
"MA","MCD","MCHP","MCK","MCO","MDLZ","MDT","MET","MGM","MHK",
"MKC","MKTX","MLM","MMC","MMM","MNST","MO","MOS","MPC","MRK",
"MRO","MS","MSFT","MSI","MTB","MTD","MU","NFLX","NI","NKE",
"NLOK","NOV","NRG","NSC","NTAP","NTRS","NUE","NVDA","NVR","NWL",
"NWS","NWSA","NXPI","O","ODFL","OGN","OKE","OMC","ORCL","ORLY",
"OTIS","OXY","PAYC","PAYX","PBCT","PCAR","PCG","PFG","PG","PGR",
"PH","PHM","PKG","PKI","PLD","PM","PNC","PNR","PNW","PPG",
"PPL","PRGO","PRU","PSA","PSX","PVH","PWR","PXD","PYPL","QCOM",
"QRVO","RCL","RE","REG","REGN","RF","RHI","RJF","RL","RMD",
"ROK","ROL","ROP","ROST","RSG","RTX","SBAC","SBUX","SCHW","SEE",
"SHW","SIVB","SJM","SLB","SNA","SNPS","SO","SPG","SPGI","SRE",
"STE","STT","STZ","SWK","SWKS","SYF","SYK","SYY","T","TAK",
"TBH","TDG","TEL","TER","TFC","TGT","TIF","TJX","TMO","TMUS",
"TPR","TRGP","TRV","TSCO","TSLA","TSN","TT","TUB","TWTR","TXN",
"TXT","TZOO","UAL","UDR","UHS","ULTA","UNH","UNM","UNP","UPS",
"URI","USB","V","VAR","VFC","VLO","VMC","VNO","VRTX","VTR",
"VZ","WAB","WAT","WBA","WB","WDC","WEC","WELL","WFC","WFT",
"WHR","WLTW","WM","WMB","WMT","WRB","WRK","WY","WYNN","XEL",
"XLNX","XOM","XRAY","XRX","XYL","YUM","ZBH","ZBRA","ZION","ZTS"
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
if 'df' not in st.session_state:
    st.session_state['df'] = generar_scanner("scanner_sp500_v1")
    st.session_state['last_refresh'] = datetime.now()

if st.button("Actualizar datos"):
    generar_scanner.clear()
    st.session_state['df'] = generar_scanner("scanner_sp500_v1")
    st.session_state['last_refresh'] = datetime.now()

df = st.session_state['df']

# ================== SIDEBAR ==================
st.sidebar.markdown(f"**Hora actual:** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**Última actualización:** {st.session_state['last_refresh'].strftime('%d/%m/%Y %H:%M:%S')}")
st.sidebar.header("Filtros")

score_min, score_max = st.sidebar.slider(
    "Score",
    min_value=float(df["Score"].min()),
    max_value=float(df["Score"].max()),
    value=(float(df["Score"].min()), float(df["Score"].max())),
    step=0.1
)

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

accion_global = st.selectbox("Selecciona acción", df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"], key="accion_global")

# ================== FORMATO DE COLUMNAS ==================
formato_columnas = {
    "Precio": "{:.2f}",
    "Score": "{:.1f}",
    "RSI": "{:.2f}",
    "SMA20": "{:.2f}",
    "SMA50": "{:.2f}",
    "SMA200": "{:.2f}",
    "ATR": "{:.2f}",
    "ATR Ratio": "{:.4f}",
    "Volatilidad Anual": "{:.4f}",
    "Volumen Actual": "{:.0f}",
    "Volumen Medio (Mes)": "{:.0f}",
    "Volumen Relativo": "{:.2f}",
    "Soporte": "{:.2f}",
    "Resistencia": "{:.2f}",
    "Stop Loss": "{:.2f}",
    "Take Profit": "{:.2f}"
}

# ================== ESTILO SCORE ==================
def color_score(val):
    if val >= 7:
        return 'background-color: #2ECC71; color: white'
    elif val >= 4:
        return 'background-color: #F1C40F; color: black'
    else:
        return 'background-color: #E74C3C; color: white'

# ================== TABS ==================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Acciones","📈 Gráfico","📊 Resultados","📰 Noticias","🌍 Other"])

# ================== TAB 1 ==================
with tab1:
    df_accion = df_filtrado[df_filtrado["Ticker"] == accion_global.split(" - ")[0]]
    st.subheader("📌 Acción seleccionada")
    st.dataframe(
        df_accion.style.applymap(color_score, subset=['Score']).format(formato_columnas),
        use_container_width=True
    )

    df_restantes = df_filtrado[df_filtrado["Ticker"] != accion_global.split(" - ")[0]]
    if not df_restantes.empty:
        st.subheader("📊 Resto de acciones")
        st.dataframe(
            df_restantes.style.applymap(color_score, subset=['Score']).format(formato_columnas),
            use_container_width=True
        )

# ================== TAB 2 ==================
with tab2:
    ticker = accion_global.split(" - ")[0]
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

# ================== TAB 3 ==================
with tab3:
    ticker = accion_global.split(" - ")[0]
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

# ================== TAB 4 ==================
with tab4:
    ticker = accion_global.split(" - ")[0]
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


# ================== TAB 5 ==================
with tab5:

    st.subheader("🌍 Bitcoin, Oro & Plata")

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
