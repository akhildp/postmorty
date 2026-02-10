"""Technical indicator calculations using pandas/numpy (no pandas_ta dependency)."""

import logging
from typing import List, Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    Calculate all 22 technical indicators using pure pandas/numpy.
    
    Indicators:
    - Trend: EMA 10, 36, 100, 200
    - Volatility: BB Basis 20, BB Upper 20, BB Lower 20
    - Momentum: RSI 14
    - Hybrid: Supertrend (7, 3.0), Supertrend Direction
    - Custom: TD Sequential
    - Candle Metrics: Body Range %, Full Range %
    - Distance: % from EMA 10/36/100/200, % from BB Basis
    - Streaks: Streak BB Basis, Streak EMA 36/100/200
    """
    
    def calculate_all(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Calculate all indicators for OHLCV data.
        
        Args:
            records: List of dictionaries with OHLCV data
            
        Returns:
            DataFrame with OHLCV + all 22 indicators
        """
        if not records:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        # Calculate all indicators
        df = self._calculate_emas(df)
        df = self._calculate_bollinger_bands(df)
        df = self._calculate_rsi(df)
        df = self._calculate_supertrend(df)
        df = self._calculate_td_sequential(df)
        df = self._calculate_candle_metrics(df)
        df = self._calculate_distance_metrics(df)
        df = self._calculate_streaks(df)
        
        return df
    
    def _calculate_emas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA 10, 36, 100, 200."""
        df["ema_10"] = df["close"].ewm(span=10, adjust=False).mean()
        df["ema_36"] = df["close"].ewm(span=36, adjust=False).mean()
        df["ema_100"] = df["close"].ewm(span=100, adjust=False).mean()
        df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()
        return df
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands (20, 2σ)."""
        df["bb_basis_20"] = df["close"].rolling(window=20).mean()
        rolling_std = df["close"].rolling(window=20).std()
        df["bb_upper_20"] = df["bb_basis_20"] + (2 * rolling_std)
        df["bb_lower_20"] = df["bb_basis_20"] - (2 * rolling_std)
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate RSI 14."""
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        df["rsi_14"] = 100 - (100 / (1 + rs))
        return df
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 7) -> pd.Series:
        """Calculate Average True Range."""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()
        return atr
    
    def _calculate_supertrend(self, df: pd.DataFrame, period: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
        """Calculate Supertrend (7, 3.0)."""
        hl2 = (df["high"] + df["low"]) / 2
        atr = self._calculate_atr(df, period)
        
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        
        close = df["close"]
        
        for i in range(len(df)):
            if i == 0:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
                continue
            
            # Lower band
            if lower_band.iloc[i] > lower_band.iloc[i-1] or close.iloc[i-1] < lower_band.iloc[i-1]:
                pass  # keep current lower_band
            else:
                lower_band.iloc[i] = lower_band.iloc[i-1]
            
            # Upper band
            if upper_band.iloc[i] < upper_band.iloc[i-1] or close.iloc[i-1] > upper_band.iloc[i-1]:
                pass  # keep current upper_band
            else:
                upper_band.iloc[i] = upper_band.iloc[i-1]
            
            # Supertrend calculation
            if supertrend.iloc[i-1] == upper_band.iloc[i-1]:
                if close.iloc[i] > upper_band.iloc[i]:
                    supertrend.iloc[i] = lower_band.iloc[i]
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = upper_band.iloc[i]
                    direction.iloc[i] = -1
            else:
                if close.iloc[i] < lower_band.iloc[i]:
                    supertrend.iloc[i] = upper_band.iloc[i]
                    direction.iloc[i] = -1
                else:
                    supertrend.iloc[i] = lower_band.iloc[i]
                    direction.iloc[i] = 1
        
        df["supertrend_7_3"] = supertrend
        df["supertrend_direction"] = direction
        return df
    
    def _calculate_td_sequential(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate TD Sequential count (custom implementation).
        
        Compares close to close 4 bars back.
        Increments up for higher, down for lower.
        Clamped to [-13, +13].
        """
        df["td_seq"] = 0
        
        if len(df) < 5:
            return df
        
        counts = [0] * len(df)
        
        for i in range(4, len(df)):
            current_close = df.iloc[i]["close"]
            prev_close_4 = df.iloc[i - 4]["close"]
            prev_count = counts[i - 1]
            
            if current_close > prev_close_4:
                # Bullish count
                if prev_count > 0:
                    counts[i] = min(prev_count + 1, 13)
                else:
                    counts[i] = 1
            elif current_close < prev_close_4:
                # Bearish count
                if prev_count < 0:
                    counts[i] = max(prev_count - 1, -13)
                else:
                    counts[i] = -1
            else:
                # Equal - reset to 0
                counts[i] = 0
        
        df["td_seq"] = counts
        return df
    
    def _calculate_candle_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate body range % and full range %."""
        # Body Range %: (close - open) / open * 100
        df["pct_body_range"] = ((df["close"] - df["open"]) / df["open"]) * 100
        
        # Full Range %: (high - low) / low * 100
        df["pct_full_range"] = ((df["high"] - df["low"]) / df["low"]) * 100
        
        return df
    
    def _calculate_distance_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate percentage distance from EMAs and BB basis."""
        # % from EMA 10
        df["pct_from_ema_10"] = ((df["close"] - df["ema_10"]) / df["ema_10"]) * 100
        
        # % from EMA 36
        df["pct_from_ema_36"] = ((df["close"] - df["ema_36"]) / df["ema_36"]) * 100
        
        # % from EMA 100
        df["pct_from_ema_100"] = ((df["close"] - df["ema_100"]) / df["ema_100"]) * 100
        
        # % from EMA 200
        df["pct_from_ema_200"] = ((df["close"] - df["ema_200"]) / df["ema_200"]) * 100
        
        # % from BB Basis 20
        df["pct_from_bb_basis_20"] = ((df["close"] - df["bb_basis_20"]) / df["bb_basis_20"]) * 100
        
        return df
    
    def _calculate_streaks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate streak indicators.
        
        Consecutive closes above/below a reference.
        Positive count = above, negative count = below.
        Resets to 0 on cross.
        """
        df["streak_bb_basis_20"] = self._calculate_streak(df["close"], df["bb_basis_20"])
        df["streak_ema_36"] = self._calculate_streak(df["close"], df["ema_36"])
        df["streak_ema_100"] = self._calculate_streak(df["close"], df["ema_100"])
        df["streak_ema_200"] = self._calculate_streak(df["close"], df["ema_200"])
        
        return df
    
    def _calculate_streak(self, close: pd.Series, reference: pd.Series) -> pd.Series:
        """
        Calculate streak for a single reference.
        
        Args:
            close: Close price series
            reference: Reference value series (e.g., EMA)
            
        Returns:
            Streak count series
        """
        streaks = [0] * len(close)
        
        for i in range(len(close)):
            if pd.isna(reference.iloc[i]):
                streaks[i] = 0
                continue
            
            close_val = close.iloc[i]
            ref_val = reference.iloc[i]
            
            if i == 0:
                if close_val > ref_val:
                    streaks[i] = 1
                elif close_val < ref_val:
                    streaks[i] = -1
                else:
                    streaks[i] = 0
            else:
                prev_streak = streaks[i - 1]
                
                if close_val > ref_val:
                    # Above reference
                    if prev_streak > 0:
                        streaks[i] = prev_streak + 1
                    else:
                        streaks[i] = 1
                elif close_val < ref_val:
                    # Below reference
                    if prev_streak < 0:
                        streaks[i] = prev_streak - 1
                    else:
                        streaks[i] = -1
                else:
                    # Equal - continue previous streak direction
                    streaks[i] = prev_streak
        
        return pd.Series(streaks, index=close.index)
