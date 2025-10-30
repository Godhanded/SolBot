import asyncio
import traceback
from token_detector import run
from telegram_bot import send_telegram_alert
from token_quality import TokenQualityAnalyzer, quick_filter
from dotenv import load_dotenv
import psutil

load_dotenv()  # Load environment variables from .env

SOLANA_MINT_ADDRESS = "So11111111111111111111111111111111111111112"

# Initialize quality analyzer
quality_analyzer = TokenQualityAnalyzer()


async def run_bot() -> None:
    print("Starting Solana Bot with Quality Filtering...")
    total_detected = 0
    filtered_out = 0
    alerts_sent = 0

    try:
        async for signature, pool, volumes in run():
            total_detected += 1

            # Step 1: Quick pre-filter (saves API calls)
            if not quick_filter(
                volumes['Token0Volume'],
                volumes['Token1Volume'],
                pool['Token0'],
                pool['Token1']
            ):
                filtered_out += 1
                print(f"[{total_detected}] ❌ Quick filter rejected - Bad liquidity or pump.fun")
                continue

            print(f"[{total_detected}] ✓ Passed quick filter - Running full analysis...")

            # Step 2: Full quality analysis
            analysis = quality_analyzer.analyze_token(
                pool['Amm'],  # AMM address
                volumes['Token0Volume'],
                volumes['Token1Volume'],
                pool['Token0'],
                pool['Token1']
            )

            # Print analysis summary
            print(f"Quality Score: {analysis['quality_score']}/100")
            for reason in analysis['reasons']:
                print(f"  {reason}")

            # Step 3: Only alert on high-quality tokens
            if analysis['should_alert']:
                alerts_sent += 1

                # Determine token addresses for links
                if pool['Token0'] == SOLANA_MINT_ADDRESS:
                    token_address = pool['Token1']
                    token_volume = volumes['Token1Volume']
                    sol_volume = volumes['Token0Volume']
                else:
                    token_address = pool['Token0']
                    token_volume = volumes['Token0Volume']
                    sol_volume = volumes['Token1Volume']

                # Create enhanced alert with quality metrics
                alert_message = (
                    f"🚀 *HIGH QUALITY GEM DETECTED!*\n\n"
                    f"⭐ *Quality Score:* {analysis['quality_score']}/100\n"
                    f"💰 *Market Cap:* ${analysis['market_cap']:,.0f}\n"
                    f"💧 *Liquidity:* {analysis['liquidity_sol']:.2f} SOL\n\n"
                    f"🪙 *Token:* `{token_address}`\n"
                    f"📊 *Supply in Pool:* {token_volume:,.0f}\n\n"
                    f"🔒 *Security:*\n"
                    f"{'✅' if analysis['security_checks'].get('mint_authority_revoked') else '❌'} Mint Authority Revoked\n"
                    f"{'✅' if analysis['security_checks'].get('freeze_authority_revoked') else '❌'} Freeze Authority Revoked\n\n"
                    f"📈 *Analysis:*\n"
                )

                # Add top analysis reasons
                for reason in analysis['reasons'][:5]:  # Top 5 reasons
                    alert_message += f"• {reason}\n"

                alert_message += (
                    f"\n🔗 *Links:*\n"
                    f"[Solscan](https://solscan.io/token/{token_address}) | "
                    f"[DexScreener](https://dexscreener.com/solana/{pool['Amm']}) | "
                    f"[Swap](https://raydium.io/swap/?inputMint=So11111111111111111111111111111111111111112&outputMint={token_address})\n\n"
                    f"🧾 *Tx:* https://solscan.io/tx/{signature}\n\n"
                    f"⚡ Stats: Detected {total_detected} | Filtered {filtered_out} | Alerted {alerts_sent}"
                )

                print(f"🚀 SENDING ALERT! Quality score: {analysis['quality_score']}/100")
                send_telegram_alert(alert_message)
                print("✅ Alert sent!")
            else:
                filtered_out += 1
                print(f"❌ Quality score too low: {analysis['quality_score']}/100 (minimum 70)")
                print(f"   Stats: Detected {total_detected} | Filtered {filtered_out} | Alerted {alerts_sent}")

    except asyncio.CancelledError:
        print("Bot is shutting down gracefully...")
        raise  # Re-raise the exception to ensure the task is cancelled
    except Exception as e:
        print(f"An error occurred: {e}")
        print(traceback.format_exc())
        print(f"Memory usage: {psutil.Process().memory_info().rss / 1024 ** 2} MB")
        print(f"CPU usage: {psutil.cpu_percent(interval=1)}%")


async def main() -> None:
    task = asyncio.create_task(run_bot())
    try:
        await task
    except KeyboardInterrupt:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("Main task cancelled successfully.")
    except Exception as e:
        print(f"An error occurred in main: {e}")


asyncio.run(main())
