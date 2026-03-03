import yfinance as yf
import ta
import pandas as pd
from datetime import datetime

# Lista oficial de tickers SP500 Yahoo Finance
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

def analizar_SP500_profesional(ticker_symbol):
    try:
        yf_ticker = ticker_symbol.replace('.', '-')
        t = yf.Ticker(yf_ticker)
        hist = t.history(period="15mo")
        if hist.empty or len(hist) < 200:
            return None

        nombre_accion = t.info.get('longName', ticker_symbol)
        hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]

        # Precios
        c_actual = hist['Close'].iloc[-1]
        h_5d = hist['High'].tail(5).max()
        l_5d = hist['Low'].tail(5).min()

        # Soporte/Resistencia pivote
        pivot = (h_5d + l_5d + c_actual) / 3
        resistencia = (2 * pivot) - l_5d
        soporte = (2 * pivot) - h_5d

        # Indicadores
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

        # Score
        score = 0
        if rsi < 40: score += 2
        elif rsi > 70: score -= 2
        if c_actual > sma20: score += 2
        if c_actual > sma50: score += 1
        if c_actual > sma200: score += 1
        if vol_relativo > 1.2: score += 1

        # Señal
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

    except Exception as e:
        print(f"❌ Error en {ticker_symbol}: {e}")
        return None

if __name__ == "__main__":
    print(f"🔍 Escaneando SP500 - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    resultados = []
    for tick in sp500_tickers:
        res = analizar_SP500_profesional(tick)
        if res:
            resultados.append(res)
            print(f"✅ {tick} analizado.")

    if resultados:
        df = pd.DataFrame(resultados)
        df = df.sort_values(by="Score", ascending=False)
        df.to_csv("Scanner_SP500_Profesional.csv", index=False)
        print(f"\n📁 Archivo 'Scanner_SP500_Profesional.csv' generado correctamente.")
    else:
        print("No se pudieron obtener datos. Revisa la conexión.")
