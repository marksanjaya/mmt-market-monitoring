import streamlit as st

st.set_page_config(
    page_title="MMT - Market Monitoring Tools",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

from modules.watchlist import render_watchlist
from modules.technical import render_technical
from modules.fundamental import render_fundamental
from modules.foreign_flow import render_foreign_flow

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📈 MMT")
    st.markdown("Market Monitoring Tools")
    st.divider()

    mode = st.radio(
        "Mode",
        ["Trader", "Investor"],
        index=0
    )

    st.divider()
    st.markdown("**Watchlist**")
    TICKERS = ["BBCA.JK", "BBRI.JK", "GOTO.JK", "ANTM.JK", "BMRI.JK", "BJTM.JK"]
    selected = st.multiselect(
        "Pilih saham",
        TICKERS,
        default=TICKERS
    )

    st.divider()
    st.caption("Data: yfinance · IDX public")
    st.caption("v0.1 · Phase 1")

# --- Main content ---
if not selected:
    st.warning("Pilih minimal satu saham dari sidebar.")
    st.stop()

if mode == "Trader":
    tab1, tab2, tab3 = st.tabs(["Watchlist", "Technical", "Foreign Flow"])
    with tab1:
        render_watchlist(selected)
    with tab2:
        render_technical(selected)
    with tab3:
        render_foreign_flow(selected)

elif mode == "Investor":
    tab1, tab2 = st.tabs(["Watchlist", "Fundamental"])
    with tab1:
        render_watchlist(selected)
    with tab2:
        render_fundamental(selected)