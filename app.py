import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Pro-Trade F&O Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Professional Custom CSS for Dark Mode & Better UI
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 22px; color: #00ffcc; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px; white-space: pre-wrap; background-color: #1e2129;
        border-radius: 5px; color: white; padding: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #00ffcc !important; color: black !important; }
    </style>
    """, unsafe_base_html=True)

# 180 Second Auto-Refresh (3 Minutes)
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
            hist = ticker.history(period="2d")
            price = hist['Close'].iloc[-1]
            change = price - hist['Close'].iloc[-2]
            p_change = (change / hist['Close'].iloc[-2]) * 100
            data[name] = {"price": round(price, 2), "change": round(p_change, 2)}
        except: data[name] = {"price": 0, "change": 0}
    return data

def scan_logic(symbol, vol_trigger):
    try:
        df = yf.download(symbol, period="2d", interval="15m", progress=False)
        if len(df) < 5: return None
        
        # Split Data
        dates = df.index.date
        unique_dates = sorted(list(set(dates)))
        yest = df[dates == unique_dates[-2]]
        today = df[dates == unique_dates[-1]]

        # Stats
        pdh, pdl = yest['High'].max(), yest['Low'].min()
        yest_vol = yest['Volume'].sum()
        curr_price = today['Close'].iloc[-1]
        today_vol = today['Volume'].sum()
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

        # Momentum Filter
        if curr_price > pdh and vol_ratio > vol_trigger and curr_price > vwap:
            res["Signal"] = "🚀 BUY"
        elif curr_price < pdl and vol_ratio > vol_trigger and curr_price < vwap:
            res["Signal"] = "📉 SELL"
        
        return res
    except: return None

# --- APP LAYOUT ---
st.title("🛡️ Pro-Trader F&O Intelligence")
st.caption(f"Real-time Pulse • Last Update: {datetime.now().strftime('%H:%M:%S')}")

# Top Bar: Index Tickers
idx_data = get_index_data()
cols = st.columns(len(idx_data))
for i, (name, val) in enumerate(idx_data.items()):
    color = "normal" if val['change'] >= 0 else "inverse"
    cols[i].metric(name, f"₹{val['price']}", f"{val['change']}%", delta_color=color)

st.divider()

# Sidebar Settings
st.sidebar.header("Scanner Settings")
vol_threshold = st.sidebar.slider("Volume Sensitivity %", 5, 50, 25)
st.sidebar.write("---")
st.sidebar.write("🟢 **Buy Criteria:** Price > PDH + High Volume + Above VWAP")
st.sidebar.write("🔴 **Sell Criteria:** Price < PDL + High Volume + Below VWAP")

# Main Dashboard Tabs
tab1, tab2 = st.tabs(["🔥 Momentum Picks", "📋 All F&O Stocks"])

with st.spinner("Analyzing Market Flow..."):
    # Run scanning in parallel threads for speed
    all_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(scan_logic, s, vol_threshold/100) for s in FO_STOCKS]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r: all_data.append(r)

    df_master = pd.DataFrame(all_data)

with tab1:
    st.subheader(f"Institutional Momentum (> {vol_threshold}% Volume Surge)")
    momentum_df = df_master[df_master['Signal'] != "Neutral"]
    if not momentum_df.empty:
        # Styled Table for Alerts
        st.dataframe(momentum_df.sort_values(by="Vol Ratio", ascending=False), 
                     use_container_width=True, hide_index=True)
    else:
        st.info(f"Scanning {len(FO_STOCKS)} stocks... No breakouts confirmed yet. Best trades usually appear after 9:45 AM.")

with tab2:
    st.subheader("Live F&O Price List")
    search = st.text_input("Search Stock (e.g. RELIANCE, HDFC)")
    display_df = df_master.copy()
    if search:
        display_df = display_df[display_df['Symbol'].str.contains(search.upper())]
    
    st.dataframe(display_df[['Symbol', 'LTP', 'Chg %', 'Vol Ratio']].sort_values(by="Chg %", ascending=False), 
                 use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Data source: Yahoo Finance. Accuracy depends on feed delay (1-2 mins). Build for educational trading analysis.")