import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. SETTINGS & CSS ---
st.set_page_config(page_title="PRO-QUANT ELITE v7.1", layout="wide")

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass

local_css("style.css")
st_autorefresh(interval=3 * 60 * 1000, key="global_sync")

# --- 2. THE COMPLETE 212 F&O DATABASE (Corrected & Categorized) ---
SECTOR_MAP = {
    "BANKS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "AUBANK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "BANDHANBNK.NS", "INDUSINDBK.NS", "IDFC.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS", "COFORGE.NS", "MPHASIS.NS", "TECHM.NS", "PERSISTENT.NS", "LTTS.NS", "BSOFT.NS", "KPITTECH.NS", "OFSS.NS"],
    "AUTO": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "BALKRISIND.NS", "BHARATFORG.NS", "ESCORTS.NS", "MOTHERSON.NS"],
    "METALS": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS", "NATIONALUM.NS", "NMDC.NS", "HINDCOPPER.NS"],
    "ENERGY/POWER": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "HINDPETRO.NS", "TATAPOWER.NS", "GAIL.NS", "SUZLON.NS", "COALINDIA.NS", "NHPC.NS", "SJVN.NS", "RECLTD.NS", "PFC.NS"],
    "PHARMA": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "ALKEM.NS", "BIOCON.NS", "GLENMARK.NS", "TORNTPHARM.NS", "ZYDUSLIFE.NS", "APOLLOHOSP.NS"],
    "CEMENT/INFRA": ["ULTRACEMCO.NS", "GRASIM.NS", "JKCEMENT.NS", "ACC.NS", "AMBUJACEM.NS", "LT.NS", "ADANIPORTS.NS", "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "BEL.NS", "BHEL.NS", "HAL.NS", "MAZDOCK.NS", "RVNL.NS", "IRCTC.NS"],
    "FMCG/RETAIL": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TATACONSUM.NS", "COLPAL.NS", "TITAN.NS", "ASIANPAINT.NS", "TRENT.NS", "ABFRL.NS", "ZOMATO.NS", "VBL.NS", "JUBLFOOD.NS"],
    "NBFC/FINANCE": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "M&MFIN.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIGI.NS", "SHRIRAMFIN.NS", "L&TFH.NS", "ABCAPITAL.NS", "MNAPPURAM.NS"],
    "OTHERS": ["SRF.NS", "UPL.NS", "CHAMBLFERT.NS", "DEEPAKNTR.NS", "NAVINFLUOR.NS", "POLYCAB.NS", "DIXON.NS", "INDIGO.NS", "IEX.NS", "PVRINOX.NS", "ZEEL.NS", "IDEA.NS", "MCX.NS"]
}

ALL_STOCKS = [s for sub in SECTOR_MAP.values() for s in sub]
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}

# --- 3. THE VOLUME SCORING ENGINE ---
def calculate_volume_score(ratio):
    if ratio >= 3.0: return 30
    elif ratio >= 2.5: return 27
    elif ratio >= 2.0: return 24
    elif ratio >= 1.75: return 20
    elif ratio >= 1.5: return 16
    elif ratio >= 1.25: return 12
    elif ratio >= 1.1: return 8
    elif ratio >= 1.0: return 4
    return 0

@st.cache_data(ttl=120)
def fetch_master_data():
    all_tkr = list(set(ALL_STOCKS + list(INDICES.values())))
    raw = yf.download(all_tkr, period="7d", interval="1d", group_by='ticker', progress=False)
    
    s_rows, i_rows = [], []
    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if df.empty or len(df) < 2: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_v, chg_p = p - prev_p, ((p - prev_p)/prev_p)*100
            
            if t in ALL_STOCKS:
                vr = curr['Volume']/prev['Volume'] if prev['Volume']>0 else 0
                v_score = calculate_volume_score(vr)
                sig = "🚀 BUY" if p > prev['High'] else "📉 SELL" if p < prev['Low'] else "Neutral"
                sec = next((k for k, v in SECTOR_MAP.items() if t in v), "Other")
                s_rows.append({
                    "Sector": sec, "Symbol": t.replace(".NS",""), 
                    "LTP": round(p, 2), "Change(₹)": round(chg_v, 2), "Change(%)": round(chg_p, 2), 
                    "Vol_Ratio": round(vr, 2), "Vol_Score": v_score, "Signal": sig
                })
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "ChgV": round(chg_v, 2), "ChgP": round(chg_p, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

df_s, df_i = fetch_master_data()

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color:#58a6ff'>TERMINAL v7.1</h2>", unsafe_allow_html=True)
    menu = option_menu(None, ["Dashboard", "Sector Pulse", "Volume Scoreboard", "Watchlist"], 
                       icons=["speedometer", "pie-chart", "star-fill", "list"], default_index=0)
    tz = pytz.timezone('Asia/Kolkata')
    st.info(f"Market Status: {'🟢 LIVE' if (now := datetime.now(tz)).weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")

# --- 5. DASHBOARD ---
if menu == "Dashboard":
    cols = st.columns(len(df_i))
    for i, r in df_i.iterrows():
        with cols[i]:
            st.markdown(f"**{r['Name']}**")
            st.markdown(f"<div class='price-blink'>₹{r['Price']:,.2f}</div>", unsafe_allow_html=True)
            clr = "#10b981" if r['ChgP'] >= 0 else "#f43f5e"
            st.markdown(f"<span style='color:{clr}; font-weight:bold;'>{r['ChgV']:+.2f} ({r['ChgP']:+.2f}%)</span>", unsafe_allow_html=True)

    st.divider()
    
    st.subheader("🎯 Institutional Conviction (Score > 20 Only)")
    c1, c2 = st.columns(2)
    with c1:
        st.write("🟢 **Strongest Buy Setup** (Vol Score > 20)")
        # STRICT FILTER: SIGNAL IS BUY AND SCORE > 20
        bulls = df_s[(df_s['Signal']=="🚀 BUY") & (df_s['Vol_Score'] > 20)].nlargest(3, 'Vol_Score')
        if not bulls.empty:
            for _, r in bulls.iterrows():
                st.markdown(f"<div class='bull-card'><b>{r['Symbol']}</b> | Score: {r['Vol_Score']} | ₹{r['LTP']} | <span style='color:#10b981'>+{r['Change(%)']}%</span></div>", unsafe_allow_html=True)
        else: st.info("No stocks currently meet Buy Momentum + Vol Score > 20")
            
    with c2:
        st.write("🔴 **Strongest Sell Setup** (Vol Score > 20)")
        # STRICT FILTER: SIGNAL IS SELL AND SCORE > 20
        bears = df_s[(df_s['Signal']=="📉 SELL") & (df_s['Vol_Score'] > 20)].nlargest(3, 'Vol_Score')
        if not bears.empty:
            for _, r in bears.iterrows():
                st.markdown(f"<div class='bear-card'><b>{r['Symbol']}</b> | Score: {r['Vol_Score']} | ₹{r['LTP']} | <span style='color:#f43f5e'>{r['Change(%)']}%</span></div>", unsafe_allow_html=True)
        else: st.info("No stocks currently meet Sell Momentum + Vol Score > 20")

# --- 6. SECTOR PULSE (FIXED) ---
elif menu == "Sector Pulse":
    st.subheader("🏗️ Interactive Sector Heatmap")
    
    # Calculate Sector averages
    sec_data = df_s.groupby("Sector")["Change(%)"].mean().reset_index().sort_values("Change(%)", ascending=False)
    
    # Chart
    fig = px.bar(sec_data, x='Sector', y='Change(%)', color='Change(%)', 
                 color_continuous_scale=['#f43f5e', '#10b981'], 
                 color_continuous_midpoint=0, text_auto='.2f')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="#8b949e", showlegend=False, height=400, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    # Drill down
    sel_sec = st.selectbox("Select Sector to explore:", sec_data['Sector'].tolist())
    st.markdown(f"### Stocks in {sel_sec}")
    st.dataframe(df_s[df_s['Sector']==sel_sec].sort_values("Change(%)", ascending=False).style.format({"LTP": "{:.2f}", "Change(₹)": "{:+.2f}", "Change(%)": "{:+.2f}%"}).applymap(lambda x: 'background-color: rgba(16, 185, 129, 0.2); color: #10b981' if isinstance(x, (int, float)) and x > 0 else 'background-color: rgba(244, 63, 94, 0.2); color: #f43f5e' if isinstance(x, (int, float)) and x < 0 else '', subset=['Change(%)', 'Change(₹)']), use_container_width=True, hide_index=True)

# --- 7. VOLUME SCOREBOARD ---
elif menu == "Volume Scoreboard":
    st.subheader("📊 Full Volume Intensity Analysis")
    st.dataframe(df_s.sort_values("Vol_Score", ascending=False), use_container_width=True, hide_index=True, 
                 column_config={
                     "Vol_Score": st.column_config.ProgressColumn("Volume Score", min_value=0, max_value=30, format="%d pts"),
                     "Change(%)": st.column_config.NumberColumn(format="%+.2f%%")
                 })

elif menu == "Watchlist":
    st.subheader("📋 Master F&O Monitor")
    search = st.text_input("🔍 Quick Search Stock...").upper()
    disp = df_s[df_s['Symbol'].str.contains(search)] if search else df_s
    st.dataframe(disp.sort_values("Vol_Score", ascending=False), use_container_width=True, hide_index=True)