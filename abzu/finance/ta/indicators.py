from dataclasses import dataclass

import pandas as pd
import talib


@dataclass
class TechnicalIndicators:
    """Container for all technical indicators"""

    # Trend indicators
    sma_10: pd.Series
    sma_20: pd.Series
    sma_50: pd.Series
    ema_12: pd.Series
    ema_26: pd.Series

    # Momentum indicators
    rsi: pd.Series
    macd: pd.Series
    macd_signal: pd.Series
    macd_histogram: pd.Series
    stoch_k: pd.Series
    stoch_d: pd.Series

    # Volatility indicators
    bb_upper: pd.Series
    bb_middle: pd.Series
    bb_lower: pd.Series
    atr: pd.Series

    # Volume indicators
    obv: pd.Series
    adl: pd.Series

    # Additional indicators
    adx: pd.Series
    cci: pd.Series
    mfi: pd.Series
    williams_r: pd.Series


class IndicatorCalculator:
    """Calculate technical indicators using TA-Lib"""

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV dataframe

        Args:
            df: DataFrame with columns: open, high, low, close, volume
        """
        self.df = df.copy()
        self._validate_data()

    def _validate_data(self):
        """Validate input data has required columns"""
        required = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def calculate_all_indicators(self) -> TechnicalIndicators:
        """Calculate all technical indicators"""

        # Extract price arrays
        close = self.df["close"].values
        high = self.df["high"].values
        low = self.df["low"].values
        volume = self.df["volume"].values

        # Moving averages
        sma_10 = talib.SMA(close, timeperiod=10)
        sma_20 = talib.SMA(close, timeperiod=20)
        sma_50 = talib.SMA(close, timeperiod=50)
        ema_12 = talib.EMA(close, timeperiod=12)
        ema_26 = talib.EMA(close, timeperiod=26)

        # RSI
        rsi = talib.RSI(close, timeperiod=14)

        # MACD
        macd, macd_signal, macd_histogram = talib.MACD(
            close, fastperiod=12, slowperiod=26, signalperiod=9
        )

        # Stochastic
        stoch_k, stoch_d = talib.STOCH(
            high,
            low,
            close,
            fastk_period=14,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0,
        )

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = talib.BBANDS(
            close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )

        # ATR
        atr = talib.ATR(high, low, close, timeperiod=14)

        # Volume indicators
        obv = talib.OBV(close, volume)
        adl = talib.AD(high, low, close, volume)

        # Additional indicators
        adx = talib.ADX(high, low, close, timeperiod=14)
        cci = talib.CCI(high, low, close, timeperiod=20)
        mfi = talib.MFI(high, low, close, volume, timeperiod=14)
        williams_r = talib.WILLR(high, low, close, timeperiod=14)

        # Convert to pandas Series and add to dataframe
        indicators = {
            "sma_10": sma_10,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "ema_12": ema_12,
            "ema_26": ema_26,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
            "macd_histogram": macd_histogram,
            "stoch_k": stoch_k,
            "stoch_d": stoch_d,
            "bb_upper": bb_upper,
            "bb_middle": bb_middle,
            "bb_lower": bb_lower,
            "atr": atr,
            "obv": obv,
            "adl": adl,
            "adx": adx,
            "cci": cci,
            "mfi": mfi,
            "williams_r": williams_r,
        }

        # Add to dataframe
        for name, values in indicators.items():
            self.df[name] = values

        # Return as TechnicalIndicators object
        return TechnicalIndicators(
            **{name: pd.Series(values, index=self.df.index) for name, values in indicators.items()}
        )

    def add_custom_indicators(self):
        """Add custom calculated indicators"""
        # Volume ratio
        self.df["volume_sma"] = talib.SMA(self.df["volume"].values, timeperiod=20)
        self.df["volume_ratio"] = self.df["volume"] / self.df["volume_sma"]

        # Price change metrics
        self.df["pct_change"] = self.df["close"].pct_change()
        self.df["intraday_range"] = (self.df["high"] - self.df["low"]) / self.df["close"]

        # True Range percentage
        self.df["atr_pct"] = self.df["atr"] / self.df["close"] * 100

        # Bollinger Band width
        self.df["bb_width"] = (self.df["bb_upper"] - self.df["bb_lower"]) / self.df["bb_middle"]

        # Price position within Bollinger Bands
        self.df["bb_position"] = (self.df["close"] - self.df["bb_lower"]) / (
            self.df["bb_upper"] - self.df["bb_lower"]
        )

    def get_dataframe(self) -> pd.DataFrame:
        """Return the dataframe with all indicators"""
        return self.df
