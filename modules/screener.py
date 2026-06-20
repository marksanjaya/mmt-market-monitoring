import streamlit as st
import pandas as pd
from utils.fetcher import get_quick_stats, get_price_data, get_fundamental
from utils.indicators import (
    get_rsi_signal, get_ma_signal, enrich_df,
    get_valuation_label, get_historical_valuation_series
)


def render_trader_screener(tickers: list):
    st.subheader("Screener — Trader")
    st.caption("Pilih kriteria, MMT cariin saham yang cocok dari watchlist lo.")

    col1, col2, col3 = st.columns(3)
    with col1:
        rsi_filter = st.multiselect(
            "RSI Signal",
            ["Oversold", "Neutral", "Overbought"],
            default=[]
        )
    with col2:
        ma_filter = st.multiselect(
            "MA Signal",
            ["Golden Cross", "Bullish", "Bearish", "Death Cross"],
            default=[]
        )
    with col3:
        vol_filter = st.checkbox("Volume spike (≥ 2x rata-rata)", value=False)

    if not rsi_filter and not ma_filter and not vol_filter:
        st.info("Pilih minimal satu kriteria di atas buat mulai screening.")
        return

    rows = []
    with st.spinner("Scanning watchlist..."):
        for ticker in tickers:
            stats = get_quick_stats(ticker)
            if not stats:
                continue

            df = get_price_data(ticker, period="3mo")
            df = enrich_df(df)
            if df.empty:
                continue

            rsi_val = df["RSI"].iloc[-1]
            rsi_label, _ = get_rsi_signal(rsi_val)
            ma_label, _ = get_ma_signal(df)
            vol_ratio = stats.get("vol_ratio")
            is_spike = vol_ratio is not None and vol_ratio >= 2.0

            # Cek kecocokan tiap kriteria yang aktif
            match_rsi = (not rsi_filter) or (rsi_label in rsi_filter)
            match_ma = (not ma_filter) or (ma_label in ma_filter)
            match_vol = (not vol_filter) or is_spike

            if match_rsi and match_ma and match_vol:
                rows.append({
                    "Ticker": stats.get("ticker"),
                    "Nama": stats.get("name"),
                    "Harga (IDR)": stats.get("price"),
                    "% Change": stats.get("pct_change"),
                    "RSI 14": round(rsi_val, 1) if rsi_val else None,
                    "RSI Signal": rsi_label,
                    "MA Signal": ma_label,
                    "Vol Ratio": vol_ratio,
                })

    if not rows:
        st.warning("Tidak ada saham di watchlist yang cocok dengan kriteria ini.")
        return

    df_result = pd.DataFrame(rows)

    def color_pct(val):
        if pd.isna(val):
            return ""
        return "color: green" if val > 0 else "color: red"

    def color_signal(val):
        if val in ("Overbought", "Death Cross", "Bearish"):
            return "color: red"
        elif val in ("Oversold", "Golden Cross", "Bullish"):
            return "color: green"
        return ""

    styled = (
        df_result.style
        .map(color_pct, subset=["% Change"])
        .map(color_signal, subset=["RSI Signal", "MA Signal"])
        .format({
            "Harga (IDR)": lambda x: f"Rp {x:,.0f}" if x else "-",
            "% Change": lambda x: f"{x:+.2f}%" if x else "-",
            "Vol Ratio": lambda x: f"{x:.2f}x" if x else "-",
        })
    )

    st.success(f"Ketemu {len(rows)} saham yang cocok.")
    st.dataframe(styled, use_container_width=True, hide_index=True)


def render_investor_screener(tickers: list):
    st.subheader("Screener — Investor")
    st.caption("Pilih kriteria valuasi, MMT cariin saham yang cocok dari watchlist lo.")

    col1, col2 = st.columns(2)
    with col1:
        per_filter = st.multiselect(
            "Valuasi PER",
            ["Murah", "Wajar", "Mahal"],
            default=[]
        )
    with col2:
        pbv_filter = st.multiselect(
            "Valuasi PBV",
            ["Murah", "Wajar", "Mahal"],
            default=[]
        )

    if not per_filter and not pbv_filter:
        st.info("Pilih minimal satu kriteria di atas buat mulai screening.")
        return

    rows = []
    with st.spinner("Scanning watchlist..."):
        for ticker in tickers:
            data = get_fundamental(ticker)
            if not data:
                continue

            per = data.get("per")
            pbv = data.get("pbv")
            price_now = data.get("price")
            eps = data.get("eps")
            bvps = (price_now / pbv) if (price_now and pbv) else None

            hist_2y = get_price_data(ticker, period="2y")
            if hist_2y.empty:
                continue

            per_series = get_historical_valuation_series(hist_2y["Close"], eps) if eps else pd.Series(dtype=float)
            pbv_series = get_historical_valuation_series(hist_2y["Close"], bvps) if bvps else pd.Series(dtype=float)

            per_label, _, _ = get_valuation_label(per, per_series)
            pbv_label, _, _ = get_valuation_label(pbv, pbv_series)

            match_per = (not per_filter) or (per_label in per_filter)
            match_pbv = (not pbv_filter) or (pbv_label in pbv_filter)

            if match_per and match_pbv:
                rows.append({
                    "Ticker": ticker.replace(".JK", ""),
                    "Nama": data.get("name"),
                    "PER": per,
                    "Label PER": per_label,
                    "PBV": pbv,
                    "Label PBV": pbv_label,
                    "Div Yield": data.get("dividend_yield"),
                })

    if not rows:
        st.warning("Tidak ada saham di watchlist yang cocok dengan kriteria ini.")
        return

    df_result = pd.DataFrame(rows)

    def color_label(val):
        if val == "Murah":
            return "color: green"
        elif val == "Mahal":
            return "color: red"
        return ""

    styled = (
        df_result.style
        .map(color_label, subset=["Label PER", "Label PBV"])
        .format({
            "PER": lambda x: f"{x:.1f}x" if x else "-",
            "PBV": lambda x: f"{x:.2f}x" if x else "-",
            "Div Yield": lambda x: f"{x:.2f}%" if x else "-",
        })
    )

    st.success(f"Ketemu {len(rows)} saham yang cocok.")
    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.caption(
        "⚠️ Label valuasi relatif terhadap rata-rata historis saham itu sendiri 2 tahun terakhir, "
        "bukan rekomendasi beli/jual."
    )