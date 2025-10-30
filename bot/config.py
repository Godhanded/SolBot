import os
from dotenv import load_dotenv

load_dotenv()
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
SOLANA_RPC_WSS = os.getenv("SOLANA_RPC_WSS")
# SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"


START_DATE = "2024-12-15"  # Date to start detecting tokens from
RESET_INTERVAL_DAYS = 2  # Time interval to reset volumes and market caps

# =====================================================
# QUALITY FILTER SETTINGS - Adjust these to fine-tune
# =====================================================

# Minimum quality score to send alerts (0-100)
# 70+ = High quality gems with good potential
# 50-69 = Moderate quality (not alerted by default)
# <50 = Low quality (rejected)
MINIMUM_QUALITY_SCORE = 70

# Liquidity Filters (in SOL)
MIN_LIQUIDITY_SOL = 10   # Minimum SOL in pool (below = scam/low liquidity)
MAX_LIQUIDITY_SOL = 500  # Maximum SOL in pool (above = harder to pump)

# Optimal liquidity range for maximum score (15-100 SOL is sweet spot)
OPTIMAL_LIQUIDITY_MIN = 15
OPTIMAL_LIQUIDITY_MAX = 100

# Market Cap Filters (in USD)
# Sweet spot for moonshots: $5k - $300k
MARKET_CAP_MIN = 5_000      # Minimum market cap
MARKET_CAP_MAX = 300_000    # Maximum market cap for best score
MARKET_CAP_UPPER_LIMIT = 500_000  # Hard upper limit

# Security Requirements
REQUIRE_MINT_REVOKED = False    # If True, only alert if mint authority is revoked
REQUIRE_FREEZE_REVOKED = False  # If True, only alert if freeze authority is revoked

# Holder Distribution
MAX_TOP_HOLDER_PERCENTAGE = 70  # Reject if top holder owns more than this %

# Filter Settings
FILTER_PUMP_FUN_TOKENS = True  # Filter out pump.fun tokens (recommended)

# SOL Price for Market Cap Calculations (update periodically)
SOL_PRICE_USD = 200

# Legacy thresholds (kept for backwards compatibility)
ALERT_VOLUME_THRESHOLD = 1000  # Deprecated - use MIN_LIQUIDITY_SOL instead
ALERT_MARKET_CAP_THRESHOLD = 1_000_000  # Deprecated - use MARKET_CAP_MIN instead

# =====================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Replace with your bot token
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Replace with your chat ID
