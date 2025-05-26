import websockets
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, AsyncIterator, List
import pytz
from .base import DataConnector
from config import POLYGON_API_KEY
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class PolygonConnector(DataConnector):
    def __init__(self):
        self.api_key = POLYGON_API_KEY
        self.websocket = None
        self.rest_url = "https://api.polygon.io"
        self.ws_url = "wss://socket.polygon.io/crypto"
        
    async def connect(self) -> None:
        try:
            self.websocket = await websockets.connect(self.ws_url)
            
            await self.websocket.send(json.dumps({
                "action": "auth",
                "params": self.api_key
            }))
            
            auth_response = await self.websocket.recv()
            auth_data = json.dumps(auth_response)
            logger.debug(f"Auth response: {auth_data}")
            
            if isinstance(auth_data, list):
                connected_msg = any(msg.get('status') == 'connected' for msg in auth_data)
                auth_msg = any(msg.get('status') == 'auth_success' for msg in auth_data)
                if connected_msg or auth_msg:
                    logger.info("Successfully connected to Polygon.io crypto websocket")
                    await self.websocket.send(json.dumps({
                        "action": "subscribe",
                        "params": "XA.*"
                    }))
                else:
                    logger.error(f"Authentication failed: {auth_data}")
            else:
                if "Connected Successfully" in auth_data:
                    logger.info("Successfully connected to Polygon.io crypto websocket")
                    await self.websocket.send(json.dumps({
                        "action": "subscribe",
                        "params": "XA.*"
                    }))
                else:
                    logger.error(f"Authentication failed: {auth_data}")

        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
            
    async def disconnect(self) -> None:
        try:
            if hasattr(self, 'websocket') and self.websocket:
                await self.websocket.close()
                logger.info("Disconnected from Polygon.io websocket")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
        
    async def stream_minute_bars(self, symbol: str) -> AsyncIterator[Dict[str, Any]]:
        if not self.websocket:
            await self.connect()

        subscription_message = json.dumps({
            "action": "subscribe",
            "params": f"XA.{symbol}"
        })
        
        logger.debug(f"Subscribing with: {subscription_message}")
        await self.websocket.send(subscription_message)
        
        while True:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                logger.debug(f"Received websocket message: {data}")
                
                if isinstance(data, list):
                    for msg in data:
                        if msg.get('ev') == 'XA':
                            try:
                                formatted_bar = self._format_bar_data(msg)
                                yield formatted_bar
                            except Exception as e:
                                logger.error(f"Error processing message: {msg}")
                                logger.error(f"Error details: {e}")
                elif isinstance(data, dict) and data.get('ev') == 'XA':
                    try:
                        formatted_bar = self._format_bar_data(data)
                        yield formatted_bar
                    except Exception as e:
                        logger.error(f"Error processing message: {data}")
                        logger.error(f"Error details: {e}")

            except websockets.ConnectionClosed:
                logger.warning("Connection closed, reconnecting...")
                await asyncio.sleep(1)
                await self.connect()
            except Exception as e:
                logger.error(f"Error in stream_minute_bars: {e}")
                await asyncio.sleep(1)

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        all_bars: List[Dict[str, Any]] = []
        
        async with aiohttp.ClientSession() as session:
            url = (
                f"{self.rest_url}/v2/aggs/ticker/X:{symbol}/"
                f"range/1/minute/{start_date.strftime('%Y-%m-%d')}/"
                f"{end_date.strftime('%Y-%m-%d')}"
                f"?adjusted=true&sort=asc&limit=50000"
            )
        
            logger.info(f"Fetching crypto data from {url}")
            
            try:
                async with session.get(
                    url, 
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    if response.status == 429:
                        wait_time = float(response.headers.get('retry-after', '60'))
                        logger.warning(f"Rate limit hit, waiting {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                        return []
                    
                    data = await response.json()
                    logger.debug(f"API Response: {data}")
                    
                    if data['status'] == 'OK' and data.get('results'):
                        bars = [self._format_historical_bar(bar) for bar in data['results']]
                        all_bars.extend(bars)
                        logger.info(f"Retrieved {len(bars)} bars")
                    else:
                        logger.warning(f"No data in response: {data}")
                    
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
        return all_bars

    def _format_bar_data(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        try:
            est_timestamp = datetime.fromtimestamp(msg.get('s', 0)/1000).astimezone(
                pytz.timezone("America/New_York")
            )
            
            return {
                "timestamp": est_timestamp.isoformat(),
                "open": msg.get('o', 0.0),
                "high": msg.get('h', 0.0),
                "low": msg.get('l', 0.0),
                "close": msg.get('c', 0.0),
                "volume": msg.get('v', 0.0),
                "vwap": msg.get('vw', 0.0),
                "trade_count": msg.get('n', 0)
            }
        except Exception as e:
            logger.error(f"Error formatting bar data: {msg}")
            logger.error(f"Error details: {e}")
            raise

    def _format_historical_bar(self, bar: Dict[str, Any]) -> Dict[str, Any]:
        est_timestamp = datetime.fromtimestamp(bar['t']/1000).astimezone(
            pytz.timezone("America/New_York")
        )
        
        return {
            "timestamp": est_timestamp.isoformat(),
            "open": bar['o'],
            "high": bar['h'],
            "low": bar['l'],
            "close": bar['c'],
            "volume": bar['v'],
            "vwap": bar['vw'],
            "trade_count": bar['n']
        }