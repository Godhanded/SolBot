import pprint
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
        # print({"sigs":signatures})

        for signature in signatures:
            await asyncio.sleep(6)
            transaction = get_transaction(signature)

            if transaction:
                token_data = parse_new_token(transaction)
                print({"dat":token_data},"\n")

                if token_data:
                    mint = token_data['mint']

                    # Update market cap/volume for tokens
                    if mint not in tracked_tokens:
                        tracked_tokens[mint] = {
                            "mint": token_data["mint"],
                            "account": token_data["account"],
                            "source": token_data["source"],
                            "volume": Decimal(0),
                        }

                    tracked_tokens[mint]["volume"] = str(Decimal(tracked_tokens[mint]["volume"])+ Decimal(token_data["volume"]))
                    tracked_tokens[mint]["market_cap"] = str(calculate_market_cap(
                        token_data
                    ))

                    # Check if thresholds are exceeded
                    if (
                        Decimal(tracked_tokens[mint]["volume"]) >= THRESHOLD_VOLUME
                        and Decimal(tracked_tokens[mint]["market_cap"])
                        >= THRESHOLD_MARKET_CAP
                    ):
                        save_token_data(tracked_tokens)  # Save updated stats
                        yield token_data, tracked_tokens[mint]

        await asyncio.sleep(30)  # Delay between fetches

def get_recent_signatures_from_after_current_date(date):
    """
    Fetch recent transaction signatures for SPL Token Program.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [TOKEN_PROGRAM_ID, {"limit": 50, "before": date}],
    }
    response = requests.post(SOLANA_RPC_URL, json=payload)
    print(response.json().get("result", []),"\n")
    return [sig["signature"] for sig in response.json().get("result", [])]

def get_recent_signatures(limit=50):
    """
    Fetch recent transaction signatures for SPL Token Program starting from the last checked block height.
    """
    last_checked_block = load_token_data().get("last_checked_block", None)
    params = [TOKEN_PROGRAM_ID, {"limit": limit}]
    if last_checked_block:
        params[1]["before"] = last_checked_block

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": params,
    }
    response = requests.post(SOLANA_RPC_URL, json=payload)
    signatures = response.json().get("result", [])
    
    if signatures:
        last_checked_block = signatures[-1]["slot"]
        save_token_data({"last_checked_block": last_checked_block})

    return [sig["signature"] for sig in signatures]


def get_transaction(signature, retries=5):
    """
    Fetch a transaction by its signature with retry logic.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"encoding": "jsonParsed","maxSupportedTransactionVersion": 0}],
    }
    for attempt in range(retries):
        response = requests.post(SOLANA_RPC_URL, json=payload)
        if response.status_code == 200:
            result = response.json().get("result")
            if result:
                pprint.pprint(result)
                return result
        else:
            print(f"Attempt {attempt + 1} failed: {response.json().get('error')}")
            sleep(2 ** attempt)  # Exponential backoff
    return None



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
                        "account": instruction["parsed"]["info"].get("destination"),
                        "source": instruction["parsed"]["info"]["source"],
                        "volume": Decimal(instruction["parsed"]["info"]["tokenAmount"].get("uiAmountString"),0),
                    }
    except KeyError:
        return None
    return None

def calculate_market_cap(token_data):
    """
    Calculate market cap based on circulating supply and token price.
    """
    # Fetch circulating supply from Solana token metadata
    response = requests.get(
        f"https://api.mainnet-beta.solana.com/token/{token_data['mint']}"
    )
    circulating_supply = Decimal(response.json()["supply"])
    print(circulating_supply,"\n")

    # Fetch token price from a price oracle
    response = requests.get(
        f"https://api.mainnet-beta.solana.com/token/{token_data['mint']}/price"
    )
    price_per_token = Decimal(response.json()["result"].get("price"))
    print(price_per_token,"\n")

    return circulating_supply * price_per_token

# def calculate_market_cap(token_data):
#     """
#     Mock market cap calculation based on circulating supply and token price.
#     Replace this with actual token data from price oracles (if needed).
#     """
#     circulating_supply = Decimal(10_000_000)  # Replace with actual supply
#     price_per_token = Decimal(0.05)  # Replace with actual price
#     return circulating_supply * price_per_token
