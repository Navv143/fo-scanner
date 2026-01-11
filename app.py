import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- THEME & UI CONFIG ---
st.set_page_config(page_title="PRO-QUANT F&O", layout="wide", initial_sidebar_state="collapsed")

# Inject Premium CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    .stMetric { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); }
    div[data-testid="stExpander"] { background: rgba(255, 255, 255, 0.03); border: none; border-radius: 12px; }
    .status-pill { padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; display: inline-block; margin-bottom: 20px; }
    /* Modern Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=3 * 60 * 1000, key="pro_refresh")

# --- CORE LOGIC ---
def get_market_info():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    is_open = now.weekday() < 5 and (time(9,15) <= now.time() <= time(15,30))
    return is_open, now

def get_indices():
    indices = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}
    data = []
    for name, ticker in indices.items():
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="5d")
            price = h['Close'].iloc[-1]
            change = ((price - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
            data.append({"name": name, "price": f"₹{price:,.2f}", "change": f"{change:+.2f}%", "raw_chg": change})
        except: pass
    return data

def fetch_stock_data(symbol, vol_trigger):
    try:
        # Fetch enough data to cover holidays/weekends
        df = yf.download(symbol, period="10d", interval="1d", progress=False)
        if df.empty or len(df) < 2: return None
        
        # Latest Row vs Previous Row
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        ltp = curr['Close']
        chg = ((ltp - prev['Close']) / prev['Close']) * 100
        vol_ratio = curr['Volume'] / prev['Volume']
        pdh, pdl = prev['High'], prev['Low']

        signal = "Neutral"
        if ltp > pdh and vol_ratio > vol_trigger: signal = "🚀 BUY"
        elif ltp < pdl and vol_ratio > vol_trigger: signal = "📉 SELL"

        return {
            "Symbol": symbol.replace(".NS",""),
            "LTP": round(ltp, 2),
            "Day Chg%": round(chg, 2),
            "Volume Ratio": round(vol_ratio, 2),
            "Signal": signal
        }
    except: return None

# --- UI HEADER ---
from datetime import time
is_market_open, curr_time = get_market_info()

col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.title("🛡️ PRO-QUANT F&O")
    status_text = "🟢 LIVE TRADING" if is_market_open else "🔴 MARKET CLOSED (SESSION SUMMARY)"
    status_clr = "#10b981" if is_market_open else "#f43f5e"
    st.markdown(f'<div class="status-pill" style="background: {status_clr}22; color: {status_clr}; border: 1px solid {status_clr}44;">{status_text}</div>', unsafe_allow_html=True)
with col_h2:
    st.markdown(f"<div style='text-align:right; color:#94a3b8; padding-top:20px;'>Last Updated: {curr_time.strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

# Indices Grid
idx_list = get_indices()
idx_cols = st.columns(len(idx_list))
for i, idx in enumerate(idx_list):
    color = "normal" if idx['raw_chg'] >= 0 else "inverse"
    idx_cols[i].metric(idx['name'], idx['price'], idx['change'], delta_color=color)

st.write("")

# --- NAVIGATION ---
selected = option_menu(
    menu_title=None,
    options=["Momentum Radar", "Master Watchlist", "Market Analytics"],
    icons=["lightning-charge", "list-columns", "graph-up"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "transparent"},
        "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "color": "#94a3b8"},
        "nav-link-selected": {"background-color": "#3b82f6", "color": "white"},
    }
)

# --- SCANNING ---
FO_STOCKS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "AXISBANK.NS", "ADANIENT.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "BAJFINANCE.NS", "LT.NS", "MARUTI.NS", "JKCEMENT.NS", "ADANIPORTS.NS", "ACC.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "AUROPHARMA.NS", "BAJAJ-AUTO.NS", "BANKBARODA.NS", "BEL.NS", "BPCL.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "GAIL.NS", "HCLTECH.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ITC.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "M&M.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS"] # Add all 212 here

st.sidebar.header("Configuration")
vol_threshold = st.sidebar.slider("Momentum Sensitivity (Volume %)", 10, 100, 30) / 100

with st.spinner("🔄 Deep-Scanning F&O Universe..."):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_stock_data, s, vol_threshold) for s in FO_STOCKS]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: results.append(res)
    
    df = pd.DataFrame(results)

# --- TAB CONTENT ---
if selected == "Momentum Radar":
    st.subheader("🚀 High-Conviction Breakouts")
    if not df.empty:
        alerts = df[df['Signal'] != "Neutral"].sort_values(by="Volume Ratio", ascending=False)
        if not alerts.empty:
            st.dataframe(
                alerts, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Day Chg%": st.column_config.NumberColumn(format="%.2f%%"),
                    "Volume Ratio": st.column_config.ProgressColumn(min_value=0, max_value=3, format="%.2fx"),
                    "Signal": st.column_config.TextColumn(help="Breakout direction confirmed by PDH/PDL")
                }
            )
        else:
            st.info("No breakouts meeting your volume threshold right now.")
    else: st.error("System connection error. Please refresh.")

elif selected == "Master Watchlist":
    st.subheader("📋 All F&O Stocks Pulse")
    if not df.empty:
        col_s1, col_s2 = st.columns([1, 2])
        search = col_s1.text_input("🔍 Search Asset...", placeholder="e.g. RELIANCE")
        
        filtered_df = df.copy()
        if search: filtered_df = df[df['Symbol'].str.contains(search.upper())]
        
        st.dataframe(
            filtered_df.sort_values(by="Day Chg%", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Day Chg%": st.column_config.NumberColumn(format="%.2f%%"),
                "Volume Ratio": st.column_config.NumberColumn(format="%.2fx")
            }
        )

elif selected == "Market Analytics":
    st.subheader("📊 Session Statistics")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Advancers", len(df[df['Day Chg%'] > 0]), delta="Green")
        c2.metric("Decliners", len(df[df['Day Chg%'] < 0]), delta="-Red", delta_color="inverse")
        c3.metric("Avg Vol Surge", f"{df['Volume Ratio'].mean():.2f}x")
        
        st.write("---")
        st.write("📈 **Top 5 Gainer Momentum**")
        st.table(df.nlargest(5, 'Day Chg%')[['Symbol', 'LTP', 'Day Chg%']])

st.markdown("---")
st.caption("⚡ Premium Data Feed by Yahoo Finance. Strategy: Volume Expansion + Price Range Breakout.")