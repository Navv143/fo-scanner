import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# --- MODULE 0: CONFIG & UI ---
st.set_page_config(page_title="PRO-QUANT ELITE v16", layout="wide", initial_sidebar_state="expanded")

def load_ui():
    try:
        with open("style.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        st.markdown("<style>.main {background-color: #05070a; color: white;}</style>", unsafe_allow_html=True)

load_ui()
st_autorefresh(interval=3 * 60 * 1000, key="pro_sync")

# --- DATA LISTS ---
INDICES = {
    "NIFTY 50": "^NSEI", 
    "BANK NIFTY": "^NSEBANK", 
    "FIN NIFTY": "NIFTY_FIN_SERVICE.NS",
    "SENSEX": "^BSESN",
    "MIDCAP": "NIFTY_MID_SELECT.NS",
    "INDIA VIX": "^INDIAVIX"
}

SECTOR_MAP = {
    "METALS": ["VEDL.NS", "HINDCOPPER.NS", "NATIONALUM.NS", "TATASTEEL.NS"],
    "BANKS": ["AXISBANK.NS", "INDUSINDBK.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS"],
    "ENERGY/POWER": ["MCX.NS", "ONGC.NS", "NTPC.NS", "RELIANCE.NS"],
    "PHARMA": ["LAURUSLABS.NS", "SUNPHARMA.NS", "CIPLA.NS"],
    "INFRA": ["DELTACORP.NS", "INDUSTOWER.NS", "DLF.NS", "RVNL.NS"],
    "FMCG/RETAIL": ["DALBHARAT.NS", "ITC.NS", "ZOMATO.NS"],
    "FINANCE": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS"],
    "OTHERS": ["IDEA.NS", "UPL.NS", "IEX.NS"]
}

ALL_STOCKS = [s for sub in SECTOR_MAP.values() for s in sub]

# --- 3. DATA ENGINES ---

@st.cache_data(ttl=120)
def fetch_master_data():
    all_tkr = list(set(ALL_STOCKS + list(INDICES.values())))
    raw = yf.download(all_tkr, period="10d", interval="1d", group_by='ticker', progress=False)
    s_rows, i_rows = [], []
    for t in all_tkr:
        try:
            df = raw[t].dropna()
            if len(df) < 2: continue
            curr, prev = df.iloc[-1], df.iloc[-2]
            p, prev_p = curr['Close'], prev['Close']
            chg_p = ((p - prev_p)/prev_p)*100
            if t in ALL_STOCKS:
                vr = curr['Volume']/prev['Volume'] if prev['Volume'] > 0 else 0
                sig = "🚀 BULLISH" if p > prev['High'] else "📉 BEARISH" if p < prev['Low'] else "Neutral"
                s_rows.append({"Symbol": t.replace(".NS",""), "LTP": round(p, 2), "Chg%": round(chg_p, 2), "Signal": sig, "Vol_R": round(vr, 2)})
            elif t in INDICES.values():
                name = [k for k, v in INDICES.items() if v == t][0]
                i_rows.append({"Name": name, "Price": round(p, 2), "ChgP": round(chg_p, 2)})
        except: continue
    return pd.DataFrame(s_rows), pd.DataFrame(i_rows)

def get_index_strategy(ticker_symbol):
    try:
        # Fetch 5-minute data for the current day
        df = yf.download(ticker_symbol, period="2d", interval="15m", progress=False)
        if df.empty: return "NO DATA", "WAIT", 0
        
        ltp = df['Close'].iloc[-1]
        open_price = df['Open'].iloc[0]
        high_15m = df['High'].iloc[0]
        low_15m = df['Low'].iloc[0]
        
        # Simple VWAP Approximation
        vwap = (df['Close'] * df['Volume']).sum() / df['Volume'].sum()
        
        # Strategy Logic
        if ltp > high_15m and ltp > vwap:
            action = "🚀 BUY CALL"
            strength = "STRONG BULLISH"
        elif ltp < low_15m and ltp < vwap:
            action = "📉 BUY PUT"
            strength = "STRONG BEARISH"
        else:
            action = "⏸️ NO TRADE"
            strength = "SIDEWAYS"
            
        return action, strength, round(ltp, 2)
    except:
        return "ERROR", "N/A", 0

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color:#00d4ff'>QUANT ELITE v16</h2>", unsafe_allow_html=True)
    menu = option_menu(None, ["Terminal", "Index Pro Strategy", "Impulse Radar", "Sector Map"], 
                       icons=["speedometer", "cpu", "lightning", "grid"], default_index=0)
    st.info(f"Market Status: {'🟢 LIVE' if (now := datetime.now(pytz.timezone('Asia/Kolkata'))).weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)) else '🔴 CLOSED'}")

df_s, df_i = fetch_master_data()

# --- 5. PAGE MODULES ---

if menu == "Terminal":
    # (Existing Indices Display)
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

elif menu == "Index Pro Strategy":
    st.subheader("🤖 Index Option Auto-Strategy")
    st.write("Calculates Entry based on 15-min Range + Trend Confluence.")
    
    target_indices = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS"}
    
    for name, tkr in target_indices.items():
        action, trend, price = get_index_strategy(tkr)
        
        # Visual Card for Strategy
        card_bg = "#10b98122" if "CALL" in action else "#f43f5e22" if "PUT" in action else "#30363d"
        border_clr = "#10b981" if "CALL" in action else "#f43f5e" if "PUT" in action else "#8b949e"
        
        st.markdown(f"""
        <div style='background:{card_bg}; border: 1px solid {border_clr}; padding:20px; border-radius:12px; margin-bottom:15px;'>
            <h3 style='margin:0; color:white;'>{name}</h3>
            <p style='color:#8b949e; margin-bottom:10px;'>LTP: ₹{price}</p>
            <div style='font-size:24px; font-weight:bold; color:{border_clr};'>{action}</div>
            <p style='margin-top:5px; font-size:12px;'>Trend: {trend} | Strategy: Opening Range Breakout</p>
        </div>
        """, unsafe_allow_html=True)
        
        if action != "⏸️ NO TRADE":
            strike = round(price / 50 if "NIFTY 50" in name else price / 100) * (50 if "NIFTY 50" in name else 100)
            st.success(f"💡 Recommended Strike: {strike} {'CE' if 'CALL' in action else 'PE'}")

elif menu == "Impulse Radar":
    st.subheader("🚀 Radar (Breakouts Only)")
    st.dataframe(df_s[df_s['Signal'] != "Neutral"].sort_values("Vol_R", ascending=False), use_container_width=True, hide_index=True)

elif menu == "Sector Map":
    sec_data = df_s.groupby("Symbol").first() # Simplification for demo
    st.info("Sector Logic is processing... Refresh in 1 min.")