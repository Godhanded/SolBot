"""
Telegram Notifier - Alert System
Sends detailed notifications to Telegram for all bot events

This module handles all Telegram communications including:
- Token detection alerts with quality scores
- Trade execution notifications (buys/sells)
- Position updates and exit alerts
- Error notifications
- Performance statistics

Key Features:
- Rich formatted messages with Markdown
- Clickable links to BSCScan, DexScreener, etc.
- Automatic rate limiting to avoid spam
- Error handling and retry logic
- Statistics tracking
"""

import asyncio
import time
from typing import Dict, List, Optional
from decimal import Decimal
import aiohttp
import logging

from . import config

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Sends notifications to Telegram

    Handles formatting and sending messages for various bot events
    """

    def __init__(self):
        """Initialize Telegram notifier"""
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured - notifications disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Telegram notifier initialized (Chat ID: {self.chat_id})")

        # API endpoint
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

        # Rate limiting
        self.last_message_time = 0
        self.min_message_interval = 2  # Minimum 2 seconds between messages

        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "detection_alerts": 0,
            "trade_alerts": 0,
            "exit_alerts": 0,
            "error_alerts": 0
        }

    async def send_detection_alert(self, pair_data: Dict, analysis: Dict):
        """
        Send alert for new token detection

        Args:
            pair_data: Token pair data from detector
            analysis: Quality analysis results
        """
        if not config.SEND_DETECTION_ALERTS or not self.enabled:
            return

        token_address = pair_data["token_address"]
        quality_score = analysis["quality_score"]
        should_trade = analysis["should_trade"]

        # Build message
        message = self._build_detection_message(pair_data, analysis)

        # Send
        await self._send_message(message)
        self.stats["detection_alerts"] += 1

    async def send_buy_alert(self, token_address: str, buy_data: Dict, analysis: Dict):
        """
        Send alert for token purchase

        Args:
            token_address: Token that was bought
            buy_data: Buy transaction data
            analysis: Quality analysis results
        """
        if not config.SEND_TRADE_ALERTS or not self.enabled:
            return

        message = self._build_buy_message(token_address, buy_data, analysis)
        await self._send_message(message)
        self.stats["trade_alerts"] += 1

    async def send_sell_alert(self, position: 'Position', sell_data: Dict):
        """
        Send alert for token sale

        Args:
            position: Position that was closed
            sell_data: Sell transaction data
        """
        if not config.SEND_EXIT_ALERTS or not self.enabled:
            return

        message = self._build_sell_message(position, sell_data)
        await self._send_message(message)
        self.stats["exit_alerts"] += 1

    async def send_error_alert(self, error_type: str, error_message: str, details: Optional[Dict] = None):
        """
        Send alert for errors

        Args:
            error_type: Type of error
            error_message: Error message
            details: Additional details
        """
        if not config.SEND_ERROR_ALERTS or not self.enabled:
            return

        message = f"🚨 *ERROR: {error_type}*\n\n"
        message += f"`{error_message}`\n\n"

        if details:
            message += "*Details:*\n"
            for key, value in details.items():
                message += f"• {key}: `{value}`\n"

        await self._send_message(message)
        self.stats["error_alerts"] += 1

    async def send_stats_update(self, stats: Dict):
        """
        Send periodic statistics update

        Args:
            stats: Combined statistics from all modules
        """
        if not self.enabled:
            return

        message = self._build_stats_message(stats)
        await self._send_message(message)

    def _build_detection_message(self, pair_data: Dict, analysis: Dict) -> str:
        """Build detection alert message"""
        token_address = pair_data["token_address"]
        pair_address = pair_data["pair_address"]
        quality_score = analysis["quality_score"]
        should_trade = analysis["should_trade"]
        metrics = analysis.get("metrics", {})

        # Emoji based on quality score
        if quality_score >= 80:
            emoji = "🚀"
            quality_text = "EXCELLENT"
        elif quality_score >= 70:
            emoji = "⭐"
            quality_text = "HIGH QUALITY"
        else:
            emoji = "ℹ️"
            quality_text = "MODERATE"

        # Build message
        message = f"{emoji} *{quality_text} TOKEN DETECTED!*\n\n"

        # Quality score with progress bar
        progress = self._create_progress_bar(quality_score, 100)
        message += f"*Quality Score:* `{quality_score}/100`\n{progress}\n\n"

        # Token info
        token_info = metrics.get("token_info", {})
        message += f"*Token:* `{token_info.get('symbol', '???')}`\n"
        message += f"*Name:* {token_info.get('name', 'Unknown')}\n\n"

        # Key metrics
        liquidity = metrics.get("liquidity", {})
        market_cap = metrics.get("market_cap", {})
        security = metrics.get("security", {})

        message += "*📊 Metrics:*\n"
        message += f"• Liquidity: `{liquidity.get('bnb_amount', 0):.2f} BNB`\n"
        message += f"• Market Cap: `${market_cap.get('value_usd', 0):,.0f}`\n"

        # Security info
        if "honeypot" in metrics:
            honeypot = metrics["honeypot"]
            buy_tax = honeypot.get("buy_tax", 0)
            sell_tax = honeypot.get("sell_tax", 0)
            message += f"• Buy Tax: `{buy_tax}%` | Sell Tax: `{sell_tax}%`\n"

        security_details = security.get("details", {})
        if security_details.get("ownership_renounced"):
            message += "• ✅ Ownership Renounced\n"

        message += "\n"

        # Trading action
        if should_trade:
            message += "🤖 *ACTION: BUYING NOW*\n"
            message += f"Amount: `{config.TRADE_AMOUNT_BNB} BNB`\n\n"
        else:
            message += "📡 *ACTION: SIGNAL ONLY*\n"
            message += "(Auto-trade disabled)\n\n"

        # Top reasons
        reasons = analysis.get("reasons", [])
        if reasons:
            message += "*Analysis:*\n"
            for reason in reasons[:5]:  # Top 5 reasons
                message += f"{reason}\n"
            message += "\n"

        # Links
        message += self._build_links(token_address, pair_address)

        return message

    def _build_buy_message(self, token_address: str, buy_data: Dict, analysis: Dict) -> str:
        """Build buy notification message"""
        quality_score = analysis["quality_score"]
        token_info = analysis.get("metrics", {}).get("token_info", {})

        message = "💰 *BUY EXECUTED!*\n\n"

        # Token info
        message += f"*Token:* `{token_info.get('symbol', '???')}`\n"
        message += f"*Quality:* `{quality_score}/100`\n\n"

        # Transaction details
        message += "*Transaction:*\n"
        message += f"• Spent: `{buy_data['amount_bnb']:.4f} BNB`\n"
        message += f"• Tokens: `{buy_data['tokens_received']:,.0f}`\n"
        message += f"• Price: `{buy_data['buy_price_bnb']:.12f} BNB`\n"
        message += f"• Gas: `{buy_data['gas_cost_bnb']:.4f} BNB`\n\n"

        # Risk management
        entry_price = Decimal(str(buy_data['buy_price_bnb']))
        stop_loss = entry_price * (1 - config.STOP_LOSS_PERCENT / 100)
        take_profit = entry_price * (1 + config.TAKE_PROFIT_PERCENT / 100)

        message += "*Risk Management:*\n"
        message += f"• Stop-Loss: `-{config.STOP_LOSS_PERCENT}%`\n"
        message += f"• Take-Profit: `+{config.TAKE_PROFIT_PERCENT}%`\n"
        if config.USE_TRAILING_STOP:
            message += f"• Trailing Stop: `{config.TRAILING_STOP_PERCENT}%`\n"
        message += f"• Max Hold: `{config.MAX_HOLD_TIME_SECONDS / 3600:.1f} hours`\n\n"

        # Transaction link
        message += f"[View Transaction](https://bscscan.com/tx/{buy_data['tx_hash']})\n"

        return message

    def _build_sell_message(self, position: 'Position', sell_data: Dict) -> str:
        """Build sell notification message"""
        profit_loss_percent = position.profit_loss_percent
        profit_loss_bnb = position.profit_loss_bnb

        # Emoji based on profit/loss
        if profit_loss_percent >= 50:
            emoji = "🎉"
            result = "BIG WIN"
        elif profit_loss_percent >= 10:
            emoji = "✅"
            result = "PROFIT"
        elif profit_loss_percent >= 0:
            emoji = "🔄"
            result = "SMALL PROFIT"
        elif profit_loss_percent >= -10:
            emoji = "⚠️"
            result = "SMALL LOSS"
        else:
            emoji = "❌"
            result = "LOSS"

        message = f"{emoji} *SELL EXECUTED - {result}*\n\n"

        # P/L summary
        sign = "+" if profit_loss_bnb >= 0 else ""
        message += f"*P/L:* `{sign}{profit_loss_bnb:.4f} BNB ({sign}{profit_loss_percent:.2f}%)`\n\n"

        # Position details
        hold_time_hours = (position.exit_time - position.entry_time) / 3600
        message += "*Position:*\n"
        message += f"• Entry: `{position.amount_bnb:.4f} BNB @ {position.buy_price:.12f}`\n"
        message += f"• Exit: `{sell_data['bnb_received']:.4f} BNB @ {position.current_price:.12f}`\n"
        message += f"• Hold Time: `{hold_time_hours:.2f} hours`\n\n"

        # Peak price (if trailing stop was enabled)
        if config.USE_TRAILING_STOP and position.peak_price > position.buy_price:
            peak_gain = ((position.peak_price - position.buy_price) / position.buy_price * 100)
            message += f"• Peak Gain: `+{peak_gain:.2f}%`\n\n"

        # Exit reason
        message += f"*Exit Reason:*\n{position.exit_reason}\n\n"

        # Transaction link
        message += f"[View Transaction](https://bscscan.com/tx/{sell_data['tx_hash']})\n"

        return message

    def _build_stats_message(self, stats: Dict) -> str:
        """Build statistics message"""
        message = "📊 *BOT STATISTICS*\n\n"

        # Detector stats
        detector = stats.get("detector", {})
        message += "*Detection:*\n"
        message += f"• Pairs Detected: `{detector.get('pairs_detected', 0)}`\n"
        message += f"• Pairs Processed: `{detector.get('pairs_processed', 0)}`\n"
        message += f"• BNB Pairs: `{detector.get('pairs_detected', 0) - detector.get('pairs_filtered', 0)}`\n\n"

        # Analyzer stats
        analyzer = stats.get("analyzer", {})
        message += "*Analysis:*\n"
        message += f"• Analyzed: `{analyzer.get('analyzed', 0)}`\n"
        message += f"• Passed: `{analyzer.get('passed', 0)}`\n"
        message += f"• Pass Rate: `{analyzer.get('pass_rate', 0):.1f}%`\n"
        message += f"• Honeypots: `{analyzer.get('honeypots_detected', 0)}`\n\n"

        # Trading stats
        trading = stats.get("trading", {})
        message += "*Trading:*\n"
        message += f"• Buys: `{trading.get('buys_successful', 0)}/{trading.get('buys_attempted', 0)}`\n"
        message += f"• Sells: `{trading.get('sells_successful', 0)}/{trading.get('sells_attempted', 0)}`\n"
        message += f"• Net: `{trading.get('net_bnb', 0):+.4f} BNB`\n\n"

        # Position stats
        positions = stats.get("positions", {})
        message += "*Positions:*\n"
        message += f"• Open: `{positions.get('open_positions', 0)}`\n"
        message += f"• Closed: `{positions.get('closed_positions', 0)}`\n"
        message += f"• Win Rate: `{positions.get('win_rate', 0):.1f}%`\n"
        message += f"• Net Profit: `{positions.get('net_profit_bnb', 0):+.4f} BNB`\n"

        return message

    def _build_links(self, token_address: str, pair_address: str) -> str:
        """Build links section"""
        links = "*🔗 Links:*\n"
        links += f"[BSCScan](https://bscscan.com/token/{token_address}) | "
        links += f"[PooCoin](https://poocoin.app/tokens/{token_address}) | "
        links += f"[DexScreener](https://dexscreener.com/bsc/{pair_address}) | "
        links += f"[DexTools](https://www.dextools.io/app/bsc/pair-explorer/{pair_address})\n"
        return links

    def _create_progress_bar(self, value: int, max_value: int, length: int = 10) -> str:
        """Create a visual progress bar"""
        filled = int((value / max_value) * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"`{bar}`"

    async def _send_message(self, message: str):
        """
        Send message to Telegram with rate limiting

        Args:
            message: Message text (supports Markdown)
        """
        if not self.enabled:
            return

        try:
            # Rate limiting
            time_since_last = time.time() - self.last_message_time
            if time_since_last < self.min_message_interval:
                await asyncio.sleep(self.min_message_interval - time_since_last)

            # Send message
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        self.stats["messages_sent"] += 1
                        logger.debug("Telegram message sent successfully")
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram API error {response.status}: {error_text}")
                        self.stats["messages_failed"] += 1

            self.last_message_time = time.time()

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            self.stats["messages_failed"] += 1

    def get_stats(self) -> Dict:
        """Get notifier statistics"""
        return self.stats.copy()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """Example usage"""
    notifier = TelegramNotifier()

    # Example detection alert
    pair_data = {
        "token_address": "0x1234567890123456789012345678901234567890",
        "pair_address": "0x0987654321098765432109876543210987654321",
    }

    analysis = {
        "quality_score": 85,
        "should_trade": True,
        "metrics": {
            "token_info": {
                "name": "Test Token",
                "symbol": "TEST"
            },
            "liquidity": {
                "bnb_amount": 45.5
            },
            "market_cap": {
                "value_usd": 125000
            }
        },
        "reasons": [
            "✅ Optimal liquidity",
            "✅ Moonshot market cap",
            "✅ Not a honeypot"
        ]
    }

    await notifier.send_detection_alert(pair_data, analysis)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
