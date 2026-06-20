import pandas as pd
import numpy as np


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_ma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def get_rsi_signal(rsi_value: float) -> tuple:
    """
    Returns (signal_label, color)
    """
    if rsi_value is None or pd.isna(rsi_value):
        return "-", "gray"
    if rsi_value >= 70:
        return "Overbought", "red"
    elif rsi_value <= 30:
        return "Oversold", "green"
    else:
        return "Neutral", "gray"


def get_ma_signal(df: pd.DataFrame) -> tuple:
    """
    MA20/MA50 crossover signal.
    Returns (signal_label, color)
    """
    if df.empty or len(df) < 50:
        return "Data kurang", "gray"

    ma20 = calc_ma(df["Close"], 20)
    ma50 = calc_ma(df["Close"], 50)

    last_ma20 = ma20.iloc[-1]
    last_ma50 = ma50.iloc[-1]
    prev_ma20 = ma20.iloc[-2]
    prev_ma50 = ma50.iloc[-2]

    if prev_ma20 <= prev_ma50 and last_ma20 > last_ma50:
        return "Golden Cross", "green"
    elif prev_ma20 >= prev_ma50 and last_ma20 < last_ma50:
        return "Death Cross", "red"
    elif last_ma20 > last_ma50:
        return "Bullish", "green"
    else:
        return "Bearish", "red"


def enrich_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tambah kolom RSI, MA20, MA50 ke dataframe OHLCV.
    """
    if df.empty:
        return df
    df = df.copy()
    df["RSI"] = calc_rsi(df["Close"])
    df["MA20"] = calc_ma(df["Close"], 20)
    df["MA50"] = calc_ma(df["Close"], 50)
    return df


def get_valuation_label(current_value: float, historical_series: pd.Series, threshold: float = 0.5) -> tuple:
    """
    Bandingkan nilai valuasi sekarang (PER/PBV) terhadap rata-rata historisnya.
    Approximation: historical price / current EPS (atau BVPS), karena EPS historis
    per-periode tidak tersedia gratis. Cukup representatif untuk konteks swing/investing,
    bukan untuk akurasi akademis.

    Returns (label, color, detail_text)
    """
    if current_value is None or historical_series is None or historical_series.empty:
        return "-", "gray", "Data historis tidak cukup"

    clean = historical_series.dropna()
    if len(clean) < 30:
        return "-", "gray", "Data historis tidak cukup"

    avg = clean.mean()
    std = clean.std()

    if std == 0 or pd.isna(std):
        return "-", "gray", "Data historis tidak cukup"

    lower_bound = avg - (threshold * std)
    upper_bound = avg + (threshold * std)

    if current_value < lower_bound:
        label, color = "Murah", "green"
    elif current_value > upper_bound:
        label, color = "Mahal", "red"
    else:
        label, color = "Wajar", "gray"

    detail = f"Rata-rata 2th: {avg:.1f}x · Sekarang: {current_value:.1f}x"
    return label, color, detail


def get_historical_valuation_series(price_series: pd.Series, current_eps_or_bvps: float) -> pd.Series:
    """
    Approximate historical PER/PBV dengan: harga historis / EPS atau BVPS sekarang.
    Limitasi: EPS/BVPS dianggap konstan sepanjang periode (yfinance free tier tidak
    kasih EPS per-kuartal historis), jadi ini approximation, bukan PER historis exact.
    """
    if price_series is None or price_series.empty or not current_eps_or_bvps:
        return pd.Series(dtype=float)
    return price_series / current_eps_or_bvps