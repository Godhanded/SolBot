from solana.rpc.async_api import AsyncClient
from solana.rpc.types import MemcmpOpts
from datetime import datetime
from storage import load_tracked_tokens, save_tracked_tokens

async def get_block_height_for_date(client, date_str):
    """Fetch block height for a specific date using Solana's RPC."""
    timestamp = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())
    response = await client.get_block_time(timestamp)
    if response["result"]:
        return response["result"]
    return None

async def detect_new_tokens():
    """Detect new tokens created after the START_DATE."""
    from config import SOLANA_RPC_URL, START_DATE
    tracked_tokens = load_tracked_tokens()

    async with AsyncClient(SOLANA_RPC_URL) as client:
        # Get block height for the start date
        start_block_height = await get_block_height_for_date(client, START_DATE)
        if not start_block_height:
            print(f"Failed to fetch block height for start date: {START_DATE}")
            return []

        # Query the token program for new tokens
        filters = [MemcmpOpts(offset=0, bytes="mint")]

        response = await client.get_program_accounts(
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  filters=filters, encoding="jsonParsed"
        )

        new_tokens = []
        for account in response["result"]:
            pubkey = account["pubkey"]

            # Fetch the slot (block height) for the account's creation date
            transaction_history = await client.get_signatures_for_address(pubkey, limit=1)
            if transaction_history["result"] and int(transaction_history["result"][0]["slot"]) >= start_block_height:
                if pubkey not in tracked_tokens:
                    tracked_tokens[pubkey] = {"volume": 0, "last_reset": datetime.utcnow().timestamp()}
                    new_tokens.append(pubkey)

        if new_tokens:
            save_tracked_tokens(tracked_tokens)

        return new_tokens
