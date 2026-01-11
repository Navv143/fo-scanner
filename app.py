import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- THEME CONFIG ---
st.set_page_config(page_title="PRO-QUANT ELITE", layout="wide", initial_sidebar_state="expanded")

# Advanced CSS for Multi-Color UI & Professional Tables
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0b0e14; color: #e2e8f0; }
    .stMetric { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; padding: 15px; border: 1px solid #334155; }
    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid #334155; }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #334155; }
    .status-pill { padding: 4px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: bold; }
    h1, h2, h3 { color: #f8fafc; font-weight: 700; }
    /* Metric Delta Styling */
    [data-testid="stMetricDelta"] > div { font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=5 * 60 * 1000, key="global_refresh")

# --- DATA TICKERS ---
INDICES = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS",
    "NIFTY NEXT 50": "^NSMIDCP50", "INDIA VIX": "^INDIAVIX", "NIFTY IT": "NIFTY_IT.NS"
}

SECTORS = {
    "IT": "NIFTY_IT.NS", "AUTO": "NIFTY_AUTO.NS", "PHARMA": "NIFTY_PHARMA.NS",
    "METAL": "NIFTY_METAL.NS", "REALTY": "NIFTY_REALTY.NS", "FMCG": "NIFTY_FMCG.NS",
    "ENERGY": "NIFTY_ENERGY.NS", "INFRA": "NIFTY_INFRA.NS", "BANKS": "NIFTY_BANK.NS"
}

FO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "AXISBANK.NS", 
    "ADANIENT.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "BAJFINANCE.NS", "LT.NS", "MARUTI.NS", "JKCEMENT.NS", "ADANIPORTS.NS",
    "ACC.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AUROPHARMA.NS", "BAJAJ-AUTO.NS", "BANKBARODA.NS", 
    "BEL.NS", "BPCL.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "GAIL.NS", 
    "HCLTECH.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ITC.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "M&M.NS", 
    "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS", "ZEEL.NS"
] # Expand as needed

# --- DATA ENGINE ---
@st.cache_data(ttl=300)
def fetch_all_data():
    all_tickers = list(set(FO_STOCKS + list(INDICES.values()) + list(SECTORS.values())))
    raw = yf.download(all_tickers, period="5d", interval="1d", group_by='ticker', progress=False)
    
    stock_list = []
    for s in FO_STOCKS:
        try:
            d = raw[s]
            p, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
            chg_prc = p - prev
            chg_pct = (chg_prc / prev) * 100
            vol_r = d['Volume'].iloc[-1] / d['Volume'].iloc[-2]
            stock_list.append({
                "Symbol": s.replace(".NS",""), "LTP": round(p, 2), 
                "Change": round(chg_prc, 2), "Change%": round(chg_pct, 2), 
                "Vol Ratio": round(vol_r, 2)
            })
        except: pass
    
    idx_list = []
    for name, sym in INDICES.items():
        try:
            d = raw[sym]
            p, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
            idx_list.append({"Name": name, "Price": round(p, 2), "Change": round(p-prev, 2), "Change%": round(((p-prev)/prev)*100, 2)})
        except: pass

    sec_list = []
    for name, sym in SECTORS.items():
        try:
            d = raw[sym]
            p, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
            sec_list.append({"Sector": name, "Price": round(p, 2), "Change%": round(((p-prev)/prev)*100, 2)})
        except: pass

    return pd.DataFrame(stock_list), pd.DataFrame(idx_list), pd.DataFrame(sec_list)

# --- SIDEBAR MENU ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("PRO-QUANT")
    menu = option_menu(
        menu_title=None,
        options=["Dashboard", "Indices", "F&O Stocks", "Sector Heatmap"],
        icons=["speedometer2", "graph-up", "currency-exchange", "grid-3x3-gap"],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"background-color": "#0f172a"},
            "nav-link": {"color": "#94a3b8", "font-size": "14px", "text-align": "left"},
            "nav-link-selected": {"background-color": "#2563eb", "color": "white"},
        }
    )
    st.write("---")
    tz = pytz.timezone('Asia/Kolkata')
    st.caption(f"Last Sync: {datetime.now(tz).strftime('%H:%M:%S')}")

# --- APP EXECUTION ---
df_stocks, df_indices, df_sectors = fetch_all_data()

if menu == "Dashboard":
    st.header("🏠 Market Overview")
    
    # Top Metrics
    m1, m2, m3 = st.columns(3)
    nifty = df_indices[df_indices['Name'] == "NIFTY 50"].iloc[0]
    m1.metric("NIFTY 50", f"₹{nifty['Price']}", f"{nifty['Change%']}%")
    
    vix = df_indices[df_indices['Name'] == "INDIA VIX"].iloc[0]
    m2.metric("INDIA VIX", vix['Price'], f"{vix['Change%']}%", delta_color="inverse")
    
    m3.metric("Adv/Dec Ratio", f"{len(df_stocks[df_stocks['Change%']>0])}/{len(df_stocks[df_stocks['Change%']<0])}")

    st.write("---")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🟢 Top Gainers")
        st.dataframe(df_stocks.nlargest(5, 'Change%')[['Symbol', 'LTP', 'Change%']], use_container_width=True, hide_index=True)
        
    with col_right:
        st.subheader("🔴 Top Losers")
        st.dataframe(df_stocks.nsmallest(5, 'Change%')[['Symbol', 'LTP', 'Change%']], use_container_width=True, hide_index=True)

elif menu == "Indices":
    st.header("📈 Major Indices")
    st.table(df_indices.style.format({"Price": "₹{:,.2f}", "Change": "{:+,.2f}", "Change%": "{:+.2f}%"}).applymap(lambda x: 'color: #10b981' if isinstance(x, (int, float)) and x > 0 else 'color: #f43f5e' if isinstance(x, (int, float)) and x < 0 else '', subset=['Change', 'Change%']))

elif menu == "F&O Stocks":
    st.header("💰 F&O Stock Monitor")
    search = st.text_input("🔍 Search Stock Name...")
    disp = df_stocks.copy()
    if search: disp = disp[disp['Symbol'].str.contains(search.upper())]
    
    st.dataframe(
        disp.sort_values("Change%", ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "Change%": st.column_config.NumberColumn(format="%+.2f%%"),
            "Change": st.column_config.NumberColumn(format="%+.2f"),
            "Vol Ratio": st.column_config.ProgressColumn(min_value=0, max_value=3)
        }
    )

elif menu == "Sector Heatmap":
    st.header("🧱 Sector Pulse")
    s_cols = st.columns(3)
    for i, row in df_sectors.iterrows():
        with s_cols[i % 3]:
            st.metric(row['Sector'], f"₹{row['Price']}", f"{row['Change%']}%")
    
    st.write("---")
    st.subheader("📊 Relative Strength Map")
    st.bar_chart(df_sectors.set_index('Sector')['Change%'])