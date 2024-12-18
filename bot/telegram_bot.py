import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

async def send_telegram_alert(token_address:str, volume:str, market_cap:str):
    """Send an alert when volume and market cap exceed the thresholds."""
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    message = (
        f"🚨 Token Alert!\n\n"
        f"📈 Token Address: {token_address}\n"
        f"💸 Volume: {volume}\n"
        f"💰 Market Cap: ${market_cap:,}"
    )
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
