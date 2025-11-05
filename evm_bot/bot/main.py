"""
EVM Bot - Main Application
BSC/PancakeSwap token monitoring and automated trading bot

This is the main entry point that orchestrates all bot components:
- Token detection (monitors PancakeSwap for new pairs)
- Quality analysis (scores tokens across multiple dimensions)
- Automated trading (buys high-quality tokens)
- Risk management (manages positions with stop-loss/take-profit)
- Telegram notifications (alerts for all events)

Usage:
    python -m evm_bot.bot.main

The bot runs continuously, monitoring for new tokens and managing positions.
Press Ctrl+C to stop gracefully.
"""

import asyncio
import signal
import time
import logging
from pathlib import Path
from typing import Dict
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evm_bot.bot import config
from evm_bot.bot.token_detector import PancakeSwapDetector
from evm_bot.bot.token_quality import TokenQualityAnalyzer
from evm_bot.bot.trading_engine import TradingEngine
from evm_bot.bot.position_manager import PositionManager
from evm_bot.bot.telegram_notifier import TelegramNotifier


# Configure logging
def setup_logging():
    """Setup logging configuration"""
    # Create logs directory
    log_dir = Path(config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    # Format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # File handler (with rotation)
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.MAX_LOG_SIZE,
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Console handler (more concise)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = '%(asctime)s - %(levelname)s - %(message)s'
    console_handler.setFormatter(logging.Formatter(console_format, date_format))

    # Configure root logger
    logging.root.setLevel(log_level)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)

    # Reduce noise from some libraries
    logging.getLogger("web3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


class EVMBot:
    """
    Main bot orchestrator

    Coordinates all bot components and manages the main event loop
    """

    def __init__(self):
        """Initialize the bot"""
        logger.info("="*60)
        logger.info("EVM BOT - Initializing...")
        logger.info("="*60)

        # Validate configuration
        try:
            config.validate_config()
            logger.info("✅ Configuration validated")
        except ValueError as e:
            logger.error(f"❌ Configuration error: {e}")
            sys.exit(1)

        # Display configuration
        self._log_config()

        # Initialize components
        logger.info("\n📦 Initializing components...")

        # 1. Telegram notifier
        self.telegram = TelegramNotifier()

        # 2. Token quality analyzer
        self.analyzer = TokenQualityAnalyzer()

        # 3. Trading engine (if auto-trade enabled)
        self.trading_engine = None
        if config.AUTO_TRADE:
            try:
                self.trading_engine = TradingEngine()
                logger.info("✅ Trading engine initialized (AUTO-TRADE ENABLED)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize trading engine: {e}")
                logger.error("Running in SIGNAL-ONLY mode")
                config.AUTO_TRADE = False
        else:
            logger.info("📡 Running in SIGNAL-ONLY mode")

        # 4. Position manager (if trading enabled)
        self.position_manager = None
        if self.trading_engine:
            self.position_manager = PositionManager(self.trading_engine)
            logger.info("✅ Position manager initialized")

        # 5. Token detector (set up callback, but don't start yet)
        self.detector = PancakeSwapDetector(callback=self._on_new_pair)
        logger.info("✅ Token detector initialized")

        # State
        self.running = False
        self.start_time = None

        # Statistics
        self.session_stats = {
            "start_time": None,
            "pairs_detected": 0,
            "pairs_analyzed": 0,
            "signals_sent": 0,
            "trades_executed": 0,
            "errors": 0
        }

        logger.info("\n✅ All components initialized successfully!")
        logger.info("="*60)

    def _log_config(self):
        """Log important configuration settings"""
        logger.info("\n⚙️  Configuration:")
        logger.info(f"  • Network: BSC (Chain ID: {config.CHAIN_ID})")
        logger.info(f"  • Auto-Trade: {'✅ ENABLED' if config.AUTO_TRADE else '❌ DISABLED (Signal-only)'}")

        if config.AUTO_TRADE:
            logger.info(f"  • Trade Amount: {config.TRADE_AMOUNT_BNB} BNB per trade")
            logger.info(f"  • Max Positions: {config.MAX_CONCURRENT_POSITIONS}")
            logger.info(f"  • Stop-Loss: -{config.STOP_LOSS_PERCENT}%")
            logger.info(f"  • Take-Profit: +{config.TAKE_PROFIT_PERCENT}%")
            if config.USE_TRAILING_STOP:
                logger.info(f"  • Trailing Stop: {config.TRAILING_STOP_PERCENT}%")

        logger.info(f"  • Quality Threshold: {config.MINIMUM_QUALITY_SCORE}/100")
        logger.info(f"  • Liquidity: {config.MIN_LIQUIDITY_BNB}-{config.MAX_LIQUIDITY_BNB} BNB")
        logger.info(f"  • Market Cap: ${config.MARKET_CAP_MIN_USD:,.0f}-${config.MARKET_CAP_MAX_USD:,.0f}")
        logger.info(f"  • Honeypot Check: {'✅ Enabled' if config.CHECK_HONEYPOT else '❌ Disabled'}")

        if config.DRY_RUN:
            logger.warning("  ⚠️  DRY RUN MODE - Trades will be simulated only!")

    async def start(self):
        """Start the bot"""
        self.running = True
        self.start_time = time.time()
        self.session_stats["start_time"] = self.start_time

        logger.info("\n🚀 Starting EVM Bot...")
        logger.info("="*60)

        # Send startup notification
        await self.telegram.send_message(
            "🤖 *EVM Bot Started*\n\n"
            f"Mode: {'AUTO-TRADE' if config.AUTO_TRADE else 'SIGNAL-ONLY'}\n"
            f"Network: BSC\n"
            f"Quality Threshold: {config.MINIMUM_QUALITY_SCORE}/100\n\n"
            "Monitoring for new tokens..."
        )

        # Start background tasks
        tasks = []

        # 1. Token detector (main event loop)
        tasks.append(asyncio.create_task(self.detector.start()))

        # 2. Position monitoring (if trading enabled)
        if self.position_manager:
            tasks.append(asyncio.create_task(self._position_monitoring_loop()))

        # 3. Statistics reporting
        tasks.append(asyncio.create_task(self._stats_reporting_loop()))

        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled, shutting down...")

    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("\n🛑 Stopping bot...")

        self.running = False

        # Stop detector
        if self.detector:
            self.detector.stop()

        # Get final statistics
        stats = self._get_combined_stats()

        # Send shutdown notification
        runtime_hours = (time.time() - self.start_time) / 3600 if self.start_time else 0

        message = "🛑 *Bot Stopped*\n\n"
        message += f"Runtime: `{runtime_hours:.2f} hours`\n"
        message += f"Pairs Detected: `{self.session_stats['pairs_detected']}`\n"
        message += f"Signals Sent: `{self.session_stats['signals_sent']}`\n"

        if config.AUTO_TRADE:
            message += f"Trades Executed: `{self.session_stats['trades_executed']}`\n"

            # Add P/L if available
            positions = stats.get("positions", {})
            net_profit = positions.get("net_profit_bnb", 0)
            if net_profit != 0:
                sign = "+" if net_profit > 0 else ""
                message += f"Session P/L: `{sign}{net_profit:.4f} BNB`\n"

        await self.telegram.send_message(message)

        logger.info("✅ Bot stopped successfully")

    async def _on_new_pair(self, pair_data: Dict):
        """
        Callback when new pair is detected

        Args:
            pair_data: Pair information from detector
        """
        self.session_stats["pairs_detected"] += 1

        token_address = pair_data["token_address"]

        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 NEW PAIR DETECTED")
        logger.info(f"{'='*60}")

        try:
            # Analyze token quality
            self.session_stats["pairs_analyzed"] += 1
            analysis = await self.analyzer.analyze_token(pair_data)

            should_alert = analysis["should_alert"]
            should_trade = analysis["should_trade"]
            quality_score = analysis["quality_score"]

            logger.info(f"Quality Score: {quality_score}/100")
            logger.info(f"Should Alert: {should_alert}")
            logger.info(f"Should Trade: {should_trade}")

            # Send alert if quality is good
            if should_alert:
                self.session_stats["signals_sent"] += 1
                await self.telegram.send_detection_alert(pair_data, analysis)

            # Execute trade if auto-trade enabled
            if should_trade and self.trading_engine and self.position_manager:
                # Check if we can open new position
                if not self.position_manager.can_open_new_position():
                    logger.warning("Cannot trade: Max concurrent positions reached")
                    await self.telegram.send_message(
                        f"⚠️ *Max Positions Reached*\n\n"
                        f"Cannot buy `{token_address[:8]}...`\n"
                        f"Current positions: {len(self.position_manager.positions)}/{config.MAX_CONCURRENT_POSITIONS}"
                    )
                else:
                    # Execute buy
                    logger.info("💰 Executing BUY order...")
                    buy_data = await self.trading_engine.buy_token(
                        token_address, pair_data, analysis
                    )

                    if buy_data and buy_data["success"]:
                        self.session_stats["trades_executed"] += 1

                        # Create position
                        position = self.position_manager.add_position(
                            token_address, buy_data, analysis
                        )

                        # Send buy alert
                        await self.telegram.send_buy_alert(token_address, buy_data, analysis)

                        logger.info("✅ Trade executed and position opened")
                    else:
                        logger.error("❌ Trade failed")
                        await self.telegram.send_error_alert(
                            "Trade Execution Failed",
                            f"Failed to buy {token_address[:8]}...",
                            {"token": token_address}
                        )

        except Exception as e:
            self.session_stats["errors"] += 1
            logger.error(f"Error processing pair: {e}", exc_info=True)
            await self.telegram.send_error_alert(
                "Pair Processing Error",
                str(e),
                {"token": token_address}
            )

    async def _position_monitoring_loop(self):
        """Background loop to monitor and update positions"""
        logger.info("📊 Position monitoring started")

        while self.running:
            try:
                # Update all positions
                await self.position_manager.update_positions()

                # Sleep until next check
                await asyncio.sleep(config.POSITION_CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"Error in position monitoring: {e}", exc_info=True)
                await asyncio.sleep(10)  # Wait longer on error

    async def _stats_reporting_loop(self):
        """Background loop to periodically report statistics"""
        logger.info("📊 Statistics reporting started")

        # Report every hour
        report_interval = 3600

        while self.running:
            try:
                await asyncio.sleep(report_interval)

                # Get combined statistics
                stats = self._get_combined_stats()

                # Send stats update
                await self.telegram.send_stats_update(stats)

                logger.info("📊 Hourly statistics sent")

            except Exception as e:
                logger.error(f"Error in stats reporting: {e}", exc_info=True)

    def _get_combined_stats(self) -> Dict:
        """Get combined statistics from all components"""
        return {
            "session": self.session_stats,
            "detector": self.detector.get_stats() if self.detector else {},
            "analyzer": self.analyzer.get_stats() if self.analyzer else {},
            "trading": self.trading_engine.get_stats() if self.trading_engine else {},
            "positions": self.position_manager.get_stats() if self.position_manager else {},
            "telegram": self.telegram.get_stats() if self.telegram else {}
        }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()

    # Create bot instance
    bot = EVMBot()

    # Setup graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"\nReceived signal {sig}, stopping bot...")
        asyncio.create_task(bot.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start bot
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await bot.stop()


if __name__ == "__main__":
    # Create data directories
    Path("evm_bot/data").mkdir(parents=True, exist_ok=True)
    Path("evm_bot/logs").mkdir(parents=True, exist_ok=True)

    # Run bot
    asyncio.run(main())
