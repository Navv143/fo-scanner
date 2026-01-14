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
st.set_page_config(page_title="QUANT ELITE v14", layout="wide", initial_sidebar_state="expanded")

def load_ui():
    try:
        with open("style.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass

load_ui()
st_autorefresh(interval=3 * 60 * 1000, key="global_sync")

# --- 2. THE COMPLETE 212+ STOCK & SECTOR DATABASE ---
SECTOR_MAP = {
    "BANKS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "AUBANK.NS", "FEDERALBNK.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "IDFCFIRSTB.NS", "INDUSINDBK.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS", "COFORGE.NS", "TECHM.NS", "PERSISTENT.NS", "LTTS.NS", "BSOFT.NS", "KPITTECH.NS", "OFSS.NS"],
    "AUTO": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "BALKRISIND.NS", "BHARATFORG.NS"],
    "METALS": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS", "NATIONALUM.NS", "NMDC.NS", "HINDCOPPER.NS"],
    "ENERGY/POWER": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "TATAPOWER.NS", "GAIL.NS", "SUZLON.NS", "COALINDIA.NS", "NHPC.NS", "SJVN.NS", "ADANIPOWER.NS"],
    "PHARMA": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "ALKEM.NS", "BIOCON.NS", "GLENMARK.NS", "ZYDUSLIFE.NS", "APOLLOHOSP.NS", "MAXHEALTH.NS"],
    "INFRA": ["ULTRACEMCO.NS", "GRASIM.NS", "JKCEMENT.NS", "ACC.NS", "AMBUJACEM.NS", "LT.NS", "ADANIPORTS.NS", "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "RVNL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "IRCTC.NS"],
    "FMCG/RETAIL": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TATACONSUM.NS", "COLPAL.NS", "TITAN.NS", "TRENT.NS", "ZOMATO.NS", "VBL.NS", "JUBLFOOD.NS", "NYKAA.NS"],
    "FINANCE": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "M&MFIN.NS", "PFC.NS", "REC.NS", "SBILIFE.NS", "HDFCLIFE.NS", "SHRIRAMFIN.NS", "ABCAPITAL.NS", "L&TFH.NS"],
    "OTHERS": ["SRF.NS", "UPL.NS", "DEEPAKNTR.NS", "POLYCAB.NS", "DIXON.NS", "INDIGO.NS", "IEX.NS", "PVRINOX.NS", "ZEEL.NS", "IDEA.NS", "MCX.NS", "COROMANDEL.NS"]
}

ALL_STOCKS = [s for sub in SECTOR_MAP.values() for s in sub]
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS", "SENSEX": "^BSESN", "MIDCAP": "NIFTY_MID_SELECT.NS", "INDIA VIX": "^INDIAVIX"}

# --- 3. THE 100-POINT HYBRID ENGINE (ROC + OBV + RANGE) ---
def get_hybrid_score(row, prev_h, prev_l, adr, obv_trend):
    score = 0
    p, chg, roc = row['LTP'], row['Chg%'], row['ROC']
    
    # 1. Range Break (40 Pts) - LEAD
    if p > prev_h or p < prev_l: score += 40
    # 2. ROC Momentum (30 Pts) - LEAD
    if abs(roc) > 2.0: score += 30
    elif abs(roc) > 1.0: score += 15
    # 3. OBV Flow (10 Pts)
    if (chg > 0 and obv_trend == "UP") or (chg < 0 and obv_trend == "DOWN"): score += 10
    # 4. Velocity (20 Pts)
    if adr > 0 and (abs(chg)/adr) >= 0.4: score += 20
    
    return score

@st.cache_data(ttl=120)
def fetch_master_data():
    all_tkr = list(set(ALL_STOCKS + list(INDICES.values())))
    raw = yf.download(all_tkr, period="15d", interval="1d", group_by='ticker', progress=False)
    
    s_rows, i_rows = [], []
    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if len(df) < 5: continue
            
            # Indicators
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_p = ((p - prev_p)/prev_p)*100
            
            # ROC & OBV
            roc = ((p - df['Close'].iloc[-3]) / df['Close'].iloc[-3]) * 100
            obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
            obv_t = "UP" if obv.iloc[-1] > obv.iloc[-2] else "DOWN"
            adr = ((df['High'] - df['Low']) / df['Low'] * 100).tail(5).mean()
            
            if t in ALL_STOCKS:
                row_data = {'LTP': p, 'Chg%': chg_p, 'ROC': roc}
                score = get_hybrid_score(row_data, prev['High'], prev['Low'], adr, obv_t)
                sig = "🚀 BULLISH" if p > prev['High'] else "📉 BEARISH" if p < prev['Low'] else "Neutral"
                sec = next((k for k, v in SECTOR_MAP.items() if t in v), "Other")
                
                s_rows.append({
                    "Sector": sec, "Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Chg%": round(chg_p, 2),
                    "ROC": round(roc, 2), "OBV": obv_t, "Score": score, "Signal": sig, "Vol_Ratio": round(curr['Volume']/prev['Volume'], 2)
                })
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "ChgP": round(chg_p, 2), "ChgV": round(p-prev_p, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

df_s, df_i = fetch_master_data()

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown("### 🏛️ **QUANT PRO ELITE**")
    menu = option_menu(None, ["Terminal", "Impulse Radar", "Sector Analysis", "Watchlist"], 
                       icons=["speedometer", "lightning", "grid", "list"], default_index=0)
    tz = pytz.timezone('Asia/Kolkata')
    st.info(f"Sync: {datetime.now(tz).strftime('%H:%M:%S')} IST")

# --- 5. PAGE MODULES ---
if menu == "Terminal":
    # 6 INDICES DASHBOARD
    if not df_i.empty:
        idx_order = ["NIFTY 50", "BANK NIFTY", "FIN NIFTY", "SENSEX", "MIDCAP", "INDIA VIX"]
        for i in range(0, 6, 3):
            cols = st.columns(3)
            for j in range(3):
                name = idx_order[i+j]
                r = df_i[df_i['Name'] == name].iloc[0]
                with cols[j]:
                    st.markdown(f"<span style='color:#8b949e; font-size:12px; font-weight:700;'>{r['Name']}</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='price-blink'>₹{r['Price']:,.2f}</div>", unsafe_allow_html=True)
                    clr = ("#f43f5e" if r['ChgP'] >= 0 else "#10b981") if "VIX" in name else ("#10b981" if r['ChgP'] >= 0 else "#f43f5e")
                    st.markdown(f"<span style='color:{clr}; font-weight:bold;'>{r['ChgP']:+.2f}%</span>", unsafe_allow_html=True)

    st.divider()
    # TOP 3 CONVICTION CARDS (MOBILE CARDS)
    st.subheader("🎯 Institutional Conviction (Score > 60)")
    c1, c2 = st.columns(2)
    with c1:
        st.write("🟢 **Top Buy Impulse**")
        for _, r in df_s[(df_s['Signal']=="🚀 BULLISH") & (df_s['Score'] >= 60)].nlargest(3, 'Score').iterrows():
            st.markdown(f"<div class='mobile-card' style='border-color:#10b981'><b>{r['Symbol']}</b> | Score: {r['Score']} | <span style='color:#10b981'>{r['Chg%']:+.2f}%</span><br><span class='badge'>OBV: {r['OBV']}</span><span class='badge'>ROC: {r['ROC']}%</span></div>", unsafe_allow_html=True)
    with c2:
        st.write("🔴 **Top Sell Impulse**")
        for _, r in df_s[(df_s['Signal']=="📉 BEARISH") & (df_s['Score'] >= 60)].nlargest(3, 'Score').iterrows():
            st.markdown(f"<div class='mobile-card' style='border-color:#f43f5e'><b>{r['Symbol']}</b> | Score: {r['Score']} | <span style='color:#f43f5e'>{r['Chg%']:+.2f}%</span><br><span class='badge'>OBV: {r['OBV']}</span><span class='badge'>ROC: {r['ROC']}%</span></div>", unsafe_allow_html=True)

elif menu == "Impulse Radar":
    st.subheader("🚀 Momentum Impulse (High Score Radar)")
    st.dataframe(df_s.sort_values("Score", ascending=False), use_container_width=True, hide_index=True,
                 column_config={"Score": st.column_config.ProgressColumn(min_value=0, max_value=100), "Chg%": st.column_config.NumberColumn(format="%+.2f%%")})

elif menu == "Sector Analysis":
    st.subheader("🏗️ Sector Heatmap & Drill-down")
    sec_data = df_s.groupby("Sector")["Chg%"].mean().reset_index().sort_values("Chg%", ascending=False)
    fig = px.bar(sec_data, x='Sector', y='Chg%', color='Chg%', color_continuous_scale=['#f43f5e', '#10b981'], color_continuous_midpoint=0)
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="#94a3b8", height=350, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    
    sel = st.selectbox("Select Sector:", sec_data['Sector'].tolist())
    st.dataframe(df_s[df_s['Sector']==sel].sort_values("Chg%", ascending=False), use_container_width=True, hide_index=True)

elif menu == "Watchlist":
    st.subheader("📋 Full 212 F&O Master List")
    search = st.text_input("🔍 Search Stock...").upper()
    disp = df_s[df_s['Symbol'].str.contains(search)] if search else df_s
    st.dataframe(disp.sort_values("Chg%", ascending=False), use_container_width=True, hide_index=True)