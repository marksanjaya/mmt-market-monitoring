import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="MMT - Market Monitoring Tools",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

from modules.watchlist import render_watchlist
from modules.technical import render_technical
from modules.fundamental import render_fundamental
from modules.screener import render_trader_screener, render_investor_screener


@st.cache_data(ttl=3600)
def validate_ticker(code: str):
    """
    Cek apakah ticker valid di yfinance. Return (is_valid, ticker_full, name).
    """
    code = code.strip().upper().replace(".JK", "")
    if not code:
        return False, None, None
    ticker_full = f"{code}.JK"
    try:
        t = yf.Ticker(ticker_full)
        info = t.info
        name = info.get("shortName") or info.get("longName")
        if name and info.get("regularMarketPrice") is not None:
            return True, ticker_full, name
        return False, None, None
    except Exception:
        return False, None, None


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
    DEFAULT_TICKERS = ["BBCA.JK", "BBRI.JK", "GOTO.JK", "ANTM.JK", "BMRI.JK", "BJTM.JK"]

    # Saham hasil search disimpan di session_state biar persist selama sesi
    if "extra_tickers" not in st.session_state:
        st.session_state.extra_tickers = []

    selected = st.multiselect(
        "Pilih saham",
        DEFAULT_TICKERS + st.session_state.extra_tickers,
        default=DEFAULT_TICKERS
    )

    st.divider()
    st.markdown("**Cari saham lain**")
    search_input = st.text_input(
        "Kode saham (contoh: TLKM)",
        placeholder="Ketik kode saham...",
        label_visibility="collapsed"
    )

    if search_input:
        is_valid, ticker_full, name = validate_ticker(search_input)
        if is_valid:
            st.success(f"✓ {name} ({ticker_full.replace('.JK','')})")
            if st.button("➕ Tambah ke watchlist", use_container_width=True):
                if ticker_full not in st.session_state.extra_tickers and ticker_full not in DEFAULT_TICKERS:
                    st.session_state.extra_tickers.append(ticker_full)
                    st.rerun()
        else:
            st.error("Kode saham tidak ditemukan di IHSG.")

    if st.session_state.extra_tickers:
        st.caption("Saham tambahan: " + ", ".join(t.replace(".JK", "") for t in st.session_state.extra_tickers))
        if st.button("🗑️ Reset saham tambahan", use_container_width=True):
            st.session_state.extra_tickers = []
            st.rerun()

    st.divider()
    st.caption("Data: yfinance · IDX public")
    st.caption("v0.2 · Phase 2")

# --- Main content ---
if not selected:
    st.warning("Pilih minimal satu saham dari sidebar.")
    st.stop()

if mode == "Trader":
    tab1, tab2, tab3 = st.tabs(["Watchlist", "Technical", "Screener"])
    with tab1:
        render_watchlist(selected)
    with tab2:
        render_technical(selected)
    with tab3:
        render_trader_screener(selected)

elif mode == "Investor":
    tab1, tab2, tab3 = st.tabs(["Watchlist", "Fundamental", "Screener"])
    with tab1:
        render_watchlist(selected)
    with tab2:
        render_fundamental(selected)
    with tab3:
        render_investor_screener(selected)