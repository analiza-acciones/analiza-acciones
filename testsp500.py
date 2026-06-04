import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import numpy as np

st.set_page_config(page_title="Dashboard SP500", layout="wide")
st.title("📊 TESTS&P500")

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
    if value is None or np.isnan(float(value if value is not None else 0)):
        return 0.5
    return max(0.0, min(1.0, (float(value) - min_val) / (max_val - min_val)))

def safe(value, default=None):
    """Devuelve None si el valor es NaN o None."""
    if value is None:
        return default
    try:
        f = float(value)
        return default if np.isnan(f) else f
    except (TypeError, ValueError):
        return default

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

        # ── Soporte/Resistencia (pivot points 5 días) ──────────────────────────
        h_5d = hist['High'].tail(5).max()
        l_5d = hist['Low'].tail(5).min()
        pivot = (h_5d + l_5d + c_actual) / 3
        resistencia = (2 * pivot) - l_5d
        soporte = (2 * pivot) - h_5d

        # ── Indicadores técnicos ────────────────────────────────────────────────
        close = hist['Close']
        high  = hist['High']
        low   = hist['Low']

        rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]

        sma20  = ta.trend.sma_indicator(close, window=20).iloc[-1]
        sma50  = ta.trend.sma_indicator(close, window=50).iloc[-1]
        sma200 = ta.trend.sma_indicator(close, window=200).iloc[-1]

        # Pendiente normalizada de SMAs (positiva = tendencia alcista)
        sma20_slope  = (ta.trend.sma_indicator(close, window=20).iloc[-1]  - ta.trend.sma_indicator(close, window=20).iloc[-6])  / c_actual
        sma50_slope  = (ta.trend.sma_indicator(close, window=50).iloc[-1]  - ta.trend.sma_indicator(close, window=50).iloc[-11]) / c_actual
        sma200_slope = (ta.trend.sma_indicator(close, window=200).iloc[-1] - ta.trend.sma_indicator(close, window=200).iloc[-21]) / c_actual

        # MACD
        macd_obj   = ta.trend.MACD(close)
        macd_line  = macd_obj.macd().iloc[-1]
        macd_signal= macd_obj.macd_signal().iloc[-1]
        macd_hist  = macd_obj.macd_diff().iloc[-1]   # histograma = MACD - Signal
        # Cambio del histograma respecto a la barra anterior (momentum del MACD)
        macd_hist_prev = macd_obj.macd_diff().iloc[-2]
        macd_aceleracion = macd_hist - macd_hist_prev

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]
        bb_mid   = bb.bollinger_mavg().iloc[-1]
        bb_width = (bb_upper - bb_lower) / bb_mid      # volatilidad relativa
        bb_pos   = (c_actual - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

        # ATR
        atr = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1]
        atr_ratio = atr / c_actual

        # Volatilidad histórica anualizada
        volatilidad = close.pct_change().rolling(252).std().iloc[-1] * (252 ** 0.5)

        # Volumen
        vol_actual   = hist['Volume'].iloc[-1]
        vol_medio_mes = hist['Volume'].tail(21).mean()
        vol_relativo = vol_actual / vol_medio_mes if vol_medio_mes > 0 else 1.0

        # Momentum de precio (retornos a 1m, 3m, 6m)
        ret_1m  = (c_actual / close.iloc[-22]  - 1) if len(close) >= 22  else 0
        ret_3m  = (c_actual / close.iloc[-66]  - 1) if len(close) >= 66  else 0
        ret_6m  = (c_actual / close.iloc[-126] - 1) if len(close) >= 126 else 0
        momentum = ret_1m * 0.5 + ret_3m * 0.3 + ret_6m * 0.2   # ponderado por recencia

        # ── Fundamentales ──────────────────────────────────────────────────────
        per                = safe(t.info.get('trailingPE'))
        roe                = safe(t.info.get('returnOnEquity'))
        deuda_equity       = safe(t.info.get('debtToEquity'))
        crecimiento_ingresos = safe(t.info.get('revenueGrowth'))
        beta               = safe(t.info.get('beta'))
        margen_neto        = safe(t.info.get('profitMargins'))
        fcf_yield          = safe(t.info.get('freeCashflow'))
        market_cap         = safe(t.info.get('marketCap'))
        fcf_yield_ratio    = (fcf_yield / market_cap) if (fcf_yield and market_cap and market_cap > 0) else None

        # ── SCORE FUNDAMENTAL (mejorado) ───────────────────────────────────────
        # PER: rango sectorial aproximado; penaliza extremos altos pero no premia demasiado bajo
        # Usamos rango 8-35 como "razonable"
        score_per  = 1 - normalize(per, 8, 40)           if per  is not None else 0.5
        score_roe  = normalize(roe, 0.05, 0.35)           if roe  is not None else 0.5
        score_deuda = 1 - normalize(deuda_equity, 0, 150) if deuda_equity is not None else 0.5  # D/E en % (yfinance)
        score_crec = normalize(crecimiento_ingresos, -0.05, 0.25) if crecimiento_ingresos is not None else 0.5
        score_margen = normalize(margen_neto, 0.0, 0.30)  if margen_neto is not None else 0.5
        score_fcf  = normalize(fcf_yield_ratio, 0.01, 0.08) if fcf_yield_ratio is not None else 0.5

        score_fund = (
            score_per    * 0.20 +
            score_roe    * 0.20 +
            score_deuda  * 0.15 +
            score_crec   * 0.15 +
            score_margen * 0.15 +
            score_fcf    * 0.15
        )

        # ── SCORE TÉCNICO (mejorado) ───────────────────────────────────────────
        # RSI: zona óptima de entrada ≈ 40-60 (no sobrecomprado, no sobrevendido)
        # En tendencia alcista, RSI 50-65 es fuerte. Penalizamos <30 (pánico) y >75 (euforia).
        if rsi < 30:
            score_rsi = 0.2   # sobreventa extrema → riesgo
        elif rsi < 45:
            score_rsi = 0.5 + (rsi - 30) / 15 * 0.3   # recuperación
        elif rsi <= 65:
            score_rsi = 0.8   # zona sana
        elif rsi <= 75:
            score_rsi = 0.8 - (rsi - 65) / 10 * 0.4   # sobrecompra moderada
        else:
            score_rsi = 0.2   # sobrecompra extrema

        # SMA: precio vs medias + pendiente (dirección de la tendencia)
        pos_sma20  = 1 if c_actual > sma20  else 0
        pos_sma50  = 1 if c_actual > sma50  else 0
        pos_sma200 = 1 if c_actual > sma200 else 0
        slope_sma20  = 1 if sma20_slope  > 0 else 0
        slope_sma50  = 1 if sma50_slope  > 0 else 0
        slope_sma200 = 1 if sma200_slope > 0 else 0
        # Golden cross: SMA50 > SMA200
        golden_cross = 1 if sma50 > sma200 else 0
        score_sma = (pos_sma20*0.15 + pos_sma50*0.15 + pos_sma200*0.20 +
                     slope_sma20*0.10 + slope_sma50*0.10 + slope_sma200*0.10 +
                     golden_cross*0.20)

        # MACD: señal de cruce y aceleración del histograma
        macd_bullish = 1 if macd_line > macd_signal else 0          # MACD sobre señal
        macd_accel   = 1 if macd_aceleracion > 0 else 0              # histograma creciendo
        score_macd   = macd_bullish * 0.6 + macd_accel * 0.4

        # Bollinger: preferimos precio cerca de la media (no en extremos)
        # bb_pos=0 → en banda inferior (sobreventa), bb_pos=1 → banda superior (sobrecompra)
        # Óptimo: 0.35-0.65
        score_bb = 1 - abs(bb_pos - 0.5) * 2   # máximo en 0.5, mínimo en extremos

        # Momentum de precio: preferimos tendencias positivas moderadas
        score_momentum = normalize(momentum, -0.10, 0.25)

        # Volumen relativo: volumen alto en subida es señal positiva (confirmación)
        if vol_relativo > 1.5 and ret_1m > 0:
            score_vol_tec = 0.9   # volumen alto con subida = muy positivo
        elif vol_relativo > 1.0:
            score_vol_tec = 0.6   # volumen normal-alto
        elif vol_relativo > 0.5:
            score_vol_tec = 0.4
        else:
            score_vol_tec = 0.2   # volumen muy bajo = poca convicción

        score_tec = (
            score_rsi      * 0.20 +
            score_sma      * 0.25 +
            score_macd     * 0.20 +
            score_bb       * 0.10 +
            score_momentum * 0.15 +
            score_vol_tec  * 0.10
        )

        # ── SCORE DE RIESGO (mejorado) ─────────────────────────────────────────
        score_atr  = 1 - normalize(atr_ratio, 0.005, 0.06)   # ATR/precio ajustado
        score_beta = 1 - normalize(beta, 0.3, 2.0) if beta is not None else 0.5
        score_vol_anual = 1 - normalize(volatilidad, 0.10, 0.60)

        score_riesgo = (
            score_atr      * 0.35 +
            score_beta     * 0.35 +
            score_vol_anual * 0.30
        )

        # ── SCORE FINAL ───────────────────────────────────────────────────────
        score_final = score_fund * 0.40 + score_tec * 0.40 + score_riesgo * 0.20
        score_final_10 = round(score_final * 10, 1)

        señal = "BUY" if score_final_10 >= 7 else "HOLD" if score_final_10 >= 4 else "SELL"

        # ── Stop Loss / Take Profit dinámicos ──────────────────────────────────
        # Ajustamos el multiplicador según el score de riesgo: menor riesgo → SL más ajustado
        riesgo_mult = 1.0 + (1 - score_riesgo) * 1.0   # rango ~1.0 - 2.0
        stop_loss   = max(soporte, c_actual - riesgo_mult * 1.5 * atr)
        take_profit = min(resistencia, c_actual + riesgo_mult * 2.5 * atr)

        return {
            "Ticker": ticker_symbol,
            "Nombre": nombre_accion,
            "Precio": round(c_actual, 2),
            "Score": score_final_10,
            "Señal": señal,
            "RSI": round(rsi, 2),
            "MACD": round(macd_line, 4),
            "MACD_Signal": round(macd_signal, 4),
            "MACD_Hist": round(macd_hist, 4),
            "BB_Pos": round(bb_pos, 3),
            "Momentum_1M": round(ret_1m * 100, 2),
            "Momentum_3M": round(ret_3m * 100, 2),
            "Momentum_6M": round(ret_6m * 100, 2),
            "SMA20": round(sma20, 2),
            "SMA50": round(sma50, 2),
            "SMA200": round(sma200, 2),
            "Golden_Cross": "✅" if sma50 > sma200 else "❌",
            "ATR": round(atr, 2),
            "ATR Ratio": round(atr_ratio, 4),
            "Volatilidad Anual": round(volatilidad, 4),
            "Volumen Actual": int(vol_actual),
            "Volumen Medio (Mes)": int(vol_medio_mes),
            "Volumen Relativo": round(vol_relativo, 2),
            "Soporte": round(soporte, 2),
            "Resistencia": round(resistencia, 2),
            "Stop Loss": round(stop_loss, 2),
            "Take Profit": round(take_profit, 2),
            # Sub-scores para transparencia
            "Score_Fund": round(score_fund * 10, 1),
            "Score_Tec": round(score_tec * 10, 1),
            "Score_Riesgo": round(score_riesgo * 10, 1),
        }
    except Exception:
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
    st.session_state['df'] = generar_scanner("scanner_sp500_v2")
    st.session_state['last_refresh'] = datetime.now()

if st.button("Actualizar datos"):
    generar_scanner.clear()
    st.session_state['df'] = generar_scanner("scanner_sp500_v2")
    st.session_state['last_refresh'] = datetime.now()

df = st.session_state['df']

# ================== SIDEBAR ==================
st.sidebar.markdown(f"**Dia:** {datetime.now().strftime('%d/%m/%Y')}")

hora_mas_una = datetime.now() + timedelta(hours=1)
st.sidebar.markdown(f"**Hora:** {hora_mas_una.strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**Ultima Actualización Datos:** {hora_mas_una.strftime('%d/%m/%Y %H:%M:%S')}")
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
    "Score_Fund": "{:.1f}",
    "Score_Tec": "{:.1f}",
    "Score_Riesgo": "{:.1f}",
    "RSI": "{:.2f}",
    "MACD": "{:.4f}",
    "MACD_Signal": "{:.4f}",
    "MACD_Hist": "{:.4f}",
    "BB_Pos": "{:.3f}",
    "Momentum_1M": "{:.2f}%",
    "Momentum_3M": "{:.2f}%",
    "Momentum_6M": "{:.2f}%",
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
    ticker_sel = accion_global.split(" - ")[0]
    df_accion = df_filtrado[df_filtrado["Ticker"] == ticker_sel]
    st.subheader("📌 Acción seleccionada")
    # Columnas principales
    cols_principales = ["Ticker","Nombre","Precio","Score","Señal","Score_Fund","Score_Tec","Score_Riesgo",
                        "RSI","MACD_Hist","BB_Pos","Golden_Cross",
                        "Momentum_1M","Momentum_3M","Momentum_6M",
                        "Volumen Relativo","Soporte","Resistencia","Stop Loss","Take Profit"]
    st.dataframe(
        df_accion[cols_principales].style.applymap(color_score, subset=['Score','Score_Fund','Score_Tec','Score_Riesgo']).format(
            {k:v for k,v in formato_columnas.items() if k in cols_principales}
        ),
        use_container_width=True
    )

    df_restantes = df_filtrado[df_filtrado["Ticker"] != ticker_sel]
    if not df_restantes.empty:
        st.subheader("📊 Resto de acciones")
        st.dataframe(
            df_restantes[cols_principales].style.applymap(color_score, subset=['Score','Score_Fund','Score_Tec','Score_Riesgo']).format(
                {k:v for k,v in formato_columnas.items() if k in cols_principales}
            ),
            use_container_width=True
        )

# ================== TAB 2 ==================
with tab2:
    ticker = accion_global.split(" - ")[0]
    hist = yf.Ticker(ticker).history(period="1y")
    hist["SMA20"]  = hist["Close"].rolling(20).mean()
    hist["SMA50"]  = hist["Close"].rolling(50).mean()
    hist["SMA200"] = hist["Close"].rolling(200).mean()

    # MACD para el gráfico
    macd_obj_g   = ta.trend.MACD(hist["Close"])
    hist["MACD"]       = macd_obj_g.macd()
    hist["MACD_Signal"]= macd_obj_g.macd_signal()
    hist["MACD_Hist"]  = macd_obj_g.macd_diff()

    fila = df_filtrado[df_filtrado["Ticker"] == ticker].iloc[0]
    soporte    = fila["Soporte"]
    resistencia= fila["Resistencia"]

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.55, 0.20, 0.25],
        subplot_titles=("Precio", "Volumen", "MACD")
    )

    # Velas
    fig.add_trace(go.Candlestick(x=hist.index,
        open=hist["Open"], high=hist["High"], low=hist["Low"], close=hist["Close"],
        name="Precio"), row=1, col=1)
    for sma, color, name in [(hist["SMA20"],"#F1C40F","SMA20"),(hist["SMA50"],"#3498DB","SMA50"),(hist["SMA200"],"#E74C3C","SMA200")]:
        fig.add_trace(go.Scatter(x=hist.index, y=sma, name=name, line=dict(color=color, width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=[hist.index[0], hist.index[-1]], y=[soporte, soporte],
        name="Soporte", line=dict(dash='dash', color='green', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=[hist.index[0], hist.index[-1]], y=[resistencia, resistencia],
        name="Resistencia", line=dict(dash='dash', color='red', width=1)), row=1, col=1)

    # Volumen coloreado (verde si sube, rojo si baja)
    colors_vol = ['#2ECC71' if c >= o else '#E74C3C'
                  for c, o in zip(hist['Close'], hist['Open'])]
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volumen",
        marker_color=colors_vol, opacity=0.7), row=2, col=1)

    # MACD
    colors_hist = ['#2ECC71' if v >= 0 else '#E74C3C' for v in hist["MACD_Hist"].fillna(0)]
    fig.add_trace(go.Bar(x=hist.index, y=hist["MACD_Hist"], name="MACD Hist",
        marker_color=colors_hist, opacity=0.7), row=3, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["MACD"], name="MACD",
        line=dict(color="#3498DB", width=1.2)), row=3, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["MACD_Signal"], name="Signal",
        line=dict(color="#F1C40F", width=1.2)), row=3, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False, height=850, showlegend=True)
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
    st.subheader("🌍 Bitcoin // Oro // Plata")

    activos = {
        "Bitcoin":    {"ticker": "BTC-USD", "moneda": "USD"},
        "Bitcoin €":  {"ticker": "BTC-EUR", "moneda": "EUR"},
        "Oro":        {"ticker": "GC=F",    "moneda": "USD"},
        "Plata":      {"ticker": "SI=F",    "moneda": "USD"}
    }

    tickers = [v["ticker"] for v in activos.values()]
    data = yf.download(tickers, period="1y", group_by="ticker", progress=False)

    datos_tabla = []
    historicos  = {}

    for nombre, info in activos.items():
        ticker  = info["ticker"]
        moneda  = info["moneda"]
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
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name=nombre))
        fig.update_layout(title=f"{nombre} - Histórico 1 año",
                          xaxis_title="Fecha", yaxis_title="Precio", height=400)
        st.plotly_chart(fig, use_container_width=True)
