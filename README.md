# TradingSignals
Create Sales/Purchasing Signals usign Yahoo Finance data. Input a tickers csv file. Output a googleSheet file

# Análisis de Señales en Tickers Financieros

Este script en Python realiza análisis técnico sobre tickers financieros utilizando bibliotecas como `numpy`, `pandas`, `yfinance`, `talib`, y `pandas_ta`. Además, guarda los resultados en una hoja de cálculo de Google Sheets.

## 🚀 Características

- Obtención de datos históricos de tickers usando `yfinance`
- Cálculo de indicadores técnicos como **RSI**, **MACD**, y **Bandas de Bollinger**
- Implementación del **Ichimoku Kinko Hyo**
- Exportación de señales de compra/venta a Google Sheets

## 📦 Requisitos

Antes de ejecutar el script, asegúrate de tener las siguientes bibliotecas instaladas:

```bash
pip install numpy pandas yfinance talib pandas-ta pygsheets matplotlib

