import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from utils.fetcher import get_price_data
from utils.indicators import enrich_df, get_rsi_signal, get_ma_signal


def render_technical(tickers: list):
    st.subheader("Technical View")

    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.selectbox("Pilih saham", tickers, format_func=lambda x: x.replace(".JK", ""))
    with col2:
        period = st.selectbox("Periode", ["1mo", "3mo", "6mo", "1y"], index=1)

    df = get_price_data(ticker, period=period)
    if df.empty:
        st.error("Data tidak tersedia.")
        return

    df = enrich_df(df)

    rsi_val = df["RSI"].iloc[-1]
    ma_signal, ma_color = get_ma_signal(df)
    rsi_label, rsi_color = get_rsi_signal(rsi_val)

    last_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2]
    pct = (last_close - prev_close) / prev_close * 100
    vol_ratio = df["Volume"].iloc[-1] / df["Volume"].tail(20).mean()

    # Quick stats: 2x2 grid biar tetap kebaca di layar sempit
    r1c1, r1c2 = st.columns(2)
    r1c1.metric("Harga", f"Rp {last_close:,.0f}", f"{pct:+.2f}%")
    r1c2.metric("RSI 14", f"{rsi_val:.1f}", rsi_label)

    r2c1, r2c2 = st.columns(2)
    r2c1.metric("MA Signal", ma_signal)
    r2c2.metric("Vol Ratio", f"{vol_ratio:.2f}x")

    st.divider()

    # Toggle mode ringkas untuk chart yang lebih pendek di HP
    compact_chart = st.toggle(
        "📱 Chart ringkas (untuk HP)",
        value=False,
        help="Perpendek tinggi chart biar pas di layar HP tanpa banyak scroll"
    )
    chart_height = 380 if compact_chart else 550

    # Chart: candlestick + MA + RSI
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="OHLC",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350"
    ), row=1, col=1)

    # MA20
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MA20"],
        name="MA20", line=dict(color="#FFA726", width=1.5)
    ), row=1, col=1)

    # MA50
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MA50"],
        name="MA50", line=dict(color="#42A5F5", width=1.5)
    ), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"],
        name="RSI 14", line=dict(color="#AB47BC", width=1.5)
    ), row=2, col=1)

    # RSI lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=chart_height,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.02),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.1)")
    fig.update_xaxes(gridcolor="rgba(128,128,128,0.1)")

    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Menampilkan data {ticker.replace('.JK','')} · {period} · delayed ~15 menit")