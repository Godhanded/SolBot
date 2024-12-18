import asyncio
from token_detector import monitor_tokens
from telegram_bot import send_telegram_alert
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


async def run_bot():
    print("Starting Solana Bot...")
    async for token, stats in monitor_tokens():
        # If thresholds are exceeded, send Telegram notification
        alert_message = (
            f"🚨 *Token Alert!*\n\n"
            f"🪙 Token: {token['mint']}\n"
            f"💸 Volume: {stats['volume']} Sol\n"
            f"💰 Market Cap: ${stats['market_cap']}\n"
        )
        await send_telegram_alert(alert_message)


if __name__ == "__main__":
    asyncio.run(run_bot())
