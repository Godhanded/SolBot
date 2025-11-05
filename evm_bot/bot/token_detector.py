"""
BSC/PancakeSwap Token Detector
Monitors PancakeSwap V2 factory for new pair creation events in real-time

This module listens for 'PairCreated' events from the PancakeSwap factory contract
and detects new liquidity pools as they are created. It filters for BNB pairs and
extracts all relevant data needed for quality analysis.

Key Features:
- WebSocket connection for real-time event monitoring
- Automatic reconnection with exponential backoff
- Duplicate detection to avoid reprocessing
- BNB pair filtering (ignores non-BNB pairs)
- Detailed event parsing with error handling
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Callable
from web3 import Web3
from web3.exceptions import Web3Exception
from eth_utils import to_checksum_address
import logging

from . import config

# Configure logging
logger = logging.getLogger(__name__)

class PancakeSwapDetector:
    """
    Monitors PancakeSwap V2 Factory for new pair creation events

    This class establishes a WebSocket connection to BSC and listens for
    PairCreated events emitted by the PancakeSwap factory contract. When
    a new pair is created, it extracts the token addresses and initial
    liquidity information.
    """

    # PancakeSwap Factory ABI (only PairCreated event)
    FACTORY_ABI = [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "token0", "type": "address"},
                {"indexed": True, "name": "token1", "type": "address"},
                {"indexed": False, "name": "pair", "type": "address"},
                {"indexed": False, "name": "index", "type": "uint256"}
            ],
            "name": "PairCreated",
            "type": "event"
        }
    ]

    def __init__(self, callback: Callable):
        """
        Initialize the PancakeSwap detector

        Args:
            callback: Async function to call when new pair is detected.
                     Should accept pair_data dict as parameter.
        """
        self.callback = callback
        self.running = False
        self.seen_pairs = set()  # Track processed pairs to avoid duplicates

        # Initialize Web3 connections
        # HTTP connection for queries
        self.w3_http = Web3(Web3.HTTPProvider(config.BSC_RPC_URL))

        # WebSocket connection for events (if available)
        try:
            self.w3_ws = Web3(Web3.WebsocketProvider(config.BSC_WSS_URL))
            self.use_websocket = True
            logger.info("WebSocket connection established")
        except Exception as e:
            logger.warning(f"WebSocket unavailable, falling back to polling: {e}")
            self.w3_ws = None
            self.use_websocket = False

        # Verify connection
        if not self.w3_http.is_connected():
            raise ConnectionError("Failed to connect to BSC RPC endpoint")

        logger.info(f"Connected to BSC (Chain ID: {self.w3_http.eth.chain_id})")

        # Get factory contract
        self.factory_address = to_checksum_address(config.PANCAKE_FACTORY_V2)
        self.factory_contract = self.w3_http.eth.contract(
            address=self.factory_address,
            abi=self.FACTORY_ABI
        )

        # WBNB address for filtering
        self.wbnb_address = to_checksum_address(config.WBNB_ADDRESS).lower()

        # Statistics
        self.stats = {
            "pairs_detected": 0,
            "pairs_processed": 0,
            "pairs_filtered": 0,  # Non-BNB pairs
            "errors": 0,
            "last_pair_time": None
        }

    async def start(self):
        """
        Start monitoring for new pairs

        This method runs indefinitely, monitoring the PancakeSwap factory
        for new pair creation events. It handles reconnection automatically.
        """
        self.running = True
        logger.info("Starting PancakeSwap pair detector...")

        retry_delay = 1  # Start with 1 second delay
        max_retry_delay = 60  # Max 60 seconds between retries

        while self.running:
            try:
                if self.use_websocket:
                    await self._monitor_via_websocket()
                else:
                    await self._monitor_via_polling()

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break

            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Detector error: {e}", exc_info=True)

                # Exponential backoff
                logger.info(f"Reconnecting in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

                # Try to reconnect
                try:
                    self._reconnect()
                    retry_delay = 1  # Reset delay on successful reconnection
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")

    def _reconnect(self):
        """Attempt to reconnect to BSC"""
        logger.info("Attempting to reconnect...")

        # Recreate HTTP connection
        self.w3_http = Web3(Web3.HTTPProvider(config.BSC_RPC_URL))

        # Try WebSocket if it was being used
        if self.use_websocket:
            try:
                self.w3_ws = Web3(Web3.WebsocketProvider(config.BSC_WSS_URL))
                logger.info("WebSocket reconnected")
            except Exception as e:
                logger.warning(f"WebSocket reconnection failed: {e}")
                self.use_websocket = False

        # Verify connection
        if not self.w3_http.is_connected():
            raise ConnectionError("Failed to reconnect to BSC")

        # Recreate contract
        self.factory_contract = self.w3_http.eth.contract(
            address=self.factory_address,
            abi=self.FACTORY_ABI
        )

        logger.info("Reconnection successful")

    async def _monitor_via_websocket(self):
        """Monitor using WebSocket connection (real-time)"""
        logger.info("Monitoring via WebSocket...")

        # Create event filter for PairCreated
        event_filter = self.factory_contract.events.PairCreated.create_filter(
            fromBlock='latest'
        )

        while self.running:
            try:
                # Check for new events
                for event in event_filter.get_new_entries():
                    await self._process_pair_event(event)

                # Small delay to prevent hammering
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing events: {e}")
                raise  # Re-raise to trigger reconnection

    async def _monitor_via_polling(self):
        """Monitor using HTTP polling (fallback method)"""
        logger.info("Monitoring via polling (checking every 3 seconds)...")

        # Get current block
        current_block = self.w3_http.eth.block_number
        logger.info(f"Starting from block {current_block}")

        while self.running:
            try:
                # Get latest block
                latest_block = self.w3_http.eth.block_number

                # Check for new blocks
                if latest_block > current_block:
                    # Get events from new blocks
                    events = self.factory_contract.events.PairCreated.get_logs(
                        fromBlock=current_block + 1,
                        toBlock=latest_block
                    )

                    # Process each event
                    for event in events:
                        await self._process_pair_event(event)

                    current_block = latest_block

                # Wait before next poll
                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Error polling events: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def _process_pair_event(self, event):
        """
        Process a PairCreated event

        Args:
            event: Web3 event object containing pair creation data
        """
        try:
            # Extract event data
            pair_address = event['args']['pair']
            token0 = event['args']['token0']
            token1 = event['args']['token1']

            # Convert to checksum addresses
            pair_address = to_checksum_address(pair_address)
            token0 = to_checksum_address(token0)
            token1 = to_checksum_address(token1)

            # Check for duplicates
            if pair_address.lower() in self.seen_pairs:
                logger.debug(f"Skipping duplicate pair: {pair_address}")
                return

            self.seen_pairs.add(pair_address.lower())
            self.stats["pairs_detected"] += 1

            # Check if either token is WBNB (we only want BNB pairs)
            token0_lower = token0.lower()
            token1_lower = token1.lower()

            is_bnb_pair = (token0_lower == self.wbnb_address or
                          token1_lower == self.wbnb_address)

            if not is_bnb_pair:
                self.stats["pairs_filtered"] += 1
                logger.debug(f"Skipping non-BNB pair: {pair_address}")
                return

            # Determine which token is the new token (not WBNB)
            if token0_lower == self.wbnb_address:
                token_address = token1
                bnb_is_token0 = True
            else:
                token_address = token0
                bnb_is_token0 = False

            # Get transaction info
            tx_hash = event['transactionHash'].hex()
            block_number = event['blockNumber']

            # Log detection
            logger.info(f"🎯 New BNB pair detected!")
            logger.info(f"   Pair: {pair_address}")
            logger.info(f"   Token: {token_address}")
            logger.info(f"   Block: {block_number}")
            logger.info(f"   TX: {tx_hash}")

            # Build pair data structure
            pair_data = {
                "pair_address": pair_address,
                "token_address": token_address,
                "bnb_address": config.WBNB_ADDRESS,
                "token0": token0,
                "token1": token1,
                "bnb_is_token0": bnb_is_token0,
                "tx_hash": tx_hash,
                "block_number": block_number,
                "timestamp": int(time.time()),
                "exchange": "PancakeSwap V2"
            }

            # Get initial liquidity info
            try:
                liquidity_info = await self._get_pair_liquidity(pair_address)
                pair_data.update(liquidity_info)
            except Exception as e:
                logger.warning(f"Could not get liquidity for {pair_address}: {e}")
                # Set defaults
                pair_data.update({
                    "reserve_bnb": 0,
                    "reserve_token": 0,
                    "initial_price": 0
                })

            # Update stats
            self.stats["pairs_processed"] += 1
            self.stats["last_pair_time"] = time.time()

            # Call the callback with pair data
            await self.callback(pair_data)

        except Exception as e:
            logger.error(f"Error processing pair event: {e}", exc_info=True)
            self.stats["errors"] += 1

    async def _get_pair_liquidity(self, pair_address: str) -> Dict:
        """
        Get liquidity information for a pair

        Args:
            pair_address: Address of the liquidity pair

        Returns:
            Dict containing reserve amounts and initial price
        """
        # Minimal pair ABI for getReserves
        pair_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"name": "reserve0", "type": "uint112"},
                    {"name": "reserve1", "type": "uint112"},
                    {"name": "blockTimestampLast", "type": "uint32"}
                ],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token0",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token1",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            }
        ]

        pair_contract = self.w3_http.eth.contract(
            address=to_checksum_address(pair_address),
            abi=pair_abi
        )

        # Get reserves
        reserves = pair_contract.functions.getReserves().call()
        reserve0 = reserves[0]
        reserve1 = reserves[1]

        # Get token addresses to determine which reserve is which
        token0 = pair_contract.functions.token0().call()
        token1 = pair_contract.functions.token1().call()

        # Determine BNB and token reserves
        if token0.lower() == self.wbnb_address:
            reserve_bnb = reserve0
            reserve_token = reserve1
        else:
            reserve_bnb = reserve1
            reserve_token = reserve0

        # Convert from Wei to BNB (18 decimals)
        reserve_bnb_decimal = reserve_bnb / (10 ** 18)

        # Calculate initial price (BNB per token)
        if reserve_token > 0:
            initial_price = reserve_bnb / reserve_token
        else:
            initial_price = 0

        return {
            "reserve_bnb": reserve_bnb,
            "reserve_token": reserve_token,
            "reserve_bnb_decimal": reserve_bnb_decimal,
            "initial_price": initial_price
        }

    def get_stats(self) -> Dict:
        """Get detector statistics"""
        stats = self.stats.copy()

        # Add connection status
        stats["connected"] = self.w3_http.is_connected()
        stats["websocket_enabled"] = self.use_websocket

        # Add time since last pair
        if stats["last_pair_time"]:
            stats["seconds_since_last_pair"] = int(time.time() - stats["last_pair_time"])

        return stats

    def stop(self):
        """Stop monitoring"""
        logger.info("Stopping detector...")
        self.running = False


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_callback(pair_data: Dict):
    """Example callback function"""
    print(f"\n🚀 New pair detected: {pair_data['token_address']}")
    print(f"   Liquidity: {pair_data.get('reserve_bnb_decimal', 0):.4f} BNB")
    print(f"   Pair: {pair_data['pair_address']}")


async def main():
    """Example main function for testing"""
    # Create detector
    detector = PancakeSwapDetector(callback=example_callback)

    try:
        # Start monitoring
        await detector.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        detector.stop()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run detector
    asyncio.run(main())
