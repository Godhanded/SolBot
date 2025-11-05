# 🤖 EVM Bot - BSC/PancakeSwap Trading Bot

An advanced automated trading bot for Binance Smart Chain (BSC) that monitors PancakeSwap for new token launches, analyzes their quality, and optionally executes trades automatically with sophisticated risk management.

## 🌟 Features

### Core Capabilities
- **🔍 Real-time Detection**: Monitors PancakeSwap V2 for new token pairs as they're created
- **📊 Multi-Factor Analysis**: Scores tokens across 5 dimensions (liquidity, market cap, security, holders, contract)
- **🍯 Honeypot Detection**: Automatically detects and rejects tokens that can't be sold
- **💰 Automated Trading**: Optional auto-buy with configurable position sizing
- **🛡️ Risk Management**: Stop-loss, take-profit, and trailing stop features
- **📱 Telegram Alerts**: Real-time notifications for all bot events
- **📈 Position Tracking**: Monitors open positions and executes exits automatically

### Advanced Features
- **Trailing Stop Loss**: Follows price up to maximize profits
- **Gas Optimization**: Smart gas price management
- **Slippage Protection**: Configurable slippage tolerance
- **Tax Detection**: Identifies and rejects high-tax tokens
- **Security Analysis**: Checks ownership renouncement and contract verification
- **Concurrent Positions**: Manages multiple positions simultaneously
- **Comprehensive Logging**: Detailed logs with rotation

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **BNB** in your wallet (if using auto-trade)
3. **Telegram account** for alerts
4. **BSC RPC endpoint** (free from chainlist.org)

### Installation

```bash
# 1. Navigate to evm_bot directory
cd evm_bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure .env file
cp .env.example .env
nano .env  # Edit with your settings
```

### Configuration

Edit the `.env` file with your settings:

#### Essential Settings

```env
# Telegram (REQUIRED)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Network
BSC_RPC_URL=https://bsc-dataseed1.binance.org

# Trading Mode
AUTO_TRADE=false  # Set to 'true' to enable automated trading
```

#### For Auto-Trading (Optional)

```env
AUTO_TRADE=true
PRIVATE_KEY=your_wallet_private_key  # KEEP THIS SECRET!
TRADE_AMOUNT_BNB=0.1  # Amount to invest per trade
```

### Running the Bot

```bash
# Run the bot
python -m bot.main

# Or from parent directory
python -m evm_bot.bot.main

# With verbose logging
LOG_LEVEL=DEBUG python -m bot.main
```

### Stopping the Bot

Press `Ctrl+C` to stop gracefully. The bot will:
- Close WebSocket connections
- Save all positions
- Send final statistics to Telegram

## 📖 How It Works

### 1. Token Detection

The bot monitors PancakeSwap V2 Factory for `PairCreated` events:

```
New Pair Created → Filter for BNB pairs → Extract liquidity info → Analyze
```

### 2. Quality Analysis

Each token is scored across multiple dimensions (0-100 points):

#### Liquidity Score (25 points)
- **Best**: 10-100 BNB → 25 pts
- **Good**: 5-10 or 100-500 BNB → Partial points
- **Reject**: <5 BNB or >500 BNB

#### Market Cap Score (20 points)
- **Best**: $5k-$300k (moonshot range) → 20 pts
- **Good**: $300k-$500k → Partial points
- **Reject**: >$500k (limited upside)

#### Security Score (30 points)
- **Honeypot Check**: Can token be sold? (Critical)
- **Buy/Sell Tax**: Rejects if >10%/15%
- **Ownership**: Bonus if renounced
- **Contract**: Bonus if verified

#### Holder Distribution (15 points)
- **Best**: Top holder <30% → 15 pts
- **Good**: Top holder 30-70% → Partial points
- **Reject**: Top holder >70% (rug risk)

#### Contract Verification (10 points)
- Verified on BSCScan → 10 pts
- Unverified → 5 pts or reject (configurable)

### 3. Trading Decision

```
Quality Score >= 70 → Send Alert

AUTO_TRADE=true + Score >= 70 → Execute Buy
```

### 4. Position Management

Once a position is opened:

```
Every 30 seconds (configurable):
  ├─ Update token price
  ├─ Check stop-loss (-30% by default)
  ├─ Check take-profit (+100% by default)
  ├─ Update trailing stop (if enabled)
  ├─ Check max hold time (6 hours by default)
  └─ Execute sell if any condition met
```

### 5. Exit Strategy

The bot will automatically sell when:

1. **Stop-Loss Hit**: Price drops 30% (configurable)
2. **Take-Profit Hit**: Price gains 100% (configurable)
3. **Trailing Stop Hit**: Price drops 20% from peak (configurable)
4. **Max Hold Time**: Held for 6 hours (configurable)

## ⚙️ Configuration Guide

### Trading Profiles

Quick presets for different risk levels:

```env
# Conservative (lower risk)
TRADING_PROFILE=CONSERVATIVE
# - Quality threshold: 80/100
# - Min liquidity: 20 BNB
# - Stop-loss: -20%
# - Take-profit: +50%

# Balanced (default)
TRADING_PROFILE=BALANCED
# - Quality threshold: 70/100
# - Min liquidity: 10 BNB
# - Stop-loss: -30%
# - Take-profit: +100%

# Aggressive (higher risk)
TRADING_PROFILE=AGGRESSIVE
# - Quality threshold: 60/100
# - Min liquidity: 5 BNB
# - Stop-loss: -40%
# - Take-profit: +200%
```

### Key Parameters Explained

#### Risk Management

```env
# Stop-loss: Exit if price drops X%
STOP_LOSS_PERCENT=30

# Take-profit: Exit if price gains X%
TAKE_PROFIT_PERCENT=100

# Trailing stop: Exit if price drops X% from peak
USE_TRAILING_STOP=true
TRAILING_STOP_PERCENT=20

# Max hold: Force sell after X seconds
MAX_HOLD_TIME_SECONDS=21600  # 6 hours
```

#### Quality Filters

```env
# Minimum score to alert (0-100)
MINIMUM_QUALITY_SCORE=70

# Liquidity range (BNB)
MIN_LIQUIDITY_BNB=5
MAX_LIQUIDITY_BNB=500

# Market cap range (USD)
MARKET_CAP_MIN_USD=5000
MARKET_CAP_MAX_USD=300000

# Security requirements
CHECK_HONEYPOT=true  # Highly recommended!
MAX_BUY_TAX_PERCENT=10
MAX_SELL_TAX_PERCENT=15
```

#### Position Sizing

```env
# Amount to invest per trade
TRADE_AMOUNT_BNB=0.1

# Maximum concurrent positions
MAX_CONCURRENT_POSITIONS=3

# Minimum balance to keep
MIN_BNB_BALANCE=0.05
```

## 📊 Understanding Alerts

### Detection Alert

```
🚀 HIGH QUALITY TOKEN DETECTED!

Quality Score: 85/100
████████░░

Token: EXAMPLE (Example Token)

📊 Metrics:
• Liquidity: 45.50 BNB
• Market Cap: $87,340
• Buy Tax: 5% | Sell Tax: 8%
• ✅ Ownership Renounced

🤖 ACTION: BUYING NOW
Amount: 0.1 BNB

Analysis:
✅ Optimal liquidity
✅ Moonshot market cap
✅ Not a honeypot
✅ Good holder distribution

🔗 Links:
BSCScan | PooCoin | DexScreener | DexTools
```

### Buy Alert

```
💰 BUY EXECUTED!

Token: EXAMPLE
Quality: 85/100

Transaction:
• Spent: 0.1000 BNB
• Tokens: 1,000,000
• Price: 0.000000100000 BNB
• Gas: 0.0008 BNB

Risk Management:
• Stop-Loss: -30%
• Take-Profit: +100%
• Trailing Stop: 20%
• Max Hold: 6.0 hours

View Transaction
```

### Sell Alert

```
✅ SELL EXECUTED - PROFIT

P/L: +0.0523 BNB (+52.30%)

Position:
• Entry: 0.1000 BNB @ 0.000000100000
• Exit: 0.1523 BNB @ 0.000000152300
• Hold Time: 2.35 hours
• Peak Gain: +78.50%

Exit Reason:
Trailing stop triggered at +52.30% (Peak: +78.50%)

View Transaction
```

## 🔒 Security Best Practices

### Private Key Safety

1. **Never** share your private key
2. **Never** commit `.env` to git
3. Use a **dedicated wallet** for the bot
4. Only fund with **what you can afford to lose**
5. Regularly **withdraw profits** to a secure wallet

### Risk Management

1. **Start small**: Test with 0.01-0.1 BNB per trade
2. **Use stop-losses**: Always enabled
3. **Limit positions**: Don't overextend (3-5 max recommended)
4. **Monitor regularly**: Check alerts frequently
5. **Test first**: Use `DRY_RUN=true` to test without real money

### RPC Provider

1. **Free RPCs** can be rate-limited or unreliable
2. Consider **paid RPC** for production (Infura, Alchemy, QuickNode)
3. Use **WebSocket** for faster detection
4. Have a **backup RPC** configured

## 🧪 Testing

### Dry Run Mode

Test the bot without executing real trades:

```env
DRY_RUN=true
AUTO_TRADE=true  # Simulates trades
```

This will:
- ✅ Detect real tokens
- ✅ Analyze quality
- ✅ Send alerts
- ✅ Simulate buys/sells
- ❌ NOT execute real transactions
- ❌ NOT require private key

### Signal-Only Mode

Run without trading to evaluate performance:

```env
AUTO_TRADE=false
```

This will:
- ✅ Detect and analyze tokens
- ✅ Send alerts for good opportunities
- ❌ NOT execute any trades

Track the alerts for a week to see which tokens would have been profitable.

## 📁 File Structure

```
evm_bot/
├── bot/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── main.py                # Main bot orchestrator
│   ├── token_detector.py      # PancakeSwap event monitor
│   ├── token_quality.py       # Quality analysis engine
│   ├── trading_engine.py      # Buy/sell execution
│   ├── position_manager.py    # Position tracking & exits
│   └── telegram_notifier.py   # Telegram integration
├── data/
│   ├── tracked_tokens.json    # Detected tokens history
│   ├── positions.json         # Open/closed positions
│   └── transactions.json      # Transaction history
├── logs/
│   └── bot.log                # Application logs
├── .env                       # Your configuration (DO NOT COMMIT!)
├── .env.example               # Configuration template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🐛 Troubleshooting

### Bot not detecting tokens

**Check:**
1. RPC endpoint is working: `curl -X POST <RPC_URL> -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'`
2. WebSocket connection (or polling mode enabled)
3. Logs for connection errors: `tail -f logs/bot.log`

### "Configuration error: TELEGRAM_BOT_TOKEN is required"

**Solution:**
1. Create bot with @BotFather on Telegram
2. Copy token to `.env` file
3. Get your chat ID from @userinfobot
4. Add to `.env` file

### "Failed to connect to BSC RPC endpoint"

**Solution:**
1. Try a different RPC from https://chainlist.org/chain/56
2. Check your internet connection
3. Consider using a paid RPC provider

### "Insufficient balance" when trying to trade

**Solution:**
1. Check wallet balance: `MIN_BNB_BALANCE + TRADE_AMOUNT_BNB` needed
2. Send more BNB to wallet
3. Reduce `TRADE_AMOUNT_BNB`

### Honeypot check always failing

**Solution:**
1. Check honeypot API is accessible: https://api.honeypot.is
2. Temporarily disable: `CHECK_HONEYPOT=false` (NOT RECOMMENDED)
3. Check internet/firewall settings

### No tokens passing quality filter

**Solution:**
1. Lower `MINIMUM_QUALITY_SCORE` (e.g., 60)
2. Widen liquidity range: `MIN_LIQUIDITY_BNB=2`, `MAX_LIQUIDITY_BNB=1000`
3. Check logs to see why tokens are rejected
4. Most tokens ARE garbage - this is expected!

## 📈 Performance Optimization

### Improve Detection Speed

1. **Use WebSocket**: Faster than polling
   ```env
   BSC_WSS_URL=wss://bsc-ws-node.nariox.org:443
   ```

2. **Use Premium RPC**: Paid endpoints are faster
   - Infura
   - Alchemy
   - QuickNode
   - Moralis

### Reduce False Positives

1. **Increase quality threshold**: `MINIMUM_QUALITY_SCORE=80`
2. **Require ownership renounced**: `REQUIRE_OWNERSHIP_RENOUNCED=true`
3. **Stricter holder distribution**: `MAX_TOP_HOLDER_PERCENT=50`
4. **Higher minimum liquidity**: `MIN_LIQUIDITY_BNB=20`

### Maximize Profits

1. **Enable trailing stop**: Captures larger gains
   ```env
   USE_TRAILING_STOP=true
   TRAILING_STOP_PERCENT=20
   ```

2. **Optimize position monitoring**: Check more frequently
   ```env
   POSITION_CHECK_INTERVAL=15  # Every 15 seconds
   ```

3. **Faster gas**: Beat other buyers
   ```env
   GAS_PRICE_MULTIPLIER=1.5  # 50% higher gas
   ```

## 🤝 Contributing

Suggestions for improvements:

1. **Enhanced honeypot detection**: Multiple API sources
2. **Liquidity lock verification**: Check lock duration
3. **Historical performance tracking**: Database integration
4. **Multi-DEX support**: Uniswap, SushiSwap, etc.
5. **Machine learning**: Predict token success probability
6. **Social sentiment**: Twitter/Telegram activity analysis
7. **Smart contract audit**: Automated code analysis

## ⚠️ Disclaimer

**This bot is for educational purposes only.**

- Trading cryptocurrencies carries significant risk
- Past performance does not guarantee future results
- Only invest what you can afford to lose
- Do your own research (DYOR)
- This is not financial advice
- The developers are not responsible for any losses

## 📜 License

MIT License - See LICENSE file for details

## 💬 Support

For issues, questions, or suggestions:

1. Check this README thoroughly
2. Review logs: `logs/bot.log`
3. Test with `DRY_RUN=true` first
4. Start with small amounts
5. Monitor Telegram alerts closely

## 🎯 Recommended Settings

### For Beginners

```env
AUTO_TRADE=false  # Signal-only mode first
MINIMUM_QUALITY_SCORE=80
MIN_LIQUIDITY_BNB=20
CHECK_HONEYPOT=true
REQUIRE_OWNERSHIP_RENOUNCED=true
```

### For Experienced Traders

```env
AUTO_TRADE=true
TRADE_AMOUNT_BNB=0.1
MINIMUM_QUALITY_SCORE=70
STOP_LOSS_PERCENT=30
TAKE_PROFIT_PERCENT=100
USE_TRAILING_STOP=true
MAX_CONCURRENT_POSITIONS=3
```

### For High Risk/Reward

```env
AUTO_TRADE=true
TRADE_AMOUNT_BNB=0.2
MINIMUM_QUALITY_SCORE=60
STOP_LOSS_PERCENT=40
TAKE_PROFIT_PERCENT=200
TRAILING_STOP_PERCENT=25
MAX_CONCURRENT_POSITIONS=5
```

---

**Happy Trading! 🚀**

*Remember: The best trade is sometimes no trade. Be patient and let the bot find quality opportunities.*
