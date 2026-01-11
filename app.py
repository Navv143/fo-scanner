import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. LOAD UI & CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="PRO-QUANT ELITE", layout="wide")
try:
    local_css("style.css")
except:
    pass # Falls back if file not found

st_autorefresh(interval=2 * 60 * 1000, key="global_sync")

# --- 2. EXTENDED SECTOR MAPPING ---
SECTOR_MAP = {
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS", "COFORGE.NS", "MPHASIS.NS"],
    "BANKS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "AUBANK.NS", "FEDERALBNK.NS"],
    "AUTO": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS"],
    "METAL": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS", "NATIONALUM.NS"],
    "PHARMA": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "ALKEM.NS"],
    "CEMENT/INFRA": ["ULTRACEMCO.NS", "GRASIM.NS", "JKCEMENT.NS", "ACC.NS", "AMBUJACEM.NS", "LT.NS", "ADANIPORTS.NS"],
    "OIL/ENERGY": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS"],
    "FMCG": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TATACONSUM.NS", "COLPAL.NS"]
}

# Flatten list for yfinance
FO_STOCKS = [item for sublist in SECTOR_MAP.values() for item in sublist]
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=120)
def fetch_elite_data():
    all_tkr = list(set(FO_STOCKS + list(INDICES.values())))
    raw = yf.download(all_tkr, period="5d", interval="1d", group_by='ticker', progress=False)
    
    s_rows, i_rows = [], []
    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if len(df) < 2: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_val = p - prev_p
            chg_pct = (chg_val / prev_p) * 100
            
            if t in FO_STOCKS:
                vr = curr['Volume'] / prev['Volume'] if prev['Volume'] > 0 else 0
                sig = "🚀 BULLISH" if p > prev['High'] else "📉 BEARISH" if p < prev['Low'] else "Neutral"
                # Find Sector
                sec = "Other"
                for k, v in SECTOR_MAP.items():
                    if t in v: sec = k; break
                
                s_rows.append({
                    "Sector": sec, "Symbol": t.replace(".NS",""), "LTP": round(p, 2),
                    "Change (₹)": round(chg_val, 2), "Change (%)": round(chg_pct, 2),
                    "Vol Ratio": round(vr, 2), "Signal": sig
                })
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "Chg_Val": round(chg_val, 2), "Chg_Pct": round(chg_pct, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

# --- 4. APP UI ---
df_s, df_i = fetch_elite_data()

with st.sidebar:
    st.markdown("<h2 style='color:#58a6ff'>TERMINAL v4.0</h2>", unsafe_allow_html=True)
    menu = option_menu(None, ["Dashboard", "Sector Analysis", "F&O Pulse"], 
                       icons=["grid", "pie-chart", "activity"], default_index=0,
                       styles={"nav-link-selected": {"background-color": "#238636"}})
    tz = pytz.timezone('Asia/Kolkata')
    st.info(f"Market: {'🟢 LIVE' if (now := datetime.now(tz)).weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")

# --- DASHBOARD ---
if menu == "Dashboard":
    # Index Row with Blinking LTP
    cols = st.columns(len(df_i))
    for i, row in df_i.iterrows():
        with cols[i]:
            st.markdown(f"**{row['Name']}**")
            st.markdown(f"<div class='price-blink'>₹{row['Price']:,}</div>", unsafe_allow_html=True)
            color = "#10b981" if row['Chg_Pct'] >= 0 else "#f43f5e"
            st.markdown(f"<span style='color:{color}'>{row['Chg_Val']:+.2f} ({row['Chg_Pct']:+.2f}%)</span>", unsafe_allow_html=True)

    st.write("---")
    
    # Top 3 High Conviction Picks
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Top 3 Bullish (Volume Surge)")
        bulls = df_s[df_s['Signal'] == "🚀 BULLISH"].nlargest(3, 'Vol Ratio')
        for _, r in bulls.iterrows():
            st.markdown(f"<div style='border: 1px solid #10b981; padding:10px; border-radius:8px; margin-bottom:5px'><b>{r['Symbol']}</b> | LTP: ₹{r['LTP']} | <span style='color:#10b981'>+{r['Change (₹)']} (+{r['Change (%)']}%)</span> | Vol: {r['Vol Ratio']}x</div>", unsafe_allow_html=True)
    
    with c2:
        st.subheader("📉 Top 3 Bearish (Volume Surge)")
        bears = df_s[df_s['Signal'] == "📉 BEARISH"].nlargest(3, 'Vol Ratio')
        for _, r in bears.iterrows():
            st.markdown(f"<div style='border: 1px solid #f43f5e; padding:10px; border-radius:8px; margin-bottom:5px'><b>{r['Symbol']}</b> | LTP: ₹{r['LTP']} | <span style='color:#f43f5e'>{r['Change (₹)']} ({r['Change (%)']}%)</span> | Vol: {r['Vol Ratio']}x</div>", unsafe_allow_html=True)

# --- SECTOR ANALYSIS ---
elif menu == "Sector Analysis":
    st.subheader("🏗️ Sector Wise Breakdown")
    sec_group = df_s.groupby("Sector")["Change (%)"].mean().sort_values(ascending=False)
    st.bar_chart(sec_group, color="#238636")
    
    selected_sec = st.selectbox("Select Sector to view stocks:", list(SECTOR_MAP.keys()))
    sec_df = df_s[df_s['Sector'] == selected_sec].sort_values("Change (%)", ascending=False)
    
    # Custom colored table logic
    st.dataframe(sec_df.style.applymap(lambda x: 'background-color: rgba(16, 185, 129, 0.2)' if isinstance(x, (int,float)) and x > 0 else 'background-color: rgba(244, 63, 94, 0.2)' if isinstance(x, (int,float)) and x < 0 else '', subset=['Change (%)', 'Change (₹)']), use_container_width=True, hide_index=True)

# --- F&O PULSE ---
elif menu == "F&O Pulse":
    st.subheader("📋 Master Watchlist (Blinking Prices)")
    search = st.text_input("Search Symbol...")
    disp = df_s[df_s['Symbol'].str.contains(search.upper())] if search else df_s
    
    st.dataframe(
        disp.sort_values("Change (%)", ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "Change (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            "Change (₹)": st.column_config.NumberColumn(format="%+.2f"),
            "Vol Ratio": st.column_config.ProgressColumn(min_value=0, max_value=3)
        }
    )

st.markdown("---")
st.caption(f"Sync Time: {datetime.now(tz).strftime('%H:%M:%S')} IST | Data: Yahoo Finance (Delayed)")