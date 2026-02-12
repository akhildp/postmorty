import pandas as pd
from typing import List, Type
from postmorty.core import database
from postmorty.core.engine import Strategy, StrategyResult

class Scanner:
    def __init__(self, strategy_class: Type[Strategy]):
        self.strategy = strategy_class()
        
    def scan(self, min_market_cap: int = 500_000_000, max_market_cap: int = 5_000_000_000) -> List[StrategyResult]:
        """
        Scans the market for setup matches.
        """
        conn = database.get_connection()
        cur = conn.cursor()
        
        # 1. Universe Selection (Market Cap Filter)
        print("Fetching universe...")
        cur.execute("""
            SELECT symbol FROM company_valuations 
            WHERE market_cap >= %s AND market_cap <= %s
            ORDER BY market_cap DESC
        """, (min_market_cap, max_market_cap))
        
        symbols = [row[0] for row in cur.fetchall()]
        print(f"Found {len(symbols)} candidates in range ${min_market_cap/1e6:,.0f}M - ${max_market_cap/1e6:,.0f}M.")
        
        results = []
        
        # 2. Batch Processing (Fetch data for each)
        # Note: For speed, we could fetch ALL candles in one query, but logic is easier per symbol.
        for i, symbol in enumerate(symbols):
            try:
                # Fetch last 60 days to ensure enough for 50-day window + lookback
                cur.execute("""
                    SELECT * FROM candles_d1 
                    WHERE symbol = %s 
                    ORDER BY timestamp ASC 
                    LIMIT 60
                """, (symbol,))
                
                rows = cur.fetchall()
                if not rows:
                    continue
                    
                # Convert to DataFrame
                # We need column names. 
                # Ideally, simple fetch:
                cols = [desc[0] for desc in cur.description]
                df = pd.DataFrame(rows, columns=cols)
                
                # Run Strategy
                result = self.strategy.analyze(symbol, df)
                
                if result.score > 0 or any("SELL" in s for s in result.signals):
                    results.append(result)
                    
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
                
            if i % 100 == 0 and i > 0:
                print(f"Scanned {i}/{len(symbols)}...")
                
        cur.close()
        conn.close()
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results
