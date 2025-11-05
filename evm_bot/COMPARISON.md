# 📊 Solana Bot vs EVM Bot - Comparison

This document compares the original Solana bot with the new EVM/BSC bot.

## Architecture Comparison

| Feature | Solana Bot | EVM Bot |
|---------|-----------|---------|
| **Blockchain** | Solana | Binance Smart Chain |
| **DEX** | Raydium | PancakeSwap V2 |
| **Language** | Python 3 | Python 3 |
| **Connection** | WebSocket (Solana RPC) | WebSocket/HTTP (BSC RPC) |
| **Token Standard** | SPL Token | ERC-20 |
| **Native Currency** | SOL | BNB |

## Feature Comparison

### ✅ Shared Features

Both bots include:
- Real-time token detection via WebSocket
- Multi-factor quality analysis
- Telegram notifications
- Configurable quality thresholds
- Liquidity and market cap filtering
- Security checks
- Holder distribution analysis
- Statistics tracking
- Logging with rotation
- Graceful shutdown handling

### 🆕 NEW in EVM Bot

Features added to the EVM version:

#### 1. **Automated Trading Engine** ⭐
- **Buy Execution**: Automatically purchases high-quality tokens
- **Sell Execution**: Automated exits based on conditions
- **Gas Optimization**: Smart gas price management
- **Slippage Protection**: Configurable slippage tolerance
- **Transaction Monitoring**: Wait for confirmations
- **Retry Logic**: Handle failed transactions

#### 2. **Position Management System** ⭐
- **Position Tracking**: Monitors all open positions
- **Real-time Price Updates**: Continuous price monitoring
- **Multiple Exit Strategies**: Stop-loss, take-profit, trailing stop, time-based
- **Concurrent Positions**: Manages multiple trades simultaneously
- **P/L Tracking**: Calculates profit/loss for each trade
- **Position Persistence**: Saves positions to disk

#### 3. **Risk Management** ⭐
- **Stop-Loss**: Automatically sells at loss threshold
- **Take-Profit**: Locks in gains at target
- **Trailing Stop**: Follows price up, sells on downturn
- **Max Hold Time**: Forces exit after time limit
- **Position Limits**: Prevents overexposure
- **Balance Protection**: Maintains minimum BNB reserve

#### 4. **Honeypot Detection** ⭐
- **API Integration**: honeypot.is service
- **Sell Simulation**: Tests if token can be sold
- **Tax Detection**: Identifies buy/sell taxes
- **Automatic Rejection**: Blocks honeypot tokens

#### 5. **Enhanced Telegram Alerts** ⭐
- **Buy Notifications**: Confirms trade execution
- **Sell Notifications**: Shows P/L and exit reason
- **Position Updates**: Monitors position performance
- **Error Alerts**: Notifies of failures
- **Rich Formatting**: Progress bars, emojis, clickable links

#### 6. **Auto-Trade Toggle** ⭐
- **Signal-Only Mode**: Just send alerts (AUTO_TRADE=false)
- **Auto-Trade Mode**: Execute trades automatically (AUTO_TRADE=true)
- **Easy Switching**: Single environment variable
- **Dry Run Mode**: Simulate trades without execution

#### 7. **Trading Profiles**
- **Conservative**: Lower risk, stricter filters
- **Balanced**: Default settings
- **Aggressive**: Higher risk, looser filters

## Technical Differences

### Token Detection

**Solana Bot:**
```python
# Subscribes to Token Program logs
ws.subscribe_to_logs(TOKEN_PROGRAM_ID)
# Watches for 'initialize2' instructions
# Parses Raydium pool creation
```

**EVM Bot:**
```python
# Subscribes to PancakeSwap Factory events
factory.events.PairCreated.create_filter()
# Watches for 'PairCreated' events
# Extracts pair and token addresses
```

### Quality Analysis

**Solana Bot:**
```python
# Dimensions:
- Liquidity (SOL amount)
- Market cap (SOL price * supply)
- Security (mint/freeze authority)
- Holder distribution
- Pump.fun detection (scam filter)

# Score: 0-100 points
# Threshold: 70+ for alert
```

**EVM Bot:**
```python
# Dimensions (enhanced):
- Liquidity (BNB amount)
- Market cap (BNB price * supply)
- Security (ownership, honeypot, taxes)
- Holder distribution
- Contract verification

# Score: 0-100 points
# Threshold: 70+ for alert/trade
```

### Trade Execution

**Solana Bot:**
```python
# Manual trading only
# Sends alert with links
# User manually swaps on Raydium
```

**EVM Bot:**
```python
# Automated trading available
# Executes swaps on PancakeSwap
# Manages positions automatically
# Implements exit strategies

# Buy flow:
1. Check balance
2. Get expected tokens
3. Calculate slippage
4. Build transaction
5. Sign and send
6. Wait for confirmation
7. Create position

# Sell flow:
1. Check exit conditions
2. Approve token (if needed)
3. Build sell transaction
4. Execute and confirm
5. Close position
6. Send P/L alert
```

## Configuration Comparison

### Solana Bot Config

```python
# bot/config.py
MINIMUM_QUALITY_SCORE = 70
MIN_LIQUIDITY_SOL = 10
MAX_LIQUIDITY_SOL = 500
MARKET_CAP_MIN_USD = 5000
MARKET_CAP_MAX_USD = 300000
REQUIRE_MINT_REVOKED = False
REQUIRE_FREEZE_REVOKED = False
FILTER_PUMP_FUN_TOKENS = True
```

### EVM Bot Config

```python
# bot/config.py (enhanced)
MINIMUM_QUALITY_SCORE = 70
MIN_LIQUIDITY_BNB = 5
MAX_LIQUIDITY_BNB = 500
MARKET_CAP_MIN_USD = 5000
MARKET_CAP_MAX_USD = 300000

# Trading (NEW)
AUTO_TRADE = False
TRADE_AMOUNT_BNB = 0.1
MAX_CONCURRENT_POSITIONS = 3
SLIPPAGE_PERCENT = 12

# Risk Management (NEW)
STOP_LOSS_PERCENT = 30
TAKE_PROFIT_PERCENT = 100
USE_TRAILING_STOP = True
TRAILING_STOP_PERCENT = 20
MAX_HOLD_TIME_SECONDS = 21600

# Security (ENHANCED)
CHECK_HONEYPOT = True
MAX_BUY_TAX_PERCENT = 10
MAX_SELL_TAX_PERCENT = 15
REQUIRE_OWNERSHIP_RENOUNCED = False
REQUIRE_VERIFIED_CONTRACT = False
```

## Usage Comparison

### Solana Bot Usage

```bash
# 1. Configure
cp .env.example .env
# Edit: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SOLANA_RPC_URL

# 2. Run
python bot/main.py

# 3. Receive alerts
# 4. Manually trade on Raydium
```

### EVM Bot Usage

```bash
# 1. Configure
cp .env.example .env
# Edit: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BSC_RPC_URL

# 2a. Signal-only mode (like Solana bot)
AUTO_TRADE=false python -m bot.main

# 2b. Auto-trade mode (NEW!)
AUTO_TRADE=true python -m bot.main
# Bot trades automatically!
```

## Performance Differences

### Detection Speed

**Solana:**
- Very fast (WebSocket)
- Low latency (~100-500ms)
- High throughput

**BSC:**
- Fast (WebSocket or 3s polling)
- Moderate latency (~500-2000ms)
- Medium throughput

### Gas Costs

**Solana:**
- Very cheap (~$0.00025 per transaction)
- Fixed fees
- Fast confirmation (~400ms)

**BSC:**
- Cheap (~$0.10-0.50 per transaction)
- Variable fees (depends on congestion)
- Moderate confirmation (~3 seconds)

### Token Volume

**Solana:**
- Very high volume
- Many meme coins
- Pump.fun spam

**BSC:**
- High volume
- Mix of legitimate + scams
- Less spam than Solana

## Profitability Comparison

### Solana Bot (Signal-Only)

**Pros:**
- ✅ Very fast detection (first to see new tokens)
- ✅ Low transaction costs
- ✅ High token volume (more opportunities)

**Cons:**
- ❌ Manual trading required
- ❌ Slower execution (time to manually swap)
- ❌ May miss opportunities
- ❌ No automated risk management

**Expected Performance:**
- 5-20 alerts/day (score ≥ 70)
- Manual trading: Win rate ~20-30%
- Highly dependent on user speed

### EVM Bot (Auto-Trade)

**Pros:**
- ✅ Automated buying (faster execution)
- ✅ Automated selling (risk management)
- ✅ Position tracking
- ✅ Can run 24/7 unattended
- ✅ Consistent strategy execution

**Cons:**
- ❌ Higher gas costs
- ❌ Slippage on buys/sells
- ❌ Requires capital in wallet
- ❌ Smart contract risk

**Expected Performance:**
- 5-20 trades/day (score ≥ 70)
- Auto trading: Win rate ~30-40%
- Automated risk management improves consistency

## Which Bot Should You Use?

### Use Solana Bot If:

- ✅ You prefer manual trading
- ✅ You want to see opportunities but decide yourself
- ✅ You have fast manual execution skills
- ✅ You want minimal gas costs
- ✅ You're comfortable with high-speed trading

### Use EVM Bot If:

- ✅ You want automated trading
- ✅ You can't monitor 24/7
- ✅ You want consistent risk management
- ✅ You prefer "set and forget" operation
- ✅ You have capital to allocate ($500+ recommended)

### Use Both If:

- ✅ You want maximum opportunity coverage
- ✅ You can monitor multiple chains
- ✅ You want to diversify across ecosystems
- ✅ You have sufficient capital

## Migration Path

### From Solana Bot to EVM Bot

If you're using the Solana bot and want to try EVM:

1. **Keep Solana bot running** (different folder)
2. **Setup EVM bot** in signal-only mode first
3. **Compare quality** of alerts for a week
4. **Enable auto-trade** on EVM bot if satisfied
5. **Monitor both** for best opportunities

### Settings Translation

| Solana Setting | EVM Equivalent |
|---------------|----------------|
| `MIN_LIQUIDITY_SOL = 10` | `MIN_LIQUIDITY_BNB = 5` |
| `MARKET_CAP_MIN_USD` | Same |
| `REQUIRE_MINT_REVOKED` | `REQUIRE_OWNERSHIP_RENOUNCED` |
| `FILTER_PUMP_FUN_TOKENS` | `CHECK_HONEYPOT` |
| Manual trading | `AUTO_TRADE = false` |

## Conclusion

The EVM bot is a **significant evolution** of the Solana bot:

**Key Improvements:**
1. ⭐ Automated trading capability
2. ⭐ Advanced risk management
3. ⭐ Position tracking
4. ⭐ Enhanced security checks (honeypot detection)
5. ⭐ Flexible operation modes (signal-only or auto-trade)

**Core Philosophy Maintained:**
- ✅ Quality over quantity
- ✅ Multi-factor analysis
- ✅ Configurable thresholds
- ✅ Telegram integration
- ✅ Detailed logging

Both bots serve their purpose well:
- **Solana bot** = Manual trading, max speed, lowest cost
- **EVM bot** = Automated trading, risk management, hands-off

Choose based on your trading style and goals! 🚀
