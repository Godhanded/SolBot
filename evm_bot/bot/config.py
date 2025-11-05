"""
EVM Bot Configuration
Configurable parameters for BSC/PancakeSwap token monitoring and trading

This configuration file controls all aspects of the bot's behavior including:
- Network settings (BSC mainnet/testnet)
- Trading parameters (auto-trade, position sizing, slippage)
- Quality filters (liquidity, market cap, security)
- Risk management (stop-loss, take-profit, trailing stop)
- Alert settings (Telegram integration)
"""

import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

# BSC RPC endpoints
BSC_RPC_URL = os.getenv("BSC_RPC_URL", "https://bsc-dataseed1.binance.org")
BSC_WSS_URL = os.getenv("BSC_WSS_URL", "wss://bsc-ws-node.nariox.org:443")

# Chain ID (56 = BSC Mainnet, 97 = BSC Testnet)
CHAIN_ID = int(os.getenv("CHAIN_ID", "56"))

# ============================================================================
# PANCAKESWAP CONFIGURATION
# ============================================================================

# PancakeSwap V2 Router address
PANCAKE_ROUTER_V2 = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

# PancakeSwap V2 Factory address
PANCAKE_FACTORY_V2 = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"

# WBNB address (Wrapped BNB)
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"

# Stablecoins for market cap calculation
BUSD_ADDRESS = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"

# ============================================================================
# WALLET CONFIGURATION
# ============================================================================

# Private key for trading (KEEP THIS SECRET!)
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

# Wallet address (derived from private key)
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")

# ============================================================================
# AUTOMATED TRADING CONFIGURATION
# ============================================================================

# AUTO_TRADE: If True, bot will automatically buy/sell tokens
# If False, bot will only send alerts to Telegram (signal-only mode)
AUTO_TRADE = os.getenv("AUTO_TRADE", "false").lower() == "true"

# Position sizing - How much BNB to invest per trade
TRADE_AMOUNT_BNB = Decimal(os.getenv("TRADE_AMOUNT_BNB", "0.1"))  # 0.1 BNB per trade

# Maximum number of concurrent positions
MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "3"))

# Minimum BNB balance to keep in wallet (don't trade below this)
MIN_BNB_BALANCE = Decimal(os.getenv("MIN_BNB_BALANCE", "0.05"))

# ============================================================================
# SLIPPAGE & GAS CONFIGURATION
# ============================================================================

# Slippage tolerance (percentage) - protects against price movement during trade
SLIPPAGE_PERCENT = Decimal(os.getenv("SLIPPAGE_PERCENT", "12"))  # 12% default for volatile tokens

# Gas price multiplier (1.0 = normal, 1.5 = 50% higher for faster execution)
GAS_PRICE_MULTIPLIER = Decimal(os.getenv("GAS_PRICE_MULTIPLIER", "1.2"))

# Maximum gas price in Gwei (prevents overpaying during network congestion)
MAX_GAS_PRICE_GWEI = int(os.getenv("MAX_GAS_PRICE_GWEI", "20"))

# ============================================================================
# RISK MANAGEMENT CONFIGURATION
# ============================================================================

# STOP LOSS: Sell if token drops below this percentage
STOP_LOSS_PERCENT = Decimal(os.getenv("STOP_LOSS_PERCENT", "30"))  # Sell at -30%

# TAKE PROFIT: Sell if token gains above this percentage
TAKE_PROFIT_PERCENT = Decimal(os.getenv("TAKE_PROFIT_PERCENT", "100"))  # Sell at +100% (2x)

# TRAILING STOP: Enable trailing stop-loss that follows price up
USE_TRAILING_STOP = os.getenv("USE_TRAILING_STOP", "true").lower() == "true"

# Trailing stop distance (percentage from peak)
TRAILING_STOP_PERCENT = Decimal(os.getenv("TRAILING_STOP_PERCENT", "20"))  # Trail 20% from peak

# Maximum hold time in seconds (force sell after this time)
MAX_HOLD_TIME_SECONDS = int(os.getenv("MAX_HOLD_TIME_SECONDS", "21600"))  # 6 hours

# Minimum profit to take (won't sell at take-profit if below this)
MIN_PROFIT_PERCENT = Decimal(os.getenv("MIN_PROFIT_PERCENT", "10"))  # At least +10%

# ============================================================================
# TOKEN QUALITY FILTERS
# ============================================================================

# Minimum quality score to alert/trade (0-100)
MINIMUM_QUALITY_SCORE = int(os.getenv("MINIMUM_QUALITY_SCORE", "70"))

# -------------------- Liquidity Filters --------------------

# Minimum liquidity in BNB (too low = high slippage)
MIN_LIQUIDITY_BNB = Decimal(os.getenv("MIN_LIQUIDITY_BNB", "5"))

# Maximum liquidity in BNB (too high = hard to pump)
MAX_LIQUIDITY_BNB = Decimal(os.getenv("MAX_LIQUIDITY_BNB", "500"))

# Optimal liquidity range (gets bonus points)
OPTIMAL_LIQUIDITY_MIN_BNB = Decimal(os.getenv("OPTIMAL_LIQUIDITY_MIN_BNB", "10"))
OPTIMAL_LIQUIDITY_MAX_BNB = Decimal(os.getenv("OPTIMAL_LIQUIDITY_MAX_BNB", "100"))

# -------------------- Market Cap Filters --------------------

# Minimum market cap in USD (too low = might be scam)
MARKET_CAP_MIN_USD = Decimal(os.getenv("MARKET_CAP_MIN_USD", "5000"))

# Maximum market cap in USD (sweet spot for moonshots)
MARKET_CAP_MAX_USD = Decimal(os.getenv("MARKET_CAP_MAX_USD", "300000"))

# Upper limit for market cap (hard rejection above this)
MARKET_CAP_UPPER_LIMIT_USD = Decimal(os.getenv("MARKET_CAP_UPPER_LIMIT_USD", "500000"))

# BNB price in USD (for market cap calculations)
BNB_PRICE_USD = Decimal(os.getenv("BNB_PRICE_USD", "600"))

# -------------------- Security Filters --------------------

# Require contract verification on BSCScan
REQUIRE_VERIFIED_CONTRACT = os.getenv("REQUIRE_VERIFIED_CONTRACT", "false").lower() == "true"

# Require ownership renounced (prevents rug pulls)
REQUIRE_OWNERSHIP_RENOUNCED = os.getenv("REQUIRE_OWNERSHIP_RENOUNCED", "false").lower() == "true"

# Check for honeypot (token that can't be sold)
CHECK_HONEYPOT = os.getenv("CHECK_HONEYPOT", "true").lower() == "true"

# Maximum buy/sell tax percentage (prevents excessive fees)
MAX_BUY_TAX_PERCENT = Decimal(os.getenv("MAX_BUY_TAX_PERCENT", "10"))
MAX_SELL_TAX_PERCENT = Decimal(os.getenv("MAX_SELL_TAX_PERCENT", "15"))

# Require liquidity locked (prevents rug pulls)
REQUIRE_LIQUIDITY_LOCKED = os.getenv("REQUIRE_LIQUIDITY_LOCKED", "false").lower() == "true"

# -------------------- Holder Distribution Filters --------------------

# Maximum percentage held by top holder (prevents whale dumps)
MAX_TOP_HOLDER_PERCENT = Decimal(os.getenv("MAX_TOP_HOLDER_PERCENT", "70"))

# Maximum percentage held by top 10 holders
MAX_TOP_10_HOLDERS_PERCENT = Decimal(os.getenv("MAX_TOP_10_HOLDERS_PERCENT", "90"))

# Minimum number of holders (too few = low distribution)
MIN_HOLDERS_COUNT = int(os.getenv("MIN_HOLDERS_COUNT", "50"))

# ============================================================================
# QUALITY SCORE WEIGHTS
# ============================================================================

# These weights determine how points are distributed (should total 100)

SCORE_WEIGHT_LIQUIDITY = int(os.getenv("SCORE_WEIGHT_LIQUIDITY", "25"))
SCORE_WEIGHT_MARKET_CAP = int(os.getenv("SCORE_WEIGHT_MARKET_CAP", "20"))
SCORE_WEIGHT_SECURITY = int(os.getenv("SCORE_WEIGHT_SECURITY", "30"))
SCORE_WEIGHT_HOLDERS = int(os.getenv("SCORE_WEIGHT_HOLDERS", "15"))
SCORE_WEIGHT_CONTRACT = int(os.getenv("SCORE_WEIGHT_CONTRACT", "10"))

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

# Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Telegram chat ID (your user ID or group chat ID)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Alert settings
SEND_DETECTION_ALERTS = os.getenv("SEND_DETECTION_ALERTS", "true").lower() == "true"
SEND_TRADE_ALERTS = os.getenv("SEND_TRADE_ALERTS", "true").lower() == "true"
SEND_EXIT_ALERTS = os.getenv("SEND_EXIT_ALERTS", "true").lower() == "true"
SEND_ERROR_ALERTS = os.getenv("SEND_ERROR_ALERTS", "true").lower() == "true"

# ============================================================================
# MONITORING CONFIGURATION
# ============================================================================

# How often to check positions for exit conditions (seconds)
POSITION_CHECK_INTERVAL = int(os.getenv("POSITION_CHECK_INTERVAL", "30"))

# How often to update token prices (seconds)
PRICE_UPDATE_INTERVAL = int(os.getenv("PRICE_UPDATE_INTERVAL", "10"))

# Retry settings for failed RPC calls
RPC_RETRY_ATTEMPTS = int(os.getenv("RPC_RETRY_ATTEMPTS", "3"))
RPC_RETRY_DELAY = int(os.getenv("RPC_RETRY_DELAY", "2"))

# ============================================================================
# DATA PERSISTENCE
# ============================================================================

# File to store tracked tokens
TRACKED_TOKENS_FILE = "evm_bot/data/tracked_tokens.json"

# File to store active positions
POSITIONS_FILE = "evm_bot/data/positions.json"

# File to store transaction history
TRANSACTIONS_FILE = "evm_bot/data/transactions.json"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Log file path
LOG_FILE = "evm_bot/logs/bot.log"

# Maximum log file size in bytes (10MB)
MAX_LOG_SIZE = int(os.getenv("MAX_LOG_SIZE", "10485760"))

# Number of backup log files to keep
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# ============================================================================
# DEVELOPMENT/DEBUG SETTINGS
# ============================================================================

# Dry run mode (simulate trades without executing)
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# Verbose logging
VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"

# Save all analyzed tokens (even rejected ones)
SAVE_ALL_TOKENS = os.getenv("SAVE_ALL_TOKENS", "false").lower() == "true"

# ============================================================================
# HONEYPOT DETECTION API (Optional)
# ============================================================================

# Honeypot.is API endpoint (free service)
HONEYPOT_API_URL = "https://api.honeypot.is/v2/IsHoneypot"

# Alternative: RugDoc API (requires key)
RUGDOC_API_URL = os.getenv("RUGDOC_API_URL", "")
RUGDOC_API_KEY = os.getenv("RUGDOC_API_KEY", "")

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """
    Validates configuration to ensure all required settings are present
    and within acceptable ranges
    """
    errors = []

    # Check required environment variables
    if AUTO_TRADE and not PRIVATE_KEY:
        errors.append("PRIVATE_KEY is required when AUTO_TRADE is enabled")

    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is required")

    if not TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID is required")

    # Validate ranges
    if not (0 <= MINIMUM_QUALITY_SCORE <= 100):
        errors.append("MINIMUM_QUALITY_SCORE must be between 0 and 100")

    if SLIPPAGE_PERCENT > 49:
        errors.append("SLIPPAGE_PERCENT too high (max 49%)")

    if TRADE_AMOUNT_BNB <= 0:
        errors.append("TRADE_AMOUNT_BNB must be positive")

    # Validate score weights sum to 100
    total_weight = (SCORE_WEIGHT_LIQUIDITY + SCORE_WEIGHT_MARKET_CAP +
                   SCORE_WEIGHT_SECURITY + SCORE_WEIGHT_HOLDERS +
                   SCORE_WEIGHT_CONTRACT)
    if total_weight != 100:
        errors.append(f"Score weights must sum to 100 (current: {total_weight})")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True

# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

class TradingProfile:
    """Preset configurations for different risk tolerances"""

    CONSERVATIVE = {
        "MINIMUM_QUALITY_SCORE": 80,
        "MIN_LIQUIDITY_BNB": 20,
        "STOP_LOSS_PERCENT": 20,
        "TAKE_PROFIT_PERCENT": 50,
        "MAX_BUY_TAX_PERCENT": 5,
        "MAX_SELL_TAX_PERCENT": 10,
        "REQUIRE_OWNERSHIP_RENOUNCED": True,
    }

    BALANCED = {
        "MINIMUM_QUALITY_SCORE": 70,
        "MIN_LIQUIDITY_BNB": 10,
        "STOP_LOSS_PERCENT": 30,
        "TAKE_PROFIT_PERCENT": 100,
        "MAX_BUY_TAX_PERCENT": 10,
        "MAX_SELL_TAX_PERCENT": 15,
    }

    AGGRESSIVE = {
        "MINIMUM_QUALITY_SCORE": 60,
        "MIN_LIQUIDITY_BNB": 5,
        "STOP_LOSS_PERCENT": 40,
        "TAKE_PROFIT_PERCENT": 200,
        "MAX_BUY_TAX_PERCENT": 15,
        "MAX_SELL_TAX_PERCENT": 20,
    }

# Apply profile if specified
TRADING_PROFILE = os.getenv("TRADING_PROFILE", "").upper()
if TRADING_PROFILE in ["CONSERVATIVE", "BALANCED", "AGGRESSIVE"]:
    profile = getattr(TradingProfile, TRADING_PROFILE)
    globals().update(profile)
