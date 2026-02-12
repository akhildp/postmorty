from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd

@dataclass
class StrategyResult:
    symbol: str
    score: float = 0.0
    signals: List[str] = field(default_factory=list)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "score": self.score,
            "signals": self.signals,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "metadata": self.metadata
        }

class Strategy(ABC):
    @abstractmethod
    def analyze(self, symbol: str, df: pd.DataFrame) -> StrategyResult:
        """
        Analyzes the given DataFrame (history) for a symbol and returns a result.
        The DataFrame should contain standard OHLCV and indicator columns.
        """
        pass
