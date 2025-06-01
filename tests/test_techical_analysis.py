import numpy as np
import pandas as pd
import pytest

from abzu.finance.ta.indicators import IndicatorCalculator


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    data = {
        "open": np.random.uniform(90, 110, 100),
        "high": np.random.uniform(95, 115, 100),
        "low": np.random.uniform(85, 105, 100),
        "close": np.random.uniform(90, 110, 100),
        "volume": np.random.randint(100000, 1000000, 100),
    }

    return pd.DataFrame(data, index=dates)


def test_initialization(sample_ohlcv_data):
    """Test calculator initialization"""
    calc = IndicatorCalculator(sample_ohlcv_data)
    assert calc is not None


def test_missing_columns(sample_ohlcv_data):
    """Test error on missing columns"""
    bad_df = sample_ohlcv_data.drop(columns=["close"])
    with pytest.raises(ValueError):
        IndicatorCalculator(bad_df)


def test_calculate_all_indicators(sample_ohlcv_data):
    """Test calculation of all indicators"""
    calc = IndicatorCalculator(sample_ohlcv_data)
    indicators = calc.calculate_all_indicators()

    # Check that all indicators are calculated
    assert indicators.rsi is not None
    assert indicators.macd is not None
    assert indicators.bb_upper is not None
    assert indicators.atr is not None


def test_indicator_lengths(sample_ohlcv_data):
    """Test that indicators have correct length"""
    calc = IndicatorCalculator(sample_ohlcv_data)
    indicators = calc.calculate_all_indicators()

    # All indicators should have same length as input
    assert len(indicators.rsi) == len(sample_ohlcv_data)
    assert len(indicators.macd) == len(sample_ohlcv_data)


def test_custom_indicators(sample_ohlcv_data):
    """Test custom indicator calculations"""
    calc = IndicatorCalculator(sample_ohlcv_data)
    calc.calculate_all_indicators()
    calc.add_custom_indicators()

    result_df = calc.get_dataframe()

    # Check custom indicators exist
    assert "volume_ratio" in result_df.columns
    assert "atr_pct" in result_df.columns
    assert "bb_position" in result_df.columns
