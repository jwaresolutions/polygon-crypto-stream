import os
import asyncio
import logging
from datetime import datetime
import pandas as pd
from connectors.polygon import PolygonConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variable to store data before writing to CSV
current_data = []

def save_data() -> None:
    """Save data to CSV file"""
    global current_data
    try:
        if not current_data:
            return

        df: pd.DataFrame = pd.DataFrame(current_data)
        date_str: str = datetime.now().strftime("%Y-%m-%d")

        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)

        filename: str = f"data/BTCUSD_{date_str}.csv"

        if os.path.exists(filename):
            df.to_csv(filename, mode="a", header=False, index=False)
        else:
            df.to_csv(filename, index=False)

        logger.info(f"Saved {len(current_data)} records to {filename}")
        current_data = []

    except Exception as e:
        logger.error(f"Error saving data: {e}")

async def process_crypto_data() -> None:
    """Process incoming crypto data"""
    connector = PolygonConnector()
    
    try:
        async for bar in connector.stream_minute_bars("BTCUSD"):
            try:
                current_data.append(bar)
                
                # Save to file every 100 records
                if len(current_data) >= 100:
                    save_data()
                    
            except Exception as e:
                logger.error(f"Error processing bar: {e}")
                
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise

async def main_async() -> None:
    """Async main function"""
    while True:
        try:
            await process_crypto_data()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)  # Wait before reconnecting

def main() -> None:
    """Main function to run the streaming service"""
    try:
        logger.info("Starting BTCUSD data streaming service...")
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        save_data()
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        save_data()

if __name__ == "__main__":
    main()