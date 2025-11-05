"""
Position Manager - Risk Management System
Tracks open positions and manages exit strategies

This module manages all open trading positions and implements sophisticated
exit strategies including:
- Stop-loss (protect against losses)
- Take-profit (lock in gains)
- Trailing stop (maximize profits)
- Time-based exits (prevent holding too long)
- Position monitoring and updates

Key Features:
- Real-time position tracking
- Multiple exit conditions with priority
- Trailing stop that follows price up
- Automatic position closure on triggers
- Detailed exit logging and reasoning
"""

import asyncio
import time
import json
from typing import Dict, List, Optional
from decimal import Decimal
from pathlib import Path
import logging

from . import config

logger = logging.getLogger(__name__)


class Position:
    """
    Represents a single trading position

    Tracks entry price, current price, profit/loss, and exit conditions
    """

    def __init__(self, token_address: str, buy_data: Dict, analysis: Dict):
        """
        Initialize a position

        Args:
            token_address: Token contract address
            buy_data: Buy transaction data
            analysis: Quality analysis results
        """
        self.token_address = token_address
        self.buy_tx_hash = buy_data["tx_hash"]
        self.amount_bnb = Decimal(str(buy_data["amount_bnb"]))
        self.tokens_held = buy_data["tokens_received"]
        self.buy_price = Decimal(str(buy_data["buy_price_bnb"]))
        self.entry_time = buy_data["timestamp"]
        self.quality_score = analysis["quality_score"]

        # Current state
        self.current_price = self.buy_price
        self.current_value_bnb = self.amount_bnb
        self.profit_loss_percent = Decimal(0)
        self.profit_loss_bnb = Decimal(0)

        # Peak tracking (for trailing stop)
        self.peak_price = self.buy_price
        self.peak_value_bnb = self.amount_bnb

        # Exit conditions
        self.stop_loss_price = self.buy_price * (1 - config.STOP_LOSS_PERCENT / 100)
        self.take_profit_price = self.buy_price * (1 + config.TAKE_PROFIT_PERCENT / 100)
        self.trailing_stop_price = None  # Set when price goes up

        # Status
        self.closed = False
        self.exit_reason = None
        self.exit_time = None
        self.sell_tx_hash = None

        # Update tracking
        self.last_update_time = time.time()
        self.update_count = 0

        logger.info(f"📊 New position opened:")
        logger.info(f"   Token: {token_address}")
        logger.info(f"   Amount: {self.amount_bnb} BNB")
        logger.info(f"   Tokens: {self.tokens_held}")
        logger.info(f"   Entry price: {self.buy_price}")
        logger.info(f"   Stop-loss: {self.stop_loss_price} (-{config.STOP_LOSS_PERCENT}%)")
        logger.info(f"   Take-profit: {self.take_profit_price} (+{config.TAKE_PROFIT_PERCENT}%)")

    def update_price(self, new_price: Decimal):
        """
        Update position with new token price

        Args:
            new_price: Current token price in BNB
        """
        self.current_price = new_price
        self.current_value_bnb = new_price * self.tokens_held
        self.profit_loss_bnb = self.current_value_bnb - self.amount_bnb
        self.profit_loss_percent = (self.profit_loss_bnb / self.amount_bnb) * 100

        # Update peak (for trailing stop)
        if new_price > self.peak_price:
            self.peak_price = new_price
            self.peak_value_bnb = self.current_value_bnb

            # Update trailing stop
            if config.USE_TRAILING_STOP:
                self.trailing_stop_price = self.peak_price * (
                    1 - config.TRAILING_STOP_PERCENT / 100
                )

        self.last_update_time = time.time()
        self.update_count += 1

    def should_exit(self) -> tuple[bool, Optional[str]]:
        """
        Check if position should be exited

        Returns:
            Tuple of (should_exit: bool, reason: str or None)
        """
        # Check stop-loss
        if self.current_price <= self.stop_loss_price:
            return True, f"Stop-loss triggered at {self.profit_loss_percent:.2f}%"

        # Check trailing stop
        if config.USE_TRAILING_STOP and self.trailing_stop_price:
            if self.current_price <= self.trailing_stop_price:
                return True, f"Trailing stop triggered at {self.profit_loss_percent:.2f}% (Peak: {((self.peak_price - self.buy_price) / self.buy_price * 100):.2f}%)"

        # Check take-profit
        if self.current_price >= self.take_profit_price:
            # Only take profit if above minimum profit threshold
            if self.profit_loss_percent >= config.MIN_PROFIT_PERCENT:
                return True, f"Take-profit triggered at {self.profit_loss_percent:.2f}%"

        # Check max hold time
        hold_time = time.time() - self.entry_time
        if hold_time >= config.MAX_HOLD_TIME_SECONDS:
            return True, f"Max hold time reached ({hold_time / 3600:.1f} hours, P/L: {self.profit_loss_percent:.2f}%)"

        return False, None

    def close(self, sell_data: Dict):
        """
        Close the position

        Args:
            sell_data: Sell transaction data
        """
        self.closed = True
        self.exit_time = sell_data["timestamp"]
        self.sell_tx_hash = sell_data["tx_hash"]
        self.exit_reason = sell_data["reason"]

        # Final calculations
        final_bnb = Decimal(str(sell_data["bnb_received"]))
        gas_cost = Decimal(str(sell_data["gas_cost_bnb"]))

        self.profit_loss_bnb = final_bnb - self.amount_bnb - gas_cost
        self.profit_loss_percent = (self.profit_loss_bnb / self.amount_bnb) * 100

        hold_time_hours = (self.exit_time - self.entry_time) / 3600

        logger.info(f"📊 Position closed:")
        logger.info(f"   Token: {self.token_address}")
        logger.info(f"   Hold time: {hold_time_hours:.2f} hours")
        logger.info(f"   Entry: {self.amount_bnb} BNB @ {self.buy_price}")
        logger.info(f"   Exit: {final_bnb} BNB @ {self.current_price}")
        logger.info(f"   P/L: {self.profit_loss_bnb:+.4f} BNB ({self.profit_loss_percent:+.2f}%)")
        logger.info(f"   Reason: {self.exit_reason}")

    def to_dict(self) -> Dict:
        """Convert position to dictionary for storage"""
        return {
            "token_address": self.token_address,
            "buy_tx_hash": self.buy_tx_hash,
            "amount_bnb": float(self.amount_bnb),
            "tokens_held": self.tokens_held,
            "buy_price": float(self.buy_price),
            "entry_time": self.entry_time,
            "quality_score": self.quality_score,
            "current_price": float(self.current_price),
            "current_value_bnb": float(self.current_value_bnb),
            "profit_loss_percent": float(self.profit_loss_percent),
            "profit_loss_bnb": float(self.profit_loss_bnb),
            "peak_price": float(self.peak_price),
            "stop_loss_price": float(self.stop_loss_price),
            "take_profit_price": float(self.take_profit_price),
            "trailing_stop_price": float(self.trailing_stop_price) if self.trailing_stop_price else None,
            "closed": self.closed,
            "exit_reason": self.exit_reason,
            "exit_time": self.exit_time,
            "sell_tx_hash": self.sell_tx_hash,
            "last_update_time": self.last_update_time,
            "update_count": self.update_count
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        """Create position from dictionary"""
        # Create minimal buy_data and analysis for reconstruction
        buy_data = {
            "tx_hash": data["buy_tx_hash"],
            "amount_bnb": data["amount_bnb"],
            "tokens_received": data["tokens_held"],
            "buy_price_bnb": data["buy_price"],
            "timestamp": data["entry_time"]
        }

        analysis = {
            "quality_score": data["quality_score"]
        }

        position = cls(data["token_address"], buy_data, analysis)

        # Restore state
        position.current_price = Decimal(str(data["current_price"]))
        position.current_value_bnb = Decimal(str(data["current_value_bnb"]))
        position.profit_loss_percent = Decimal(str(data["profit_loss_percent"]))
        position.profit_loss_bnb = Decimal(str(data["profit_loss_bnb"]))
        position.peak_price = Decimal(str(data["peak_price"]))
        position.closed = data["closed"]
        position.exit_reason = data.get("exit_reason")
        position.exit_time = data.get("exit_time")
        position.sell_tx_hash = data.get("sell_tx_hash")

        if data.get("trailing_stop_price"):
            position.trailing_stop_price = Decimal(str(data["trailing_stop_price"]))

        return position


class PositionManager:
    """
    Manages all trading positions and exit strategies

    Monitors positions, checks exit conditions, and executes sells
    """

    def __init__(self, trading_engine):
        """
        Initialize position manager

        Args:
            trading_engine: TradingEngine instance for executing trades
        """
        self.trading_engine = trading_engine
        self.positions: Dict[str, Position] = {}  # token_address -> Position
        self.closed_positions: List[Position] = []

        # Load existing positions from disk
        self._load_positions()

        # Statistics
        self.stats = {
            "total_positions": 0,
            "open_positions": 0,
            "closed_positions": 0,
            "winning_positions": 0,
            "losing_positions": 0,
            "total_profit_bnb": Decimal(0),
            "total_loss_bnb": Decimal(0),
        }

        logger.info("Position Manager initialized")

    def add_position(self, token_address: str, buy_data: Dict, analysis: Dict) -> Position:
        """
        Add a new position

        Args:
            token_address: Token contract address
            buy_data: Buy transaction data
            analysis: Quality analysis results

        Returns:
            Created Position object
        """
        position = Position(token_address, buy_data, analysis)
        self.positions[token_address] = position

        self.stats["total_positions"] += 1
        self.stats["open_positions"] += 1

        self._save_positions()

        return position

    async def update_positions(self):
        """
        Update all open positions with current prices

        This should be called periodically to check exit conditions
        """
        if not self.positions:
            return

        logger.debug(f"Updating {len(self.positions)} positions...")

        for token_address, position in list(self.positions.items()):
            if position.closed:
                continue

            try:
                # Get current token price
                current_price = await self._get_token_price(token_address)

                if current_price:
                    position.update_price(current_price)

                    # Check if should exit
                    should_exit, reason = position.should_exit()

                    if should_exit:
                        logger.info(f"🚨 Exit condition met for {token_address}")
                        logger.info(f"   Reason: {reason}")

                        # Execute sell
                        await self._exit_position(token_address, reason)

                else:
                    logger.warning(f"Could not get price for {token_address}")

            except Exception as e:
                logger.error(f"Error updating position {token_address}: {e}")

        self._save_positions()

    async def _exit_position(self, token_address: str, reason: str):
        """
        Exit a position by selling the token

        Args:
            token_address: Token to sell
            reason: Reason for exit
        """
        position = self.positions.get(token_address)
        if not position or position.closed:
            return

        logger.info(f"💸 Exiting position: {token_address}")
        logger.info(f"   Reason: {reason}")

        # Execute sell
        sell_data = await self.trading_engine.sell_token(
            token_address,
            amount=position.tokens_held,
            reason=reason
        )

        if sell_data and sell_data["success"]:
            # Close position
            position.close(sell_data)

            # Move to closed positions
            self.closed_positions.append(position)
            del self.positions[token_address]

            # Update stats
            self.stats["open_positions"] -= 1
            self.stats["closed_positions"] += 1

            if position.profit_loss_bnb > 0:
                self.stats["winning_positions"] += 1
                self.stats["total_profit_bnb"] += position.profit_loss_bnb
            else:
                self.stats["losing_positions"] += 1
                self.stats["total_loss_bnb"] += abs(position.profit_loss_bnb)

            self._save_positions()

            return sell_data

        else:
            logger.error(f"Failed to sell {token_address}")
            return None

    async def _get_token_price(self, token_address: str) -> Optional[Decimal]:
        """
        Get current token price in BNB

        Args:
            token_address: Token contract address

        Returns:
            Current price in BNB, or None if unavailable
        """
        try:
            from web3 import Web3
            from eth_utils import to_checksum_address

            w3 = self.trading_engine.w3
            router = self.trading_engine.router

            # Get price for 1 token (in token's smallest unit)
            # We need to know decimals first
            token_contract = w3.eth.contract(
                address=to_checksum_address(token_address),
                abi=self.trading_engine.ERC20_ABI
            )

            decimals = token_contract.functions.decimals().call()
            one_token = 10 ** decimals

            # Get amounts out
            path = [to_checksum_address(token_address), self.trading_engine.wbnb_address]
            amounts_out = router.functions.getAmountsOut(one_token, path).call()

            # Convert to BNB
            bnb_amount = Decimal(amounts_out[1]) / Decimal(10 ** 18)

            return bnb_amount

        except Exception as e:
            logger.error(f"Error getting token price: {e}")
            return None

    def can_open_new_position(self) -> bool:
        """Check if we can open a new position"""
        return len(self.positions) < config.MAX_CONCURRENT_POSITIONS

    def get_position(self, token_address: str) -> Optional[Position]:
        """Get a position by token address"""
        return self.positions.get(token_address)

    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())

    def get_closed_positions(self, limit: int = 10) -> List[Position]:
        """Get recent closed positions"""
        return self.closed_positions[-limit:]

    def _save_positions(self):
        """Save positions to disk"""
        try:
            # Ensure directory exists
            Path(config.POSITIONS_FILE).parent.mkdir(parents=True, exist_ok=True)

            data = {
                "open_positions": {
                    addr: pos.to_dict() for addr, pos in self.positions.items()
                },
                "closed_positions": [
                    pos.to_dict() for pos in self.closed_positions[-100:]  # Keep last 100
                ]
            }

            with open(config.POSITIONS_FILE, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving positions: {e}")

    def _load_positions(self):
        """Load positions from disk"""
        try:
            if not Path(config.POSITIONS_FILE).exists():
                return

            with open(config.POSITIONS_FILE, 'r') as f:
                data = json.load(f)

            # Load open positions
            for addr, pos_data in data.get("open_positions", {}).items():
                try:
                    position = Position.from_dict(pos_data)
                    self.positions[addr] = position
                    self.stats["open_positions"] += 1
                    self.stats["total_positions"] += 1
                except Exception as e:
                    logger.error(f"Error loading position {addr}: {e}")

            # Load closed positions
            for pos_data in data.get("closed_positions", []):
                try:
                    position = Position.from_dict(pos_data)
                    self.closed_positions.append(position)
                    self.stats["closed_positions"] += 1
                    self.stats["total_positions"] += 1

                    # Update stats
                    if position.profit_loss_bnb > 0:
                        self.stats["winning_positions"] += 1
                        self.stats["total_profit_bnb"] += position.profit_loss_bnb
                    else:
                        self.stats["losing_positions"] += 1
                        self.stats["total_loss_bnb"] += abs(position.profit_loss_bnb)

                except Exception as e:
                    logger.error(f"Error loading closed position: {e}")

            logger.info(f"Loaded {self.stats['open_positions']} open positions, "
                       f"{self.stats['closed_positions']} closed positions")

        except Exception as e:
            logger.error(f"Error loading positions: {e}")

    def get_stats(self) -> Dict:
        """Get position manager statistics"""
        stats = self.stats.copy()

        # Calculate win rate
        total_closed = stats["winning_positions"] + stats["losing_positions"]
        if total_closed > 0:
            stats["win_rate"] = round(stats["winning_positions"] / total_closed * 100, 2)
        else:
            stats["win_rate"] = 0

        # Calculate net profit
        stats["net_profit_bnb"] = float(
            stats["total_profit_bnb"] - stats["total_loss_bnb"]
        )

        # Convert Decimals to float for JSON serialization
        stats["total_profit_bnb"] = float(stats["total_profit_bnb"])
        stats["total_loss_bnb"] = float(stats["total_loss_bnb"])

        return stats
