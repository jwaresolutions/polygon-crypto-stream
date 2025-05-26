import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from connectors.polygon import PolygonConnector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def fetch_historical_data(
    symbol: str = "BTCUSD",
    days: int = 7
) -> None:
    """Fetch historical crypto data"""
    connector = PolygonConnector()
    
    try:
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Fetching {symbol} data from {start_date} to {end_date}")
        
        data = await connector.get_historical_data(symbol, start_date, end_date)
        logger.info(f"Retrieved {len(data)} historical bars")
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_historical_data())