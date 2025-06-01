from datetime import datetime

import numpy as np
import pandas as pd

from abzu.finance.ta.analysis import TechnicalAnalyzer
from abzu.finance.ta.patterns import PatternDetector
from abzu.finance.ta.prompts import PromptGenerator


def generate_sample_data(days: int = 100) -> pd.DataFrame:
    """Generate sample OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

    # Generate realistic price data
    np.random.seed(42)
    price: float = 100.0
    data = []

    for date in dates:
        # Random walk with trend
        change: float = np.random.normal(0.001, 0.02)
        price *= 1.0 + change

        # OHLC with realistic relationships
        open_price = price * (1 + np.random.normal(0, 0.005))
        close_price = price
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
        volume = int(np.random.normal(1000000, 200000))

        data.append(
            {
                "date": date,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            }
        )

    return pd.DataFrame(data).set_index("date")


"""Run example analysis"""

# Generate or load your data
print("Generating sample data...")
df = generate_sample_data(100)

# Initialize analyzer
print("\nInitializing technical analyzer...")
analyzer = TechnicalAnalyzer(df)

# Get market snapshot
print("\n=== MARKET SNAPSHOT ===")
snapshot = analyzer.get_market_snapshot()
print(f"Current Price: ${snapshot.price:.2f}")
print(
    f"Trend: Short={snapshot.trend_short}, Medium={snapshot.trend_medium}, Long={snapshot.trend_long}"
)
print(f"RSI Status: {snapshot.rsi_status}")
print(f"Risk Level: {snapshot.risk_level}")

# Detect patterns
print("\n=== PATTERN DETECTION ===")
pattern_detector = PatternDetector(df)
active_patterns = pattern_detector.detect_active_patterns(lookback=5)

if active_patterns:
    print("Active Candlestick Patterns:")
    for pattern in active_patterns:
        print(f"- {pattern['pattern']} ({pattern['signal']}) on {pattern['date']}")
else:
    print("No active patterns detected")

# Generate prompts for LLM
print("\n=== GENERATING ANALYSIS PROMPTS ===")
prompt_gen = PromptGenerator(analyzer)

# Generate comprehensive prompt
comprehensive_prompt = prompt_gen.generate_comprehensive_prompt()
print("\nComprehensive Analysis Prompt:")
print(comprehensive_prompt[:500] + "...\n")  # Show first 500 chars

# Generate pattern-focused prompt
pattern_prompt = prompt_gen.generate_pattern_focused_prompt()
print("\nPattern Analysis Prompt:")
print(pattern_prompt[:500] + "...\n")

# Get full analysis summary
print("\n=== ANALYSIS SUMMARY ===")
summary = analyzer.generate_analysis_summary()

print("\nKey Indicators:")
for name, value in summary["indicator_values"].items():
    if not pd.isna(value):
        print(f"- {name}: {value:.2f}")

print("\nPrice Levels:")
for name, value in summary["price_levels"].items():
    print(f"- {name}: ${value:.2f}")

# Show entry/exit signals
if snapshot.entry_signals:
    print("\nEntry Signals:")
    for signal in snapshot.entry_signals:
        print(f"- {signal['type']} at ${signal['price']:.2f}")

if snapshot.exit_signals:
    print("\nExit Signals:")
    for signal in snapshot.exit_signals:
        print(f"- {signal['type']} at ${signal['price']:.2f}")
