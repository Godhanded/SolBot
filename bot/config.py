import os
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
# SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"


START_DATE = "2024-12-15"  # Date to start detecting tokens from
RESET_INTERVAL_DAYS = 2    # Time interval to reset volumes and market caps

# Thresholds
ALERT_VOLUME_THRESHOLD = 1000  # Example volume threshold for alerts
ALERT_MARKET_CAP_THRESHOLD = 1_000_000  # Example market cap threshold in USD

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Replace with your bot token
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")     # Replace with your chat ID
