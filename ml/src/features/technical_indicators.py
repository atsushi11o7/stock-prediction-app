# python/utils/technical_indicators.py
import pandas as pd

def add_moving_averages(df: pd.DataFrame, short_window: int = 5, long_window: int = 20) -> pd.DataFrame:
    """
    DFに移動平均（短期・長期）を追加

    Args:
        df (pd.DataFrame): 株価データ（'Close'列を含む）
        short_window (int): 短期移動平均の期間（デフォルト: 5）
        long_window (int): 長期移動平均の期間（デフォルト: 20）

    Returns:
        pd.DataFrame: 'MA_5', 'MA_20'列が追加されたデータフレーム
    """
    df[f'MA_{short_window}'] = df['Close'].rolling(window=short_window).mean()
    df[f'MA_{long_window}'] = df['Close'].rolling(window=long_window).mean()
    return df

def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    DFにRSI（Relative Strength Index）を追加

    Args:
        df (pd.DataFrame): 株価データ（'Close'列を含む）
        period (int): RSIの計算期間（デフォルト: 14）

    Returns:
        pd.DataFrame: 'RSI'列が追加されたデータフレーム
    """
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / (loss + 1e-5)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26) -> pd.DataFrame:
    """
    DFにMACD（Moving Average Convergence Divergence）を追加

    Args:
        df (pd.DataFrame): 株価データ（'Close'列を含む）
        fast (int): 短期EMAの期間（デフォルト: 12）
        slow (int): 長期EMAの期間（デフォルト: 26）

    Returns:
        pd.DataFrame: 'MACD'列が追加されたデータフレーム
    """
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    return df