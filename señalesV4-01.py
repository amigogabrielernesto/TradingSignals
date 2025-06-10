import numpy as np
import pandas as pd
import pandas_ta as pdta
import matplotlib.pyplot as plt
import yfinance as yf
import talib
import pygsheets
from datetime import datetime

# Configuración
CLIENT_SECRETS_FILE = r"C:\temp\client_secret.json"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
INPUT_FILE = "tickers.txt"
OUTPUT_FILE = "señales.txt"
RANGO_HOJA = "A1:AI200"
NOMBRE_HOJA = 'Señales'
NOMBRE_ARCHIVO_GOOGLE = 'seniales'

# Autenticación
gc = pygsheets.authorize(service_file=CLIENT_SECRETS_FILE)
sh = gc.open(NOMBRE_ARCHIVO_GOOGLE)
wks = sh.worksheet('title', NOMBRE_HOJA)
wks.range(RANGO_HOJA).clear()

# Cargar tickers
tickers_df = pd.read_csv(INPUT_FILE, sep=",", names=["TickerBA", "TickerYF"])
tickers_list = tickers_df["TickerYF"].tolist()

def obtener_datos(ticker):
    try:
        papel = yf.Ticker(ticker)
        history = papel.history(interval='1d', period="5mo")
        return papel, history
    except Exception as e:
        print(f"[ERROR] Falló al obtener datos de {ticker}: {e}")
        return None, None

def calcular_ichimoku(df):
    df['Conversion'] = (df['High'].rolling(9).max() + df['Low'].rolling(9).min()) / 2
    df['Base'] = (df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 2
    df['lead_span_A'] = ((df['Conversion'] + df['Base']) / 2).shift(26)
    df['lead_span_B'] = ((df['High'].rolling(52).max() + df['Low'].rolling(52).min()) / 2).shift(26)
    df['Lagging_span'] = df['Close'].shift(-26)
    return df

def calcular_indicadores(df):
    df["RSI"] = talib.RSI(df["Close"], 14)
    df["RSI_Change"] = df["RSI"].diff()
    df["RSI_Signal"] = "Hold"
    df.loc[(df["RSI"] > 35) & (df["RSI"].shift(1) < 35), "RSI_Signal"] = "Comprar"
    df.loc[(df["RSI"] < 65) & (df["RSI"].shift(1) > 65), "RSI_Signal"] = "Vender"

    df["MACD"], df["MACD_Signal"], _ = talib.MACD(df["Close"])
    df["MACD_Change"] = df["MACD"] - df["MACD_Signal"]
    df["Prev_MACD_Change"] = df["MACD_Change"].shift(1)
    df["MACD_Signal_Trade"] = "Hold"
    df.loc[(df["MACD_Change"] > 0) & (df["Prev_MACD_Change"] < 0), "MACD_Signal_Trade"] = "Comprar"
    df.loc[(df["MACD_Change"] < 0) & (df["Prev_MACD_Change"] > 0), "MACD_Signal_Trade"] = "Vender"

    bb = pdta.bbands(df["Close"], length=20, std=2)
    df = pd.concat([df, bb], axis=1)
    df["BB_Signal"] = "Hold"
    df.loc[df["Close"] < df["BBL_20_2.0"], "BB_Signal"] = "Comprar"
    df.loc[df["Close"] > df["BBU_20_2.0"], "BB_Signal"] = "Vender"
    
    return df

def calcular_seniales(df):
    df["lean_span_max"] = df[["lead_span_A", "lead_span_B"]].max(axis=1)
    df["lean_span_min"] = df[["lead_span_A", "lead_span_B"]].min(axis=1)
    df["ISHI_Signal"] = np.where(df["Close"] > df["lean_span_max"], "Vender",
                          np.where(df["Close"] < df["lean_span_min"], "Comprar", "Hold"))
    return df

def procesar_ticker(row, i):
    tickerBA = row["TickerBA"]
    ticker = row["TickerYF"]
    
    papel, result = obtener_datos(ticker)
    if result is None or result.empty:
        return None

    per_ratio = papel.info.get("trailingPE", 0)
    exDividend = papel.info.get('exDividendDate', None)
    exDividend = pd.to_datetime(exDividend, unit='s') if exDividend else "No disponible"

    try:
        fechaBalance = papel.earnings_dates.index[0].strftime(DATE_FORMAT) if not papel.earnings_dates.empty else "No disponible"
    except:
        fechaBalance = "No disponible"

    result.index = pd.to_datetime(result.index)
    result = calcular_ichimoku(result)
    result = calcular_seniales(result)
    result = calcular_indicadores(result)

    ultima = result.tail(1).copy()
    ultima["TickerBA"] = tickerBA
    ultima["Ticker"] = ticker
    ultima["Per_Ratio"] = per_ratio
    ultima["Prox_Balance"] = fechaBalance
    ultima["Fecha Calculo"] = datetime.now().strftime(DATE_FORMAT)

    if i == 1:
        ultima.to_csv(OUTPUT_FILE, sep="\t", index=False, header=True, mode="w")
    else:
        ultima.to_csv(OUTPUT_FILE, sep="\t", index=False, header=False, mode="a")

    print(f"{i} {ticker} Close={ultima['Close'].values[0]} ExDiv={exDividend} Señales: ISHI={ultima['ISHI_Signal'].values[0]} MACD={ultima['MACD_Signal_Trade'].values[0]} RSI={ultima['RSI_Signal'].values[0]} BB={ultima['BB_Signal'].values[0]}")
    return ultima

# Loop principal
for i, row in enumerate(tickers_df.itertuples(index=False), start=1):
    procesar_ticker(row._asdict(), i)

# Subir a Google Sheets
df_final = pd.read_csv(OUTPUT_FILE, sep="\t")
wks.set_dataframe(df_final, (1, 1))
