import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.fetcher import get_fundamental, get_price_data
from utils.indicators import get_valuation_label, get_historical_valuation_series
import yfinance as yf


def fmt(val, prefix="", suffix="", decimals=2, billions=False):
    if val is None:
        return "-"
    if billions:
        return f"{prefix}{val/1e12:.2f}T" if val >= 1e12 else f"{prefix}{val/1e9:.1f}B"
    return f"{prefix}{val:.{decimals}f}{suffix}"


def render_fundamental(tickers: list):
    st.subheader("Fundamental View")

    ticker = st.selectbox(
        "Pilih saham",
        tickers,
        format_func=lambda x: x.replace(".JK", "")
    )

    with st.spinner("Loading fundamental data..."):
        data = get_fundamental(ticker)

    if not data:
        st.error("Data tidak tersedia.")
        return

    st.markdown(f"### {data.get('name', ticker)}")
    st.caption(f"Sektor: {data.get('sector', '-')}")
    st.divider()

    # Valuasi metrics + quick-read label
    st.markdown("**Valuasi**")

    per = data.get("per")
    pbv = data.get("pbv")
    eps = data.get("eps")

    # Approximate BVPS dari price / PBV (karena yfinance tidak kasih BVPS langsung)
    price_now = data.get("price")
    bvps = (price_now / pbv) if (price_now and pbv) else None

    # Ambil historical price 2 tahun untuk approximate historical PER/PBV
    hist_2y = get_price_data(ticker, period="2y")
    per_series = get_historical_valuation_series(hist_2y["Close"], eps) if not hist_2y.empty and eps else pd.Series(dtype=float)
    pbv_series = get_historical_valuation_series(hist_2y["Close"], bvps) if not hist_2y.empty and bvps else pd.Series(dtype=float)

    per_label, per_color, per_detail = get_valuation_label(per, per_series)
    pbv_label, pbv_color, pbv_detail = get_valuation_label(pbv, pbv_series)

    badge_style = {
        "green": "background:#EAF3DE;color:#3B6D11;",
        "red": "background:#FBE9E7;color:#B3261E;",
        "gray": "background:#F0F0EE;color:#6B6B68;",
    }

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.metric(
            "PER", fmt(per, decimals=1, suffix="x"),
            help="Label relatif terhadap rata-rata PER saham ini sendiri 2 tahun terakhir, bukan valuasi absolut"
        )
        if per_label != "-":
            st.markdown(
                f'<span style="font-size:11px;padding:2px 8px;border-radius:10px;{badge_style[per_color]}">{per_label}</span>',
                unsafe_allow_html=True
            )
            st.caption(per_detail)
    with r1c2:
        st.metric(
            "PBV", fmt(pbv, decimals=2, suffix="x"),
            help="Label relatif terhadap rata-rata PBV saham ini sendiri 2 tahun terakhir, bukan valuasi absolut"
        )
        if pbv_label != "-":
            st.markdown(
                f'<span style="font-size:11px;padding:2px 8px;border-radius:10px;{badge_style[pbv_color]}">{pbv_label}</span>',
                unsafe_allow_html=True
            )
            st.caption(pbv_detail)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.metric("EPS", fmt(eps, prefix="Rp ", decimals=0))
    with r2c2:
        st.metric("Div Yield", fmt(data.get("dividend_yield"), suffix="%", decimals=2)
                  if data.get("dividend_yield") else "-")

    st.caption(
        "⚠️ Label \"Murah/Wajar/Mahal\" membandingkan valuasi saham ini terhadap "
        "rata-rata historisnya sendiri 2 tahun terakhir, bukan terhadap sektor, "
        "bukan valuasi absolut, dan bukan rekomendasi beli/jual. Saham yang lagi "
        "downtrend panjang bisa kebaca \"Murah\" padahal sedang underperform, "
        "bukan undervalued. Selalu cross-check dengan kondisi fundamental dan "
        "tren harga aktualnya."
    )

    st.divider()

    # Profitabilitas
    st.markdown("**Profitabilitas**")
    roe = data.get("roe")
    der = data.get("der")
    mktcap = data.get("market_cap")

    r3c1, r3c2 = st.columns(2)
    r3c1.metric("ROE", f"{roe*100:.1f}%" if roe else "-")
    r3c2.metric("DER", f"{der:.2f}x" if der else "-")
    st.metric("Market Cap", fmt(mktcap, prefix="Rp ", billions=True) if mktcap else "-")

    st.divider()

    # Revenue & Net Income (dari financials yfinance)
    st.markdown("**Tren Revenue & Laba Bersih**")
    try:
        t = yf.Ticker(ticker)
        fin = t.financials
        if fin is not None and not fin.empty:
            fin = fin.T.sort_index()
            rev_col = [c for c in fin.columns if "Total Revenue" in str(c)]
            ni_col = [c for c in fin.columns if "Net Income" in str(c)]

            if rev_col and ni_col:
                chart_df = pd.DataFrame({
                    "Revenue": fin[rev_col[0]] / 1e12,
                    "Net Income": fin[ni_col[0]] / 1e12,
                }).dropna()

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=chart_df.index.strftime("%Y"),
                    y=chart_df["Revenue"],
                    name="Revenue (T)",
                    marker_color="#42A5F5"
                ))
                fig.add_trace(go.Bar(
                    x=chart_df.index.strftime("%Y"),
                    y=chart_df["Net Income"],
                    name="Net Income (T)",
                    marker_color="#26a69a"
                ))
                fig.update_layout(
                    barmode="group",
                    height=300,
                    margin=dict(l=0, r=0, t=10, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", y=1.1),
                    yaxis_title="Triliun IDR"
                )
                fig.update_yaxes(gridcolor="rgba(128,128,128,0.1)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data revenue tidak tersedia untuk emiten ini.")
        else:
            st.info("Data laporan keuangan tidak tersedia.")
    except Exception as e:
        st.warning(f"Tidak bisa ambil data financials: {e}")

    st.caption("Data dari yfinance · Annual · Update tiap 1 jam")