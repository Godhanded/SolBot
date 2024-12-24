import telegram
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


async def send_telegram_alert(token_address: str, volume: str, market_cap: str)->None:
    """Send an alert when volume and market cap exceed the thresholds."""
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    message = (
        f"🚨 Token Alert!\n\n"
        f"📈 Token Address: {token_address}\n"
        f"💸 Volume: {volume}\n"
        f"💰 Market Cap: ${market_cap:,}"
    )
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def send_telegram_alert(message:str)->None:
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
