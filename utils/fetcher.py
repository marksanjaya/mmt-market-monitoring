import yfinance as yf
import pandas as pd
import streamlit as st


@st.cache_data(ttl=900)  # Cache 15 menit (sesuai delay yfinance)
def get_price_data(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """
    Ambil OHLCV historical data dari yfinance.
    period options: 1mo, 3mo, 6mo, 1y, 2y, 5y
    """
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        st.error(f"Gagal ambil data {ticker}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache 1 jam (fundamental jarang berubah)
def get_fundamental(ticker: str) -> dict:
    """
    Ambil fundamental data dari yfinance: PER, PBV, EPS, ROE, dll.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "-"),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "per": info.get("trailingPE"),
            "pbv": info.get("priceToBook"),
            "eps": info.get("trailingEps"),
            "roe": info.get("returnOnEquity"),
            "der": info.get("debtToEquity"),
            "market_cap": info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
        }
    except Exception as e:
        st.error(f"Gagal ambil fundamental {ticker}: {e}")
        return {}


@st.cache_data(ttl=900)
def get_quick_stats(ticker: str) -> dict:
    """
    Ambil snapshot harian: harga, % change, volume.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = get_price_data(ticker, period="1mo")

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("regularMarketPreviousClose")
        pct_change = ((price - prev_close) / prev_close * 100) if price and prev_close else None

        vol_today = info.get("regularMarketVolume")
        vol_avg20 = hist["Volume"].tail(20).mean() if not hist.empty else None
        vol_ratio = (vol_today / vol_avg20) if vol_today and vol_avg20 else None

        return {
            "ticker": ticker.replace(".JK", ""),
            "name": info.get("shortName", ticker),
            "price": price,
            "pct_change": pct_change,
            "volume": vol_today,
            "vol_avg20": vol_avg20,
            "vol_ratio": vol_ratio,
        }
    except Exception as e:
        st.error(f"Gagal ambil stats {ticker}: {e}")
        return {}