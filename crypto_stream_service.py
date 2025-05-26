from typing import List, Dict, Any
import logging
from datetime import datetime
import asyncio
import pandas as pd
import os
from connectors.polygon import PolygonConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("spy_stream.log"), logging.StreamHandler()],
)
logger: logging.Logger = logging.getLogger(__name__)

current_data: List[Dict[str, Any]] = []

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

        filename: str = f"data/SPY_{date_str}.csv"

        if os.path.exists(filename):
            df.to_csv(filename, mode="a", header=False, index=False)
        else:
            df.to_csv(filename, index=False)

        logger.info(f"Saved {len(current_data)} records to {filename}")
        current_data = []

    except Exception as e:
        logger.error(f"Error saving data: {e}")

async def main_async() -> None:
    """Main async function to run the streaming service"""
    connector = PolygonConnector()
    
    while True:
        try:
            await connector.connect()
            
            async for bar_data in connector.stream_minute_bars("SPY"):
                current_data.append(bar_data)
                logger.info(f"Received bar: {bar_data['timestamp']} - Close: {bar_data['close']}")
                
                if len(current_data) >= 100:
                    save_data()
                    
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)  # Wait before reconnecting

def main() -> None:
    """Main function to run the streaming service"""
    try:
        logger.info("Starting SPY data streaming service...")
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        save_data()
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        save_data()

if __name__ == "__main__":
    main()