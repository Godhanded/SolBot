# 🚀 Moonshot Trading Strategy Guide

## Fast 3x-10x Trades with $5 Position Sizes

This guide explains how to use the EVM Bot for aggressive moonshot hunting - targeting 3x-10x gains within 24 hours using small $5 positions.

## ⚠️ WARNING: EXTREME RISK

**This is a VERY HIGH RISK strategy:**
- 70-80% of trades will lose money
- You need BIG wins (5x-10x) to be profitable overall
- Gas costs are ~20% of each $5 trade
- Most tokens will rug pull or die quickly
- You can lose 100% of trading capital

**Only use money you can afford to lose completely!**

## 🎯 Strategy Overview

### The Concept

Buy micro-cap tokens at launch (market cap $1k-$50k), hold max 24 hours, target 3x-10x gains with trailing stop to lock in profits.

### Why $5 Trades?

- **Low Risk per Trade**: Losing $5 doesn't hurt
- **High Position Count**: Can take 10-20 positions with $100
- **Learning Opportunity**: Cheap way to test strategy
- **Psychological**: Easier to hold through volatility

### The Math

```
Starting Capital: $100
Position Size: $5
Max Positions: 10
Total Exposure: $50

Scenario 1 (Typical Week):
- 20 trades executed
- 16 losers at -50% = -$40
- 4 winners:
  - 2 at 2x = +$10
  - 1 at 5x = +$20
  - 1 at 10x = +$45
- Total: +$35 profit (35% weekly return)

Scenario 2 (Bad Week):
- 20 trades executed
- 18 losers at -50% = -$45
- 2 winners at 2x = +$10
- Total: -$35 loss (35% weekly loss)

Scenario 3 (Great Week):
- 20 trades executed
- 15 losers at -50% = -$37.50
- 3 at 3x = +$30
- 2 at 10x = +$90
- Total: +$82.50 profit (82% weekly return)
```

**You need 1-2 big wins per week to be profitable!**

## 🛠️ Setup for Moonshot Mode

### Option 1: Use Moonshot Profile (Easiest)

```bash
cd evm_bot

# 1. Copy the moonshot config
cp .env.moonshot .env

# 2. Edit with your details
nano .env
# Add your PRIVATE_KEY and TELEGRAM credentials

# 3. Calculate your position size
# At BNB = $600:
# $5 = 0.0083 BNB
# Set: TRADE_AMOUNT_BNB=0.0083

# 4. Set profile
# Already set in .env.moonshot, but you can also use:
# TRADING_PROFILE=MOONSHOT

# 5. Run!
python -m bot.main
```

### Option 2: Manual Configuration

Edit `.env`:

```env
# Core Settings
AUTO_TRADE=true
PRIVATE_KEY=your_key_here
TRADE_AMOUNT_BNB=0.0083  # ~$5 at BNB=$600

# Moonshot Filters
MINIMUM_QUALITY_SCORE=50
MIN_LIQUIDITY_BNB=2
MAX_LIQUIDITY_BNB=50
MARKET_CAP_MIN_USD=1000
MARKET_CAP_MAX_USD=50000

# Aggressive Risk Management
STOP_LOSS_PERCENT=50
TAKE_PROFIT_PERCENT=300  # 3x
USE_TRAILING_STOP=true
TRAILING_STOP_PERCENT=30
MAX_HOLD_TIME_SECONDS=86400  # 24 hours
MIN_PROFIT_PERCENT=200  # Don't sell <2x

# High Volume Settings
MAX_CONCURRENT_POSITIONS=10
SLIPPAGE_PERCENT=20
GAS_PRICE_MULTIPLIER=1.5
POSITION_CHECK_INTERVAL=15

# Or simply use:
TRADING_PROFILE=MOONSHOT
```

## 📊 Understanding the Settings

### Position Sizing

```env
TRADE_AMOUNT_BNB=0.0083  # $5 at BNB=$600
```

**Calculate your size:**
```
Position Size USD / BNB Price = Amount in BNB

Examples:
$5 / $600 = 0.0083 BNB
$10 / $600 = 0.0167 BNB
$20 / $600 = 0.0333 BNB
```

**Recommended:** Start with $5-10 per trade.

### Market Cap Range

```env
MARKET_CAP_MIN_USD=1000   # Very early
MARKET_CAP_MAX_USD=50000  # Still has 10x potential
```

**Why this range?**
- Below $1k: Often scams/rugs
- $1k-$10k: 10x-100x potential (but very risky)
- $10k-$50k: 3x-10x potential (sweet spot)
- Above $50k: Less upside for moonshots

### Liquidity Range

```env
MIN_LIQUIDITY_BNB=2   # Can still trade
MAX_LIQUIDITY_BNB=50  # Not too established
```

**Why low liquidity?**
- Lower liquidity = earlier stage = higher potential
- But too low = can't exit (set min at 2 BNB)
- Above 50 BNB usually = already pumped

### Exit Strategy

```env
STOP_LOSS_PERCENT=50          # Exit at -50%
TAKE_PROFIT_PERCENT=300       # Exit at 3x
TRAILING_STOP_PERCENT=30      # Trail by 30%
MIN_PROFIT_PERCENT=200        # Don't sell <2x
MAX_HOLD_TIME_SECONDS=86400   # Force exit after 24h
```

**How it works:**

```
Entry: $5 (price: 0.0001)

Scenario 1: Steady climb to 5x
- Price hits 0.0002 (2x) → Hold (below MIN_PROFIT_PERCENT)
- Price hits 0.0003 (3x) → Could take profit, but trailing stop active
- Price hits 0.0005 (5x) → Trailing stop now at 0.00035 (3.5x)
- Price drops to 0.00035 → SELL at 3.5x (+$12.50)

Scenario 2: Quick pump to 10x then dump
- Price rockets to 0.001 (10x) in 2 hours
- Trailing stop at 0.0007 (7x)
- Price dumps fast to 0.0007 → SELL at 7x (+$30)
- Without trailing stop, might have held all the way down!

Scenario 3: Slow bleed
- Price drops to 0.00005 (-50%) → STOP LOSS triggered
- Exit at -50% (-$2.50)
- Prevents holding to -90% or worse

Scenario 4: Sideways then time out
- Price bounces between -20% and +50% for 24 hours
- Max hold time reached → Force sell at current price
- Free up capital for next opportunity
```

### Gas Considerations

```env
SLIPPAGE_PERCENT=20        # High for low liquidity
GAS_PRICE_MULTIPLIER=1.5   # Fast execution
```

**Gas Impact on $5 Trades:**

```
Buy:  $0.30-0.50 gas
Sell: $0.30-0.50 gas
Total: ~$1.00 gas per round trip

On $5 trade:
- Gas = 20% of position
- Need 1.25x just to break even!
- This is why we target 3x+
```

**If gas is eating your profits:**
- Increase position size to $10-20
- Trade less frequently
- Use lower gas multiplier (but slower execution)

## 📈 Expected Performance

### Daily Activity

With MOONSHOT settings:

```
Pairs Detected: 100-300/day
Quality Score >50: 20-40/day
Trades Executed: 10-30/day (if slots available)
```

**You'll get LOTS of alerts!** Most will lose, but you're hunting for the few big winners.

### Win Rate

```
Realistic Expectations:
- Win Rate: 20-30%
- Avg Winner: 3x-5x (occasionally 10x+)
- Avg Loser: -50%
- Break-even Win Rate: ~25%

You MUST have big winners to overcome:
- 70% losing trades
- 20% gas costs
- Slippage on entry/exit
```

### Weekly Results (Examples)

**Conservative Week (20 trades):**
```
15 losses at -50% = -$37.50
4 wins at 2x = +$20
1 win at 5x = +$20
Net: +$2.50 (2.5% return)
```

**Average Week (25 trades):**
```
18 losses at -50% = -$45
5 wins at 3x = +$50
2 wins at 7x = +$60
Net: +$65 (65% return on $100 capital)
```

**Bad Week (30 trades):**
```
25 losses at -50% = -$62.50
5 wins at 2x = +$25
Net: -$37.50 (37.5% loss)
```

**Great Week (25 trades):**
```
20 losses at -50% = -$50
3 wins at 4x = +$45
2 wins at 15x = +$140
Net: +$135 (135% return!)
```

## 🎯 What Makes a Good Moonshot?

The bot looks for:

### ✅ Green Flags

1. **Very Low Market Cap**: $2k-$20k (10x-50x potential)
2. **Low Liquidity**: 3-10 BNB (early stage)
3. **Not a Honeypot**: Can actually sell it
4. **Reasonable Taxes**: <15% buy, <20% sell
5. **Some Holder Distribution**: Not 100% in one wallet
6. **Recent Creation**: <1 hour old

### ❌ Red Flags (Auto-Rejected)

1. **Honeypot**: Can't sell → Bot rejects
2. **High Taxes**: >15% buy or >20% sell → Rejected
3. **Too Low Liquidity**: <2 BNB → Can't exit safely
4. **Already Pumped**: >$50k market cap → Limited upside
5. **Top Holder >80%**: Rug pull risk → Rejected

## 💡 Advanced Tips

### 1. Adjust Position Size Based on BNB Price

```bash
# Update when BNB price changes significantly
Current BNB Price: $600
$5 position = 0.0083 BNB

If BNB drops to $500:
$5 position = 0.01 BNB

If BNB rises to $700:
$5 position = 0.0071 BNB
```

### 2. Monitor Capital Efficiency

```
Capital: $100
Max Positions: 10
Position Size: $5

Best case: All 10 slots filled = $50 deployed (50% efficiency)
Worst case: Always in trades = $100 deployed (100% efficiency)

Adjust MAX_CONCURRENT_POSITIONS based on trade frequency:
- High volume (30+ trades/day): 10-15 positions
- Medium volume (15-30 trades/day): 5-10 positions
- Low volume (<15 trades/day): 3-5 positions
```

### 3. Trailing Stop Optimization

```env
# Tighter trailing stop (25%) = Lock profits faster, might exit early
TRAILING_STOP_PERCENT=25

# Wider trailing stop (40%) = More room for volatility, might give back more
TRAILING_STOP_PERCENT=40

# Recommended: 30% (good balance)
TRAILING_STOP_PERCENT=30
```

### 4. Quality Score Tuning

Start at 50, adjust based on results:

```env
# Too many bad trades? Raise threshold
MINIMUM_QUALITY_SCORE=55

# Not enough opportunities? Lower threshold
MINIMUM_QUALITY_SCORE=45

# Finding good tokens but missing them? Lower threshold + faster gas
MINIMUM_QUALITY_SCORE=45
GAS_PRICE_MULTIPLIER=2.0
```

### 5. Time-Based Adjustments

Different times of day have different activity:

```
High Activity (More New Tokens):
- 8am-12pm EST
- 6pm-10pm EST

Lower Activity:
- 12am-6am EST

Consider running 24/7 to catch all opportunities,
or focus on high-activity times to save on server costs.
```

## 🔍 Monitoring Your Performance

### Daily Check-In

```bash
# Check logs
tail -f logs/bot.log

# Look for:
- How many tokens detected?
- How many passed quality filter?
- Win rate on closed positions
- Average winner vs average loser
- Gas costs total
```

### Weekly Review

Track in spreadsheet:
```
Week 1:
- Trades: 150
- Winners: 35 (23%)
- Avg Winner: 4.2x
- Avg Loser: -48%
- Net P/L: +$145 (145% weekly return)
- Best Trade: 12x (+$55)
- Worst Trade: -50% (-$2.50)
```

**Adjust based on results:**
- Win rate <20%? → Raise quality score
- Avg winner <3x? → Raise take-profit or trailing stop
- Avg loser >-60%? → Tighten stop-loss
- Not enough trades? → Lower quality score or market cap max

## ⚡ Quick Start Checklist

- [ ] Copy `.env.moonshot` to `.env`
- [ ] Add `PRIVATE_KEY` (dedicated wallet only!)
- [ ] Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- [ ] Calculate position size: `$5 / current_BNB_price`
- [ ] Set `TRADE_AMOUNT_BNB`
- [ ] Fund wallet with at least $100 + gas ($20)
- [ ] Start with `DRY_RUN=true` for first day
- [ ] Check results, then set `DRY_RUN=false`
- [ ] Monitor first 10 trades closely
- [ ] Adjust settings based on performance
- [ ] Track weekly stats

## 🚨 Risk Management Rules

### 1. Never Risk More Than You Can Lose

- Only use "fun money"
- Expect to lose it all in worst case
- Don't use rent/bill money
- Start with $50-100 total

### 2. Capital Limits

```env
Max Capital in Bot: $100-500
Position Size: $5-10
Max Positions: 10-20
Reserve for Gas: $20-50
```

### 3. Stop Trading If...

- Down >50% in a week → Review strategy
- Win rate <15% → Raise quality score
- Getting emotional → Take a break
- Can't afford to lose more → Stop immediately

### 4. Regularly Withdraw Profits

```
Every Week:
- Withdraw 50% of profits
- Keep 50% to compound
- Never let bot balance exceed your comfort level
```

## 📱 Telegram Alert Examples

### Detection Alert (Moonshot Mode)

```
⭐ HIGH QUALITY TOKEN DETECTED!

Quality Score: 52/100
█████░░░░░

Token: MOON (Moon Token)

📊 Metrics:
• Liquidity: 4.50 BNB
• Market Cap: $8,340
• Buy Tax: 5% | Sell Tax: 10%

🤖 ACTION: BUYING NOW
Amount: 0.0083 BNB ($5)

Analysis:
✅ Micro-cap (10x potential)
✅ Low liquidity (early stage)
✅ Not a honeypot
⚠️  Moderate quality (high risk!)

🔗 Links: BSCScan | DexScreener
```

### Buy Confirmation

```
💰 BUY EXECUTED!

Token: MOON
Quality: 52/100

Transaction:
• Spent: 0.0083 BNB ($5.00)
• Tokens: 500,000
• Price: 0.00000001660 BNB
• Gas: 0.0005 BNB ($0.30)

Risk Management:
• Stop-Loss: -50%
• Take-Profit: +300% (3x)
• Trailing Stop: 30%
• Max Hold: 24.0 hours

View Transaction
```

### Winner Alert (7x!)

```
🎉 SELL EXECUTED - BIG WIN

P/L: +0.0498 BNB (+600% = 7x)

Position:
• Entry: 0.0083 BNB @ 0.00000001660
• Exit: 0.0581 BNB @ 0.00000011620
• Hold Time: 3.2 hours
• Peak Gain: +850% (8.5x)

Exit Reason:
Trailing stop triggered at +600% (Peak: +850%)

🚀 Captured most of the move!

View Transaction
```

### Loser Alert

```
❌ SELL EXECUTED - LOSS

P/L: -0.0042 BNB (-50%)

Position:
• Entry: 0.0083 BNB @ 0.00000001660
• Exit: 0.0041 BNB @ 0.00000000830
• Hold Time: 1.8 hours

Exit Reason:
Stop-loss triggered at -50%

💡 Cut the loss, move to next opportunity

View Transaction
```

## 🎓 Learning from Trades

### Analyze Your Winners

```
Why did MOON token 7x?
- Caught very early (market cap $8k)
- Good entry price (low liquidity, we got in first)
- Community formed quickly (holders went from 20 → 500)
- Trailed the top well (exited at 7x vs peak of 8.5x)

Lesson: Early entry + trailing stop = captured 82% of the move
```

### Analyze Your Losers

```
Why did RUG token -50%?
- Launched with high hype, dumped immediately
- Liquidity pulled after 2 hours
- Should have had tighter stop-loss? No - 50% is already tight for moonshots

Lesson: Some will rug. That's priced in. Move on.
```

## 🎯 Success Metrics

### What "Success" Looks Like

**Monthly Results:**
```
Capital: $100
Trades: 300
Win Rate: 25%
Avg Winner: 4x (+$12)
Avg Loser: -50% (-$2.50)

Winners: 75 × $12 = $900
Losers: 225 × -$2.50 = -$562.50
Net: +$337.50 (337% monthly return)

But expect wild swings:
- Some weeks: +100%
- Other weeks: -50%
- Requires emotional discipline!
```

### Compound Growth (If Successful)

```
Month 1: $100 → $337 (237% gain)
Month 2: $337 → $1,136 (237% gain)
Month 3: $1,136 → $3,828 (237% gain)

But this is IDEAL scenario. Reality:
- Most traders: Break even or small loss
- Good traders: 50-100% monthly
- Great traders: 100-300% monthly (rare!)
```

## 🔄 When to Adjust Strategy

### Increase Position Size When:
- ✅ Win rate >30% for 2+ weeks
- ✅ Comfortable with risk
- ✅ Built up capital
- ✅ Understand the patterns

### Decrease Position Size When:
- ❌ Win rate <20% for 2+ weeks
- ❌ Feeling stressed about losses
- ❌ Capital running low
- ❌ Too many honeypots getting through

### Stop Moonshot Strategy When:
- ❌ Consistently losing money (>4 weeks)
- ❌ Can't emotionally handle volatility
- ❌ Market conditions changed (no good launches)
- ❌ Gas costs >30% of trades

## 🚀 Final Thoughts

Moonshot trading is:
- ✅ Exciting and potentially very profitable
- ✅ Good for learning about token mechanics
- ✅ Low risk per trade ($5)
- ❌ High stress (many losses)
- ❌ Requires discipline
- ❌ Not for everyone

**Start small, learn the patterns, scale slowly!**

---

**Remember: You need just 1-2 big wins per week to be profitable. Stay patient, let the bot do the work, and don't chase every pump!** 🚀💎
