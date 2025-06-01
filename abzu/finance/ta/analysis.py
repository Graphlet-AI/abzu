from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import pandas as pd

from .indicators import IndicatorCalculator
from .patterns import PatternDetector


@dataclass
class MarketSnapshot:
    """Current market state snapshot"""

    timestamp: datetime
    price: float
    volume: float

    # Trend
    trend_short: str  # bullish/bearish/neutral
    trend_medium: str
    trend_long: str

    # Key levels
    support_levels: List[float]
    resistance_levels: List[float]

    # Indicator status
    rsi_status: str  # oversold/neutral/overbought
    macd_status: str  # bullish/bearish/neutral
    volume_status: str  # high/normal/low

    # Signals
    entry_signals: List[Dict]
    exit_signals: List[Dict]

    # Risk metrics
    volatility: float
    risk_level: str  # low/medium/high


class TechnicalAnalyzer:
    """Main technical analysis class"""

    def __init__(self, df: pd.DataFrame):
        """Initialize with OHLCV data"""
        self.df = df.copy()
        self.calculator = IndicatorCalculator(df)
        self.pattern_detector = PatternDetector(df)

        # Calculate indicators
        self.indicators = self.calculator.calculate_all_indicators()
        self.calculator.add_custom_indicators()
        self.df = self.calculator.get_dataframe()

    def get_market_snapshot(self) -> MarketSnapshot:
        """Get current market analysis snapshot"""
        latest = self.df.iloc[-1]

        # Determine trends
        trend_short = self._determine_trend(10)
        trend_medium = self._determine_trend(20)
        trend_long = self._determine_trend(50)

        # Find support/resistance
        sr_levels = self.pattern_detector.find_support_resistance()

        # Analyze indicators
        rsi_status = self._analyze_rsi(latest["rsi"])
        macd_status = self._analyze_macd(latest)
        volume_status = self._analyze_volume(latest)

        # Generate signals
        entry_signals = self._generate_entry_signals()
        exit_signals = self._generate_exit_signals()

        # Risk metrics
        volatility = latest["atr_pct"]
        risk_level = self._assess_risk_level(volatility)

        return MarketSnapshot(
            timestamp=latest.name if isinstance(latest.name, datetime) else datetime.now(),
            price=latest["close"],
            volume=latest["volume"],
            trend_short=trend_short,
            trend_medium=trend_medium,
            trend_long=trend_long,
            support_levels=sr_levels["support"],
            resistance_levels=sr_levels["resistance"],
            rsi_status=rsi_status,
            macd_status=macd_status,
            volume_status=volume_status,
            entry_signals=entry_signals,
            exit_signals=exit_signals,
            volatility=volatility,
            risk_level=risk_level,
        )

    def _determine_trend(self, period: int) -> str:
        """Determine trend based on SMA"""
        latest = self.df.iloc[-1]
        sma_col = f"sma_{period}"

        if sma_col not in self.df.columns:
            return "neutral"

        price = latest["close"]
        sma = latest[sma_col]

        if pd.isna(sma):
            return "neutral"

        # Calculate slope of SMA
        if len(self.df) > period:
            sma_slope = (self.df[sma_col].iloc[-1] - self.df[sma_col].iloc[-period]) / period

            if price > sma and sma_slope > 0:
                return "bullish"
            elif price < sma and sma_slope < 0:
                return "bearish"

        return "neutral"

    def _analyze_rsi(self, rsi_value: float) -> str:
        """Analyze RSI status"""
        if pd.isna(rsi_value):
            return "neutral"

        if rsi_value < 30:
            return "oversold"
        elif rsi_value > 70:
            return "overbought"
        else:
            return "neutral"

    def _analyze_macd(self, latest_row: pd.Series) -> str:
        """Analyze MACD status"""
        macd = latest_row["macd"]
        signal = latest_row["macd_signal"]
        histogram = latest_row["macd_histogram"]

        if pd.isna(macd) or pd.isna(signal):
            return "neutral"

        # Check for crossover
        if len(self.df) > 1:
            prev_hist = self.df["macd_histogram"].iloc[-2]
            if histogram > 0 and prev_hist <= 0:
                return "bullish_crossover"
            elif histogram < 0 and prev_hist >= 0:
                return "bearish_crossover"

        # General status
        if histogram > 0:
            return "bullish"
        elif histogram < 0:
            return "bearish"

        return "neutral"

    def _analyze_volume(self, latest_row: pd.Series) -> str:
        """Analyze volume status"""
        volume_ratio = latest_row.get("volume_ratio", 1.0)

        if volume_ratio > 2.0:
            return "very_high"
        elif volume_ratio > 1.5:
            return "high"
        elif volume_ratio < 0.5:
            return "low"
        else:
            return "normal"

    def _generate_entry_signals(self) -> List[Dict]:
        """Generate potential entry signals"""
        signals = []
        latest = self.df.iloc[-1]

        # RSI oversold bounce
        if latest["rsi"] < 30 and self.df["rsi"].iloc[-2] < latest["rsi"]:
            signals.append(
                {
                    "type": "rsi_oversold_bounce",
                    "strength": "medium",
                    "price": latest["close"],
                    "target": latest["close"] * 1.02,
                    "stop_loss": latest["close"] * 0.98,
                }
            )

        # MACD bullish crossover
        if self._analyze_macd(latest) == "bullish_crossover":
            signals.append(
                {
                    "type": "macd_bullish_crossover",
                    "strength": "strong",
                    "price": latest["close"],
                    "target": latest["close"] * 1.03,
                    "stop_loss": latest["close"] * 0.97,
                }
            )

        # Bollinger Band squeeze
        if latest["bb_width"] < self.df["bb_width"].rolling(20).mean().iloc[-1] * 0.8:
            signals.append(
                {
                    "type": "bollinger_squeeze",
                    "strength": "medium",
                    "price": latest["close"],
                    "note": "Potential breakout setup",
                }
            )

        # Add pattern-based signals
        candlestick_patterns = self.pattern_detector.detect_active_patterns(lookback=3)
        for pattern in candlestick_patterns:
            if pattern["signal"] == "bullish":
                signals.append(
                    {
                        "type": f"candlestick_{pattern['pattern']}",
                        "strength": "medium",
                        "price": latest["close"],
                        "date": pattern["date"],
                    }
                )

        return signals

    def _generate_exit_signals(self) -> List[Dict]:
        """Generate potential exit signals"""
        signals = []
        latest = self.df.iloc[-1]

        # RSI overbought
        if latest["rsi"] > 70:
            signals.append(
                {"type": "rsi_overbought", "strength": "medium", "price": latest["close"]}
            )

        # MACD bearish crossover
        if self._analyze_macd(latest) == "bearish_crossover":
            signals.append(
                {"type": "macd_bearish_crossover", "strength": "strong", "price": latest["close"]}
            )

        # Price at resistance
        resistance_levels = self.pattern_detector.find_support_resistance()["resistance"]
        for resistance in resistance_levels:
            if abs(latest["close"] - resistance) / resistance < 0.01:  # Within 1%
                signals.append(
                    {
                        "type": "at_resistance",
                        "strength": "medium",
                        "price": latest["close"],
                        "resistance_level": resistance,
                    }
                )

        return signals

    def _assess_risk_level(self, volatility_pct: float) -> str:
        """Assess current risk level"""
        if volatility_pct < 1.0:
            return "low"
        elif volatility_pct < 2.5:
            return "medium"
        else:
            return "high"

    def generate_analysis_summary(self) -> Dict:
        """Generate comprehensive analysis summary"""
        snapshot = self.get_market_snapshot()
        patterns = self.pattern_detector.detect_active_patterns()

        return {
            "snapshot": snapshot,
            "active_patterns": patterns,
            "indicator_values": {
                "rsi": self.df["rsi"].iloc[-1],
                "macd": self.df["macd"].iloc[-1],
                "adx": self.df["adx"].iloc[-1],
                "atr_pct": self.df["atr_pct"].iloc[-1],
                "volume_ratio": self.df["volume_ratio"].iloc[-1],
            },
            "price_levels": {
                "current": self.df["close"].iloc[-1],
                "day_high": self.df["high"].iloc[-1],
                "day_low": self.df["low"].iloc[-1],
                "20d_high": self.df["high"].tail(20).max(),
                "20d_low": self.df["low"].tail(20).min(),
            },
        }
