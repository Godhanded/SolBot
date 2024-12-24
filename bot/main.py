import asyncio
from token_detector import run
from telegram_bot import send_telegram_alert
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


async def run_bot():
    print("Starting Solana Bot...")
    try:
        async for signature, pool in run():
            # If thresholds are exceeded, send Telegram notification
            alert_message = (
                f"🚨 *Token Alert!*\n\n"
                f"🪙 Token0: {pool['Token0']}\n"
                f"🪙 Token1: {pool['Token1']}\n"
                f"🧾 Signature: https://solscan.io/tx/{signature}\n"
                # f"💸 Volume: {stats['volume']} Sol\n"
                # f"💰 Market Cap: ${stats['market_cap']}\n"
            )
            print("Alerting....")
            await send_telegram_alert(alert_message)
    except asyncio.CancelledError:
        print("Bot is shutting down gracefully...")
    except Exception as e:
        print(f"An error occurred: {e}")


async def main():
    task = asyncio.create_task(run_bot())
    try:
        await task
    except KeyboardInterrupt:
        task.cancel()
        await task
    except Exception as e:
        print(f"An error occurred in main: {e}")


if __name__ == "__main__":
    asyncio.run(main())
