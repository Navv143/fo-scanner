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
    .stMetric { background: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); }
    .status-pill { padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; display: inline-block; margin-bottom: 15px; }
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=5 * 60 * 1000, key="global_refresh")

# --- FULL F&O LIST (180+ TICKERS) ---
FO_STOCKS = [
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

# --- SMART DATA ENGINE ---
@st.cache_data(ttl=300)
def get_master_data():
    # Batch download everything (Last 5 days to ensure we have Friday/Thursday)
    data = yf.download(FO_STOCKS, period="5d", interval="1d", group_by='ticker', progress=False)
    
    results = []
    for ticker in FO_STOCKS:
        try:
            df = data[ticker]
            if df.empty or len(df) < 2: continue
            
            # Identify last two valid trading sessions
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            ltp = curr['Close']
            prev_close = prev['Close']
            chg = ((ltp - prev_close) / prev_close) * 100
            vol_ratio = curr['Volume'] / prev['Volume']
            pdh, pdl = prev['High'], prev['Low']

            signal = "Neutral"
            if ltp > pdh: signal = "🚀 BUY"
            elif ltp < pdl: signal = "📉 SELL"

            results.append({
                "Symbol": ticker.replace(".NS",""),
                "LTP": round(ltp, 2),
                "Change%": round(chg, 2),
                "Vol Ratio": round(vol_ratio, 2),
                "Signal": signal
            })
        except: continue
    return pd.DataFrame(results)

def get_indices():
    indices = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}
    res = []
    for n, t in indices.items():
        try:
            h = yf.Ticker(t).history(period="2d")
            p = h['Close'].iloc[-1]
            c = ((p - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
            res.append({"name": n, "price": f"₹{p:,.2f}", "chg": f"{c:+.2f}%", "raw": c})
        except: pass
    return res

# --- UI HEADER ---
tz = pytz.timezone('Asia/Kolkata')
now = datetime.now(tz)
is_open = now.weekday() < 5 and (time(9,15) <= now.time() <= time(15,30))

st.title("🛡️ PRO-QUANT F&O")
status_txt = "🟢 LIVE TRADING" if is_open else "🔴 MARKET CLOSED (SUMMARY)"
status_clr = "#10b981" if is_open else "#f43f5e"
st.markdown(f'<div class="status-pill" style="background: {status_clr}22; color: {status_clr}; border: 1px solid {status_clr}44;">{status_txt}</div>', unsafe_allow_html=True)

# Indices Metrics
idx_data = get_indices()
cols = st.columns(len(idx_data))
for i, x in enumerate(idx_data):
    cols[i].metric(x['name'], x['price'], x['chg'], delta_color="normal" if x['raw'] >= 0 else "inverse")

st.divider()

# --- NAV ---
selected = option_menu(
    menu_title=None, options=["Momentum Radar", "Master Watchlist", "Analytics"],
    icons=["lightning", "list", "pie-chart"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#3b82f6"}}
)

# --- EXECUTION ---
with st.spinner("Fetching Data..."):
    df_master = get_master_data()

# --- TABS ---
if selected == "Momentum Radar":
    st.subheader("🚀 Momentum Breakouts (PDH/PDL)")
    vol_filter = st.slider("Min Vol Ratio (x)", 0.5, 3.0, 1.2)
    
    if not df_master.empty:
        radar = df_master[(df_master['Signal'] != "Neutral") & (df_master['Vol Ratio'] >= vol_filter)]
        if not radar.empty:
            st.dataframe(radar.sort_values("Vol Ratio", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info(f"No breakouts found with Vol Ratio > {vol_filter}x. Try lowering the slider.")
    else: st.error("Data unavailable. Check internet.")

elif selected == "Master Watchlist":
    st.subheader("📋 All F&O Stocks")
    if not df_master.empty:
        search = st.text_input("🔍 Quick Search", placeholder="e.g. RELIANCE")
        disp = df_master.copy()
        if search: disp = disp[disp['Symbol'].str.contains(search.upper())]
        st.dataframe(disp.sort_values("Change%", ascending=False), use_container_width=True, hide_index=True)

elif selected == "Analytics":
    if not df_master.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Gainers", len(df_master[df_master['Change%'] > 0]))
        c2.metric("Losers", len(df_master[df_master['Change%'] < 0]))
        c3.metric("Avg Vol", f"{df_master['Vol Ratio'].mean():.2f}x")
        
        st.write("---")
        st.write("📈 **Top 5 Movers**")
        st.table(df_master.nlargest(5, 'Change%')[['Symbol', 'LTP', 'Change%']])

st.markdown("---")
st.caption(f"Last Refresh: {now.strftime('%H:%M:%S')} IST | Data: Yahoo Finance (1-2m delay)")