from datetime import datetime, timedelta

from httpx import AsyncClient
from storage import load_tracked_tokens, save_tracked_tokens
from market_cap_tracker import calculate_market_cap

async def calculate_volume(client:AsyncClient, token_address:str):
    """Calculate volume by summing transactions for the token."""
    try:
        from solders.pubkey import Pubkey
        pubkey = Pubkey.from_string(token_address)

        transactions = await client.get_signatures_for_address(pubkey, limit=100)
        total_volume = 0

        if "result" in transactions:
            for tx in transactions["result"]:
                # Replace with logic to calculate transaction amount
                total_volume += 1  # Placeholder for trade volume calculation

        return total_volume

    except Exception as e:
        print(f"Error calculating volume for {token_address}: {e}")
        return 0

def reset_data(tracked_tokens:dict):
    """Reset volumes and market caps after RESET_INTERVAL_DAYS."""
    from bot.config import RESET_INTERVAL_DAYS
    current_time = datetime.utcnow()
    reset_interval = timedelta(days=RESET_INTERVAL_DAYS)

    for token_address, data in tracked_tokens.items():
        last_reset = datetime.utcfromtimestamp(data["last_reset"])
        if current_time - last_reset >= reset_interval:
            data["volume"] = 0
            data["market_cap"] = 0
            data["last_reset"] = current_time.timestamp()

    return tracked_tokens

async def update_tracking():
    """Update both token volumes and market caps."""
    from bot.config import SOLANA_RPC_URL
    tracked_tokens = load_tracked_tokens()

    # Reset data for tokens past the reset interval
    tracked_tokens = reset_data(tracked_tokens)

    async with AsyncClient(SOLANA_RPC_URL) as client:
        for token_address in tracked_tokens:
            # Update volume
            new_volume = await calculate_volume(client, token_address)
            tracked_tokens[token_address]["volume"] += new_volume

            # Update market cap
            market_cap = await calculate_market_cap(client, token_address)
            tracked_tokens[token_address]["market_cap"] = market_cap

        save_tracked_tokens(tracked_tokens)

    return tracked_tokens
