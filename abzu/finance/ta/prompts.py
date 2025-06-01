from datetime import datetime
from typing import Dict, List

import numpy as np

from .analysis import TechnicalAnalyzer


class PromptGenerator:
    """Generate structured prompts for LLM analysis"""

    def __init__(self, analyzer: TechnicalAnalyzer):
        self.analyzer = analyzer
        self.df = analyzer.df

    def generate_comprehensive_prompt(self) -> str:
        """Generate comprehensive technical analysis prompt"""
        snapshot = self.analyzer.get_market_snapshot()
        summary = self.analyzer.generate_analysis_summary()

        prompt = f"""
TECHNICAL ANALYSIS REQUEST

Asset: [SYMBOL]
Timeframe: Daily
Analysis Date: {snapshot.timestamp.strftime('%Y-%m-%d')}

## MARKET OVERVIEW
Current Price: ${snapshot.price:.2f}
Volume: {snapshot.volume:,.0f} ({snapshot.volume_status} relative to average)

## TREND ANALYSIS
- Short-term (10-day): {snapshot.trend_short.upper()}
- Medium-term (20-day): {snapshot.trend_medium.upper()}
- Long-term (50-day): {snapshot.trend_long.upper()}

## KEY TECHNICAL LEVELS
Support Levels: {self._format_price_levels(snapshot.support_levels)}
Resistance Levels: {self._format_price_levels(snapshot.resistance_levels)}

## MOMENTUM INDICATORS
- RSI(14): {summary['indicator_values']['rsi']:.2f} ({snapshot.rsi_status})
- MACD Status: {snapshot.macd_status.replace('_', ' ').title()}
- ADX(14): {summary['indicator_values']['adx']:.2f}

## VOLATILITY METRICS
- ATR%: {snapshot.volatility:.2f}%
- Risk Level: {snapshot.risk_level.upper()}
- Bollinger Band Width: {self.df['bb_width'].iloc[-1]:.3f}

## RECENT PRICE ACTION
{self._format_recent_prices()}

## ACTIVE SIGNALS
{self._format_signals(snapshot.entry_signals, snapshot.exit_signals)}

## DETECTED PATTERNS
{self._format_patterns(summary['active_patterns'])}

Please provide:
1. Comprehensive market assessment
2. Primary trend direction and strength
3. Key support/resistance levels to watch
4. Risk/reward analysis for potential trades
5. Recommended trading strategy
6. Critical levels for stop-loss placement
"""

        return prompt

    def generate_pattern_focused_prompt(self) -> str:
        """Generate pattern-focused analysis prompt"""
        patterns = self.analyzer.pattern_detector.detect_active_patterns()
        chart_patterns = self.analyzer.pattern_detector.detect_chart_patterns()
        sr_levels = self.analyzer.pattern_detector.find_support_resistance()

        prompt = f"""
PATTERN RECOGNITION ANALYSIS

## CANDLESTICK PATTERNS (Last 5 Days)
{self._format_candlestick_patterns(patterns)}

## CHART PATTERNS
{self._format_chart_patterns(chart_patterns)}

## SUPPORT & RESISTANCE ANALYSIS
Support Levels: {self._format_price_levels(sr_levels['support'])}
Resistance Levels: {self._format_price_levels(sr_levels['resistance'])}

## PRICE STRUCTURE
20-Day Range: ${self.df['low'].tail(20).min():.2f} - ${self.df['high'].tail(20).max():.2f}
Current Position in Range: {((self.df['close'].iloc[-1] - self.df['low'].tail(20).min()) / (self.df['high'].tail(20).max() - self.df['low'].tail(20).min()) * 100):.1f}%

Please analyze:
1. Significance of detected patterns
2. Pattern reliability and expected outcomes
3. Key breakout/breakdown levels
4. Pattern-based price targets
5. Failed pattern risks
"""

        return prompt

    def generate_momentum_prompt(self) -> str:
        """Generate momentum-focused analysis prompt"""
        latest = self.df.iloc[-1]

        # Calculate momentum metrics
        rsi_divergence = self._check_divergence("rsi", "close")
        macd_divergence = self._check_divergence("macd_histogram", "close")

        prompt = f"""
MOMENTUM ANALYSIS

## CURRENT MOMENTUM INDICATORS
- RSI(14): {latest['rsi']:.2f}
- Stochastic %K: {latest['stoch_k']:.2f}, %D: {latest['stoch_d']:.2f}
- CCI(20): {latest['cci']:.2f}
- Williams %R: {latest['williams_r']:.2f}
- MFI(14): {latest['mfi']:.2f}

## MOMENTUM TRENDS (Last 10 Days)
RSI Values: {self.df['rsi'].tail(10).round(2).tolist()}
MACD Histogram: {self.df['macd_histogram'].tail(10).round(4).tolist()}

## DIVERGENCE ANALYSIS
RSI Divergence: {rsi_divergence}
MACD Divergence: {macd_divergence}

## MOMENTUM SHIFTS
{self._analyze_momentum_shifts()}

Please analyze:
1. Overall momentum strength and direction
2. Overbought/oversold conditions
3. Divergence implications
4. Momentum continuation probability
5. Potential reversal signals
"""

        return prompt

    def generate_risk_analysis_prompt(self) -> str:
        """Generate risk-focused analysis prompt"""
        snapshot = self.analyzer.get_market_snapshot()
        latest = self.df.iloc[-1]

        # Calculate risk metrics
        daily_returns = self.df["close"].pct_change()
        volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized

        prompt = f"""
RISK ANALYSIS

## VOLATILITY METRICS
- Current ATR: ${latest['atr']:.2f} ({latest['atr_pct']:.2f}% of price)
- Annualized Volatility: {volatility:.1f}%
- Bollinger Band Width: {latest['bb_width']:.3f}
- Current Risk Level: {snapshot.risk_level.upper()}

## POSITION SIZING RECOMMENDATIONS
Based on ATR (2% risk per trade):
- Position Size: {(0.02 / (latest['atr_pct'] / 100)):.1f}% of portfolio
- Stop Loss Distance: ${latest['atr'] * 1.5:.2f} ({(latest['atr'] * 1.5 / latest['close'] * 100):.1f}%)

## KEY RISK LEVELS
- Support Break: ${min(snapshot.support_levels) if snapshot.support_levels else 0:.2f}
- Resistance Break: ${min(snapshot.resistance_levels) if snapshot.resistance_levels else 0:.2f}

Please provide:
1. Current market risk assessment
2. Optimal position sizing recommendations
3. Stop-loss placement strategies
4. Risk/reward scenarios
5. Volatility-based trading adjustments
"""

        return prompt

    def _format_price_levels(self, levels: List[float]) -> str:
        """Format price levels for display"""
        if not levels:
            return "None identified"
        return ", ".join([f"${level:.2f}" for level in sorted(levels)])

    def _format_recent_prices(self) -> str:
        """Format recent price action"""
        recent = self.df.tail(5)
        lines = []
        for idx, row in recent.iterrows():
            date = idx.strftime("%Y-%m-%d") if isinstance(idx, datetime) else str(idx)
            lines.append(
                f"{date}: O:{row['open']:.2f} H:{row['high']:.2f} "
                f"L:{row['low']:.2f} C:{row['close']:.2f} V:{row['volume']:,.0f}"
            )
        return "\n".join(lines)

    def _format_signals(self, entry_signals: List[Dict], exit_signals: List[Dict]) -> str:
        """Format trading signals"""
        lines = []

        if entry_signals:
            lines.append("ENTRY SIGNALS:")
            for signal in entry_signals:
                lines.append(
                    f"- {signal['type']}: {signal.get('strength', 'N/A')} strength at ${signal['price']:.2f}"
                )

        if exit_signals:
            lines.append("\nEXIT SIGNALS:")
            for signal in exit_signals:
                lines.append(
                    f"- {signal['type']}: {signal.get('strength', 'N/A')} strength at ${signal['price']:.2f}"
                )

        return "\n".join(lines) if lines else "No active signals"

    def _format_patterns(self, patterns: List[Dict]) -> str:
        """Format detected patterns"""
        if not patterns:
            return "No significant patterns detected"

        lines = []
        for pattern in patterns:
            lines.append(f"- {pattern['pattern']} ({pattern['signal']}) on {pattern['date']}")

        return "\n".join(lines)

    def _format_candlestick_patterns(self, patterns: List[Dict]) -> str:
        """Format candlestick patterns"""
        if not patterns:
            return "No candlestick patterns detected"

        bullish = [p for p in patterns if p["signal"] == "bullish"]
        bearish = [p for p in patterns if p["signal"] == "bearish"]

        lines = []
        if bullish:
            lines.append("Bullish Patterns:")
            for p in bullish:
                lines.append(f"- {p['pattern']} on {p['date']}")

        if bearish:
            lines.append("\nBearish Patterns:")
            for p in bearish:
                lines.append(f"- {p['pattern']} on {p['date']}")

        return "\n".join(lines)

    def _format_chart_patterns(self, patterns: Dict) -> str:
        """Format chart patterns"""
        if not patterns:
            return "No chart patterns detected"

        lines = []
        for pattern_type, pattern_data in patterns.items():
            lines.append(f"{pattern_type.replace('_', ' ').title()}: {pattern_data}")

        return "\n".join(lines)

    def _check_divergence(self, indicator: str, price_col: str = "close") -> str:
        """Check for divergence between indicator and price"""
        if indicator not in self.df.columns:
            return "N/A"

        # Simple divergence check over last 20 periods
        lookback = 20
        if len(self.df) < lookback:
            return "Insufficient data"

        price_trend = np.polyfit(range(lookback), self.df[price_col].tail(lookback).values, 1)[0]
        indicator_trend = np.polyfit(range(lookback), self.df[indicator].tail(lookback).values, 1)[
            0
        ]

        if price_trend > 0 and indicator_trend < 0:
            return "Bearish divergence detected"
        elif price_trend < 0 and indicator_trend > 0:
            return "Bullish divergence detected"
        else:
            return "No divergence"

    def _analyze_momentum_shifts(self) -> str:
        """Analyze recent momentum shifts"""
        if len(self.df) < 10:
            return "Insufficient data for momentum shift analysis"

        recent_rsi = self.df["rsi"].tail(10)
        recent_macd_hist = self.df["macd_histogram"].tail(10)

        lines = []

        # RSI momentum shift
        if recent_rsi.iloc[-1] > 50 and recent_rsi.iloc[-5] < 50:
            lines.append("- RSI crossed above 50 (bullish momentum shift)")
        elif recent_rsi.iloc[-1] < 50 and recent_rsi.iloc[-5] > 50:
            lines.append("- RSI crossed below 50 (bearish momentum shift)")

        # MACD histogram expansion/contraction
        hist_expanding = abs(recent_macd_hist.iloc[-1]) > abs(recent_macd_hist.iloc[-3])
        if hist_expanding and recent_macd_hist.iloc[-1] > 0:
            lines.append("- MACD histogram expanding positive (strengthening bullish momentum)")
        elif hist_expanding and recent_macd_hist.iloc[-1] < 0:
            lines.append("- MACD histogram expanding negative (strengthening bearish momentum)")

        return "\n".join(lines) if lines else "No significant momentum shifts detected"
