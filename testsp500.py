import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import numpy as np
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Dashboard SP500 Pro", layout="wide")
st.title("📊 S&P500 - Análisis Profesional")

# ================== CONFIG ==================
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]
ALERTA_DIAS = 7
VENTANA_NOTICIAS_DIAS = 7

# ================== SESIÓN ROBUSTA HTTP ==================
def crear_sesion_robusta():
    """Crea sesión HTTP con reintentos automáticos"""
    sesion = requests.Session()
    reintentos = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adaptador = HTTPAdapter(max_retries=reintentos)
    sesion.mount('http://', adaptador)
    sesion.mount('https://', adaptador)
    return sesion

SESION_HTTP = crear_sesion_robusta()

# ================== LISTA DE TICKERS SP500 ==================
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

# ================== FUNCIONES AUXILIARES ==================
def normalize(value, min_val, max_val):
    """Normaliza un valor entre 0 y 1"""
    if value is None or np.isnan(value):
        return 0.5
    return max(0, min(1, (value - min_val) / (max_val - min_val)))

def obtener_noticias(ticker, ventana_dias=7):
    """Obtiene noticias con manejo robusto de errores"""
    try:
        fecha_fin = datetime.now().date()
        fecha_inicio = fecha_fin - timedelta(days=ventana_dias)
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={fecha_inicio}&to={fecha_fin}&token={FINNHUB_API_KEY}"
        resp = SESION_HTTP.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.warning(f"⚠️ Error obteniendo noticias para {ticker}")
        return []

def obtener_earnings(ticker):
    """Obtiene calendario de earnings"""
    try:
        fecha_inicio = datetime.now().date()
        fecha_fin = fecha_inicio + timedelta(days=60)
        url = f"https://finnhub.io/api/v1/calendar/earnings?symbol={ticker}&from={fecha_inicio}&to={fecha_fin}&token={FINNHUB_API_KEY}"
        resp = SESION_HTTP.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json().get("earningsCalendar", [])
    except:
        return []

def obtener_earnings_historicos(ticker):
    """Obtiene earnings históricos"""
    try:
        url = f"https://finnhub.io/api/v1/stock/earnings?symbol={ticker}&token={FINNHUB_API_KEY}"
        resp = SESION_HTTP.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except:
        return []

# ================== FUNCIÓN PRINCIPAL DE ANÁLISIS ==================
def analizar_SP500_profesional(ticker_symbol):
    """
    Análisis profesional completo con validación robusta
    Incluye: Técnico, Fundamental, Riesgo, MACD, Alertas
    """
    try:
        yf_ticker = ticker_symbol.replace('.', '-')
        t = yf.Ticker(yf_ticker)
        hist = t.history(period="15mo")
        
        # ========== VALIDACIÓN ESTRICTA ==========
        # 1. Validar datos históricos
        if hist.empty or len(hist) < 252:  # 252 = 1 año trading
            return None
        
        # 2. Validar NaN críticos
        if hist['Close'].isna().sum() / len(hist) > 0.05:  # >5% NaN = rechazar
            return None
        
        hist = hist.dropna()
        
        # ========== LIMPIEZA DE COLUMNAS ==========
        hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]
        
        # ========== DATOS BÁSICOS ==========
        nombre_accion = t.info.get('longName', ticker_symbol)
        c_actual = hist['Close'].iloc[-1]
        
        # ========== ANÁLISIS TÉCNICO ==========
        # Soportes y Resistencias
        h_5d = hist['High'].tail(5).max()
        l_5d = hist['Low'].tail(5).min()
        pivot = (h_5d + l_5d + c_actual) / 3
        resistencia = (2 * pivot) - l_5d
        soporte = (2 * pivot) - h_5d
        
        # Indicadores básicos
        rsi = ta.momentum.RSIIndicator(hist['Close'], window=14).rsi().iloc[-1]
        sma20 = ta.trend.sma_indicator(hist['Close'], window=20).iloc[-1]
        sma50 = ta.trend.sma_indicator(hist['Close'], window=50).iloc[-1]
        sma200 = ta.trend.sma_indicator(hist['Close'], window=200).iloc[-1]
        
        # ATR y Volatilidad
        atr = ta.volatility.AverageTrueRange(
            hist['High'], hist['Low'], hist['Close'], window=14
        ).average_true_range().iloc[-1]
        atr_ratio = atr / c_actual
        volatilidad = hist['Close'].pct_change().rolling(252).std().iloc[-1] * (252**0.5)
        
        # Volumen
        vol_actual = hist['Volume'].iloc[-1]
        vol_medio_mes = hist['Volume'].tail(21).mean()
        vol_relativo = vol_actual / vol_medio_mes
        
        # ========== MACD (NUEVO) ==========
        try:
            macd = ta.momentum.MACD(
                hist['Close'], 
                window_fast=12, 
                window_slow=26, 
                window_sign=9
            )
            macd_diff = macd.macd_diff().iloc[-1]
            macd_value = macd.macd().iloc[-1]
            signal_macd = "🟢 BULLISH" if macd_diff > 0 else "🔴 BEARISH"
        except:
            macd_diff = 0
            macd_value = 0
            signal_macd = "⚪ N/A"
        
        # ========== ANÁLISIS FUNDAMENTAL ==========
        per = t.info.get('trailingPE', None)
        roe = t.info.get('returnOnEquity', None)
        deuda_equity = t.info.get('debtToEquity', None)
        crecimiento_ingresos = t.info.get('revenueGrowth', None)
        beta = t.info.get('beta', None)
        
        # Validación y defaults seguros
        if per and per > 0:
            score_per = 1 - normalize(per, 5, 50)
        else:
            score_per = 0.3  # Penalizar PE inválido
            per = None
        
        roe_val = roe if roe and roe > 0 else 0.05
        score_roe = normalize(roe_val, 0, 0.3)
        
        deuda_val = deuda_equity if deuda_equity and deuda_equity > 0 else 1.0
        score_deuda = 1 - normalize(deuda_val, 0, 2)
        
        crec_val = crecimiento_ingresos if crecimiento_ingresos and crecimiento_ingresos > -1 else 0.05
        score_crec = normalize(crec_val, 0, 0.3)
        
        beta_val = beta if beta and beta > 0 else 1.0
        
        # Score fundamental ponderado
        score_fund = (
            score_per * 0.25 + 
            score_roe * 0.25 + 
            score_deuda * 0.25 + 
            score_crec * 0.25
        )
        
        # ========== ANÁLISIS TÉCNICO MEJORADO ==========
        score_rsi = 1 - normalize(rsi, 30, 70)
        score_sma = sum([1 if c_actual > sma else 0 for sma in [sma20, sma50, sma200]]) / 3
        score_momentum = normalize(abs(macd_diff), 0, 0.5)
        score_volumen = 1 if vol_relativo > 1.1 else 0.5
        
        score_tec = (
            score_rsi * 0.25 +
            score_sma * 0.35 +
            score_momentum * 0.25 +
            score_volumen * 0.15
        )
        
        # ========== ANÁLISIS DE RIESGO ==========
        score_vol = 1 - normalize(atr_ratio, 0.01, 0.1)
        score_beta = 1 - normalize(beta_val, 0.5, 2)
        score_riesgo = (score_vol * 0.5 + score_beta * 0.5)
        
        # ========== SCORE FINAL ==========
        score_final = score_fund * 0.5 + score_tec * 0.3 + score_riesgo * 0.2
        score_final_10 = round(score_final * 10, 1)
        
        señal = "BUY" if score_final_10 >= 7 else "HOLD" if score_final_10 >= 4 else "SELL"
        
        # ========== NIVELES DE PRECIO ==========
        stop_loss = max(soporte, c_actual - 1.5 * atr)
        take_profit = min(resistencia, c_actual + 2 * atr)
        
        # ========== ALERTAS INTELIGENTES ==========
        alertas = []
        
        # Alerta de volatilidad extrema
        if volatilidad > 0.30:
            alertas.append("📊 VOL EXTREMA")
        
        # Alerta de volumen débil
        if vol_relativo < 0.8:
            alertas.append("📉 VOL DÉBIL")
        
        # Divergencia RSI-Precio (debilidad)
        c_5d_ago = hist['Close'].iloc[-5]
        if c_actual > c_5d_ago and rsi < 50:
            alertas.append("⚠️ DIVERGENCIA")
        
        # ATR muy alto
        if atr_ratio > 0.08:
            alertas.append("🎢 ATR ALTO")
        
        alertas_text = " | ".join(alertas) if alertas else "✓ OK"
        
        # ========== RETORNAR DICCIONARIO COMPLETO ==========
        return {
            "Ticker": ticker_symbol,
            "Nombre": nombre_accion,
            "Precio": round(c_actual, 2),
            "Score": score_final_10,
            "Señal": señal,
            
            # Técnico
            "RSI": round(rsi, 2),
            "SMA20": round(sma20, 2),
            "SMA50": round(sma50, 2),
            "SMA200": round(sma200, 2),
            "MACD": round(macd_diff, 4),
            "MACD_Signal": signal_macd,
            
            # Volatilidad y Volumen
            "ATR": round(atr, 2),
            "ATR_Ratio": round(atr_ratio, 4),
            "Volatilidad_Anual": round(volatilidad, 4),
            "Vol_Actual": int(vol_actual),
            "Vol_Media_Mes": int(vol_medio_mes),
            "Vol_Relativo": round(vol_relativo, 2),
            
            # Fundamental
            "PE": round(per, 2) if per else None,
            "ROE": round(roe_val * 100, 2) if roe else None,
            "Deuda/Equity": round(deuda_val, 2) if deuda_equity else None,
            "Crec_Ingresos": round(crec_val * 100, 2) if crecimiento_ingresos else None,
            "Beta": round(beta_val, 2),
            
            # Niveles
            "Soporte": round(soporte, 2),
            "Resistencia": round(resistencia, 2),
            "Stop_Loss": round(stop_loss, 2),
            "Take_Profit": round(take_profit, 2),
            
            # Alertas
            "Alertas": alertas_text,
            
            # Scores internos (para análisis)
            "Score_Fund": round(score_fund, 2),
            "Score_Tec": round(score_tec, 2),
            "Score_Riesgo": round(score_riesgo, 2),
        }
    
    except Exception as e:
        return None

# ================== FUNCIÓN CHECKLIST DE COMPRA ==========
def validar_compra_segura(ticker_info):
    """Genera checklist de seguridad para compra"""
    if ticker_info is None:
        return None
    
    pe = ticker_info.get('PE')
    roe = ticker_info.get('ROE')
    vol_relativo = ticker_info.get('Vol_Relativo', 0)
    rsi = ticker_info.get('RSI', 50)
    atr_ratio = ticker_info.get('ATR_Ratio', 0.1)
    score = ticker_info.get('Score', 0)
    
    checklist = {
        "✓ Score >= 7": score >= 7,
        "✓ PE < 25": (pe is not None and pe < 25) or pe is None,
        "✓ ROE > 10%": (roe is not None and roe > 10) or roe is None,
        "✓ Volumen confirmado": vol_relativo > 1.0,
        "✓ RSI 30-70": 30 <= rsi <= 70,
        "✓ ATR < 5% precio": atr_ratio < 0.05,
        "✓ Señal BUY/HOLD": ticker_info.get('Señal') in ['BUY', 'HOLD'],
    }
    
    aprobadas = sum(checklist.values())
    
    if aprobadas >= 6:
        recomendacion = "✅ SEGURO COMPRAR"
        color = "green"
    elif aprobadas >= 4:
        recomendacion = "⚠️ REVISAR ANTES"
        color = "orange"
    else:
        recomendacion = "❌ NO COMPRAR"
        color = "red"
    
    return {
        "checklist": checklist,
        "aprobadas": f"{aprobadas}/7",
        "recomendacion": recomendacion,
        "color": color
    }

def generar_recomendacion_precio(ticker_info):
    """Genera recomendación de precios objetivo"""
    precio = ticker_info.get('Precio', 0)
    resistencia = ticker_info.get('Resistencia', 0)
    soporte = ticker_info.get('Soporte', 0)
    score = ticker_info.get('Score', 0)
    
    if score >= 7.5:
        upside = ((resistencia - precio) / precio * 100) if precio > 0 else 0
        return f"🟢 BUY | Target +{round(upside, 1)}% @ ${round(resistencia, 2)}"
    elif score >= 5.5:
        return f"🟡 HOLD | Esperar confirmación"
    else:
        downside = ((soporte - precio) / precio * 100) if precio > 0 else 0
        return f"🔴 SELL | Riesgo {round(abs(downside), 1)}%"

# ================== GENERAR SCANNER ==========
@st.cache_data(show_spinner=True, ttl=3600, max_entries=3)
def generar_scanner(cache_key):
    """Genera scanner completo del SP500"""
    resultados = []
    total = len(sp500_tickers)
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    for i, tick in enumerate(sp500_tickers):
        res = analizar_SP500_profesional(tick)
        if res:
            resultados.append(res)
        
        porcentaje = int((i + 1) / total * 100)
        progress_bar.progress((i + 1) / total)
        progress_text.text(f"Procesando acciones... {porcentaje}% | {i + 1}/{total} ✓")
    
    df = pd.DataFrame(resultados)
    
    if "Score" in df.columns:
        df = df.sort_values(by="Score", ascending=False)
    
    progress_text.text("¡Procesamiento completado! ✅")
    return df

# ================== CARGA DE DATOS ==========
if 'df' not in st.session_state:
    st.session_state['df'] = generar_scanner("scanner_sp500_v2")
    st.session_state['last_refresh'] = datetime.now()

col_refresh, col_auto = st.columns([1, 1])

with col_refresh:
    if st.button("🔄 Actualizar datos", use_container_width=True):
        generar_scanner.clear()
        st.session_state['df'] = generar_scanner("scanner_sp500_v2")
        st.session_state['last_refresh'] = datetime.now()
        st.success("✅ Datos actualizados")

df = st.session_state['df']

if df.empty:
    st.error("❌ No hay datos disponibles")
    st.stop()

# ================== SIDEBAR - FILTROS ==========
st.sidebar.markdown("### 📊 Dashboard SP500 Pro")
st.sidebar.markdown(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y')}")
hora_más_una = datetime.now() + timedelta(hours=1)
st.sidebar.markdown(f"**Hora:** {hora_más_una.strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**Última actualización:** {st.session_state['last_refresh'].strftime('%d/%m/%Y %H:%M:%S')}")

st.sidebar.markdown("---")
st.sidebar.header("🎯 Filtros")

# Filtros dinámicos
score_min, score_max = st.sidebar.slider(
    "Score",
    min_value=float(df["Score"].min()),
    max_value=float(df["Score"].max()),
    value=(7.0, float(df["Score"].max())),
    step=0.1
)

señales = df["Señal"].unique()
señal_filtrada = st.sidebar.multiselect("Filtrar por Señal", señales, default=["BUY", "HOLD"])

# Filtro de alertas
sin_alertas = st.sidebar.checkbox("Solo sin alertas críticas", value=False)

# Filtro de volatilidad
vol_max = st.sidebar.slider("Volatilidad máxima anualizada", 0.0, 1.0, 0.5, 0.05)

# Aplicar filtros
df_filtrado = df[
    (df["Score"] >= score_min) & 
    (df["Score"] <= score_max) &
    (df["Señal"].isin(señal_filtrada)) &
    (df["Volatilidad_Anual"] <= vol_max)
]

if sin_alertas:
    df_filtrado = df_filtrado[df_filtrado["Alertas"] == "✓ OK"]

if df_filtrado.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados.")
    st.stop()

# Selector de acción
accion_global = st.sidebar.selectbox(
    "Selecciona acción",
    df_filtrado["Ticker"] + " - " + df_filtrado["Nombre"],
    key="accion_global"
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**ℹ️ Indicadores:**
- 🟢 BUY: Score >= 7
- 🟡 HOLD: Score 4-7
- 🔴 SELL: Score < 4
""")

# ================== FORMATO DE COLUMNAS ==========
formato_columnas = {
    "Precio": "{:.2f}",
    "Score": "{:.1f}",
    "RSI": "{:.2f}",
    "SMA20": "{:.2f}",
    "SMA50": "{:.2f}",
    "SMA200": "{:.2f}",
    "MACD": "{:.4f}",
    "ATR": "{:.2f}",
    "ATR_Ratio": "{:.4f}",
    "Volatilidad_Anual": "{:.4f}",
    "Vol_Actual": "{:.0f}",
    "Vol_Media_Mes": "{:.0f}",
    "Vol_Relativo": "{:.2f}",
    "Soporte": "{:.2f}",
    "Resistencia": "{:.2f}",
    "Stop_Loss": "{:.2f}",
    "Take_Profit": "{:.2f}",
    "PE": "{:.2f}",
    "ROE": "{:.2f}",
    "Deuda/Equity": "{:.2f}",
    "Crec_Ingresos": "{:.2f}",
    "Beta": "{:.2f}",
    "Score_Fund": "{:.2f}",
    "Score_Tec": "{:.2f}",
    "Score_Riesgo": "{:.2f}",
}

# ================== ESTILO SCORE ==========
def color_score(val):
    """Aplica colores según el score"""
    try:
        val = float(val)
        if val >= 7:
            return 'background-color: #2ECC71; color: white'
        elif val >= 4:
            return 'background-color: #F39C12; color: white'
        else:
            return 'background-color: #E74C3C; color: white'
    except:
        return ''

def color_señal(val):
    """Colorea las señales"""
    if val == "BUY":
        return 'background-color: #27AE60; color: white'
    elif val == "HOLD":
        return 'background-color: #F39C12; color: white'
    else:
        return 'background-color: #C0392B; color: white'

# ================== TABS PRINCIPALES ==========
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Análisis",
    "📈 Gráfico",
    "📊 Resultados",
    "📰 Noticias",
    "🌍 Otros Activos"
])

# ================== TAB 1: ANÁLISIS DETALLADO ==========
with tab1:
    st.subheader("🔍 Análisis Detallado")
    
    ticker_seleccionado = accion_global.split(" - ")[0]
    df_accion = df_filtrado[df_filtrado["Ticker"] == ticker_seleccionado]
    
    if df_accion.empty:
        st.error("Acción no encontrada en los datos filtrados")
        st.stop()
    
    accion_data = df_accion.iloc[0]
    
    # Mostrar KPIs principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Precio", f"${accion_data['Precio']}", delta=None)
    
    with col2:
        st.metric("Score", accion_data['Score'], delta=None)
    
    with col3:
        st.metric("RSI", f"{accion_data['RSI']}", delta=None)
    
    with col4:
        st.metric("Volatilidad", f"{round(accion_data['Volatilidad_Anual']*100, 1)}%", delta=None)
    
    with col5:
        st.metric("Vol Relativo", f"{accion_data['Vol_Relativo']}x", delta=None)
    
    st.markdown("---")
    
    # Mostrar tabla detallada de la acción
    columnas_mostrar = [
        "Ticker", "Nombre", "Precio", "Score", "Señal", "RSI", "MACD_Signal",
        "SMA20", "SMA50", "SMA200", "ATR", "ATR_Ratio", "Volatilidad_Anual",
        "Vol_Relativo", "PE", "ROE", "Deuda/Equity", "Beta",
        "Soporte", "Resistencia", "Stop_Loss", "Take_Profit", "Alertas"
    ]
    
    columnas_disponibles = [col for col in columnas_mostrar if col in df_accion.columns]
    
    st.dataframe(
        df_accion[columnas_disponibles].style.applymap(color_score, subset=['Score']).applymap(color_señal, subset=['Señal']).format(formato_columnas),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Recomendación de precios
    st.subheader("💰 Análisis de Precios")
    recomendacion = generar_recomendacion_precio(accion_data.to_dict())
    st.info(recomendacion)
    
    # Checklist de seguridad
    st.subheader("🔒 Checklist de Compra Segura")
    validacion = validar_compra_segura(accion_data.to_dict())
    
    if validacion:
        for check, resultado_check in validacion['checklist'].items():
            if resultado_check:
                st.success(check)
            else:
                st.warning(check)
        
        if validacion['color'] == 'green':
            st.success(f"### {validacion['recomendacion']}")
        elif validacion['color'] == 'orange':
            st.warning(f"### {validacion['recomendacion']}")
        else:
            st.error(f"### {validacion['recomendacion']}")
        
        st.caption(f"Criterios cumplidos: {validacion['aprobadas']}")
    
    # Scores desglosados
    st.subheader("📊 Desglose de Scores")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Score Fundamental", accion_data['Score_Fund'])
    
    with col2:
        st.metric("Score Técnico", accion_data['Score_Tec'])
    
    with col3:
        st.metric("Score Riesgo", accion_data['Score_Riesgo'])
    
    # Mostrar resto de acciones
    st.markdown("---")
    st.subheader("📊 Resto de Acciones Filtradas")
    
    df_restantes = df_filtrado[df_filtrado["Ticker"] != ticker_seleccionado]
    
    if not df_restantes.empty:
        st.dataframe(
            df_restantes[columnas_disponibles].style.applymap(color_score, subset=['Score']).applymap(color_señal, subset=['Señal']).format(formato_columnas),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay más acciones en los filtros actuales")

# ================== TAB 2: GRÁFICO TÉCNICO ==========
with tab2:
    st.subheader("📈 Análisis Gráfico")
    
    ticker = accion_global.split(" - ")[0]
    
    # Descargar histórico
    hist = yf.Ticker(ticker).history(period="1y")
    
    # Calcular indicadores
    hist["SMA20"] = hist["Close"].rolling(20).mean()
    hist["SMA50"] = hist["Close"].rolling(50).mean()
    hist["SMA200"] = hist["Close"].rolling(200).mean()
    
    # MACD
    macd = ta.momentum.MACD(hist['Close'], window_fast=12, window_slow=26, window_sign=9)
    hist["MACD"] = macd.macd()
    hist["MACD_Signal"] = macd.macd_signal()
    hist["MACD_Diff"] = macd.macd_diff()
    
    # Obtener niveles de soporte/resistencia de la acción
    fila = df_filtrado[df_filtrado["Ticker"] == ticker].iloc[0]
    soporte = fila["Soporte"]
    resistencia = fila["Resistencia"]
    
    # Crear gráfico con subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25]
    )
    
    # Precio y medias móviles
    fig.add_trace(
        go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name="Precio"
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=hist.index, y=hist["SMA20"], name="SMA20", line=dict(color='#3498db')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=hist.index, y=hist["SMA50"], name="SMA50", line=dict(color='#e74c3c')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=hist.index, y=hist["SMA200"], name="SMA200", line=dict(color='#f39c12')),
        row=1, col=1
    )
    
    # Soporte y Resistencia
    fig.add_trace(
        go.Scatter(
            x=[hist.index[0], hist.index[-1]],
            y=[soporte, soporte],
            name="Soporte",
            line=dict(dash='dash', color='green')
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=[hist.index[0], hist.index[-1]],
            y=[resistencia, resistencia],
            name="Resistencia",
            line=dict(dash='dash', color='red')
        ),
        row=1, col=1
    )
    
    # Volumen
    fig.add_trace(
        go.Bar(x=hist.index, y=hist["Volume"], name="Volumen", marker_color='rgba(100, 100, 200, 0.3)'),
        row=2, col=1
    )
    
    # MACD
    fig.add_trace(
        go.Scatter(x=hist.index, y=hist["MACD"], name="MACD", line=dict(color='#2ecc71')),
        row=3, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=hist.index, y=hist["MACD_Signal"], name="MACD Signal", line=dict(color='#e67e22')),
        row=3, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=hist.index,
            y=hist["MACD_Diff"],
            name="MACD Histogram",
            marker_color=['green' if x > 0 else 'red' for x in hist["MACD_Diff"]],
            showlegend=False
        ),
        row=3, col=1
    )
    
    # Actualizar layout
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=1000,
        title_text=f"Análisis Técnico - {ticker}",
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="Precio USD", row=1, col=1)
    fig.update_yaxes(title_text="Volumen", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

# ================== TAB 3: RESULTADOS Y EARNINGS ==========
with tab3:
    st.subheader("📊 Calendario de Earnings y Resultados")
    
    ticker = accion_global.split(" - ")[0]
    
    # Próximos resultados
    st.subheader("📅 Próximos Resultados")
    future_earnings = obtener_earnings(ticker)
    
    if future_earnings:
        earnings_data = []
        for e in future_earnings[:3]:
            fecha = e.get("date", "N/A")
            hora = e.get("hour", "TBD")
            dias_restantes = (pd.to_datetime(fecha).date() - datetime.now().date()).days if fecha != "N/A" else -1
            
            earnings_data.append({
                "Fecha": fecha,
                "Hora": hora,
                "Días": dias_restantes
            })
        
        df_earnings = pd.DataFrame(earnings_data)
        st.dataframe(df_earnings, use_container_width=True, hide_index=True)
        
        for e in future_earnings[:1]:
            dias = (pd.to_datetime(e.get("date")).date() - datetime.now().date()).days
            if dias <= 3:
                st.error(f"🚨 Earnings en {dias} días - RIESGO VOLATILIDAD ALTA")
            elif dias <= 7:
                st.warning(f"⚠️ Earnings en {dias} días - Monitorear posición")
            elif dias <= 14:
                st.info(f"ℹ️ Earnings en {dias} días - Vigilar")
    else:
        st.info("No hay próximos resultados disponibles")
    
    st.markdown("---")
    
    # Resultados históricos
    st.subheader("📈 Últimos Resultados")
    past_earnings = obtener_earnings_historicos(ticker)
    
    if past_earnings:
        historico_data = []
        for e in past_earnings[:6]:
            historico_data.append({
                "Período": e.get('period', 'N/A'),
                "Actual": e.get('actual', 'N/A'),
                "Estimado": e.get('estimate', 'N/A'),
                "Sorpresa": f"{e.get('surprisePercent', 0):.2f}%"
            })
        
        df_historico = pd.DataFrame(historico_data)
        st.dataframe(df_historico, use_container_width=True, hide_index=True)
    else:
        st.info("No hay resultados históricos disponibles")

# ================== TAB 4: NOTICIAS ==========
with tab4:
    st.subheader("📰 Noticias Recientes")
    
    ticker = accion_global.split(" - ")[0]
    noticias = obtener_noticias(ticker, VENTANA_NOTICIAS_DIAS)
    
    if noticias:
        for i, n in enumerate(noticias[:15]):
            col1, col2 = st.columns([1, 5])
            
            with col1:
                # Mostrar fecha
                fecha = datetime.fromtimestamp(n.get("datetime", 0))
                st.caption(fecha.strftime('%d/%m'))
            
            with col2:
                # Título
                st.markdown(f"**{n.get('headline', 'N/A')}**")
                
                # Fuente y fecha
                col_fuente, col_link = st.columns([3, 1])
                with col_fuente:
                    st.caption(f"{n.get('source', 'N/A')} • {fecha.strftime('%H:%M')}")
                
                with col_link:
                    st.markdown(f"[Leer →]({n.get('url', '#')})")
            
            st.markdown("---")
    else:
        st.info("No hay noticias recientes disponibles")

# ================== TAB 5: OTROS ACTIVOS ==========
with tab5:
    st.subheader("🌍 Otros Activos (Bitcoin, Oro, Plata)")
    
    activos = {
        "Bitcoin USD": {"ticker": "BTC-USD", "moneda": "USD"},
        "Bitcoin EUR": {"ticker": "BTC-EUR", "moneda": "EUR"},
        "Oro": {"ticker": "GC=F", "moneda": "USD"},
        "Plata": {"ticker": "SI=F", "moneda": "USD"}
    }
    
    tickers = [v["ticker"] for v in activos.values()]
    
    # Descargar datos en una sola llamada
    try:
        data = yf.download(tickers, period="1y", group_by="ticker", progress=False)
        
        datos_tabla = []
        historicos = {}
        
        for nombre, info in activos.items():
            ticker = info["ticker"]
            
            if ticker in data.columns.get_level_values(0):
                hist = data[ticker].dropna()
                
                if not hist.empty:
                    precio_actual = hist["Close"].iloc[-1]
                    precio_1m_ago = hist["Close"].iloc[-21] if len(hist) >= 21 else hist["Close"].iloc[0]
                    cambio = ((precio_actual - precio_1m_ago) / precio_1m_ago * 100) if precio_1m_ago > 0 else 0
                    
                    datos_tabla.append({
                        "Activo": nombre,
                        "Ticker": ticker,
                        "Precio Actual": round(precio_actual, 2),
                        "Cambio 1M": f"{round(cambio, 2)}%",
                        "Moneda": info["moneda"]
                    })
                    
                    historicos[nombre] = hist
        
        # Tabla de precios actuales
        if datos_tabla:
            df_activos = pd.DataFrame(datos_tabla)
            st.subheader("📊 Precios Actuales")
            st.dataframe(df_activos, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Gráficos históricos
            st.subheader("📈 Histórico 1 Año")
            
            col1, col2 = st.columns(2)
            
            for idx, (nombre, hist) in enumerate(historicos.items()):
                fig = go.Figure()
                
                fig.add_trace(
                    go.Scatter(
                        x=hist.index,
                        y=hist["Close"],
                        mode="lines",
                        name=nombre,
                        fill='tozeroy'
                    )
                )
                
                fig.update_layout(
                    title=f"{nombre} - Histórico 1 año",
                    xaxis_title="Fecha",
                    yaxis_title="Precio",
                    height=400,
                    hovermode='x unified'
                )
                
                if idx % 2 == 0:
                    with col1:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    with col2:
                        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al cargar activos alternativos: {str(e)}")

# ================== FOOTER ==========
st.markdown("---")
st.markdown("""
### ⚠️ Disclaimer Importante
Este dashboard es una **herramienta de análisis** para propósitos educativos. No constituye recomendación de inversión.

**Antes de invertir:**
1. ✅ Valida los datos con múltiples fuentes
2. ✅ Consulta con un asesor financiero profesional
3. ✅ Revisa manualmente earnings y noticias recientes
4. ✅ Establece un plan de riesgo claro (posición % y stop loss)
5. ✅ Entiende completamente la compañía antes de invertir

**Riesgos:**
- Los datos pueden estar desactualizados
- El análisis técnico no garantiza resultados futuros
- Las acciones son inversiones de alto riesgo
""")
