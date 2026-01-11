import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. PREMIUM TERMINAL UI ---
st.set_page_config(page_title="PRO-QUANT TERMINAL", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .main { background-color: #0b0e14; color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    
    /* Big Metric Cards */
    div[data-testid="stMetric"] {
        background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px !important;
    }
    div[data-testid="stMetricLabel"] > div { color: #8b949e !important; font-size: 14px !important; }
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 24px !important; font-family: 'JetBrains Mono', monospace !important; }
    
    /* Scanner Alert Box */
    .scanner-box {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 20px;
    }
    
    /* Table Styling */
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    h1, h2, h3 { color: #58a6ff !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=3 * 60 * 1000, key="m_sync")

# --- 2. VERIFIED TICKERS ---
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}
SECTORS = {"IT": "^CNXIT", "AUTO": "^CNXAUTO", "PHARMA": "^CNXPHARMA", "METAL": "^CNXMETAL", "REALTY": "^CNXREALTY", "FMCG": "^CNXFMCG", "FINANCE": "^CNXFIN"}

FO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "AXISBANK.NS", 
    "ADANIENT.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "BAJFINANCE.NS", "LT.NS", "MARUTI.NS", "JKCEMENT.NS", "ADANIPORTS.NS",
    "ACC.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "AUROPHARMA.NS", "BEL.NS", "BPCL.NS", "CIPLA.NS", "COALINDIA.NS", 
    "DLF.NS", "DRREDDY.NS", "GAIL.NS", "HCLTECH.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ITC.NS", "JINDALSTEL.NS", 
    "JSWSTEEL.NS", "KOTAKBANK.NS", "M&M.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "SUNPHARMA.NS", "TITAN.NS", 
    "ULTRACEMCO.NS", "WIPRO.NS", "COFORGE.NS", "DIXON.NS", "HAL.NS", "TRENT.NS", "POLYCAB.NS"
]

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=180)
def fetch_terminal_data():
    all_tickers = FO_STOCKS + list(INDICES.values()) + list(SECTORS.values())
    raw = yf.download(all_tickers, period="5d", interval="1d", group_by='ticker', progress=False)
    
    s_rows, i_rows, sec_rows = [], [], []

    for t in all_tickers:
        try:
            df = raw[t].dropna()
            if df.empty or len(df) < 2: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_pct = ((p - prev_p) / prev_p) * 100
            
            if t in FO_STOCKS:
                vol_r = curr['Volume'] / prev['Volume'] if prev['Volume'] > 0 else 0
                # MOMENTUM SCANNER LOGIC:
                # 1. Price > Prev Day High (BUY) OR Price < Prev Day Low (SELL)
                # 2. Volume Surge (Relative to yesterday)
                pdh, pdl = prev['High'], prev['Low']
                signal = "🚀 BULLISH BREAKOUT" if p > pdh else "📉 BEARISH BREAKDOWN" if p < pdl else "Neutral"
                
                s_rows.append({
                    "Symbol": t.replace(".NS",""), "Price": round(p, 2), 
                    "Change%": round(chg_pct, 2), "Vol_Ratio": round(vol_r, 2),
                    "Signal": signal, "PDH": round(pdh, 2), "PDL": round(pdl, 2)
                })
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "Change%": round(chg_pct, 2)})
            elif t in SECTORS.values():
                name = [k for k, v in SECTORS.items() if v == t][0]
                sec_rows.append({"Sector": name, "Change%": round(chg_pct, 2)})
        except: continue
        
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows), pd.DataFrame(sec_rows)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏛️ **QUANT TERMINAL**")
    menu = option_menu(None, ["Momentum Scanner", "Sector Analytics", "Full Watchlist"], 
                       icons=["lightning-fill", "pie-chart-fill", "list-task"], 
                       menu_icon="cast", default_index=0,
                       styles={"nav-link-selected": {"background-color": "#238636"}})
    
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    st.info(f"Market Status: {'🟢 LIVE' if now.weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")
    st.caption(f"Refresh: {now.strftime('%H:%M:%S')} IST")

# --- 5. PAGE CONTENT ---
df_s, df_i, df_sec = fetch_terminal_data()

# Global Header: Quick Indices
if not df_i.empty:
    idx_cols = st.columns(len(df_i))
    for i, row in df_i.iterrows():
        # VIX inverse logic
        d_mode = "inverse" if "VIX" in row['Name'] else "normal"
        idx_cols[i].metric(row['Name'], f"₹{row['Price']:,.2f}", f"{row['Change%']}%", delta_color=d_mode)
st.markdown("---")

if menu == "Momentum Scanner":
    st.markdown('<div class="scanner-box"><h3>🚀 Live Momentum Radar</h3><p>Scanning for Stocks breaking Previous Day High/Low with Volume Surge.</p></div>', unsafe_allow_html=True)
    
    # User Control for Volume Surge
    vol_min = st.slider("Minimum Volume Ratio (Today vs Yesterday)", 0.3, 3.0, 1.0, help="1.0 means stock has already done yesterday's full volume.")
    
    if not df_s.empty:
        # Filter only stocks with Signal and Vol Ratio > User Input
        radar_df = df_s[(df_s['Signal'] != "Neutral") & (df_s['Vol_Ratio'] >= vol_min)].sort_values("Vol_Ratio", ascending=False)
        
        if not radar_df.empty:
            st.dataframe(radar_df[["Symbol", "Price", "Change%", "Vol_Ratio", "Signal", "PDH", "PDL"]], 
                         use_container_width=True, hide_index=True,
                         column_config={
                             "Change%": st.column_config.NumberColumn(format="%+.2f%%"),
                             "Vol_Ratio": st.column_config.ProgressColumn(min_value=0, max_value=3, format="%.2fx")
                         })
        else:
            st.warning(f"No stocks currently breaking PDH/PDL with > {vol_min}x volume. Try lowering the Volume Ratio slider.")
            st.info("💡 Pro Tip: During the first 15 mins of market (9:15-9:30), set the Vol Ratio to 0.3 to find early movers.")
    else:
        st.error("Data Engine offline. Please refresh.")

elif menu == "Sector Analytics":
    st.subheader("🏗️ Sector Performance Heatmap")
    if not df_sec.empty:
        df_sec = df_sec.sort_values("Change%", ascending=False)
        st.bar_chart(df_sec.set_index("Sector")["Change%"], color="#238636")
        st.dataframe(df_sec, use_container_width=True, hide_index=True)

elif menu == "Full Watchlist":
    st.subheader("📋 Master Watchlist (All F&O)")
    search = st.text_input("🔍 Quick Search Stock...")
    disp = df_s[df_s['Symbol'].str.contains(search.upper())] if search else df_s
    st.dataframe(disp.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True)