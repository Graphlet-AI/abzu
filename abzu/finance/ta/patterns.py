from typing import Any, Dict, List

import numpy as np
import pandas as pd
import talib


class PatternDetector:
    """Detect candlestick and chart patterns using TA-Lib"""

    # TA-Lib candlestick pattern functions
    CANDLESTICK_PATTERNS = {
        "CDL2CROWS": "Two Crows",
        "CDL3BLACKCROWS": "Three Black Crows",
        "CDL3INSIDE": "Three Inside Up/Down",
        "CDL3LINESTRIKE": "Three-Line Strike",
        "CDL3OUTSIDE": "Three Outside Up/Down",
        "CDL3STARSINSOUTH": "Three Stars In The South",
        "CDL3WHITESOLDIERS": "Three Advancing White Soldiers",
        "CDLABANDONEDBABY": "Abandoned Baby",
        "CDLADVANCEBLOCK": "Advance Block",
        "CDLBELTHOLD": "Belt-hold",
        "CDLBREAKAWAY": "Breakaway",
        "CDLCLOSINGMARUBOZU": "Closing Marubozu",
        "CDLCONCEALBABYSWALL": "Concealing Baby Swallow",
        "CDLCOUNTERATTACK": "Counterattack",
        "CDLDARKCLOUDCOVER": "Dark Cloud Cover",
        "CDLDOJI": "Doji",
        "CDLDOJISTAR": "Doji Star",
        "CDLDRAGONFLYDOJI": "Dragonfly Doji",
        "CDLENGULFING": "Engulfing Pattern",
        "CDLEVENINGDOJISTAR": "Evening Doji Star",
        "CDLEVENINGSTAR": "Evening Star",
        "CDLGAPSIDESIDEWHITE": "Up/Down-gap side-by-side white lines",
        "CDLGRAVESTONEDOJI": "Gravestone Doji",
        "CDLHAMMER": "Hammer",
        "CDLHANGINGMAN": "Hanging Man",
        "CDLHARAMI": "Harami Pattern",
        "CDLHARAMICROSS": "Harami Cross Pattern",
        "CDLHIGHWAVE": "High-Wave Candle",
        "CDLHIKKAKE": "Hikkake Pattern",
        "CDLHIKKAKEMOD": "Modified Hikkake Pattern",
        "CDLHOMINGPIGEON": "Homing Pigeon",
        "CDLIDENTICAL3CROWS": "Identical Three Crows",
        "CDLINNECK": "In-Neck Pattern",
        "CDLINVERTEDHAMMER": "Inverted Hammer",
        "CDLKICKING": "Kicking",
        "CDLKICKINGBYLENGTH": "Kicking by length",
        "CDLLADDERBOTTOM": "Ladder Bottom",
        "CDLLONGLEGGEDDOJI": "Long Legged Doji",
        "CDLLONGLINE": "Long Line Candle",
        "CDLMARUBOZU": "Marubozu",
        "CDLMATCHINGLOW": "Matching Low",
        "CDLMATHOLD": "Mat Hold",
        "CDLMORNINGDOJISTAR": "Morning Doji Star",
        "CDLMORNINGSTAR": "Morning Star",
        "CDLONNECK": "On-Neck Pattern",
        "CDLPIERCING": "Piercing Pattern",
        "CDLRICKSHAWMAN": "Rickshaw Man",
        "CDLRISEFALL3METHODS": "Rising/Falling Three Methods",
        "CDLSEPARATINGLINES": "Separating Lines",
        "CDLSHOOTINGSTAR": "Shooting Star",
        "CDLSHORTLINE": "Short Line Candle",
        "CDLSPINNINGTOP": "Spinning Top",
        "CDLSTALLEDPATTERN": "Stalled Pattern",
        "CDLSTICKSANDWICH": "Stick Sandwich",
        "CDLTAKURI": "Takuri (Dragonfly Doji with very long lower shadow)",
        "CDLTASUKIGAP": "Tasuki Gap",
        "CDLTHRUSTING": "Thrusting Pattern",
        "CDLTRISTAR": "Tristar Pattern",
        "CDLUNIQUE3RIVER": "Unique 3 River",
        "CDLUPSIDEGAP2CROWS": "Upside Gap Two Crows",
        "CDLXSIDEGAP3METHODS": "Upside/Downside Gap Three Methods",
    }

    def __init__(self, df: pd.DataFrame):
        """Initialize with OHLCV dataframe"""
        self.df = df.copy()
        self.open = df["open"].values
        self.high = df["high"].values
        self.low = df["low"].values
        self.close = df["close"].values

    def detect_all_candlestick_patterns(self) -> Dict[str, pd.Series]:
        """Detect all candlestick patterns"""
        patterns = {}

        for func_name, pattern_name in self.CANDLESTICK_PATTERNS.items():
            pattern_func = getattr(talib, func_name)
            try:
                result = pattern_func(self.open, self.high, self.low, self.close)
                patterns[pattern_name] = pd.Series(result, index=self.df.index)
            except Exception as e:
                print(f"Error calculating {pattern_name}: {e}")

        return patterns

    def detect_active_patterns(self, lookback: int = 5) -> List[Dict]:
        """Find patterns that are currently active or recently triggered"""
        all_patterns = self.detect_all_candlestick_patterns()
        active_patterns = []

        for pattern_name, values in all_patterns.items():
            recent_values = values.tail(lookback)
            if recent_values.abs().sum() > 0:  # Pattern detected
                for idx, val in recent_values.items():
                    if val != 0:
                        active_patterns.append(
                            {
                                "pattern": pattern_name,
                                "date": idx,
                                "signal": "bullish" if val > 0 else "bearish",
                                "strength": abs(val),
                            }
                        )

        return active_patterns

    def find_support_resistance(
        self, window: int = 20, min_touches: int = 2
    ) -> Dict[str, List[float]]:
        """Find support and resistance levels"""
        highs = self.df["high"].rolling(window=window, center=True).max()
        lows = self.df["low"].rolling(window=window, center=True).min()

        # Find peaks and troughs
        peaks = self.df[self.df["high"] == highs]["high"]
        troughs = self.df[self.df["low"] == lows]["low"]

        # Cluster nearby levels
        resistance_levels = self._cluster_levels(peaks.values, threshold=0.02)
        support_levels = self._cluster_levels(troughs.values, threshold=0.02)

        return {"resistance": resistance_levels, "support": support_levels}

    def _cluster_levels(self, levels: np.ndarray, threshold: float = 0.02) -> List[float]:
        """Cluster nearby price levels"""
        if len(levels) == 0:
            return []

        sorted_levels = np.sort(levels)
        clusters = []
        current_cluster = [sorted_levels[0]]

        for level in sorted_levels[1:]:
            if (level - current_cluster[-1]) / current_cluster[-1] <= threshold:
                current_cluster.append(level)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [level]

        clusters.append(np.mean(current_cluster))
        return clusters

    def detect_chart_patterns(self) -> Dict[str, Any]:
        """Detect common chart patterns (simplified version)"""
        patterns = {}

        # Double top/bottom detection
        window = 20
        peaks = self._find_peaks(self.df["high"].values, window)
        # troughs = self._find_peaks(-self.df["low"].values, window)  # TODO: Implement trough detection

        # Check for double tops
        if len(peaks) >= 2:
            last_two_peaks = peaks[-2:]
            if (
                abs(
                    self.df["high"].iloc[last_two_peaks[0]]
                    - self.df["high"].iloc[last_two_peaks[1]]
                )
                / self.df["high"].iloc[last_two_peaks[0]]
                < 0.02
            ):
                patterns["double_top"] = {
                    "dates": [self.df.index[i] for i in last_two_peaks],
                    "level": np.mean([self.df["high"].iloc[i] for i in last_two_peaks]),
                }

        # Trend line detection
        if len(self.df) >= 30:
            patterns["trend"] = self._detect_trend_lines()

        return patterns

    def _find_peaks(self, data: np.ndarray, window: int) -> List[int]:
        """Find peaks in data"""
        peaks = []
        for i in range(window, len(data) - window):
            if data[i] == max(data[i - window : i + window + 1]):
                peaks.append(i)
        return peaks

    def _detect_trend_lines(self) -> Dict[str, Dict]:
        """Detect trend lines using linear regression on peaks/troughs"""
        from scipy import stats

        # Find highs and lows
        window = 10
        high_peaks = self._find_peaks(self.df["high"].values, window)
        low_troughs = self._find_peaks(-self.df["low"].values, window)

        result = {}

        # Fit trend line to peaks (resistance)
        if len(high_peaks) >= 2:
            x = np.array(high_peaks)
            y = self.df["high"].iloc[high_peaks].values
            slope, intercept, r_value, _, _ = stats.linregress(x, y)
            result["resistance_trend"] = {
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_value**2,
                "direction": "up" if slope > 0 else "down",
            }

        # Fit trend line to troughs (support)
        if len(low_troughs) >= 2:
            x = np.array(low_troughs)
            y = self.df["low"].iloc[low_troughs].values
            slope, intercept, r_value, _, _ = stats.linregress(x, y)
            result["support_trend"] = {
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_value**2,
                "direction": "up" if slope > 0 else "down",
            }

        return result
