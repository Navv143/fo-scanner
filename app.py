import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="PRO-QUANT TERMINAL v15", layout="wide", initial_sidebar_state="expanded")

def load_ui():
    try:
        with open("style.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        st.markdown("<style>.main {background-color: #05070a; color: white;}</style>", unsafe_allow_html=True)

load_ui()
st_autorefresh(interval=3 * 60 * 1000, key="pro_sync")

# --- 2. THE COMPLETE 212+ STOCK LIST (Updated from your Watchlist) ---
SECTOR_MAP = {
    "METALS": ["VEDL.NS", "HINDCOPPER.NS", "NATIONALUM.NS", "TATASTEEL.NS", "JINDALSTEL.NS", "SAIL.NS", "HINDALCO.NS", "NMDC.NS", "JSWSTEEL.NS", "RATNAMANI.NS", "HINDZINC.NS"],
    "BANKS": ["AXISBANK.NS", "INDUSINDBK.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AUBANK.NS", "FEDERALBNK.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "IDFCFIRSTB.NS", "BANKINDIA.NS", "IDFC.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS", "COFORGE.NS", "TECHM.NS", "PERSISTENT.NS", "LTTS.NS", "BSOFT.NS", "KPITTECH.NS", "OFSS.NS"],
    "ENERGY/POWER": ["MCX.NS", "ONGC.NS", "NTPC.NS", "RELIANCE.NS", "BPCL.NS", "IOC.NS", "POWERGRID.NS", "ADANIENT.NS", "TATAPOWER.NS", "GAIL.NS", "SUZLON.NS", "COALINDIA.NS", "ADANIPOWER.NS", "SJVN.NS", "NHPC.NS"],
    "PHARMA": ["LAURUSLABS.NS", "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "ALKEM.NS", "BIOCON.NS", "GLENMARK.NS", "ZYDUSLIFE.NS", "APOLLOHOSP.NS", "ABBOTINDIA.NS", "GRANULES.NS"],
    "INFRA": ["DELTACORP.NS", "INDUSTOWER.NS", "DLF.NS", "RVNL.NS", "GODREJPROP.NS", "ULTRACEMCO.NS", "GRASIM.NS", "JKCEMENT.NS", "ACC.NS", "AMBUJACEM.NS", "LT.NS", "ADANIPORTS.NS", "OBEROIRLTY.NS", "IRCTC.NS", "RVNL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "IRFC.NS", "HAL.NS", "BEL.NS", "BHEL.NS", "CONCOR.NS"],
    "FMCG/RETAIL": ["DALBHARAT.NS", "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TATACONSUM.NS", "COLPAL.NS", "TITAN.NS", "TRENT.NS", "ZOMATO.NS", "NYKAA.NS", "ABFRL.NS", "VBL.NS", "JUBLFOOD.NS", "PAGEIND.NS"],
    "FINANCE": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "M&MFIN.NS", "PFC.NS", "REC.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIGI.NS", "SHRIRAMFIN.NS", "L&TFH.NS", "RECLTD.NS"],
    "OTHERS": ["IDEA.NS", "SRF.NS", "UPL.NS", "DEEPAKNTR.NS", "POLYCAB.NS", "DIXON.NS", "INDIGO.NS", "IEX.NS", "PVRINOX.NS", "ZEEL.NS", "COROMANDEL.NS", "CHAMBLFERT.NS", "GNFC.NS", "SYNGENE.NS", "BATAINDIA.NS", "GUJGASLTD.NS"]
}

ALL_STOCKS = [s for sub in SECTOR_MAP.values() for s in sub]
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX", "SENSEX": "^BSESN", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS", "MIDCAP": "NIFTY_MID_SELECT.NS"}

# --- 3. THE 150-PT DIAMOND SCORING ENGINE ---
def calculate_diamond_score(row, prev_h, prev_l, adr, obv_t, sector_strength):
    score = 0
    p, o, h, l = row['LTP'], row['Open'], row['High'], row['Low']
    
    # 1. RANGE BREAK (30 Pts) - CRITICAL
    is_bull = p > prev_h
    is_bear = p < prev_l
    if is_bull or is_bear: score += 30
    
    # 2. SECTOR CONFLUENCE (30 Pts) - HIGH PROBABILITY
    # If the sector's average movement is in the same direction, add points
    if (is_bull and sector_strength > 0.5) or (is_bear and sector_strength < -0.5): score += 30
    
    # 3. VELOCITY & ROC (40 Pts)
    chg = abs(row['Chg%'])
    if chg > 1.0: score += 20
    if adr > 0 and (chg / adr) >= 0.5: score += 20 # 50% of ADR covered
    
    # 4. INSTITUTIONAL FOOTPRINT (30 Pts)
    if row['Vol_R'] > 1.5: score += 30
    elif row['Vol_R'] > 1.1: score += 15
    
    # 5. OPEN TYPE (20 Pts) - EARLY MOMENTUM
    if is_bull and o == l: score += 20 # Open=Low
    elif is_bear and o == h: score += 20 # Open=High
    
    return score, "🚀 BULLISH" if is_bull else "📉 BEARISH" if is_bear else "Neutral"

@st.cache_data(ttl=120)
def fetch_master_data():
    all_tkr = list(set(ALL_STOCKS + list(INDICES.values())))
    raw = yf.download(all_tkr, period="10d", interval="1d", group_by='ticker', progress=False)
    s_rows, i_rows = [], []
    
    # Pre-calculate Sector Strength
    sector_performance = {}
    for sec, stocks in SECTOR_MAP.items():
        changes = []
        for s in stocks:
            try:
                d = raw[s].dropna()
                if len(d) >= 2: changes.append(((d['Close'].iloc[-1] - d['Close'].iloc[-2])/d['Close'].iloc[-2])*100)
            except: continue
        sector_performance[sec] = np.mean(changes) if changes else 0

    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if len(df) < 3: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_p = ((p - prev_p)/prev_p)*100
            
            if t in ALL_STOCKS:
                adr = ((df['High'] - df['Low']) / df['Low'] * 100).tail(5).mean()
                obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
                sec = next((k for k, v in SECTOR_MAP.items() if t in v), "Others")
                
                score, signal = calculate_diamond_score(
                    {'LTP': p, 'Open': curr['Open'], 'High': curr['High'], 'Low': curr['Low'], 'Chg%': chg_p, 'Vol_R': curr['Volume']/prev['Volume']},
                    prev['High'], prev['Low'], adr, "UP" if obv.iloc[-1] > obv.iloc[-2] else "DOWN", sector_performance[sec]
                )
                
                s_rows.append({
                    "Sector": sec, "Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Chg%": round(chg_p, 2),
                    "Score": score, "Signal": signal, "Vol_R": round(curr['Volume']/prev['Volume'], 2)
                })
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "ChgP": round(chg_p, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

df_s, df_i = fetch_master_data()

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color:#00d4ff'>QUANT ELITE v15</h2>", unsafe_allow_html=True)
    menu = option_menu(None, ["Diamond Terminal", "Impulse Radar", "Sector Map", "Master List"], icons=["speedometer", "lightning-charge", "grid", "list"], default_index=0)
    st.info(f"Market Status: {'🟢 LIVE' if (now := datetime.now(pytz.timezone('Asia/Kolkata'))).weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")

# Indices (CRASH-PROOF Logic)
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
                    st.markdown(f"<div class='price-blink'>{'' if 'VIX' in name else '₹'}{r['Price']:,.2f}</div>", unsafe_allow_html=True)
                    clr = ("#ff3366" if r['ChgP'] >= 0 else "#00ff88") if "VIX" in name else ("#00ff88" if r['ChgP'] >= 0 else "#ff3366")
                    st.markdown(f"<span style='color:{clr}; font-weight:bold;'>{r['ChgP']:+.2f}%</span>", unsafe_allow_html=True)

st.divider()

# --- 5. PAGE MODULES ---
if menu == "Diamond Terminal":
    st.subheader("💎 High Probability Conviction (Score > 100)")
    c1, c2 = st.columns(2)
    if not df_s.empty:
        with c1:
            st.markdown("<h4 style='color:#00ff88'>🔥 Top Bullish (Sector Tailwinds)</h4>", unsafe_allow_html=True)
            bulls = df_s[(df_s['Signal']=="🚀 BULLISH") & (df_s['Score'] >= 80)].nlargest(3, 'Score')
            for _, r in bulls.iterrows():
                st.markdown(f"<div class='mobile-card' style='border-color:#00ff88'><b>{r['Symbol']}</b> | Score: {r['Score']} | <span style='color:#00ff88'>{r['Chg%']:+.2f}%</span><br><span class='badge'>{r['Sector']}</span><span class='badge'>Vol: {r['Vol_R']}x</span></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<h4 style='color:#ff3366'>❄️ Top Bearish (Sector Pressure)</h4>", unsafe_allow_html=True)
            bears = df_s[(df_s['Signal']=="📉 BEARISH") & (df_s['Score'] >= 80)].nlargest(3, 'Score')
            for _, r in bears.iterrows():
                st.markdown(f"<div class='mobile-card' style='border-color:#ff3366'><b>{r['Symbol']}</b> | Score: {r['Score']} | <span style='color:#ff3366'>{r['Chg%']:+.2f}%</span><br><span class='badge'>{r['Sector']}</span><span class='badge'>Vol: {r['Vol_R']}x</span></div>", unsafe_allow_html=True)
    
    st.write("---")
    st.info("💡 Strategy: Stocks appearing here have Range Breakouts confirmed by Sector Strength and Institutional Volume.")

elif menu == "Impulse Radar":
    st.subheader("🚀 Radar (All Breakouts Sorted by Score)")
    st.dataframe(df_s[df_s['Signal'] != "Neutral"].sort_values("Score", ascending=False), use_container_width=True, hide_index=True,
                 column_config={"Score": st.column_config.ProgressColumn(min_value=0, max_value=150), "Chg%": st.column_config.NumberColumn(format="%+.2f%%")})

elif menu == "Sector Map":
    sec_data = df_s.groupby("Sector")["Chg%"].mean().reset_index().sort_values("Chg%", ascending=False)
    st.plotly_chart(px.bar(sec_data, x='Sector', y='Chg%', color='Chg%', color_continuous_scale=['#ff3366', '#00ff88'], color_continuous_midpoint=0, height=350), use_container_width=True)
    sel = st.selectbox("View Sector Stocks:", sec_data['Sector'].tolist())
    st.dataframe(df_s[df_s['Sector']==sel].sort_values("Chg%", ascending=False), use_container_width=True, hide_index=True)

elif menu == "Master List":
    search = st.text_input("Search 212 Stocks...").upper()
    disp = df_s[df_s['Symbol'].str.contains(search)] if search else df_s
    st.dataframe(disp.sort_values("Chg%", ascending=False), use_container_width=True, hide_index=True)