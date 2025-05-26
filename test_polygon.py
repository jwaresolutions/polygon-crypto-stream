import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from connectors.polygon import PolygonConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test both websocket streaming and REST API"""
    connector = PolygonConnector()
    
    try:
        # Test 1: Basic connection
        logger.info("Test 1: Testing connection...")
        await connector.connect()
        logger.info("✓ Connection successful")

        # Test 2: Test REST API for current data
        logger.info("\nTest 2: Testing REST API historical data for BTC...")
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(hours=1)
        
        # Using the correct symbol format for crypto
        historical_data = await connector.get_historical_data("BTCUSD", start_date, end_date)
        logger.info(f"✓ Retrieved {len(historical_data)} historical bars")
        if historical_data:
            logger.info(f"Sample bar: {historical_data[0]}")

        # Test 3: Stream test
        logger.info("\nTest 3: Testing live streaming data for BTC...")
        try:
            async with asyncio.timeout(30):
                async for bar in connector.stream_minute_bars("BTCUSD"):
                    logger.info(f"Received bar: {bar}")
                    break  # Just need one successful bar
        except asyncio.TimeoutError:
            logger.error("No data received in 30 seconds")

    except Exception as e:
        logger.error(f"Error during testing: {e}")
        logger.debug(f"Detailed error: {str(e)}", exc_info=True)
    finally:
        await connector.disconnect()
        logger.info("\nTests completed")

def main():
    logger.info(f"Starting Polygon.io Crypto test at {datetime.now(pytz.UTC)}")
    asyncio.run(test_connection())

if __name__ == "__main__":
    main()