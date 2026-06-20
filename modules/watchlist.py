import streamlit as st
import pandas as pd
from utils.fetcher import get_quick_stats
from utils.indicators import get_rsi_signal, get_ma_signal, enrich_df, calc_rsi
from utils.fetcher import get_price_data


def render_watchlist(tickers: list):
    st.subheader("Watchlist Overview")

    rows = []
    for ticker in tickers:
        with st.spinner(f"Loading {ticker}..."):
            stats = get_quick_stats(ticker)
            if not stats:
                continue

            df = get_price_data(ticker, period="3mo")
            df = enrich_df(df)

            rsi_val = df["RSI"].iloc[-1] if not df.empty else None
            rsi_label, _ = get_rsi_signal(rsi_val)
            ma_label, _ = get_ma_signal(df)

            rows.append({
                "Ticker": stats.get("ticker", "-"),
                "Nama": stats.get("name", "-"),
                "Harga (IDR)": stats.get("price"),
                "% Change": stats.get("pct_change"),
                "Volume": stats.get("volume"),
                "Vol Ratio (vs MA20)": stats.get("vol_ratio"),
                "RSI 14": round(rsi_val, 1) if rsi_val else None,
                "RSI Signal": rsi_label,
                "MA Signal": ma_label,
            })

    if not rows:
        st.warning("Tidak ada data yang berhasil diambil.")
        return

    df_table = pd.DataFrame(rows)

    # Toggle mode ringkas untuk layar kecil (HP/tablet)
    compact = st.toggle(
        "📱 Mode ringkas (untuk HP)",
        value=False,
        help="Sembunyiin kolom Nama, Volume, dan RSI angka biar tabel muat di layar kecil"
    )

    if compact:
        display_cols = ["Ticker", "Harga (IDR)", "% Change", "RSI Signal", "MA Signal"]
        df_table = df_table[display_cols]

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

    def color_vol(val):
        if pd.isna(val):
            return ""
        return "color: orange; font-weight: bold" if val >= 2.0 else ""

    style_chain = df_table.style.map(color_pct, subset=["% Change"])
    style_chain = style_chain.map(color_signal, subset=["RSI Signal", "MA Signal"])

    format_dict = {
        "Harga (IDR)": lambda x: f"Rp {x:,.0f}" if x else "-",
        "% Change": lambda x: f"{x:+.2f}%" if x else "-",
    }

    if not compact:
        style_chain = style_chain.map(color_vol, subset=["Vol Ratio (vs MA20)"])
        format_dict["Volume"] = lambda x: f"{x:,.0f}" if x else "-"
        format_dict["Vol Ratio (vs MA20)"] = lambda x: f"{x:.2f}x" if x else "-"

    styled = style_chain.format(format_dict)

    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.caption("Data delayed ~15 menit · Refresh otomatis tiap 15 menit")