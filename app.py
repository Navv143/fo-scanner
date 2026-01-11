import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Pro-Trade F&O Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Fixed the typo here: changed unsafe_base_html to unsafe_allow_html
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 20px !important; color: #00ffcc; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #1e2129;
        border-radius: 5px; color: white; padding: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #00ffcc !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# 3-Minute Auto-Refresh
st_autorefresh(interval=3 * 60 * 1000, key="fnotracker")

# --- DATA LISTS ---
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS", "INDIA VIX": "^INDIAVIX"}

FO_STOCKS = [
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BSOFT.NS", "BPCL.NS", "BRITANNIA.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

# --- LOGIC FUNCTIONS ---
def get_index_data():
    data = {}
    for name, sym in INDICES.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="3d") # Increased period for weekend/holiday safety
            if len(hist) < 2: continue
            price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((price - prev_price) / prev_price) * 100
            data[name] = {"price": round(price, 2), "change": round(change, 2)}
        except: pass
    return data

def scan_logic(symbol, vol_trigger):
    try:
        df = yf.download(symbol, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 10: return None
        
        unique_dates = sorted(list(set(df.index.date)))
        if len(unique_dates) < 2: return None
        
        yest_date = unique_dates[-2]
        today_date = unique_dates[-1]
        
        yest = df[df.index.date == yest_date]
        today = df[df.index.date == today_date]

        if today.empty: return None

        pdh, pdl = yest['High'].max(), yest['Low'].min()
        yest_vol = yest['Volume'].sum()
        curr_price = today['Close'].iloc[-1]
        today_vol = today['Volume'].sum()
        
        # VWAP Approximation
        vwap = (today['Close'] * today['Volume']).sum() / today['Volume'].sum()
        vol_ratio = today_vol / yest_vol
        day_change = ((curr_price - yest['Close'].iloc[-1]) / yest['Close'].iloc[-1]) * 100

        res = {
            "Symbol": symbol.replace(".NS", ""),
            "LTP": round(curr_price, 2),
            "Chg %": round(day_change, 2),
            "Vol Ratio": round(vol_ratio, 2),
            "Signal": "Neutral"
        }

        # Momentum Filter Logic
        if curr_price > pdh and vol_ratio > vol_trigger and curr_price > vwap:
            res["Signal"] = "🚀 BUY"
        elif curr_price < pdl and vol_ratio > vol_trigger and curr_price < vwap:
            res["Signal"] = "📉 SELL"
        
        return res
    except: return None

# --- APP LAYOUT ---
st.title("🛡️ Pro-Trader F&O Intelligence")
st.caption(f"Real-time Dashboard • Last Update: {datetime.now().strftime('%H:%M:%S')}")

# Top Bar Index Metrics
idx_data = get_index_data()
if idx_data:
    cols = st.columns(len(idx_data))
    for i, (name, val) in enumerate(idx_data.items()):
        cols[i].metric(name, f"₹{val['price']}", f"{val['change']}%")

st.divider()

# Sidebar
st.sidebar.header("Control Panel")
vol_threshold = st.sidebar.slider("Volume Threshold %", 5, 50, 25)
st.sidebar.markdown("""
---
**Scan Criteria:**
- **BUY:** Price > Prev Day High & Vol > Threshold & Above VWAP
- **SELL:** Price < Prev Day Low & Vol > Threshold & Below VWAP
""")

tab1, tab2 = st.tabs(["🔥 Momentum Alerts", "📋 Full F&O Watchlist"])

with st.spinner("Fetching market data..."):
    all_data = []
    # Multithreading for speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(scan_logic, s, vol_threshold/100) for s in FO_STOCKS]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r: all_data.append(r)

    df_master = pd.DataFrame(all_data) if all_data else pd.DataFrame()

with tab1:
    if not df_master.empty:
        alerts = df_master[df_master['Signal'] != "Neutral"]
        if not alerts.empty:
            st.dataframe(alerts.sort_values(by="Vol Ratio", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No momentum breakouts detected yet. Best monitored between 9:45 AM - 11:00 AM.")
    else:
        st.warning("Awaiting market open for fresh data.")

with tab2:
    if not df_master.empty:
        search = st.text_input("Quick Find Stock", placeholder="Type stock name...")
        disp_df = df_master.copy()
        if search:
            disp_df = disp_df[disp_df['Symbol'].str.contains(search.upper())]
        
        st.dataframe(disp_df[['Symbol', 'LTP', 'Chg %', 'Vol Ratio']].sort_values(by="Chg %", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Watchlist will populate when market is active.")

st.markdown("---")
st.caption("Powered by Yahoo Finance Free Feed. Note: Intraday data may have a 1-2 min delay.")