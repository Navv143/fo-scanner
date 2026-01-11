import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
import concurrent.futures

# Set Page Config for Mobile
st.set_page_config(page_title="F&O Pulse", layout="wide", initial_sidebar_state="collapsed")

# 1. Comprehensive F&O List (Approx 190+ Main Tickers - Add more as needed)
FO_STOCKS = [
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BSOFT.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "STL.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

def scan_stock(symbol):
    try:
        # Fetch 2 days of 15m data to calculate PDH and Today's Volume
        df = yf.download(symbol, period="2d", interval="15m", progress=False)
        if df.empty or len(df) < 5: return None

        # Split into Yesterday and Today
        dates = df.index.date
        unique_dates = sorted(list(set(dates)))
        
        yest_df = df[dates == unique_dates[-2]]
        today_df = df[dates == unique_dates[-1]]

        pdh = yest_df['High'].max()
        pdl = yest_df['Low'].min()
        yest_vol = yest_df['Volume'].sum()

        curr_price = today_df['Close'].iloc[-1]
        today_vol = today_df['Volume'].sum()
        
        # VWAP Approximation (Avg Price * Vol)
        vwap = (today_df['Close'] * today_df['Volume']).sum() / today_df['Volume'].sum()
        
        vol_ratio = today_vol / yest_vol

        # Momentum Logic
        signal = "Neutral"
        if curr_price > pdh and vol_ratio > 0.30 and curr_price > vwap:
            signal = "🚀 BULLISH"
        elif curr_price < pdl and vol_ratio > 0.30 and curr_price < vwap:
            signal = "📉 BEARISH"

        if signal != "Neutral":
            return {
                "Stock": symbol.replace(".NS", ""),
                "Price": round(curr_price, 2),
                "Signal": signal,
                "Vol % (of Yest)": f"{round(vol_ratio * 100)}%",
                "VWAP": round(vwap, 2)
            }
    except:
        return None

# Streamlit UI
st.title("⚡ F&O Intraday Scanner")
st.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

# Auto Refresh Logic (Every 180 seconds = 3 mins)
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=3 * 60 * 1000, key="datarefresh")

with st.spinner('Scanning 200+ F&O Stocks...'):
    results = []
    # Use ThreadPool to scan multiple stocks at once (MUCH faster)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scan_stock, s) for s in FO_STOCKS]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

if results:
    df_display = pd.DataFrame(results)
    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    st.info("No Momentum Stocks found right now. Criteria: Price > PDH/PDL + Vol > 30% of Yesterday + VWAP Alignment.")

st.write("---")
st.caption("Settings: Scans for 30% of yesterday's total volume achieved intraday with PDH/PDL breakout.")