"""
Momentum Indicator and Configuration Implementation
=================================================

Dedicated classes for momentum calculations and configuration management
with comprehensive validation, caching, and extensibility features.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import talib  # type: ignore

logger = logging.getLogger(__name__)


class IndicatorType(Enum):
    """Enumeration of available technical indicators"""

    ROC = "roc"
    RSI = "rsi"
    MACD = "macd"
    VOLUME_ROC = "volume_roc"
    ATR = "atr"
    STOCHASTIC = "stochastic"
    WILLIAMS_R = "williams_r"
    OBV = "obv"
    BOLLINGER_BANDS = "bollinger_bands"
    CCI = "cci"


class MomentumSignal(Enum):
    """Momentum signal strength levels"""

    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


@dataclass
class IndicatorResult:
    """Container for individual indicator results"""

    name: str
    values: np.ndarray
    signal: bool
    score: float
    latest_value: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "signal": self.signal,
            "score": self.score,
            "latest_value": self.latest_value,
            "metadata": self.metadata,
        }


@dataclass
class MomentumConfig:
    """
    Enhanced configuration class for momentum detection with validation and utilities
    """

    # API Configuration
    api_key: str = ""
    base_url: str = "https://api.financialdatasets.ai/prices/historical"
    request_timeout: int = 30
    rate_limit_delay: float = 0.1

    # Data Parameters
    days_lookback: int = 90
    interval: str = "day"
    interval_multiplier: int = 1
    min_data_points: int = 50

    # ROC Parameters
    roc_period: int = 20
    roc_threshold: float = 15.0
    roc_enabled: bool = True

    # RSI Parameters
    rsi_period: int = 14
    rsi_threshold: float = 60.0
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    rsi_enabled: bool = True

    # MACD Parameters
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    macd_enabled: bool = True

    # Volume Parameters
    volume_roc_period: int = 10
    volume_roc_threshold: float = 150.0
    volume_enabled: bool = True

    # ATR Parameters
    atr_period: int = 14
    atr_multiplier: float = 1.5
    atr_lookback_period: int = 50
    atr_enabled: bool = True

    # Stochastic Parameters
    stoch_k_period: int = 14
    stoch_d_period: int = 3
    stoch_threshold: float = 80.0
    stoch_enabled: bool = True

    # Williams %R Parameters
    willr_period: int = 14
    willr_threshold: float = -20.0
    willr_enabled: bool = True

    # Bollinger Bands Parameters
    bb_period: int = 20
    bb_std_dev: float = 2.0
    bb_enabled: bool = False

    # CCI Parameters
    cci_period: int = 14
    cci_threshold: float = 100.0
    cci_enabled: bool = False

    # Scoring Configuration
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "roc": 0.25,
            "rsi": 0.15,
            "macd": 0.20,
            "volume_roc": 0.15,
            "atr_expansion": 0.10,
            "stochastic": 0.10,
            "williams_r": 0.05,
        }
    )

    # Score thresholds for momentum classification
    score_thresholds: dict[str, float] = field(
        default_factory=lambda: {"very_strong": 1.5, "strong": 1.0, "moderate": 0.5, "weak": 0.2}
    )

    # Advanced Options
    normalize_scores: bool = True
    use_percentile_scoring: bool = False
    percentile_window: int = 252  # Trading days in a year
    cache_indicators: bool = True
    parallel_processing: bool = False

    def __post_init__(self):
        """Validate configuration after initialization"""
        self.validate()

    def validate(self) -> None:
        """Comprehensive configuration validation"""
        errors = []

        # Validate periods
        if self.days_lookback < self.min_data_points:
            errors.append(
                f"days_lookback ({self.days_lookback}) must be >= min_data_points ({self.min_data_points})"
            )

        if self.roc_period <= 0:
            errors.append("roc_period must be positive")

        if self.rsi_period <= 0:
            errors.append("rsi_period must be positive")

        if self.macd_fast >= self.macd_slow:
            errors.append("macd_fast must be less than macd_slow")

        if self.volume_roc_period <= 0:
            errors.append("volume_roc_period must be positive")

        if self.atr_period <= 0:
            errors.append("atr_period must be positive")

        # Validate thresholds
        if self.roc_threshold < 0:
            errors.append("roc_threshold should be positive")

        if not (0 <= self.rsi_threshold <= 100):
            errors.append("rsi_threshold must be between 0 and 100")

        if self.volume_roc_threshold < 0:
            errors.append("volume_roc_threshold should be positive")

        if self.atr_multiplier <= 1.0:
            errors.append("atr_multiplier should be > 1.0")

        # Validate weights
        if self.weights:
            total_weight = sum(self.weights.values())
            if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
                logger.warning(f"Weights sum to {total_weight:.3f}, not 1.0. Consider normalizing.")

            for indicator, weight in self.weights.items():
                if weight < 0:
                    errors.append(f"Weight for {indicator} must be non-negative")

        # Validate score thresholds
        thresholds = list(self.score_thresholds.values())
        if thresholds != sorted(thresholds, reverse=True):
            errors.append("Score thresholds must be in descending order")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    def get_enabled_indicators(self) -> list[IndicatorType]:
        """Get list of enabled indicators"""
        enabled = []
        if self.roc_enabled:
            enabled.append(IndicatorType.ROC)
        if self.rsi_enabled:
            enabled.append(IndicatorType.RSI)
        if self.macd_enabled:
            enabled.append(IndicatorType.MACD)
        if self.volume_enabled:
            enabled.append(IndicatorType.VOLUME_ROC)
        if self.atr_enabled:
            enabled.append(IndicatorType.ATR)
        if self.stoch_enabled:
            enabled.append(IndicatorType.STOCHASTIC)
        if self.willr_enabled:
            enabled.append(IndicatorType.WILLIAMS_R)
        if self.bb_enabled:
            enabled.append(IndicatorType.BOLLINGER_BANDS)
        if self.cci_enabled:
            enabled.append(IndicatorType.CCI)
        return enabled

    def normalize_weights(self) -> None:
        """Normalize weights to sum to 1.0"""
        if self.weights:
            total = sum(self.weights.values())
            if total > 0:
                self.weights = {k: v / total for k, v in self.weights.items()}

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert configuration to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "MomentumConfig":
        """Create configuration from dictionary"""
        return cls(**config_dict)

    @classmethod
    def from_json(cls, json_str: str) -> "MomentumConfig":
        """Create configuration from JSON string"""
        return cls.from_dict(json.loads(json_str))

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to file"""
        with open(filepath, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, filepath: str) -> "MomentumConfig":
        """Load configuration from file"""
        with open(filepath, "r") as f:
            return cls.from_json(f.read())

    def copy(self) -> "MomentumConfig":
        """Create a copy of the configuration"""
        return MomentumConfig.from_dict(self.to_dict())

    def update(self, **kwargs) -> "MomentumConfig":
        """Create updated copy with new parameters"""
        config_dict = self.to_dict()
        config_dict.update(kwargs)
        return MomentumConfig.from_dict(config_dict)


class BaseIndicator(ABC):
    """Abstract base class for technical indicators"""

    def __init__(self, config: MomentumConfig):
        self.config = config

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate indicator values and generate signals"""
        pass

    @abstractmethod
    def get_signal_threshold(self) -> float:
        """Get the threshold value for signal generation"""
        pass

    def _get_latest_value(self, arr: np.ndarray) -> float:
        """Extract latest non-NaN value from array"""
        if arr is None or len(arr) == 0:
            return np.nan
        valid_values = arr[~np.isnan(arr)]
        return valid_values[-1] if len(valid_values) > 0 else np.nan


class ROCIndicator(BaseIndicator):
    """Rate of Change indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        close = data["close"].values
        roc_values = talib.ROC(close, timeperiod=self.config.roc_period)
        latest_value = self._get_latest_value(roc_values)

        signal = not np.isnan(latest_value) and latest_value > self.config.roc_threshold
        score = min(latest_value / self.config.roc_threshold, 2.0) if latest_value > 0 else 0
        score = max(0, score)

        return IndicatorResult(
            name="ROC",
            values=roc_values,
            signal=signal,
            score=score,
            latest_value=latest_value,
            metadata={"period": self.config.roc_period, "threshold": self.config.roc_threshold},
        )

    def get_signal_threshold(self) -> float:
        return self.config.roc_threshold


class RSIIndicator(BaseIndicator):
    """RSI indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        close = data["close"].values
        rsi_values = talib.RSI(close, timeperiod=self.config.rsi_period)
        latest_value = self._get_latest_value(rsi_values)

        signal = not np.isnan(latest_value) and latest_value > self.config.rsi_threshold
        score = (latest_value - 50) / 50 if latest_value > 50 else 0
        score = max(0, score)

        return IndicatorResult(
            name="RSI",
            values=rsi_values,
            signal=signal,
            score=score,
            latest_value=latest_value,
            metadata={
                "period": self.config.rsi_period,
                "threshold": self.config.rsi_threshold,
                "overbought": self.config.rsi_overbought,
                "oversold": self.config.rsi_oversold,
            },
        )

    def get_signal_threshold(self) -> float:
        return self.config.rsi_threshold


class MACDIndicator(BaseIndicator):
    """MACD indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        close = data["close"].values
        macd, macd_signal, macd_hist = talib.MACD(
            close,
            fastperiod=self.config.macd_fast,
            slowperiod=self.config.macd_slow,
            signalperiod=self.config.macd_signal,
        )

        macd_latest = self._get_latest_value(macd)
        signal_latest = self._get_latest_value(macd_signal)
        hist_latest = self._get_latest_value(macd_hist)

        signal = (
            not any(np.isnan([macd_latest, signal_latest, hist_latest]))
            and macd_latest > signal_latest
            and hist_latest > 0
        )
        score = 1.0 if signal else 0.0

        return IndicatorResult(
            name="MACD",
            values=macd,
            signal=signal,
            score=score,
            latest_value=macd_latest,
            metadata={
                "fast": self.config.macd_fast,
                "slow": self.config.macd_slow,
                "signal_period": self.config.macd_signal,
                "macd_signal": signal_latest,
                "histogram": hist_latest,
            },
        )

    def get_signal_threshold(self) -> float:
        return 0.0  # MACD signal is binary (crossover)


class VolumeROCIndicator(BaseIndicator):
    """Volume Rate of Change indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        volume = data["volume"].values
        vol_roc_values = talib.ROC(volume, timeperiod=self.config.volume_roc_period)
        latest_value = self._get_latest_value(vol_roc_values)

        signal = not np.isnan(latest_value) and latest_value > self.config.volume_roc_threshold
        score = min(latest_value / self.config.volume_roc_threshold, 2.0) if latest_value > 0 else 0
        score = max(0, score)

        return IndicatorResult(
            name="Volume_ROC",
            values=vol_roc_values,
            signal=signal,
            score=score,
            latest_value=latest_value,
            metadata={
                "period": self.config.volume_roc_period,
                "threshold": self.config.volume_roc_threshold,
            },
        )

    def get_signal_threshold(self) -> float:
        return self.config.volume_roc_threshold


class ATRIndicator(BaseIndicator):
    """Average True Range indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        high = data["high"].values
        low = data["low"].values
        close = data["close"].values

        atr_values = talib.ATR(high, low, close, timeperiod=self.config.atr_period)

        if len(atr_values) <= self.config.atr_lookback_period:
            signal = False
            score = 0.0
            latest_value = self._get_latest_value(atr_values)
        else:
            latest_value = self._get_latest_value(atr_values)
            # Compare recent ATR to historical average
            lookback_start = max(0, len(atr_values) - self.config.atr_lookback_period - 10)
            lookback_end = len(atr_values) - 10
            historical_atr = np.nanmean(atr_values[lookback_start:lookback_end])

            if not np.isnan(latest_value) and not np.isnan(historical_atr) and historical_atr > 0:
                atr_ratio = latest_value / historical_atr
                signal = atr_ratio > self.config.atr_multiplier
                score = min(atr_ratio / self.config.atr_multiplier, 2.0) if atr_ratio > 1 else 0
            else:
                signal = False
                score = 0.0

        return IndicatorResult(
            name="ATR",
            values=atr_values,
            signal=signal,
            score=max(0, score),
            latest_value=latest_value,
            metadata={
                "period": self.config.atr_period,
                "multiplier": self.config.atr_multiplier,
                "lookback_period": self.config.atr_lookback_period,
            },
        )

    def get_signal_threshold(self) -> float:
        return self.config.atr_multiplier


class StochasticIndicator(BaseIndicator):
    """Stochastic Oscillator indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        high = data["high"].values
        low = data["low"].values
        close = data["close"].values

        slowk, slowd = talib.STOCH(
            high,
            low,
            close,
            fastk_period=self.config.stoch_k_period,
            slowk_period=3,
            slowd_period=self.config.stoch_d_period,
        )

        k_latest = self._get_latest_value(slowk)
        d_latest = self._get_latest_value(slowd)

        signal = (
            not any(np.isnan([k_latest, d_latest]))
            and k_latest > d_latest
            and k_latest > self.config.stoch_threshold
        )
        score = 1.0 if signal else 0.0

        return IndicatorResult(
            name="Stochastic",
            values=slowk,
            signal=signal,
            score=score,
            latest_value=k_latest,
            metadata={
                "k_period": self.config.stoch_k_period,
                "d_period": self.config.stoch_d_period,
                "threshold": self.config.stoch_threshold,
                "d_value": d_latest,
            },
        )

    def get_signal_threshold(self) -> float:
        return self.config.stoch_threshold


class WilliamsRIndicator(BaseIndicator):
    """Williams %R indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        high = data["high"].values
        low = data["low"].values
        close = data["close"].values

        willr_values = talib.WILLR(high, low, close, timeperiod=self.config.willr_period)
        latest_value = self._get_latest_value(willr_values)

        signal = not np.isnan(latest_value) and latest_value > self.config.willr_threshold
        score = 1.0 if signal else 0.0

        return IndicatorResult(
            name="Williams_R",
            values=willr_values,
            signal=signal,
            score=score,
            latest_value=latest_value,
            metadata={"period": self.config.willr_period, "threshold": self.config.willr_threshold},
        )

    def get_signal_threshold(self) -> float:
        return self.config.willr_threshold


class BollingerBandsIndicator(BaseIndicator):
    """Bollinger Bands indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        close = data["close"].values

        upper, middle, lower = talib.BBANDS(
            close,
            timeperiod=self.config.bb_period,
            nbdevup=self.config.bb_std_dev,
            nbdevdn=self.config.bb_std_dev,
        )

        latest_close = close[-1] if len(close) > 0 else np.nan
        latest_upper = self._get_latest_value(upper)
        latest_lower = self._get_latest_value(lower)
        latest_middle = self._get_latest_value(middle)

        # Signal when price is near upper band (momentum)
        if not any(np.isnan([latest_close, latest_upper, latest_middle])):
            band_position = (latest_close - latest_middle) / (latest_upper - latest_middle)
            signal = band_position > 0.8  # Near upper band
            score = max(0, min(band_position, 1.0))
        else:
            signal = False
            score = 0.0

        return IndicatorResult(
            name="Bollinger_Bands",
            values=middle,
            signal=signal,
            score=score,
            latest_value=latest_close,
            metadata={
                "period": self.config.bb_period,
                "std_dev": self.config.bb_std_dev,
                "upper_band": latest_upper,
                "lower_band": latest_lower,
                "band_position": band_position if "band_position" in locals() else np.nan,
            },
        )

    def get_signal_threshold(self) -> float:
        return 0.8  # 80% toward upper band


class CCIIndicator(BaseIndicator):
    """Commodity Channel Index indicator implementation"""

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        high = data["high"].values
        low = data["low"].values
        close = data["close"].values

        cci_values = talib.CCI(high, low, close, timeperiod=self.config.cci_period)
        latest_value = self._get_latest_value(cci_values)

        signal = not np.isnan(latest_value) and latest_value > self.config.cci_threshold
        score = (
            min(abs(latest_value) / self.config.cci_threshold, 2.0)
            if abs(latest_value) > self.config.cci_threshold
            else 0
        )

        return IndicatorResult(
            name="CCI",
            values=cci_values,
            signal=signal,
            score=max(0, score),
            latest_value=latest_value,
            metadata={"period": self.config.cci_period, "threshold": self.config.cci_threshold},
        )

    def get_signal_threshold(self) -> float:
        return self.config.cci_threshold


class MomentumIndicator:
    """
    Comprehensive momentum indicator calculator with modular design
    """

    def __init__(self, config: MomentumConfig):
        self.config = config
        self._indicator_cache: dict[str, dict[str, IndicatorResult]] = {}

        # Initialize indicator classes
        self._indicators = {
            IndicatorType.ROC: ROCIndicator(config),
            IndicatorType.RSI: RSIIndicator(config),
            IndicatorType.MACD: MACDIndicator(config),
            IndicatorType.VOLUME_ROC: VolumeROCIndicator(config),
            IndicatorType.ATR: ATRIndicator(config),
            IndicatorType.STOCHASTIC: StochasticIndicator(config),
            IndicatorType.WILLIAMS_R: WilliamsRIndicator(config),
            IndicatorType.BOLLINGER_BANDS: BollingerBandsIndicator(config),
            IndicatorType.CCI: CCIIndicator(config),
        }

    def calculate_all_indicators(
        self, data: pd.DataFrame, ticker: str | None = None
    ) -> dict[str, IndicatorResult]:
        """
        Calculate all enabled technical indicators for the given data

        Args:
            data: OHLCV DataFrame
            ticker: Optional ticker symbol for caching

        Returns:
            dictionary of indicator results
        """
        if len(data) < self.config.min_data_points:
            logger.warning(f"Insufficient data points: {len(data)} < {self.config.min_data_points}")
            return {}

        # Check cache if ticker is provided
        if ticker and self.config.cache_indicators and ticker in self._indicator_cache:
            # Simple cache check - in production, you'd want timestamp-based validation
            return self._indicator_cache[ticker]

        results = {}
        enabled_indicators = self.config.get_enabled_indicators()

        for indicator_type in enabled_indicators:
            try:
                indicator = self._indicators[indicator_type]
                result = indicator.calculate(data)
                results[indicator_type.value] = result

            except Exception as e:
                logger.error(f"Error calculating {indicator_type.value}: {e}")
                # Create empty result for failed indicators
                results[indicator_type.value] = IndicatorResult(
                    name=indicator_type.value,
                    values=np.array([]),
                    signal=False,
                    score=0.0,
                    latest_value=np.nan,
                )

        # Cache results if ticker is provided
        if ticker and self.config.cache_indicators:
            self._indicator_cache[ticker] = results

        return results

    def calculate_momentum_score(
        self, indicator_results: dict[str, IndicatorResult]
    ) -> dict[str, Any]:
        """
        Calculate composite momentum score from individual indicator results

        Args:
            indicator_results: dictionary of indicator results

        Returns:
            dictionary containing total score, individual scores, and signals
        """
        if not indicator_results:
            return {
                "total_score": 0.0,
                "individual_scores": {},
                "signals": {},
                "signal_count": 0,
                "momentum_level": MomentumSignal.NONE.value,
            }

        individual_scores = {}
        signals = {}

        # Extract scores and signals from indicator results
        for indicator_name, result in indicator_results.items():
            individual_scores[indicator_name] = result.score
            signals[indicator_name] = result.signal

        # Calculate weighted total score
        total_score = 0.0
        total_weight = 0.0

        for indicator_name, score in individual_scores.items():
            weight = self.config.weights.get(indicator_name, 0.0)
            total_score += score * weight
            total_weight += weight

        # Normalize if weights don't sum to 1
        if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
            total_score = total_score / total_weight

        # Apply score normalization if enabled
        if self.config.normalize_scores:
            # Normalize to 0-2 range (2 being exceptional momentum)
            total_score = min(total_score, 2.0)

        # Count signals
        signal_count = sum(signals.values())

        # Determine momentum level
        momentum_level = self._classify_momentum(total_score)

        return {
            "total_score": total_score,
            "individual_scores": individual_scores,
            "signals": signals,
            "signal_count": signal_count,
            "momentum_level": momentum_level,
            "indicator_results": {
                name: result.to_dict() for name, result in indicator_results.items()
            },
        }

    def _classify_momentum(self, score: float) -> str:
        """Classify momentum strength based on score thresholds"""
        thresholds = self.config.score_thresholds

        if score >= thresholds["very_strong"]:
            return MomentumSignal.VERY_STRONG.value
        elif score >= thresholds["strong"]:
            return MomentumSignal.STRONG.value
        elif score >= thresholds["moderate"]:
            return MomentumSignal.MODERATE.value
        elif score >= thresholds["weak"]:
            return MomentumSignal.WEAK.value
        else:
            return MomentumSignal.NONE.value

    def analyze_single_stock(self, data: pd.DataFrame, ticker: str = None) -> dict[str, Any]:
        """
        Perform complete momentum analysis for a single stock

        Args:
            data: OHLCV DataFrame
            ticker: Optional ticker symbol

        Returns:
            Complete momentum analysis results
        """
        # Calculate all indicators
        indicator_results = self.calculate_all_indicators(data, ticker)

        if not indicator_results:
            return {
                "ticker": ticker,
                "error": "Failed to calculate indicators",
                "total_score": 0.0,
                "momentum_level": MomentumSignal.NONE.value,
            }

        # Calculate momentum score
        momentum_analysis = self.calculate_momentum_score(indicator_results)

        # Add ticker and metadata
        momentum_analysis["ticker"] = ticker
        momentum_analysis["data_points"] = len(data)
        momentum_analysis["analysis_date"] = (
            data["date"].iloc[-1] if "date" in data.columns else None
        )

        # Add latest price info
        if len(data) > 0:
            latest = data.iloc[-1]
            momentum_analysis["latest_close"] = latest["close"]
            momentum_analysis["latest_volume"] = latest["volume"]
            momentum_analysis["latest_high"] = latest["high"]
            momentum_analysis["latest_low"] = latest["low"]

        return momentum_analysis

    def get_indicator_summary(self, indicator_results: dict[str, IndicatorResult]) -> pd.DataFrame:
        """
        Create a summary DataFrame of all indicator results

        Args:
            indicator_results: dictionary of indicator results

        Returns:
            DataFrame with indicator summary
        """
        summary_data = []

        for name, result in indicator_results.items():
            summary_data.append(
                {
                    "indicator": result.name,
                    "signal": result.signal,
                    "score": result.score,
                    "latest_value": result.latest_value,
                    "threshold": (
                        self._indicators[IndicatorType(name)].get_signal_threshold()
                        if IndicatorType(name) in self._indicators
                        else np.nan
                    ),
                }
            )

        return pd.DataFrame(summary_data)

    def clear_cache(self):
        """Clear the indicator cache"""
        self._indicator_cache.clear()

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the current cache state"""
        return {
            "cached_tickers": list(self._indicator_cache.keys()),
            "cache_size": len(self._indicator_cache),
            "cache_enabled": self.config.cache_indicators,
        }


# Utility functions for creating common configurations
def create_conservative_config(api_key: str) -> MomentumConfig:
    """Create a conservative momentum configuration"""
    return MomentumConfig(
        api_key=api_key,
        roc_threshold=20.0,  # Higher price movement required
        rsi_threshold=65.0,  # Higher RSI threshold
        volume_roc_threshold=200.0,  # Higher volume requirement
        atr_multiplier=2.0,  # Higher volatility requirement
        weights={"roc": 0.30, "volume_roc": 0.25, "macd": 0.20, "rsi": 0.15, "atr_expansion": 0.10},
    )


def create_aggressive_config(api_key: str) -> MomentumConfig:
    """Create an aggressive momentum configuration"""
    return MomentumConfig(
        api_key=api_key,
        roc_threshold=10.0,  # Lower price movement threshold
        rsi_threshold=55.0,  # Lower RSI threshold
        volume_roc_threshold=100.0,  # Lower volume requirement
        atr_multiplier=1.2,  # Lower volatility requirement
        # Enable additional indicators
        bb_enabled=True,
        cci_enabled=True,
        weights={
            "roc": 0.20,
            "macd": 0.20,
            "volume_roc": 0.15,
            "rsi": 0.15,
            "atr_expansion": 0.10,
            "stochastic": 0.10,
            "williams_r": 0.05,
            "bollinger_bands": 0.03,
            "cci": 0.02,
        },
    )


def create_balanced_config(api_key: str) -> MomentumConfig:
    """Create a balanced momentum configuration (default)"""
    return MomentumConfig(api_key=api_key)  # Uses default values


# Example usage and testing
if __name__ == "__main__":
    # Create sample configuration
    config = create_balanced_config("test_api_key")

    # Create momentum indicator instance
    momentum_calc = MomentumIndicator(config)

    # Create sample data for testing
    dates = pd.date_range("2024-01-01", "2024-05-31", freq="D")
    np.random.seed(42)

    sample_data = pd.DataFrame(
        {
            "date": dates,
            "open": 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            "high": lambda x: x["open"] + np.random.rand(len(dates)) * 2,
            "low": lambda x: x["open"] - np.random.rand(len(dates)) * 2,
            "close": lambda x: (x["high"] + x["low"]) / 2 + np.random.randn(len(dates)) * 0.2,
            "volume": np.random.randint(1000000, 5000000, len(dates)),
        }
    )

    # Calculate indicators
    print("Testing MomentumIndicator with sample data...")
    results = momentum_calc.analyze_single_stock(sample_data, "TEST")

    print(f"Momentum Score: {results['total_score']:.2f}")
    print(f"Momentum Level: {results['momentum_level']}")
    print(f"Signals Triggered: {results['signal_count']}")
    print(f"Individual Scores: {results['individual_scores']}")
