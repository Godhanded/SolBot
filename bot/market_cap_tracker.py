from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

async def get_token_supply(client, token_address):
    """Fetch the token's supply from the Solana blockchain."""
    try:
        response = await client.get_token_supply(Pubkey.from_string(token_address))
        if response.get("result"):
            supply = int(response["result"]["value"]["amount"])
            decimals = int(response["result"]["value"]["decimals"])
            return supply / (10**decimals)  # Normalize using decimals
    except Exception as e:
        print(f"Error fetching supply for token {token_address}: {e}")
    return 0

async def get_market_price(token_address):
    """
    Fetch market price for a token. 
    Placeholder for now (use an API like Coingecko, CoinMarketCap, etc.).
    """
    # You could integrate a real-time price API here
    return 0.5  # Mock price in USD

async def calculate_market_cap(client, token_address):
    """Calculate the token's market cap by multiplying supply and price."""
    supply = await get_token_supply(client, token_address)
    price = await get_market_price(token_address)

    if supply and price:
        return supply * price  # Market cap = supply * price
    return 0
