import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- 1. SETTINGS ---
st.set_page_config(page_title="PRO-QUANT ELITE v6.0", layout="wide")

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass

local_css("style.css")
st_autorefresh(interval=3 * 60 * 1000, key="global_sync")

# --- 2. THE FULL 212 F&O DATABASE ---
SECTOR_MAP = {
    "BANKS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "AUBANK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "BANDHANBNK.NS", "INDUSINDBK.NS", "IDFC.NS", "BANKINDIA.NS", "CENTRALBK.NS", "IOB.NS", "UCOBANK.NS", "PSB.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS", "COFORGE.NS", "MPHASIS.NS", "TECHM.NS", "PERSISTENT.NS", "LTTS.NS", "BSOFT.NS", "KPITTECH.NS", "TATAELXSI.NS", "OFSS.NS", "CYIENT.NS"],
    "AUTO": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "BALKRISIND.NS", "BHARATFORG.NS", "ESCORTS.NS", "MRF.NS", "APOLLOTYRE.NS", "MOTHERSON.NS", "BOSCHLTD.NS", "EXIDEIND.NS", "AMARAJABAT.NS", "TIINDIA.NS"],
    "METALS": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS", "NATIONALUM.NS", "NMDC.NS", "HINDCOPPER.NS", "HINDZINC.NS", "RATNAMANI.NS"],
    "ENERGY/POWER": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "HINDPETRO.NS", "TATAPOWER.NS", "GAIL.NS", "IGL.NS", "MGL.NS", "PETRONET.NS", "GUJGASLTD.NS", "ADANIPOWER.NS", "ADANIGREEN.NS", "SUZLON.NS", "NHPC.NS", "SJVN.NS", "COALINDIA.NS"],
    "PHARMA": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "ALKEM.NS", "BIOCON.NS", "GLENMARK.NS", "GRANULES.NS", "IPCALAB.NS", "SYNGENE.NS", "TORNTPHARM.NS", "ZYDUSLIFE.NS", "ABBOTINDIA.NS", "METROPOLIS.NS", "LALPATHLAB.NS", "APOLLOHOSP.NS", "MAXHEALTH.NS", "MANAPPURAM.NS"],
    "INFRA/CONSTR": ["ULTRACEMCO.NS", "GRASIM.NS", "JKCEMENT.NS", "ACC.NS", "AMBUJACEM.NS", "LT.NS", "ADANIPORTS.NS", "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "ASTRAL.NS", "CUMMINSIND.NS", "CONCOR.NS", "BEL.NS", "BHEL.NS", "HAL.NS", "MAZDOCK.NS", "RVNL.NS", "IRCON.NS", "NBCC.NS", "COCHINSHIP.NS", "GMRINFRA.NS", "KNRCON.NS", "PNCINFRA.NS"],
    "FMCG/RETAIL": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TATACONSUM.NS", "COLPAL.NS", "GODREJCP.NS", "MARICO.NS", "UBL.NS", "MCDOWELL-N.NS", "JUBLFOOD.NS", "BALRAMCHIN.NS", "PAGEIND.NS", "TITAN.NS", "ASIANPAINT.NS", "BERGERPAINT.NS", "PIDILITIND.NS", "TRENT.NS", "ABFRL.NS", "VBL.NS", "NYKAA.NS", "ZOMATO.NS"],
    "FINANCE/NBFC": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "M&MFIN.NS", "PFC.NS", "REC.NS", "LICHSGFIN.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIPRULI.NS", "ICICIGI.NS", "PEL.NS", "ABCAPITAL.NS", "CANFINHOME.NS", "SHRIRAMFIN.NS", "SBICARD.NS", "POONAWALLA.NS", "MFSL.NS", "L&TFH.NS"],
    "CHEM/OTHERS": ["SRF.NS", "UPL.NS", "COROMANDEL.NS", "CHAMBLFERT.NS", "GNFC.NS", "DEEPAKNTR.NS", "ATUL.NS", "NAVINFLUOR.NS", "PIDILITIND.NS", "POLYCAB.NS", "DIXON.NS", "SYNGENE.NS", "INDIGO.NS", "IRCTC.NS", "IEX.NS", "PVRINOX.NS", "ZEEL.NS", "DELTACORP.NS", "IDEA.NS"]
}

ALL_STOCKS = [s for sub in SECTOR_MAP.values() for s in sub]
INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=120)
def fetch_master_data():
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

df_s, df_i = fetch_master_data()

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color:#58a6ff'>TERMINAL v6.0</h2>", unsafe_allow_html=True)
    menu = option_menu(None, ["Dashboard", "Sector Analysis", "F&O Watchlist"], icons=["speedometer", "bar-chart", "list"], default_index=0, styles={"nav-link-selected": {"background-color": "#238636"}})
    tz = pytz.timezone('Asia/Kolkata')
    st.info(f"Market: {'🟢 LIVE' if (now := datetime.now(tz)).weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")

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
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Top 3 Bullish (Vol Surge)")
        for _, r in df_s[df_s['Signal']=="🚀 BUY"].nlargest(3, 'VolRatio').iterrows():
            st.markdown(f"<div class='bull-card'><b>{r['Symbol']}</b> | ₹{r['LTP']} | <span style='color:#10b981'>+{r['Change(₹)']} ({r['Change(%)']}%)</span> | Vol: {r['VolRatio']}x</div>", unsafe_allow_html=True)
    with c2:
        st.subheader("📉 Top 3 Bearish (Vol Surge)")
        for _, r in df_s[df_s['Signal']=="📉 SELL"].nlargest(3, 'VolRatio').iterrows():
            st.markdown(f"<div class='bear-card'><b>{r['Symbol']}</b> | ₹{r['LTP']} | <span style='color:#f43f5e'>{r['Change(₹)']} ({r['Change(%)']}%)</span> | Vol: {r['VolRatio']}x</div>", unsafe_allow_html=True)

# --- 6. SECTOR ANALYSIS ---
elif menu == "Sector Analysis":
    st.subheader("🏗️ Multi-Color Sector Heatmap")
    sec_data = df_s.groupby("Sector")["Change(%)"].mean().reset_index().sort_values("Change(%)", ascending=False)
    
    fig = px.bar(sec_data, x='Sector', y='Change(%)', color='Change(%)', color_continuous_scale=['#f43f5e', '#10b981'], color_continuous_midpoint=0, text_auto='.2f')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="#8b949e", showlegend=False, height=400, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    sel_sec = st.selectbox("Click Sector to view stocks:", sec_data['Sector'].tolist())
    st.dataframe(df_s[df_s['Sector']==sel_sec].sort_values("Change(%)", ascending=False).style.format({"LTP": "{:.2f}", "Change(₹)": "{:+.2f}", "Change(%)": "{:+.2f}%"}).applymap(lambda x: 'background-color: rgba(16, 185, 129, 0.2); color: #10b981' if isinstance(x, (int, float)) and x > 0 else 'background-color: rgba(244, 63, 94, 0.2); color: #f43f5e' if isinstance(x, (int, float)) and x < 0 else '', subset=['Change(%)', 'Change(₹)']), use_container_width=True, hide_index=True)

# --- 7. WATCHLIST ---
elif menu == "F&O Watchlist":
    st.subheader("📋 Full F&O Watchlist (~212 Stocks)")
    search = st.text_input("🔍 Search Asset...", placeholder="e.g. RELIANCE").upper()
    disp = df_s[df_s['Symbol'].str.contains(search)] if search else df_s
    st.dataframe(disp.sort_values("Change(%)", ascending=False), use_container_width=True, hide_index=True, column_config={"Change(%)": st.column_config.NumberColumn(format="%+.2f%%"), "VolRatio": st.column_config.ProgressColumn(min_value=0, max_value=3)})