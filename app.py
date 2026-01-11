import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- CONFIG ---
st.set_page_config(page_title="PRO-QUANT F&O", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; background-color: #0f172a; }
    .stMetric { background: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 12px; border: 1px solid rgba(255, 255, 255, 0.1); }
    .status-pill { padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; display: inline-block; margin-bottom: 15px; }
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    /* Target delta colors specifically */
    [data-testid="stMetricDelta"] > div { font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=5 * 60 * 1000, key="global_refresh")

# --- TICKER LISTS ---
INDICES = {
    "NIFTY 50": "^NSEI", 
    "BANK NIFTY": "^NSEBANK", 
    "INDIA VIX": "^INDIAVIX"
}

SECTORS = {
    "IT": "NIFTY_IT.NS",
    "AUTO": "NIFTY_AUTO.NS",
    "PHARMA": "NIFTY_PHARMA.NS",
    "METAL": "NIFTY_METAL.NS",
    "REALTY": "NIFTY_REALTY.NS",
    "FMCG": "NIFTY_FMCG.NS",
    "ENERGY": "NIFTY_ENERGY.NS",
    "INFRA": "NIFTY_INFRA.NS"
}

# Full F&O Tickers
FO_STOCKS = [
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

# --- DATA ENGINE ---
@st.cache_data(ttl=300)
def get_dashboard_data():
    all_tickers = FO_STOCKS + list(INDICES.values()) + list(SECTORS.values())
    raw = yf.download(all_tickers, period="5d", interval="1d", group_by='ticker', progress=False)
    
    stock_res, index_res, sector_res = [], [], []

    # Process Stocks
    for s in FO_STOCKS:
        try:
            d = raw[s]
            p, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
            chg = ((p - prev) / prev) * 100
            vol_r = d['Volume'].iloc[-1] / d['Volume'].iloc[-2]
            signal = "🚀 BUY" if p > d['High'].iloc[-2] else "📉 SELL" if p < d['Low'].iloc[-2] else "Neutral"
            stock_res.append({"Symbol": s.replace(".NS",""), "LTP": round(p, 2), "Change%": round(chg, 2), "Vol Ratio": round(vol_r, 2), "Signal": signal})
        except: pass

    # Process Indices & Sectors
    for label, items in [("Index", INDICES), ("Sector", SECTORS)]:
        for name, sym in items.items():
            try:
                d = raw[sym]
                p, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
                chg = round(((p - prev) / prev) * 100, 2)
                entry = {"name": name, "price": f"₹{p:,.2f}", "chg": f"{chg:+}%", "raw": chg}
                if label == "Index": index_res.append(entry)
                else: sector_res.append(entry)
            except: pass

    return pd.DataFrame(stock_res), index_res, sector_res

# --- APP UI ---
tz = pytz.timezone('Asia/Kolkata')
is_open = now.weekday() < 5 and (time(9,15) <= datetime.now(tz).time() <= time(15,30)) if 'now' in locals() else False

st.title("🛡️ PRO-QUANT F&O")
st.markdown(f'<div class="status-pill" style="background: {"#10b981" if is_open else "#f43f5e"}22; color: {"#10b981" if is_open else "#f43f5e"};">{"🟢 LIVE" if is_open else "🔴 CLOSED"}</div>', unsafe_allow_html=True)

df_master, idx_data, sct_data = get_dashboard_data()

# Index Bar
cols = st.columns(len(idx_data))
for i, x in enumerate(idx_data):
    # INDIA VIX Inverse Logic: If up, it's red.
    d_mode = "inverse" if "VIX" in x['name'] else "normal"
    cols[i].metric(x['name'], x['price'], x['chg'], delta_color=d_mode)

st.divider()

# Navigation
selected = option_menu(
    menu_title=None, options=["Momentum Radar", "Sector Pulse", "Watchlist"],
    icons=["lightning", "grid", "list"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#3b82f6"}}
)

if selected == "Momentum Radar":
    st.subheader("🚀 High Volume Breakouts")
    v_f = st.slider("Min Vol Ratio", 0.5, 3.0, 1.2)
    radar = df_master[(df_master['Signal'] != "Neutral") & (df_master['Vol Ratio'] >= v_f)]
    st.dataframe(radar.sort_values("Vol Ratio", ascending=False), use_container_width=True, hide_index=True)

elif selected == "Sector Pulse":
    st.subheader("🏗️ Sector Wise Performance")
    s_cols = st.columns(4)
    for i, s in enumerate(sct_data):
        with s_cols[i % 4]:
            st.metric(s['name'], s['price'], s['chg'], delta_color="normal")
    
    st.write("---")
    st.info("💡 Strategy: Identify the top performing sector above, then search for its stocks in the Watchlist.")

elif selected == "Watchlist":
    st.subheader("📋 Complete F&O List")
    search = st.text_input("Search Symbol...")
    disp = df_master.copy()
    if search: disp = disp[disp['Symbol'].str.contains(search.upper())]
    st.dataframe(disp.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True)

st.caption(f"Last Update: {datetime.now(tz).strftime('%H:%M:%S')} IST")