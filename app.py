import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. PROFESSIONAL UI CSS ---
st.set_page_config(page_title="PRO-QUANT ELITE", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Global Background & Font */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .main { background-color: #0b0e14; color: #e2e8f0; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    
    /* Professional Metric Cards */
    div[data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] > div { color: #8b949e !important; font-size: 14px !important; font-weight: 600 !important; }
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 28px !important; font-family: 'JetBrains Mono', monospace !important; }
    
    /* High Visibility Delta Colors */
    [data-testid="stMetricDelta"] > div { font-weight: 800 !important; font-size: 18px !important; }
    [data-testid="stMetricDelta"] svg { width: 20px; height: 20px; }

    /* Custom Status Pill */
    .status-pill {
        padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 12px;
        display: inline-block; margin-bottom: 20px; border: 1px solid;
    }
    
    /* Standard Table Styling */
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; background-color: #0d1117; }
    
    /* Titles */
    h1, h2, h3 { color: #58a6ff !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=5 * 60 * 1000, key="global_sync")

# --- 2. DATA TICKERS (VERIFIED) ---
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}

# Specific Sectoral Index Tickers for Yahoo Finance
SECTORS = {
    "IT": "^CNXIT", "AUTO": "^CNXAUTO", "PHARMA": "^CNXPHARMA", 
    "METAL": "^CNXMETAL", "REALTY": "^CNXREALTY", "FMCG": "^CNXFMCG", 
    "ENERGY": "^CNXENERGY", "FINANCE": "^CNXFIN"
}

FO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "AXISBANK.NS", 
    "ADANIENT.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "BAJFINANCE.NS", "LT.NS", "MARUTI.NS", "JKCEMENT.NS", "ADANIPORTS.NS",
    "ACC.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "AUROPHARMA.NS", "BEL.NS", "BPCL.NS", "CIPLA.NS", "COALINDIA.NS", 
    "DLF.NS", "DRREDDY.NS", "GAIL.NS", "HCLTECH.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ITC.NS", "JINDALSTEL.NS", 
    "JSWSTEEL.NS", "KOTAKBANK.NS", "M&M.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "SUNPHARMA.NS", "TITAN.NS", 
    "ULTRACEMCO.NS", "WIPRO.NS"
]

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=300)
def fetch_data():
    all_tickers = FO_STOCKS + list(INDICES.values()) + list(SECTORS.values())
    raw = yf.download(all_tickers, period="7d", interval="1d", group_by='ticker', progress=False)
    
    s_rows, i_rows, sec_rows = [], [], []

    for t in all_tickers:
        try:
            df = raw[t].dropna()
            if df.empty or len(df) < 2: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_pct = ((p - prev_p) / prev_p) * 100
            
            if t in FO_STOCKS:
                s_rows.append({
                    "Symbol": t.replace(".NS",""), "Price": round(p, 2), 
                    "Change%": round(chg_pct, 2), "Volume": int(curr['Volume']),
                    "Signal": "🚀 BUY" if p > prev['High'] else "📉 SELL" if p < prev['Low'] else "Neutral"
                })
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
    menu = option_menu(None, ["Dashboard", "F&O Watchlist", "Sector Pulse"], 
                       icons=["grid", "list-check", "bar-chart-fill"], 
                       menu_icon="cast", default_index=0,
                       styles={"nav-link-selected": {"background-color": "#238636"}})
    
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    is_live = now.weekday() < 5 and (time(9,15) <= now.time() <= time(15,30))
    st.markdown(f'<div class="status-pill" style="background: {"#002b1b" if is_live else "#2b0000"}; color: {"#00ffcc" if is_live else "#ff4b4b"}; border-color: {"#00ffcc" if is_live else "#ff4b4b"};">{"🟢 MARKET LIVE" if is_live else "🔴 MARKET CLOSED"}</div>', unsafe_allow_html=True)
    st.caption(f"Last Sync: {now.strftime('%H:%M:%S')} IST")

# --- 5. PAGE CONTENT ---
df_s, df_i, df_sec = fetch_data()

if menu == "Dashboard":
    st.subheader("Market Snapshot")
    if not df_i.empty:
        c1, c2, c3 = st.columns(3)
        nifty = df_i[df_i['Name'] == "NIFTY 50"].iloc[0]
        c1.metric("NIFTY 50", f"₹{nifty['Price']:,.2f}", f"{nifty['Change%']}%")
        
        banknifty = df_i[df_i['Name'] == "BANK NIFTY"].iloc[0]
        c2.metric("BANK NIFTY", f"₹{banknifty['Price']:,.2f}", f"{banknifty['Change%']}%")
        
        vix = df_i[df_i['Name'] == "INDIA VIX"].iloc[0]
        c3.metric("INDIA VIX", f"{vix['Price']}", f"{vix['Change%']}%", delta_color="inverse")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.write("🔥 **Top Gainers**")
        st.dataframe(df_s.nlargest(5, 'Change%')[['Symbol', 'Price', 'Change%']], use_container_width=True, hide_index=True)
    with col2:
        st.write("📉 **Top Losers**")
        st.dataframe(df_s.nsmallest(5, 'Change%')[['Symbol', 'Price', 'Change%']], use_container_width=True, hide_index=True)

elif menu == "F&O Watchlist":
    st.subheader("Live F&O Momentum")
    search = st.text_input("🔍 Search stock symbol...")
    filtered = df_s[df_s['Symbol'].str.contains(search.upper())] if search else df_s
    st.dataframe(filtered.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True,
                 column_config={"Change%": st.column_config.NumberColumn(format="%+.2f%%")})

elif menu == "Sector Pulse":
    st.subheader("Sector Performance Heatmap")
    if not df_sec.empty:
        df_sec = df_sec.sort_values("Change%", ascending=False)
        # Higher Contrast Bar Chart
        st.bar_chart(df_sec.set_index("Sector")["Change%"], color="#238636")
        st.dataframe(df_sec, use_container_width=True, hide_index=True,
                     column_config={"Change%": st.column_config.NumberColumn(format="%+.2f%%")})
    else:
        st.warning("Awaiting Sectoral Data...")