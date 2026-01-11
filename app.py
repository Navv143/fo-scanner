import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- THEME & UI ---
st.set_page_config(page_title="PRO-QUANT ELITE", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0d1117; }
    .stMetric { background: #161b22; border-radius: 8px; border: 1px solid #30363d; padding: 15px; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363d; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    /* Delta Colors Fix */
    [data-testid="stMetricDelta"] > div { font-weight: bold !important; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=5 * 60 * 1000, key="global_sync")

# --- TICKERS ---
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS"}
SECTORS = {"IT": "NIFTY_IT.NS", "AUTO": "NIFTY_AUTO.NS", "PHARMA": "NIFTY_PHARMA.NS", "METAL": "NIFTY_METAL.NS", "REALTY": "NIFTY_REALTY.NS", "FMCG": "NIFTY_FMCG.NS", "ENERGY": "NIFTY_ENERGY.NS"}
FO_STOCKS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "AXISBANK.NS", "ADANIENT.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "BAJFINANCE.NS", "LT.NS", "MARUTI.NS", "JKCEMENT.NS", "ADANIPORTS.NS", "ACC.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "AUROPHARMA.NS", "BEL.NS", "BPCL.NS", "CIPLA.NS", "COALINDIA.NS", "DLF.NS", "DRREDDY.NS", "GAIL.NS", "HCLTECH.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ITC.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "M&M.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS"]

# --- DATA ENGINE (RESILIENT) ---
@st.cache_data(ttl=300)
def fetch_elite_data():
    all_tickers = list(set(FO_STOCKS + list(INDICES.values()) + list(SECTORS.values())))
    # Fetch 10 days to handle long weekends/holidays
    raw = yf.download(all_tickers, period="10d", interval="1d", group_by='ticker', progress=False)
    
    stock_rows, idx_rows, sec_rows = [], [], []

    for ticker in all_tickers:
        try:
            df = raw[ticker].dropna()
            if len(df) < 2: continue
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_price = p - prev_p
            chg_pct = (chg_price / prev_p) * 100
            
            # Map back to category
            if ticker in FO_STOCKS:
                vol_r = curr['Volume'] / prev['Volume'] if prev['Volume'] > 0 else 0
                signal = "🚀 BUY" if p > prev['High'] else "📉 SELL" if p < prev['Low'] else "Neutral"
                stock_rows.append({"Symbol": ticker.replace(".NS",""), "LTP": round(p, 2), "Change": round(chg_price, 2), "Change%": round(chg_pct, 2), "Vol Ratio": round(vol_r, 2), "Signal": signal})
            
            elif ticker in INDICES.values():
                name = [k for k, v in INDICES.items() if v == ticker][0]
                idx_rows.append({"Name": name, "Price": round(p, 2), "Change": round(chg_price, 2), "Change%": round(chg_pct, 2)})
            
            elif ticker in SECTORS.values():
                name = [k for k, v in SECTORS.items() if v == ticker][0]
                sec_rows.append({"Sector": name, "Change%": round(chg_pct, 2), "Price": round(p, 2)})
        except: continue
        
    return pd.DataFrame(stock_rows), pd.DataFrame(idx_rows), pd.DataFrame(sec_rows)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏛️ **PRO-QUANT ELITE**")
    menu = option_menu(None, ["Dashboard", "Indices", "F&O Stocks", "Sector Pulse"], 
                       icons=["house", "activity", "currency-rupee", "bar-chart-steps"], 
                       menu_icon="cast", default_index=0,
                       styles={"nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "color": "#8b949e"},
                               "nav-link-selected": {"background-color": "#238636", "color": "white"}})
    
    tz = pytz.timezone('Asia/Kolkata')
    st.info(f"Market Status: {'🟢 LIVE' if (now := datetime.now(tz)).weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")
    st.caption(f"Sync: {now.strftime('%H:%M:%S')}")

# --- PAGE CONTENT ---
df_s, df_i, df_sec = fetch_elite_data()

if menu == "Dashboard":
    st.subheader("Market Snapshot")
    c1, c2, c3 = st.columns(3)
    if not df_i.empty:
        nifty = df_i[df_i['Name'] == "NIFTY 50"].iloc[0]
        c1.metric("NIFTY 50", f"₹{nifty['Price']}", f"{nifty['Change%']}%")
        vix = df_i[df_i['Name'] == "INDIA VIX"].iloc[0]
        c2.metric("INDIA VIX", f"{vix['Price']}", f"{vix['Change%']}%", delta_color="inverse")
    c3.metric("Breath (Adv/Dec)", f"{len(df_s[df_s['Change%']>0])} / {len(df_s[df_s['Change%']<0])}")

    st.markdown("---")
    l_col, r_col = st.columns(2)
    with l_col:
        st.write("🔥 **Top Gainers**")
        st.dataframe(df_s.nlargest(5, 'Change%')[['Symbol', 'LTP', 'Change%']], use_container_width=True, hide_index=True)
    with r_col:
        st.write("❄️ **Top Losers**")
        st.dataframe(df_s.nsmallest(5, 'Change%')[['Symbol', 'LTP', 'Change%']], use_container_width=True, hide_index=True)

elif menu == "Indices":
    st.subheader("Indices Performance")
    st.dataframe(df_i.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True)

elif menu == "F&O Stocks":
    st.subheader("F&O Watchlist")
    search = st.text_input("Search...", placeholder="e.g. RELIANCE")
    final_df = df_s[df_s['Symbol'].str.contains(search.upper())] if search else df_s
    st.dataframe(final_df.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True,
                 column_config={"Change%": st.column_config.NumberColumn(format="%+.2f%%"), "Vol Ratio": st.column_config.ProgressColumn(min_value=0, max_value=3)})

elif menu == "Sector Pulse":
    st.subheader("Sector Strength Heatmap")
    if not df_sec.empty:
        df_sec = df_sec.sort_values("Change%", ascending=False)
        st.bar_chart(df_sec.set_index("Sector")["Change%"], color="#238636")
        st.dataframe(df_sec, use_container_width=True, hide_index=True)