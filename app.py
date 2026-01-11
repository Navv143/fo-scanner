import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. UI CONFIGURATION ---
st.set_page_config(page_title="PRO-QUANT ELITE", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .main { background-color: #0b0e14; color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px !important; }
    
    /* Top Pick Highlight Boxes */
    .pick-card {
        padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid;
    }
    .bull-card { background: rgba(16, 185, 129, 0.1); border-color: #10b981; }
    .bear-card { background: rgba(244, 63, 94, 0.1); border-color: #f43f5e; }
    
    .scanner-box { background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=3 * 60 * 1000, key="m_sync")

# --- 2. ASSET LISTS ---
FO_STOCKS = [
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=120)
def fetch_data():
    all_tkr = FO_STOCKS + list(INDICES.values())
    raw = yf.download(all_tkr, period="5d", interval="1d", group_by='ticker', progress=False)
    s_rows, i_rows = [], []
    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if df.empty or len(df) < 2: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg = ((p - prev_p) / prev_p) * 100
            if t in FO_STOCKS:
                vr = curr['Volume'] / prev['Volume'] if prev['Volume'] > 0 else 0
                sig = "🚀 BULLISH" if p > prev['High'] else "📉 BEARISH" if p < prev['Low'] else "Neutral"
                s_rows.append({"Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Change%": round(chg, 2), "Vol_Ratio": round(vr, 2), "Signal": sig})
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "Change%": round(chg, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

# --- 4. NAVIGATION & HEADER ---
df_s, df_i = fetch_data()

with st.sidebar:
    st.markdown("### 🏛️ **QUANT TERMINAL**")
    menu = option_menu(None, ["Dashboard", "Sector Pulse", "Watchlist"], icons=["lightning-fill", "pie-chart-fill", "list"], default_index=0, styles={"nav-link-selected": {"background-color": "#238636"}})
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    st.info(f"Market Status: {'🟢 LIVE' if now.weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")

# Global Index Metrics
if not df_i.empty:
    cols = st.columns(len(df_i))
    for i, row in df_i.iterrows():
        cols[i].metric(row['Name'], f"₹{row['Price']:,.2f}", f"{row['Change%']}%", delta_color="inverse" if "VIX" in row['Name'] else "normal")

st.divider()

# --- 5. PAGE CONTENT ---
if menu == "Dashboard":
    st.markdown('<div class="scanner-box"><h3>🚀 Momentum Radar</h3><p>Picking Top Breakouts by Volume Surge Intensity.</p></div>', unsafe_allow_html=True)
    
    # NEW TOP 3 SECTION
    if not df_s.empty:
        col_bull, col_bear = st.columns(2)
        
        with col_bull:
            st.subheader("🔥 Top 3 Bullish Picks")
            top_bulls = df_s[df_s['Signal'] == "🚀 BULLISH"].nlargest(3, 'Vol_Ratio')
            if not top_bulls.empty:
                for _, row in top_bulls.iterrows():
                    st.markdown(f"""<div class="pick-card bull-card"><b>{row['Symbol']}</b> | LTP: ₹{row['LTP']} | Chg: {row['Change%']}% | Vol: {row['Vol_Ratio']}x</div>""", unsafe_allow_html=True)
            else: st.info("No Bullish breakouts yet.")

        with col_bear:
            st.subheader("❄️ Top 3 Bearish Picks")
            top_bears = df_s[df_s['Signal'] == "📉 BEARISH"].nlargest(3, 'Vol_Ratio')
            if not top_bears.empty:
                for _, row in top_bears.iterrows():
                    st.markdown(f"""<div class="pick-card bear-card"><b>{row['Symbol']}</b> | LTP: ₹{row['LTP']} | Chg: {row['Change%']}% | Vol: {row['Vol_Ratio']}x</div>""", unsafe_allow_html=True)
            else: st.info("No Bearish breakdowns yet.")
            
        st.write("---")
        st.write("📊 **Full Radar Table**")
        vol_min = st.slider("Filter by Vol Ratio", 0.2, 3.0, 0.8)
        radar_df = df_s[(df_s['Signal'] != "Neutral") & (df_s['Vol_Ratio'] >= vol_min)].sort_values("Vol_Ratio", ascending=False)
        st.dataframe(radar_df, use_container_width=True, hide_index=True)

# (Sector Pulse and Watchlist logic remain same as previous version)
elif menu == "Watchlist":
    st.subheader("📋 Master F&O List")
    search = st.text_input("🔍 Search Stock Symbol...")
    disp = df_s[df_s['Symbol'].str.contains(search.upper())] if search else df_s
    st.dataframe(disp.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True)