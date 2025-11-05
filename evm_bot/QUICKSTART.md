# 🚀 Quick Start Guide - EVM Bot

Get started with the EVM Bot in 5 minutes!

## Step 1: Install Dependencies (2 minutes)

```bash
cd evm_bot
pip install -r requirements.txt
```

## Step 2: Configure Telegram (2 minutes)

### Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name (e.g., "My Trading Bot")
4. Choose a username (e.g., "my_trading_bot")
5. **Copy the token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Get Your Chat ID

1. Message [@userinfobot](https://t.me/userinfobot)
2. **Copy your User ID** (looks like: `123456789`)

## Step 3: Configure the Bot (1 minute)

```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env  # or use any text editor
```

**Minimum required settings:**

```env
# Telegram (REQUIRED)
TELEGRAM_BOT_TOKEN=paste_your_bot_token_here
TELEGRAM_CHAT_ID=paste_your_chat_id_here

# Network (default is fine)
BSC_RPC_URL=https://bsc-dataseed1.binance.org

# Trading mode - START WITH FALSE!
AUTO_TRADE=false
```

Save and close the file.

## Step 4: Run the Bot!

```bash
python -m bot.main
```

You should see:
```
🤖 EVM Bot Started

Mode: SIGNAL-ONLY
Network: BSC
Quality Threshold: 70/100

Monitoring for new tokens...
```

**And receive a Telegram message confirming the bot started!**

## Step 5: Monitor for Signals

The bot will now:
- ✅ Monitor PancakeSwap for new token launches
- ✅ Analyze each token's quality
- ✅ Send you Telegram alerts for high-quality tokens (score ≥ 70)

When a good token is detected, you'll get an alert like:

```
🚀 HIGH QUALITY TOKEN DETECTED!

Quality Score: 85/100

Token: EXAMPLE
Liquidity: 45.50 BNB
Market Cap: $87,340

📡 ACTION: SIGNAL ONLY
(Auto-trade disabled)

Analysis:
✅ Optimal liquidity
✅ Moonshot market cap
✅ Not a honeypot

🔗 Links: BSCScan | PooCoin | DexScreener
```

## Next Steps

### Option 1: Keep Running in Signal-Only Mode

Leave it running for a few days to see what tokens it finds. Track which ones would have been profitable.

### Option 2: Enable Auto-Trading (Advanced)

**⚠️ WARNING: Only do this after testing signal-only mode first!**

1. **Create a separate wallet** just for the bot
2. **Send some BNB** (e.g., 0.5 BNB for testing)
3. **Export private key** from wallet
4. **Edit .env**:

```env
AUTO_TRADE=true
PRIVATE_KEY=your_wallet_private_key_here
TRADE_AMOUNT_BNB=0.05  # Start SMALL!
```

5. **Restart bot**: Stop with Ctrl+C, then run `python -m bot.main` again

Now the bot will:
- ✅ Detect high-quality tokens
- ✅ Automatically buy them
- ✅ Monitor positions
- ✅ Automatically sell based on stop-loss/take-profit

## Pro Tips

### 1. Start Conservative

```env
MINIMUM_QUALITY_SCORE=80  # Only the best tokens
TRADE_AMOUNT_BNB=0.05     # Small position size
MAX_CONCURRENT_POSITIONS=2  # Limit exposure
```

### 2. Use Dry Run for Testing

```env
DRY_RUN=true
AUTO_TRADE=true
```

This simulates trades without spending real money!

### 3. Monitor Your Logs

```bash
tail -f logs/bot.log
```

### 4. Check Performance

The bot sends hourly stats updates to Telegram automatically.

## Common Issues

### "Configuration error: TELEGRAM_BOT_TOKEN is required"

➜ You forgot to edit `.env` file. Make sure you copied `.env.example` to `.env` and added your tokens.

### "Failed to connect to BSC RPC endpoint"

➜ Try a different RPC from https://chainlist.org/chain/56

### No alerts after 1 hour

➜ This is normal! Most tokens are garbage. The bot is very selective (filters out 90-95% of tokens).

### "Insufficient balance" when trading

➜ You need: `TRADE_AMOUNT_BNB + MIN_BNB_BALANCE` (default: 0.15 BNB minimum)

## Stop the Bot

Press `Ctrl+C` once. The bot will:
- Stop monitoring
- Save all data
- Send final stats to Telegram

## FAQ

**Q: How many tokens will it detect per day?**
A: Depends on quality threshold. With score ≥ 70, expect 5-20 alerts/day.

**Q: What's a good quality score?**
A: 70-80 is good, 80-90 is excellent, 90+ is rare but amazing.

**Q: How much BNB do I need?**
A: For signal-only: None. For auto-trading: 0.5-1 BNB recommended to start.

**Q: Can I run this 24/7?**
A: Yes! Use a VPS or keep your computer running. The bot handles reconnections automatically.

**Q: Is this profitable?**
A: No guarantees! Most new tokens fail. The bot helps find better opportunities, but there's always risk.

**Q: What's the win rate?**
A: Varies. Expect 20-40% of trades to be profitable. Focus on risk/reward ratio.

## Support

- 📖 Read the full [README.md](README.md) for detailed docs
- 🔍 Check logs: `logs/bot.log`
- ⚙️ Review your `.env` configuration
- 🧪 Test with `DRY_RUN=true` first

---

**Ready? Let's find some gems! 💎**
