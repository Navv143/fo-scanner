import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- MODULE 0: CORE CONFIG ---
st.set_page_config(page_title="PRO-QUANT TERMINAL v8.2", layout="wide", initial_sidebar_state="expanded")

def load_ui():
    try:
        with open("style.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        st.warning("CSS file not found. Please ensure style.css is in your repository.")

load_ui()
st_autorefresh(interval=3 * 60 * 1000, key="global_refresh")

# --- DATA TICKERS (Verified for Yahoo Finance) ---
INDICES = {
    "NIFTY 50": "^NSEI", 
    "BANK NIFTY": "^NSEBANK", 
    "FIN NIFTY": "NIFTY_FIN_SERVICE.NS",
    "SENSEX": "^BSESN",
    "MIDCAP SELECT": "NIFTY_MID_SELECT.NS",
    "INDIA VIX": "^INDIAVIX"
}

SECTOR_MAP = {
    "BANKS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "AUBANK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "BANDHANBNK.NS", "INDUSINDBK.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS", "COFORGE.NS", "MPHASIS.NS", "TECHM.NS", "PERSISTENT.NS", "LTTS.NS", "BSOFT.NS"],
    "AUTO": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "BALKRISIND.NS", "BHARATFORG.NS"],
    "METALS": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS", "NATIONALUM.NS", "NMDC.NS", "HINDCOPPER.NS"],
    "ENERGY": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "TATAPOWER.NS", "GAIL.NS", "SUZLON.NS", "COALINDIA.NS"],
    "PHARMA": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "ALKEM.NS", "BIOCON.NS", "GLENMARK.NS", "ZYDUSLIFE.NS"],
    "INFRA": ["ULTRACEMCO.NS", "GRASIM.NS", "JKCEMENT.NS", "ACC.NS", "AMBUJACEM.NS", "LT.NS", "ADANIPORTS.NS", "DLF.NS", "GODREJPROP.NS", "BEL.NS", "BHEL.NS", "HAL.NS", "RVNL.NS"],
    "FMCG": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TATACONSUM.NS", "COLPAL.NS", "TITAN.NS", "TRENT.NS", "ABFRL.NS", "ZOMATO.NS"],
    "FINANCE": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "M&MFIN.NS", "PFC.NS", "REC.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIGI.NS", "L&TFH.NS"],
    "OTHERS": ["SRF.NS", "UPL.NS", "CHAMBLFERT.NS", "DEEPAKNTR.NS", "NAVINFLUOR.NS", "POLYCAB.NS", "DIXON.NS", "INDIGO.NS", "IEX.NS", "PVRINOX.NS", "ZEEL.NS"]
}

ALL_STOCKS = [s for sub in SECTOR_MAP.values() for s in sub]

@st.cache_data(ttl=120)
def get_data():
    all_tkr = list(set(ALL_STOCKS + list(INDICES.values())))
    # Using 10d period to ensure data is found even during long holidays
    raw = yf.download(all_tkr, period="10d", interval="1d", group_by='ticker', progress=False)
    s_rows, i_rows = [], []
    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if len(df) < 2: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_v, chg_p = p - prev_p, ((p - prev_p)/prev_p)*100
            
            if t in ALL_STOCKS:
                vr = curr['Volume']/prev['Volume'] if prev['Volume'] > 0 else 0
                v_score = 30 if vr>=3 else 24 if vr>=2 else 16 if vr>=1.5 else 8 if vr>=1.1 else 4 if vr>=1.0 else 0
                sig = "🚀 BUY" if p > prev['High'] else "📉 SELL" if p < prev['Low'] else "Neutral"
                sec = next((k for k, v in SECTOR_MAP.items() if t in v), "Other")
                s_rows.append({"Sector": sec, "Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Chg(₹)": round(chg_v, 2), "Chg(%)": round(chg_p, 2), "Vol_Ratio": round(vr, 2), "Score": v_score, "Signal": sig})
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "ChgV": round(chg_v, 2), "ChgP": round(chg_p, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

df_s, df_i = get_data()

# --- MODULE 1: DASHBOARD RENDERER ---
def render_dashboard():
    st.markdown("<br>", unsafe_allow_html=True)
    
    # SAFETY CHECK: Only try to render if indices exist
    if not df_i.empty:
        # Create grid for indices
        idx_names = ["NIFTY 50", "BANK NIFTY", "FIN NIFTY", "SENSEX", "MIDCAP SELECT", "INDIA VIX"]
        
        # Split into two rows of 3
        for i in range(0, 6, 3):
            cols = st.columns(3)
            for j in range(3):
                name = idx_names[i + j]
                # Safe filtering
                match = df_i[df_i['Name'] == name]
                if not match.empty:
                    r = match.iloc[0]
                    with cols[j]:
                        st.markdown(f"<span style='color:#94a3b8; font-size:12px; font-weight:700;'>{r['Name']}</span>", unsafe_allow_html=True)
                        st.markdown(f"<div class='price-blink'>{'' if 'VIX' in name else '₹'}{r['Price']:,.2f}</div>", unsafe_allow_html=True)
                        # Inverse color for VIX
                        clr = ("#f43f5e" if r['ChgP'] >= 0 else "#10b981") if "VIX" in name else ("#10b981" if r['ChgP'] >= 0 else "#f43f5e")
                        st.markdown(f"<span style='color:{clr}; font-weight:bold;'>{r['ChgV']:+.2f} ({r['ChgP']:+.2f}%)</span>", unsafe_allow_html=True)
    else:
        st.error("Market Index data currently unavailable. Retrying...")

    st.markdown("<br><hr style='border-color:rgba(255,255,255,0.1)'><br>", unsafe_allow_html=True)
    
    if not df_s.empty:
        st.subheader("🎯 Institutional Conviction (Score > 20)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<h4 style='color:#10b981'>🟢 Momentum BUY</h4>", unsafe_allow_html=True)
            bulls = df_s[(df_s['Signal']=="🚀 BUY") & (df_s['Score'] >= 20)].nlargest(3, 'Score')
            if not bulls.empty:
                for _, r in bulls.iterrows():
                    st.markdown(f"""<div class='pro-card bull-border'>
                        <span style='font-size:20px; font-weight:700;'>{r['Symbol']}</span> 
                        <span style='float:right; color:#10b981; font-weight:bold;'>{r['Chg(%)']:+.2f}%</span><br>
                        <span style='color:#94a3b8'>LTP: ₹{r['LTP']} | Score: {r['Score']} pts</span>
                    </div>""", unsafe_allow_html=True)
            else: st.info("No stocks currently meet Buy Momentum criteria.")

        with c2:
            st.markdown("<h4 style='color:#f43f5e'>🔴 Momentum SELL</h4>", unsafe_allow_html=True)
            bears = df_s[(df_s['Signal']=="📉 SELL") & (df_s['Score'] >= 20)].nlargest(3, 'Score')
            if not bears.empty:
                for _, r in bears.iterrows():
                    st.markdown(f"""<div class='pro-card bear-border'>
                        <span style='font-size:20px; font-weight:700;'>{r['Symbol']}</span> 
                        <span style='float:right; color:#f43f5e; font-weight:bold;'>{r['Chg(%)']:+.2f}%</span><br>
                        <span style='color:#94a3b8'>LTP: ₹{r['LTP']} | Score: {r['Score']} pts</span>
                    </div>""", unsafe_allow_html=True)
            else: st.info("No stocks currently meet Sell Momentum criteria.")
    else:
        st.warning("Stock Momentum data loading...")

# --- MODULE 2: SECTOR PULSE ---
def render_sectors():
    st.subheader("🏗️ Market Sector Analytics")
    if not df_s.empty:
        sec_data = df_s.groupby("Sector")["Chg(%)"].mean().reset_index().sort_values("Chg(%)", ascending=False)
        fig = px.bar(sec_data, x='Sector', y='Chg(%)', color='Chg(%)', color_continuous_scale=['#f43f5e', '#10b981'], color_continuous_midpoint=0)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="#94a3b8", height=400, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        sel_sec = st.selectbox("Drill down into Sector:", sec_data['Sector'].tolist())
        st.dataframe(df_s[df_s['Sector']==sel_sec].sort_values("Chg(%)", ascending=False).style.format({"Chg(%)": "{:+.2f}%", "Chg(₹)": "{:+.2f}"}).applymap(lambda x: 'color: #10b981' if isinstance(x, (int,float)) and x>0 else 'color: #f43f5e' if isinstance(x, (int,float)) and x<0 else '', subset=['Chg(%)', 'Chg(₹)']), use_container_width=True, hide_index=True)
    else:
        st.error("Sector data unavailable.")

# --- MODULE 3: SCOREBOARD ---
def render_scoreboard():
    st.subheader("📊 Institutional Volume Scoreboard")
    if not df_s.empty:
        st.dataframe(df_s.sort_values("Score", ascending=False), use_container_width=True, hide_index=True,
                     column_config={"Score": st.column_config.ProgressColumn(min_value=0, max_value=30), "Chg(%)": st.column_config.NumberColumn(format="%+.2f%%")})
    else: st.info("Data loading...")

# --- MODULE 4: WATCHLIST ---
def render_watchlist():
    st.subheader("📋 Master F&O Pulse")
    if not df_s.empty:
        search = st.text_input("🔍 Search Stock...").upper()
        disp = df_s[df_s['Symbol'].str.contains(search)] if search else df_s
        st.dataframe(disp.sort_values("Chg(%)", ascending=False), use_container_width=True, hide_index=True)
    else: st.info("Watchlist data unavailable.")

# --- APP ROUTING ---
with st.sidebar:
    st.markdown("<h2 style='color:#38bdf8'>QUANT PRO</h2>", unsafe_allow_html=True)
    menu = option_menu(None, ["Dashboard", "Sector Pulse", "Scoreboard", "Watchlist"], 
                       icons=["terminal", "activity", "award", "list"], default_index=0)
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    st.markdown(f"<div style='background:#1e293b; padding:10px; border-radius:8px; border:1px solid #334155;'>Time: {now.strftime('%H:%M:%S')} IST</div>", unsafe_allow_html=True)

# Routing Logic
if menu == "Dashboard": render_dashboard()
elif menu == "Sector Pulse": render_sectors()
elif menu == "Scoreboard": render_scoreboard()
elif menu == "Watchlist": render_watchlist()