import yfinance as yf
import pandas as pd
import streamlit as st
import time


def _fetch_with_retry(fetch_fn, max_retries: int = 3, base_delay: float = 2.0):
    """
    Jalanin fetch_fn dengan retry + exponential backoff kalau kena rate limit.
    base_delay dalam detik, delay berlipat tiap retry (2s, 4s, 8s).
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return fetch_fn()
        except Exception as e:
            last_error = e
            err_msg = str(e).lower()
            is_rate_limit = "rate limit" in err_msg or "too many requests" in err_msg or "429" in err_msg
            if is_rate_limit and attempt < max_retries - 1:
                wait = base_delay * (2 ** attempt)
                time.sleep(wait)
                continue
            else:
                raise last_error
    raise last_error


@st.cache_data(ttl=3600)  # Cache 1 jam, dinaikin dari 15 menit buat kurangin frekuensi hit ke Yahoo
def get_price_data(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """
    Ambil OHLCV historical data dari yfinance, dengan retry kalau kena rate limit.
    period options: 1mo, 3mo, 6mo, 1y, 2y, 5y
    """
    def _fetch():
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.index = pd.to_datetime(df.index)
        return df

    try:
        return _fetch_with_retry(_fetch)
    except Exception as e:
        st.error(f"Gagal ambil data {ticker}: rate limited oleh Yahoo Finance, coba lagi beberapa menit ke depan.")
        return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache 1 jam (fundamental jarang berubah)
def get_fundamental(ticker: str) -> dict:
    """
    Ambil fundamental data dari yfinance: PER, PBV, EPS, ROE, dll. Dengan retry.
    """
    def _fetch():
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

    try:
        return _fetch_with_retry(_fetch)
    except Exception:
        st.error(f"Gagal ambil fundamental {ticker}: rate limited oleh Yahoo Finance, coba lagi beberapa menit ke depan.")
        return {}


@st.cache_data(ttl=3600)  # Cache 1 jam, dinaikin dari 15 menit
def get_quick_stats(ticker: str) -> dict:
    """
    Ambil snapshot harian: harga, % change, volume. Dengan retry.
    """
    def _fetch():
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

    try:
        return _fetch_with_retry(_fetch)
    except Exception:
        st.error(f"Gagal ambil stats {ticker}: rate limited oleh Yahoo Finance, coba lagi beberapa menit ke depan.")
        return {}