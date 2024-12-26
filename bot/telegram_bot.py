from datetime import datetime
from typing import Any, cast
import telegram
import requests
from bot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

SOLANA_MINT_ADDRESS = "So11111111111111111111111111111111111111112"


async def send_telegram_alert_async(
    token_address: str, volume: str, market_cap: str
) -> None:
    """Send an alert when volume and market cap exceed the thresholds."""
    bot = telegram.Bot(token=cast(str, TELEGRAM_BOT_TOKEN))
    message = (
        f"🚨 Token Alert!\n\n"
        f"📈 Token Address: {token_address}\n"
        f"💸 Volume: {volume}\n"
        f"💰 Market Cap: ${market_cap:,}"
    )
    await bot.send_message(chat_id=cast(str, TELEGRAM_CHAT_ID), text=message)


def send_telegram_alert(message: str) -> None:
    """
    Send a notification to Telegram.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"Failed to send Telegram message: {response.content}")


def send_server_telegram_alert(signature: str, new_pool: dict[str, Any]) -> None:
    """
    Send a notification to Telegram.
    """
    message = (
        f"🚨 *Token Alert!*\n\n"
        f"📈 *Exchange:* {new_pool['exchange']}\n\n"
        f"🪙 *Token0:* [{new_pool['token0'] if new_pool['token0']!= SOLANA_MINT_ADDRESS else 'WSOL'}](https://dexscreener.com/solana/{new_pool['token0']}) \n"
        f"💸 *Token0Volume:* {new_pool['token0_volume']}\n\n"
        f"🪙 *Token1:* [{new_pool['token1'] if new_pool['token1']!= SOLANA_MINT_ADDRESS else 'WSOL'}](https://dexscreener.com/solana/{new_pool['token1']}) \n"
        f"💸 *Token1Volume:* {new_pool['token1_volume']}\n\n"
        f"⏳ *List Time:* {datetime.fromtimestamp(float(new_pool['time_stamp']))}(UTC)\n\n"
        f"🧾 *Signature:* https://solscan.io/tx/{signature}\n\n"
        f"💱 *Swap:* https://raydium.io/swap/?inputMint={new_pool['token0']}&outputMint={new_pool['token1']}\n"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"Failed to send Telegram message: {response.content}")
