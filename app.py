import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Pro-Trade F&O Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Professional UI Styling
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
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3-Minute Auto-Refresh
st_autorefresh(interval=3 * 60 * 1000, key="fnotracker")

# --- UTILS ---
def get_market_status():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    # Market open: Mon-Fri, 9:15 to 15:30
    if now.weekday() < 5 and (now.hour > 9 or (now.hour == 9 and now.minute >= 15)) and (now.hour < 15 or (now.hour == 15 and now.minute <= 30)):
        return "🟢 MARKET OPEN", "#002b1b", "#00ffcc"
    else:
        return "🔴 MARKET CLOSED (Showing Last Session Data)", "#2b0000", "#ff4b4b"

# --- DATA LISTS ---
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS", "INDIA VIX": "^INDIAVIX"}

FO_STOCKS = [
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BSOFT.NS", "BPCL.NS", "BRITANNIA.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

# --- LOGIC ---
def get_index_data():
    data = {}
    for name, sym in INDICES.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            if len(hist) < 2: continue
            price = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            chg = ((price - prev) / prev) * 100
            data[name] = {"price": round(price, 2), "chg": round(chg, 2)}
        except: pass
    return data

def scan_logic(symbol, vol_trigger):
    try:
        df = yf.download(symbol, period="7d", interval="1d", progress=False) # Get daily closes
        if df.empty or len(df) < 3: return None
        
        # Prices
        curr_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        pdh, pdl = df['High'].iloc[-2], df['Low'].iloc[-2]
        
        # Vol Logic
        today_vol = df['Volume'].iloc[-1]
        yest_vol = df['Volume'].iloc[-2]
        vol_ratio = today_vol / yest_vol
        day_chg = ((curr_price - prev_price) / prev_price) * 100

        res = {"Symbol": symbol.replace(".NS",""), "LTP": round(curr_price, 2), "Chg %": round(day_chg, 2), "Vol Ratio": round(vol_ratio, 2), "Signal": "Neutral"}

        # Momentum Signal
        if curr_price > pdh and vol_ratio > vol_trigger: res["Signal"] = "🚀 BUY"
        elif curr_price < pdl and vol_ratio > vol_trigger: res["Signal"] = "📉 SELL"
        
        return res
    except: return None

# --- UI ---
st.title("🛡️ Pro-Trader F&O Intelligence")
m_status, b_color, t_color = get_market_status()
st.markdown(f'<div class="status-box" style="background-color: {b_color}; color: {t_color};">{m_status}</div>', unsafe_allow_html=True)

# Indices
idx = get_index_data()
if idx:
    cols = st.columns(len(idx))
    for i, (n, v) in enumerate(idx.items()):
        cols[i].metric(n, f"₹{v['price']}", f"{v['chg']}%")

st.divider()

# Sidebar
vol_threshold = st.sidebar.slider("Volume Threshold %", 5, 100, 25)
st.sidebar.caption("Tip: On weekends, 100% Vol Ratio shows stocks that traded more than the previous day.")

# Processing
all_data = []
with st.spinner("Calculating stocks..."):
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(scan_logic, s, vol_threshold/100) for s in FO_STOCKS]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r: all_data.append(r)

df_master = pd.DataFrame(all_data) if all_data else pd.DataFrame()

# Tabs
tab1, tab2 = st.tabs(["🔥 Momentum Alerts", "📋 Full F&O Watchlist"])

with tab1:
    if not df_master.empty:
        alerts = df_master[df_master['Signal'] != "Neutral"]
        if not alerts.empty:
            st.dataframe(alerts.sort_values(by="Vol Ratio", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No strong momentum breakouts found in the current session data.")
    else: st.warning("Data currently unavailable.")

with tab2:
    if not df_master.empty:
        search = st.text_input("Search Stock", placeholder="Type name...")
        disp = df_master.copy()
        if search: disp = disp[disp['Symbol'].str.contains(search.upper())]
        st.dataframe(disp[['Symbol', 'LTP', 'Chg %', 'Vol Ratio']].sort_values(by="Chg %", ascending=False), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Auto-refreshes every 3 minutes. Weekends show 'Closing Data'.")