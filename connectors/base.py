from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator
from datetime import datetime

class DataConnector(ABC):
    """Base class for market data connectors"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the data provider"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the data provider"""
        pass
    
    @abstractmethod
    async def stream_minute_bars(self, symbol: str) -> AsyncIterator[Dict[str, Any]]:
        """Stream minute bar data for a given symbol"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> list[Dict[str, Any]]:
        """Get historical minute bar data"""
        pass