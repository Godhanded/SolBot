import asyncio
from token_detector import detect_new_tokens
from volume_tracker import update_tracking
from telegram_bot import send_telegram_alert
from config import ALERT_VOLUME_THRESHOLD, ALERT_MARKET_CAP_THRESHOLD

async def run_bot():
    new_tokens = await detect_new_tokens()
    print(f"New tokens detected: {new_tokens}")

    tracked_tokens = await update_tracking()

    for token_address, data in tracked_tokens.items():
        if data["volume"] >= ALERT_VOLUME_THRESHOLD and data["market_cap"] >= ALERT_MARKET_CAP_THRESHOLD:
            await send_telegram_alert(token_address, data["volume"], data["market_cap"])

if __name__ == "__main__":
    asyncio.run(run_bot())
