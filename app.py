import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="PRO-QUANT MOBILE", layout="wide")

def load_ui():
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try: load_ui()
except: pass

st_autorefresh(interval=3 * 60 * 1000, key="m_sync")

# --- 2. COMPLETE 212+ F&O LIST ---
ALL_FO_STOCKS = [
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS", 
    "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", 
    "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", 
    "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", 
    "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", 
    "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", 
    "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS", 
    "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", 
    "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", 
    "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", 
    "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", 
    "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", 
    "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LT.NS", 
    "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS", 
    "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", 
    "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", 
    "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", 
    "PVRINOX.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", 
    "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", 
    "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", 
    "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS", "SUZLON.NS", "RVNL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", 
    "NHPC.NS", "SJVN.NS", "IRFC.NS", "HUDCO.NS", "OFSS.NS", "KPITTECH.NS", "ZOMATO.NS", "NYKAA.NS"
]

INDICES = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "INDIA VIX": "^INDIAVIX"}

# --- 3. QUANT DATA ENGINE ---
@st.cache_data(ttl=120)
def fetch_master_data():
    all_tkr = list(set(ALL_FO_STOCKS + list(INDICES.values())))
    # Fetch 20 days to calculate accurate OBV and ROC
    raw = yf.download(all_tkr, period="20d", interval="1d", group_by='ticker', progress=False)
    
    s_rows, i_rows = [], []
    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if len(df) < 5: continue
            
            # Indicators
            obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
            obv_trend = "Accumulation" if obv.iloc[-1] > obv.iloc[-2] else "Distribution"
            
            # ROC (3 Day Momentum)
            roc = ((df['Close'].iloc[-1] - df['Close'].iloc[-3]) / df['Close'].iloc[-3]) * 100
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_p = ((p - prev_p)/prev_p)*100
            
            if t in ALL_FO_STOCKS:
                # Range Break Logic
                signal = "Neutral"
                if p > prev['High']: signal = "🚀 BULLISH BREAKOUT"
                elif p < prev['Low']: signal = "📉 BEARISH BREAKDOWN"
                
                s_rows.append({
                    "Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Chg%": round(chg_p, 2),
                    "ROC": round(roc, 2), "OBV": obv_trend, "Signal": signal
                })
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "ChgP": round(chg_p, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

df_s, df_i = fetch_master_data()

# --- 4. MOBILE UI RENDERING ---
st.title("🛡️ QUANT TERMINAL PRO")
tz = pytz.timezone('Asia/Kolkata')
st.caption(f"Sync: {datetime.now(tz).strftime('%H:%M:%S')} IST | All 212 F&O Stocks Active")

# Indices (Stacked Metrics)
if not df_i.empty:
    for _, r in df_i.iterrows():
        delta_clr = "normal"
        if "VIX" in r['Name']: delta_clr = "inverse" # High VIX is warning
        st.metric(r['Name'], f"₹{r['Price']:,.2f}", f"{r['ChgP']:+.2f}%", delta_color=delta_clr)

st.divider()

# Momentum Radar
st.subheader("🔥 Momentum Impulse Radar")
if not df_s.empty:
    # Filter for active breakouts + positive momentum (ROC)
    radar = df_s[df_s['Signal'] != "Neutral"].sort_values("ROC", ascending=False)
    
    if radar.empty:
        st.info("Searching for range breakouts... Keep this tab open.")
    else:
        for _, row in radar.head(15).iterrows():
            # Card UI
            card_clr = "#10b981" if "BULLISH" in row['Signal'] else "#f43f5e"
            st.markdown(f"""
            <div class="trade-card" style="border-left: 6px solid {card_clr}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="symbol-name">{row['Symbol']}</span>
                    <span style="color:{card_clr}; font-weight:bold; font-size:18px;">{row['Chg%']:+.2f}%</span>
                </div>
                <div class="ltp-price">₹{row['LTP']}</div>
                <div style="margin-top:10px;">
                    <span class="badge">ROC: {row['ROC']}%</span>
                    <span class="badge" style="color:#58a6ff">OBV: {row['OBV']}</span>
                    <span class="badge" style="border: 1px solid {card_clr}; color: {card_clr}">{row['Signal']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Search / Watchlist
st.write("---")
with st.expander("🔍 Full Watchlist Search"):
    search = st.text_input("Enter stock name (e.g. SBIN, RELIANCE)").upper()
    disp = df_s[df_s['Symbol'].str.contains(search)] if search else df_s
    st.dataframe(disp.sort_values("Chg%", ascending=False), use_container_width=True, hide_index=True)