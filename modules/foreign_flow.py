import streamlit as st
import pandas as pd
import requests
import streamlit as st


def render_foreign_flow(tickers: list):
    st.subheader("Foreign Flow")
    st.info(
        "Data foreign net buy/sell diambil dari IDX public data (idx.co.id). "
        "Update: end-of-day, T+1.",
        icon="ℹ️"
    )

    # IDX foreign flow endpoint (public, no auth required)
    # Endpoint ini tersedia di IDX untuk data summary harian
    IDX_URL = "https://www.idx.co.id/primary/TradingSummary/GetForeignFlow"

    ticker_codes = [t.replace(".JK", "") for t in tickers]

    rows = []
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.idx.co.id/",
    }

    with st.spinner("Mengambil data foreign flow dari IDX..."):
        for code in ticker_codes:
            try:
                params = {"code": code, "start": 0, "length": 5}
                resp = requests.get(IDX_URL, params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    records = data.get("data", [])
                    for rec in records:
                        rows.append({
                            "Ticker": code,
                            "Tanggal": rec.get("Date", "-"),
                            "Foreign Buy (lot)": rec.get("ForeignBuy"),
                            "Foreign Sell (lot)": rec.get("ForeignSell"),
                            "Net Foreign (lot)": rec.get("ForeignBuy", 0) - rec.get("ForeignSell", 0),
                        })
            except Exception as e:
                st.warning(f"Gagal ambil data {code}: {e}")

    if rows:
        df = pd.DataFrame(rows)

        def color_net(val):
            if pd.isna(val):
                return ""
            return "color: green" if val > 0 else "color: red"

        styled = (
            df.style
            .applymap(color_net, subset=["Net Foreign (lot)"])
            .format({
                "Foreign Buy (lot)": lambda x: f"{x:,.0f}" if x else "-",
                "Foreign Sell (lot)": lambda x: f"{x:,.0f}" if x else "-",
                "Net Foreign (lot)": lambda x: f"{x:+,.0f}" if x else "-",
            })
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        # Fallback: tampilkan info dan redirect ke IDX manual
        st.warning(
            "IDX API tidak merespons atau struktur berubah. "
            "Ini hal umum karena IDX tidak publish API resmi."
        )
        st.markdown("**Alternatif: cek langsung di sumber resmi**")
        for code in ticker_codes:
            st.markdown(
                f"- [{code} Foreign Flow](https://www.idx.co.id/id/market-data/saham/{code})"
            )
        st.caption(
            "Phase 2 akan handle ini dengan scraping HTML IDX yang lebih robust."
        )

    st.divider()
    st.caption(
        "Sumber: idx.co.id · End-of-day · Legal public data · "
        "Tidak butuh auth atau subscription"
    )