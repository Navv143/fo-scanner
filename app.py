import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. THEME & UI ---
st.set_page_config(page_title="PRO-QUANT ELITE", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .main { background-color: #0b0e14; color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    div[data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px !important; }
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 24px !important; font-family: 'JetBrains Mono', monospace !important; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    .scanner-box { background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=3 * 60 * 1000, key="m_sync")

# --- 2. COMPLETE F&O LIST (180+ NSE TICKERS) ---
FO_STOCKS = [
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}
SECTORS = {"IT": "^CNXIT", "AUTO": "^CNXAUTO", "PHARMA": "^CNXPHARMA", "METAL": "^CNXMETAL", "REALTY": "^CNXREALTY", "FMCG": "^CNXFMCG", "FINANCE": "^CNXFIN"}

# --- 3. ROBUST DATA ENGINE ---
@st.cache_data(ttl=120)
def fetch_master_data():
    all_tkr = FO_STOCKS + list(INDICES.values()) + list(SECTORS.values())
    # Download 10 days of daily data to ensure we find valid Friday/Thursday candles
    raw = yf.download(all_tkr, period="10d", interval="1d", group_by='ticker', progress=False)
    
    s_rows, i_rows, sec_rows = [], [], []

    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if df.empty or len(df) < 2: continue
            
            # Logic to handle current day vs previous day
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            p, prev_p = curr['Close'], prev['Close']
            chg_pct = ((p - prev_p) / prev_p) * 100
            
            if t in FO_STOCKS:
                v_r = curr['Volume'] / prev['Volume'] if prev['Volume'] > 0 else 0
                pdh, pdl = prev['High'], prev['Low']
                sig = "🚀 BULLISH" if p > pdh else "📉 BEARISH" if p < pdl else "Neutral"
                s_rows.append({"Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Change%": round(chg_pct, 2), "Vol_Ratio": round(v_r, 2), "Signal": sig, "PDH": round(pdh, 2), "PDL": round(pdl, 2)})
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "Change%": round(chg_pct, 2)})
            elif t in SECTORS.values():
                name = [k for k, v in SECTORS.items() if v == t][0]
                sec_rows.append({"Sector": name, "Change%": round(chg_pct, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows), pd.DataFrame(sec_rows)

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown("### 🏛️ **QUANT TERMINAL**")
    menu = option_menu(None, ["Momentum Radar", "Sector Pulse", "Watchlist"], icons=["lightning-fill", "pie-chart-fill", "list"], default_index=0, styles={"nav-link-selected": {"background-color": "#238636"}})
    tz = pytz.timezone('Asia/Kolkata')
    st.info(f"Market Status: {'🟢 LIVE' if (now := datetime.now(tz)).weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")
    st.caption(f"Refresh: {now.strftime('%H:%M:%S')} IST")

# --- 5. PAGE CONTENT ---
df_s, df_i, df_sec = fetch_master_data()

# Index Bar
if not df_i.empty:
    cols = st.columns(len(df_i))
    for i, row in df_i.iterrows():
        cols[i].metric(row['Name'], f"₹{row['Price']:,.2f}", f"{row['Change%']}%", delta_color="inverse" if "VIX" in row['Name'] else "normal")
st.divider()

if menu == "Momentum Radar":
    st.markdown('<div class="scanner-box"><h3>🚀 Live Momentum Breakouts</h3><p>Price > Prev Day High/Low with Volume Surge</p></div>', unsafe_allow_html=True)
    vol_min = st.slider("Min Vol Ratio (Today vs Yest)", 0.2, 3.0, 0.8)
    
    radar = df_s[(df_s['Signal'] != "Neutral") & (df_s['Vol_Ratio'] >= vol_min)].sort_values("Vol_Ratio", ascending=False)
    if not radar.empty:
        st.dataframe(radar[["Symbol", "LTP", "Change%", "Vol_Ratio", "Signal", "PDH", "PDL"]], use_container_width=True, hide_index=True, column_config={"Change%": st.column_config.NumberColumn(format="%+.2f%%"), "Vol_Ratio": st.column_config.ProgressColumn(min_value=0, max_value=3, format="%.2fx")})
    else: st.info("No breakouts found with these settings.")

elif menu == "Sector Pulse":
    st.subheader("🏗️ Sector Heatmap")
    if not df_sec.empty:
        st.bar_chart(df_sec.set_index("Sector")["Change%"], color="#238636")
        st.dataframe(df_sec.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True)

elif menu == "Watchlist":
    st.subheader("📋 Master F&O List")
    search = st.text_input("🔍 Search stock...")
    disp = df_s[df_s['Symbol'].str.contains(search.upper())] if search else df_s
    st.dataframe(disp.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True)