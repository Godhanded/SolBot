from time import sleep
import requests
import asyncio
from decimal import Decimal
from storage import save_token_data, load_token_data
from config import SOLANA_RPC_URL

# SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

THRESHOLD_VOLUME = Decimal(0)  # Example threshold for volume
THRESHOLD_MARKET_CAP = Decimal(0)  # Example threshold for market cap


async def monitor_tokens():
    """
    Continuously monitor tokens for market cap and volume thresholds.
    Yields token data for alerts.
    """
    tracked_tokens = load_token_data()

    while True:
        # Fetch recent signatures for SPL Token Program
        signatures = get_recent_signatures()
        print({"sigs":signatures})

        for signature in signatures:
            await asyncio.sleep(10)
            transaction = get_transaction(signature)
            print({"tra":transaction},"\n")

            if transaction:
                token_data = parse_new_token(transaction)
                print({"dat":token_data},"\n")

                if token_data:
                    mint = token_data['mint']

                    # Update market cap/volume for tokens
                    if mint not in tracked_tokens:
                        tracked_tokens[mint] = {
                            "volume": Decimal(0),
                            "market_cap": Decimal(0)
                        }

                    tracked_tokens[mint]["volume"] += token_data["volume"]
                    tracked_tokens[mint]["market_cap"] = calculate_market_cap(
                        token_data
                    )

                    # Check if thresholds are exceeded
                    if (
                        tracked_tokens[mint]["volume"] >= THRESHOLD_VOLUME
                        and tracked_tokens[mint]["market_cap"]
                        >= THRESHOLD_MARKET_CAP
                    ):
                        save_token_data(tracked_tokens)  # Save updated stats
                        yield token_data, tracked_tokens[mint]

        await asyncio.sleep(60)  # Delay between fetches


def get_recent_signatures(limit=50):
    """
    Fetch recent transaction signatures for SPL Token Program.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [TOKEN_PROGRAM_ID, {"limit": limit}],
    }
    response = requests.post(SOLANA_RPC_URL, json=payload)
    return [sig["signature"] for sig in response.json().get("result", [])]


def get_transaction(signature):
    """
    Fetch a transaction by its signature.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"encoding": "jsonParsed","maxSupportedTransactionVersion": 0}],
    }
    response = requests.post(SOLANA_RPC_URL, json=payload)
    return response.json().get("result")


def parse_new_token(transaction):
    """
    Parse a transaction to detect new token mints and track volume.
    """
    try:
        for instruction in transaction["transaction"]["message"]["instructions"]:
            program_id = instruction["programId"]
            print(program_id,"\n")

            if program_id == TOKEN_PROGRAM_ID:
                if "mint" in instruction["parsed"]["info"]:
                    return {
                        "mint": instruction["parsed"]["info"]["mint"],
                        "volume": Decimal(instruction["parsed"]["info"].get("amount", 0)),
                    }
    except KeyError:
        return None
    return None


def calculate_market_cap(token_data):
    """
    Mock market cap calculation based on circulating supply and token price.
    Replace this with actual token data from price oracles (if needed).
    """
    circulating_supply = Decimal(10_000_000)  # Replace with actual supply
    price_per_token = Decimal(0.05)  # Replace with actual price
    return circulating_supply * price_per_token
