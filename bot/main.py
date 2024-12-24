import asyncio
import traceback
from token_detector import run
from telegram_bot import send_telegram_alert
from dotenv import load_dotenv
import psutil

load_dotenv()  # Load environment variables from .env

SOLANA_MINT_ADDRESS = "So11111111111111111111111111111111111111112"


async def run_bot() -> None:
    print("Starting Solana Bot...")
    try:
        async for signature, pool, volumes in run():
            # If thresholds are exceeded, send Telegram notification
            alert_message = (
                f"🚨 *Token Alert!*\n\n"
                f"📈 *Pool:* {pool['Amm']}\n\n"
                f"🪙 *Token0:* {pool['Token0'] if pool['Token0']!= SOLANA_MINT_ADDRESS else 'WSOL'}\n"
                f"💸 *Token0Volume:* ${volumes['Token0Volume']}\n\n"
                f"🪙 *Token1:* {pool['Token1'] if pool['Token1']!= SOLANA_MINT_ADDRESS else 'WSOL'}\n"
                f"💸 *Token1Volume:* ${volumes['Token1Volume']}\n\n"
                f"🧾 *Signature:* https://solscan.io/tx/{signature}\n"
                f"💱 *Swap:* https://raydium.io/swap/?inputMint={pool['Token0']}&outputMint={pool['Token1']}\n"
                # f"💸 Volume: {stats['volume']} Sol\n"
                # f"💰 Market Cap: ${stats['market_cap']}\n"
            )
            print("Alerting....")
            send_telegram_alert(alert_message)

    except asyncio.CancelledError:
        print("Bot is shutting down gracefully...")
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
        await task
    except Exception as e:
        print(f"An error occurred in main: {e}")


asyncio.run(main())
