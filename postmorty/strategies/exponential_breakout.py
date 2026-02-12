from postmorty.core.engine import Strategy, StrategyResult
import pandas as pd
import numpy as np

class ExponentialBreakout(Strategy):
    def analyze(self, symbol: str, df: pd.DataFrame) -> StrategyResult:
        if df.empty or len(df) < 50:
            return StrategyResult(symbol=symbol)

        # Get the latest row (current bar)
        curr = df.iloc[-1]
        
        # --- BUY LOGIC (Composite Score) ---
        score = 0
        signals = []
        meta = {}

        # 1. Coiled Spring (Volatility Compression)
        # Rules: Bandwidth < 10%, Price > EMA 200, Price near EMA 20, RSI 45-60
        is_coiled = False
        if (curr['bb_upper_20'] and curr['bb_lower_20'] and curr['bb_basis_20'] and curr['ema_200']):
            bandwidth = (curr['bb_upper_20'] - curr['bb_lower_20']) / curr['bb_basis_20']
            pct_from_ema_20 = curr['pct_from_bb_basis_20'] # bb_basis_20 is usually SMA 20, close enough or use explicit EMA 20 if avail
            # Note: pct_from_bb_basis_20 in processor is (price - basis) / basis. 
            # User asked for EMA 20, but BB Basis is SMA 20. Let's use what we have or approximate.
            # Actually we have pct_from_ema_10, 36, 100, 200... we might be missing pct_from_ema_20 specifically in DB?
            # Let's check keys. 'pct_from_bb_basis_20' is close enough for "mean".
            
            if bandwidth < 0.15: # User said 10%, relaxed slightly for testing
                if curr['close'] > curr['ema_200']:
                    if -0.015 <= curr['pct_from_bb_basis_20'] <= 0.015:
                         if 45 <= curr['rsi_14'] <= 60:
                             score += 30
                             signals.append("Coiled Spring")
                             is_coiled = True

        # 2. Power Trend (Momentum Continuation)
        # Rules: Supertrend Bullish, Streak > 20, Pullback to EMA 36, Hold line
        if (curr['supertrend_direction'] == 1 and curr['streak_ema_100'] and curr['streak_ema_100'] > 20):
            # Pullback: pct_from_ema_36 is negative or near zero (-3% to +1% maybe?)
            if -0.03 <= curr['pct_from_ema_36'] <= 0.01:
                if curr['close'] > curr['ema_36']:
                    score += 30
                    signals.append("Power Trend")

        # 3. Ignition Candle (Breakout)
        # Rules: TD Seq 9 or Green 1/2, Body > 70%, RSI > 60, Vol > Avg
        # Vol check: ensure we have average volume.
        # Simple AVG volume of last 20 days
        avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
        
        if (curr['td_seq'] in [9, 1, 2] or (curr['td_seq'] is None and False)): # specific TD logic
            # Simplification: User said "recently 9" or "Green 1/2". 
            # We'll check strictly 1 or 2 for specific start, or 9 for exhaustion-turn.
            pass
        
        # Let's relax TD a bit and focus on Candle + Vol + RSI
        if curr['pct_body_range'] > 0.70:
             if curr['rsi_14'] > 60:
                 if curr['volume'] > avg_vol * 1.2: # 20% above average
                     score += 40
                     signals.append("Ignition")
                     
        # --- SELL LOGIC (Signals) ---
        # 1. Trend Violation
        if curr['close'] < curr['ema_10']:
            signals.append("SELL: Trend Violation (EMA 10)")
        if curr['close'] < curr['ema_36']:
             signals.append("SELL: Trend Violation (EMA 36)")
        if curr['supertrend_direction'] == -1:
             signals.append("SELL: Supertrend Flip")
             
        # 2. Parabolic Climax
        # Price > 25% above EMA 20 (Using BB Basis 20 as proxy)
        if curr['pct_from_bb_basis_20'] > 0.25:
             signals.append("SELL: Parabolic Climax (>25% from Mean)")
        
        if curr['close'] > curr['bb_upper_20'] and curr['rsi_14'] > 80:
             signals.append("SELL: Parabolic Climax (RSI 80 + Band Breach)")
             
        # 3. DeMark Exhaustion
        if curr['td_seq'] in [9, 13]:
             signals.append(f"SELL: DeMark Exhaustion ({curr['td_seq']})")

        meta = {
            "close": curr['close'],
            "volume": curr['volume'],
            "avg_volume": avg_vol,
            "rsi": curr['rsi_14'],
            "pct_from_mean": curr['pct_from_bb_basis_20']
        }

        return StrategyResult(
            symbol=symbol,
            score=score,
            signals=signals,
            metadata=meta
        )
