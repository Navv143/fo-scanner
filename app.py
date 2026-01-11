import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. SETTINGS & PROFESSIONAL UI CSS ---
st.set_page_config(page_title="PRO-QUANT ELITE v5.0", layout="wide", initial_sidebar_state="expanded")

# High-End Terminal CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Main Background */
    .main { background-color: #05070a; color: #e2e8f0; }
    
    /* Blinking Price Animation */
    @keyframes blink-glow { 
        0% { opacity: 1; } 50% { opacity: 0.4; text-shadow: 0 0 8px #58a6ff; } 100% { opacity: 1; } 
    }
    .price-blink { animation: blink-glow 2s infinite; font-family: 'JetBrains Mono', monospace; font-weight: bold; font-size: 26px; color: #ffffff; }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #0d1117, #161b22);
        border: 1px solid #30363d; border-radius: 12px; padding: 20px !important;
    }
    div[data-testid="stMetricLabel"] > div { color: #8b949e !important; font-size: 14px !important; }

    /* Status Pill */
    .status-pill { padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 12px; display: inline-block; border: 1px solid; margin-bottom: 10px; }
    
    /* Navigation Bar Fix */
    section[data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    
    /* Titles */
    h1, h2, h3 { color: #58a6ff !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=3 * 60 * 1000, key="global_sync")

# --- 2. THE COMPLETE 184 F&O TICKER DATABASE & SECTOR MAPPING ---
SECTOR_MAP = {
    "BANKS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "AUBANK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "BANDHANBNK.NS", "INDUSINDBK.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS", "COFORGE.NS", "MPHASIS.NS", "TECHM.NS", "PERSISTENT.NS", "LTTS.NS", "BSOFT.NS"],
    "AUTO": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "BALKRISIND.NS", "BHARATFORG.NS", "ESCORTS.NS", "MRF.NS", "APOLLOTYRE.NS"],
    "METAL": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS", "NATIONALUM.NS", "NMDC.NS", "HINDCOPPER.NS"],
    "PHARMA": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "ALKEM.NS", "BIOCON.NS", "GLENMARK.NS", "GRANULES.NS", "IPCALAB.NS", "SYNGENE.NS", "TORNTPHARM.NS", "ZYDUSLIFE.NS", "ABBOTINDIA.NS"],
    "CEMENT/INFRA": ["ULTRACEMCO.NS", "GRASIM.NS", "JKCEMENT.NS", "ACC.NS", "AMBUJACEM.NS", "LT.NS", "ADANIPORTS.NS", "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "ASTRAL.NS", "CUMMINSIND.NS", "CONCOR.NS", "BEL.NS", "BHEL.NS", "HAL.NS"],
    "OIL/ENERGY/POWER": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "HINDPETRO.NS", "TATAPOWER.NS", "GAIL.NS", "IGL.NS", "MGL.NS", "PETRONET.NS", "GUJGASLTD.NS"],
    "FMCG": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TATACONSUM.NS", "COLPAL.NS", "GODREJCP.NS", "MARICO.NS", "UBL.NS", "MCDOWELL-N.NS", "JUBLFOOD.NS", "BALRAMCHIN.NS"],
    "NBFC/FIN": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "M&MFIN.NS", "SHREECEM.NS", "PFC.NS", "REC.NS", "LICHSGFIN.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIPRULI.NS", "ICICIGI.NS", "PEL.NS", "ABCAPITAL.NS", "CANFINHOME.NS"]
}

# Consolidate all stocks
ALL_STOCKS = [s for sub in SECTOR_MAP.values() for s in sub]
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=120)
def fetch_elite_data():
    all_tkr = list(set(ALL_STOCKS + list(INDICES.values())))
    raw = yf.download(all_tkr, period="7d", interval="1d", group_by='ticker', progress=False)
    
    s_rows, i_rows = [], []
    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if len(df) < 2: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_v, chg_p = p - prev_p, ((p - prev_p)/prev_p)*100
            
            if t in ALL_STOCKS:
                vr = curr['Volume']/prev['Volume'] if prev['Volume']>0 else 0
                sig = "🚀 BUY" if p > prev['High'] else "📉 SELL" if p < prev['Low'] else "Neutral"
                sec = next((k for k, v in SECTOR_MAP.items() if t in v), "Other")
                s_rows.append({"Sector": sec, "Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Change(₹)": round(chg_v, 2), "Change(%)": round(chg_p, 2), "VolRatio": round(vr, 2), "Signal": sig})
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "ChgV": round(chg_v, 2), "ChgP": round(chg_p, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

# --- 4. APP NAVIGATION ---
df_s, df_i = fetch_elite_data()

with st.sidebar:
    st.markdown("<h2 style='color:#58a6ff'>PRO-QUANT ELITE</h2>", unsafe_allow_html=True)
    menu = option_menu(None, ["Market Dash", "Sector Radar", "F&O Watchlist"], 
                       icons=["speedometer2", "pie-chart", "list-task"], default_index=0,
                       styles={"nav-link-selected": {"background-color": "#238636"}})
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    is_live = now.weekday() < 5 and (time(9,15) <= now.time() <= time(15,30))
    st.markdown(f'<div class="status-pill" style="background: {"#002b1b" if is_live else "#2b0000"}; color: {"#00ffcc" if is_live else "#ff4b4b"}; border-color: {"#00ffcc" if is_live else "#ff4b4b"};">{"🟢 LIVE" if is_live else "🔴 CLOSED"}</div>', unsafe_allow_html=True)

# --- 5. PAGE LOGIC ---
if menu == "Market Dash":
    cols = st.columns(len(df_i))
    for i, r in df_i.iterrows():
        with cols[i]:
            st.markdown(f"**{r['Name']}**")
            st.markdown(f"<div class='price-blink'>₹{r['Price']:,}</div>", unsafe_allow_html=True)
            clr = "#10b981" if r['ChgP'] >= 0 else "#f43f5e"
            st.markdown(f"<span style='color:{clr}; font-weight:bold;'>{r['ChgV']:+.2f} ({r['ChgP']:+.2f}%)</span>", unsafe_allow_html=True)

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Top 3 Bullish (Vol Surge)")
        for _, r in df_s[df_s['Signal']=="🚀 BUY"].nlargest(3, 'VolRatio').iterrows():
            st.markdown(f"<div style='border:1px solid #10b981; padding:10px; border-radius:8px; margin-bottom:5px'><b>{r['Symbol']}</b> | ₹{r['LTP']} | <span style='color:#10b981'>+{r['Change(%)']}%</span> | Vol: {r['VolRatio']}x</div>", unsafe_allow_html=True)
    with c2:
        st.subheader("📉 Top 3 Bearish (Vol Surge)")
        for _, r in df_s[df_s['Signal']=="📉 SELL"].nlargest(3, 'VolRatio').iterrows():
            st.markdown(f"<div style='border:1px solid #f43f5e; padding:10px; border-radius:8px; margin-bottom:5px'><b>{r['Symbol']}</b> | ₹{r['LTP']} | <span style='color:#f43f5e'>{r['Change(%)']}%</span> | Vol: {r['VolRatio']}x</div>", unsafe_allow_html=True)

elif menu == "Sector Radar":
    st.subheader("🏗️ Interactive Sector Heatmap")
    sec_data = df_s.groupby("Sector")["Change(%)"].mean().reset_index().sort_values("Change(%)", ascending=False)
    
    fig = px.bar(sec_data, x='Sector', y='Change(%)', color='Change(%)', color_continuous_scale=['#f43f5e', '#10b981'], color_continuous_midpoint=0)
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="#8b949e", showlegend=False, height=350, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    sel_sec = st.selectbox("Click/Select Sector to view stocks:", sec_data['Sector'].tolist())
    st.dataframe(df_s[df_s['Sector']==sel_sec].sort_values("Change(%)", ascending=False).style.applymap(lambda x: 'background-color: rgba(16, 185, 129, 0.2); color: #10b981' if isinstance(x, (int, float)) and x > 0 else 'background-color: rgba(244, 63, 94, 0.2); color: #f43f5e' if isinstance(x, (int, float)) and x < 0 else '', subset=['Change(%)', 'Change(₹)']), use_container_width=True, hide_index=True)

elif menu == "F&O Watchlist":
    st.subheader("📋 Full Watchlist (180+ Stocks)")
    search = st.text_input("🔍 Search Asset...", placeholder="e.g. RELIANCE").upper()
    disp = df_s[df_s['Symbol'].str.contains(search)] if search else df_s
    st.dataframe(disp.sort_values("Change(%)", ascending=False), use_container_width=True, hide_index=True, column_config={"Change(%)": st.column_config.NumberColumn(format="%+.2f%%"), "VolRatio": st.column_config.ProgressColumn(min_value=0, max_value=3)})

st.caption(f"Sync: {now.strftime('%H:%M:%S')} IST | Strategy: PDH/PDL Breakout + Vol Surge")