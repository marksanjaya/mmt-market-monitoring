import streamlit as st


def render_foreign_flow(tickers: list):
    st.subheader("Foreign Flow")

    st.info(
        "Data foreign net buy/sell adalah data resmi milik IDX (Bursa Efek Indonesia) "
        "yang ToS-nya melarang redistribusi otomatis ke pihak lain. MMT tidak mengambil "
        "atau menampilkan datanya secara langsung, melainkan kasih shortcut ke halaman "
        "resmi IDX di bawah ini.",
        icon="ℹ️"
    )

    ticker_codes = [t.replace(".JK", "") for t in tickers]

    st.markdown("**Cek Foreign Flow & Ringkasan Saham di IDX**")
    st.link_button(
        "📊 Buka Ringkasan Saham — IDX",
        "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham",
        use_container_width=True
    )
    st.caption(
        "Cari kode saham (" + ", ".join(ticker_codes) + ") di kolom pencarian "
        "halaman tersebut untuk lihat data foreign buy/sell."
    )

    st.divider()
    st.caption(
        "Link membuka tab baru ke idx.co.id (sumber resmi). "
        "Data: end-of-day, T+1. MMT tidak menyimpan atau memproses data ini."
    )