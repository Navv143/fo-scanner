import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, time, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- MODULE 0: CORE SETTINGS ---
st.set_page_config(page_title="PRO-QUANT MASTER v17", layout="wide", initial_sidebar_state="expanded")

def load_ui():
    try:
        with open("style.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass

load_ui()
st_autorefresh(interval=3 * 60 * 1000, key="global_refresh")

# --- 212+ FULL F&O STOCK DATABASE (LOCKED) ---
SECTOR_MAP = {
    "BANKS": ["AXISBANK.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "INDUSINDBK.NS", "AUBANK.NS", "FEDERALBNK.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "IDFCFIRSTB.NS", "BANKINDIA.NS", "IDFC.NS", "BANDHANBNK.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS", "COFORGE.NS", "TECHM.NS", "PERSISTENT.NS", "LTTS.NS", "BSOFT.NS", "KPITTECH.NS", "OFSS.NS", "TATAELXSI.NS", "CYIENT.NS"],
    "METALS": ["VEDL.NS", "HINDCOPPER.NS", "NATIONALUM.NS", "TATASTEEL.NS", "JINDALSTEL.NS", "SAIL.NS", "HINDALCO.NS", "NMDC.NS", "JSWSTEEL.NS", "RATNAMANI.NS", "HINDZINC.NS"],
    "AUTO": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "BALKRISIND.NS", "BHARATFORG.NS", "ESCORTS.NS", "MRF.NS", "APOLLOTYRE.NS", "MOTHERSON.NS", "EXIDEIND.NS"],
    "ENERGY/POWER": ["MCX.NS", "ONGC.NS", "NTPC.NS", "RELIANCE.NS", "BPCL.NS", "IOC.NS", "POWERGRID.NS", "ADANIENT.NS", "TATAPOWER.NS", "GAIL.NS", "SUZLON.NS", "COALINDIA.NS", "ADANIPOWER.NS", "NHPC.NS", "SJVN.NS", "RECLTD.NS", "PFC.NS"],
    "PHARMA": ["LAURUSLABS.NS", "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "ALKEM.NS", "BIOCON.NS", "GLENMARK.NS", "ZYDUSLIFE.NS", "APOLLOHOSP.NS", "ABBOTINDIA.NS", "GRANULES.NS", "MAXHEALTH.NS", "IPCALAB.NS"],
    "INFRA": ["DELTACORP.NS", "INDUSTOWER.NS", "DLF.NS", "RVNL.NS", "GODREJPROP.NS", "ULTRACEMCO.NS", "GRASIM.NS", "JKCEMENT.NS", "ACC.NS", "AMBUJACEM.NS", "LT.NS", "ADANIPORTS.NS", "OBEROIRLTY.NS", "IRCTC.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "IRFC.NS", "HAL.NS", "BEL.NS", "BHEL.NS", "CONCOR.NS", "PNCINFRA.NS", "KNRCON.NS"],
    "FMCG/RETAIL": ["DALBHARAT.NS", "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TATACONSUM.NS", "COLPAL.NS", "TITAN.NS", "TRENT.NS", "ZOMATO.NS", "NYKAA.NS", "ABFRL.NS", "VBL.NS", "JUBLFOOD.NS", "PAGEIND.NS", "ASIANPAINT.NS", "BERGERPAINT.NS", "PIDILITIND.NS"],
    "FINANCE/NBFC": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "M&MFIN.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIGI.NS", "SHRIRAMFIN.NS", "L&TFH.NS", "ABCAPITAL.NS", "MNAPPURAM.NS", "SBICARD.NS", "POONAWALLA.NS", "MFSL.NS"],
    "CHEM/OTHERS": ["IDEA.NS", "SRF.NS", "UPL.NS", "DEEPAKNTR.NS", "POLYCAB.NS", "DIXON.NS", "INDIGO.NS", "IEX.NS", "PVRINOX.NS", "ZEEL.NS", "COROMANDEL.NS", "CHAMBLFERT.NS", "GNFC.NS", "SYNGENE.NS", "BATAINDIA.NS", "GUJGASLTD.NS", "IGL.NS", "MGL.NS", "PETRONET.NS", "ASTRAL.NS", "CUMMINSIND.NS", "VOLTAS.NS"]
}

ALL_STOCKS = [s for sub in SECTOR_MAP.values() for s in sub]
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS", "SENSEX": "^BSESN", "MIDCAP": "NIFTY_MID_SELECT.NS", "INDIA VIX": "^INDIAVIX"}

# --- DATA ENGINE (DIAMOND 150-PT) ---
@st.cache_data(ttl=120)
def fetch_master_data():
    all_tkr = list(set(ALL_STOCKS + list(INDICES.values())))
    raw = yf.download(all_tkr, period="15d", interval="1d", group_by='ticker', progress=False)
    s_rows, i_rows, sector_perf = [], [], {}
    
    for sec, stocks in SECTOR_MAP.items():
        changes = []
        for s in stocks:
            try:
                d = raw[s].dropna()
                if len(d) >= 2: changes.append(((d['Close'].iloc[-1] - d['Close'].iloc[-2])/d['Close'].iloc[-2])*100)
            except: continue
        sector_perf[sec] = np.mean(changes) if changes else 0

    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if len(df) < 5: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_p = ((p - prev_p)/prev_p)*100
            if t in ALL_STOCKS:
                obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
                obv_t = "UP" if obv.iloc[-1] > obv.iloc[-2] else "DOWN"
                adr = ((df['High'] - df['Low']) / df['Low'] * 100).tail(5).mean()
                sec = next((k for k, v in SECTOR_MAP.items() if t in v), "Others")
                score = 0
                is_bull, is_bear = p > prev['High'], p < prev['Low']
                if is_bull or is_bear: score += 30
                if (is_bull and sector_perf[sec] > 0.5) or (is_bear and sector_perf[sec] < -0.5): score += 30
                if abs(chg_p) > 1.0: score += 20
                if adr > 0 and (abs(chg_p)/adr) >= 0.5: score += 20
                if curr['Volume']/prev['Volume'] > 1.2: score += 30
                if (is_bull and curr['Open'] == curr['Low']) or (is_bear and curr['Open'] == curr['High']): score += 20
                s_rows.append({"Sector": sec, "Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Chg%": round(chg_p, 2), "Score": score, "Signal": "🚀 BULLISH" if is_bull else "📉 BEARISH" if is_bear else "Neutral", "OBV": obv_t, "Vol_R": round(curr['Volume']/prev['Volume'], 2)})
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "ChgP": round(chg_p, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows), sector_perf

df_s, df_i, sector_data = fetch_master_data()

# --- MODULE: SMART HOURLY BOX STRATEGY ---
def get_hourly_box_signal(ticker):
    try:
        # Fetch 5-minute data for the current session
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        if df.empty or len(df) < 15: 
            return "DATA PENDING", 0, 0, "WAIT"
        
        # Resample to get the High/Low of the last completed 1-hour candle
        df_hourly = df.resample('1H').agg({'High': 'max', 'Low': 'min', 'Close': 'last'})
        if len(df_hourly) < 2: return "SCANNING...", 0, 0, "INITIALIZING"
        
        latest_box = df_hourly.iloc[-2] # Last completed hour
        box_high, box_low = latest_box['High'], latest_box['Low']
        current_price = df['Close'].iloc[-1]
        
        if current_price > box_high:
            return "🚀 BUY CALL", box_high, box_low, "HOURLY BREAKOUT (UP)"
        elif current_price < box_low:
            return "📉 BUY PUT", box_high, box_low, "HOURLY BREAKDOWN (DOWN)"
        else:
            return "⏸️ NO TRADE", box_high, box_low, "INSIDE BOX"
    except:
        return "ERROR", 0, 0, "API LIMIT"

# --- NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color:#00d4ff'>QUANT ELITE v17</h2>", unsafe_allow_html=True)
    menu = option_menu(None, ["Terminal", "Index Pro Strategy", "Impulse Radar", "Sector Heatmap", "Master List"], 
                       icons=["speedometer", "cpu", "lightning", "grid", "list"], default_index=0)
    st.info(f"Sync: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M:%S')} IST")

# --- DASHBOARD HEADER ---
if not df_i.empty:
    idx_list = ["NIFTY 50", "BANK NIFTY", "FIN NIFTY", "SENSEX", "MIDCAP", "INDIA VIX"]
    for row_start in range(0, 6, 3):
        cols = st.columns(3)
        for j in range(3):
            name = idx_list[row_start + j]
            match = df_i[df_i['Name'] == name]
            with cols[j]:
                if not match.empty:
                    r = match.iloc[0]
                    st.markdown(f"<span style='color:#8b949e; font-size:11px; font-weight:700;'>{r['Name']}</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='price-blink'>₹{r['Price']:,.2f}</div>", unsafe_allow_html=True)
                    clr = ("#ff3366" if r['ChgP'] >= 0 else "#00ff88") if "VIX" in name else ("#00ff88" if r['ChgP'] >= 0 else "#ff3366")
                    st.markdown(f"<span style='color:{clr}; font-weight:bold;'>{r['ChgP']:+.2f}%</span>", unsafe_allow_html=True)

st.divider()

# --- PAGE ROUTING ---
if menu == "Terminal":
    st.subheader("💎 High Conviction Impulse (Score > 80)")
    c1, c2 = st.columns(2)
    if not df_s.empty:
        with c1:
            for _, r in df_s[(df_s['Signal']=="🚀 BULLISH") & (df_s['Score'] >= 80)].nlargest(3, 'Score').iterrows():
                st.markdown(f"<div class='mobile-card' style='border-color:#00ff88'><b>{r['Symbol']}</b> | Score: {r['Score']} | <span style='color:#00ff88'>{r['Chg%']:+.2f}%</span></div>", unsafe_allow_html=True)
        with c2:
            for _, r in df_s[(df_s['Signal']=="📉 BEARISH") & (df_s['Score'] >= 80)].nlargest(3, 'Score').iterrows():
                st.markdown(f"<div class='mobile-card' style='border-color:#ff3366'><b>{r['Symbol']}</b> | Score: {r['Score']} | <span style='color:#ff3366'>{r['Chg%']:+.2f}%</span></div>", unsafe_allow_html=True)

elif menu == "Index Pro Strategy":
    st.subheader("🤖 Smart Box Strategy (1-Hour Breakout)")
    st.info("Strategy: Buying happens when price breaks the High/Low of the last completed 1-hour candle.")
    targets = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS"}
    for name, tkr in targets.items():
        signal, high, low, reason = get_hourly_box_signal(tkr)
        clr = "#00ff88" if "CALL" in signal else "#ff3366" if "PUT" in signal else "#8b949e"
        st.markdown(f"""
        <div style='border: 1px solid {clr}; padding: 20px; border-radius: 15px; background: rgba(255,255,255,0.02); margin-bottom:15px;'>
            <h3 style='margin:0'>{name}</h3>
            <h1 style='color:{clr}; margin: 10px 0;'>{signal}</h1>
            <p style='color:#8b949e'><b>Box Range:</b> High ₹{high:,.2f} | Low ₹{low:,.2f}</p>
            <p style='font-size: 14px; font-weight: bold;'>Reason: {reason}</p>
        </div>
        """, unsafe_allow_html=True)

elif menu == "Impulse Radar":
    st.dataframe(df_s[df_s['Signal'] != "Neutral"].sort_values("Score", ascending=False), use_container_width=True, hide_index=True, column_config={"Score": st.column_config.ProgressColumn(min_value=0, max_value=150)})

elif menu == "Sector Heatmap":
    perf_df = pd.DataFrame(list(sector_data.items()), columns=['Sector', 'Chg%']).sort_values('Chg%', ascending=False)
    st.plotly_chart(px.bar(perf_df, x='Sector', y='Chg%', color='Chg%', color_continuous_scale=['#ff3366', '#00ff88'], color_continuous_midpoint=0, height=350), use_container_width=True)
    sel = st.selectbox("Select Sector:", perf_df['Sector'].tolist())
    st.dataframe(df_s[df_s['Sector']==sel].sort_values("Chg%", ascending=False), use_container_width=True, hide_index=True)

elif menu == "Master List":
    search = st.text_input("Search 212 Stocks...").upper()
    disp = df_s[df_s['Symbol'].str.contains(search)] if search else df_s
    st.dataframe(disp.sort_values("Chg%", ascending=False), use_container_width=True, hide_index=True)