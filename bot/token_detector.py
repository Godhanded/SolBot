import asyncio
import json
import pprint
from time import sleep
from typing import Any, AsyncGenerator
import requests
import ssl
from requests.exceptions import SSLError
from urllib3 import Retry
import websockets
from decimal import Decimal
from requests.adapters import HTTPAdapter
from storage import save_token_data, load_token_data
from config import SOLANA_RPC_URL, SOLANA_RPC_WSS

# SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
TOKEN_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"

THRESHOLD_VOLUME = Decimal(0)  # Example threshold for volume
THRESHOLD_MARKET_CAP = Decimal(0)  # Example threshold for market cap

            
async def run()->AsyncGenerator[tuple[Any, dict], Any]:
    backoff = 1  # Initial backoff time in seconds
    max_backoff = 60  # Maximum backoff time in seconds
    while True:
        async with websockets.connect(SOLANA_RPC_WSS) as websocket:
            try:
                    # Send subscription request
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "logsSubscribe",
                                "params": [
                                    {"mentions": [TOKEN_PROGRAM_ID]},
                                    {"commitment": "confirmed"},
                                ],
                            }
                        )
                    )

                    first_resp = await websocket.recv()
                    print(first_resp)
                    response_dict = json.loads(first_resp)
                    if "result" in response_dict:
                        print(
                            "Subscription successful. Subscription ID: ",
                            response_dict["result"],
                        )

                    # Continuously read from the WebSocket
                    async for response in websocket:
                        response_dict = json.loads(response)
                        pool_store = load_token_data()

                        # if response_dict['params']['result']['value']['err'] == None:
                        signature = response_dict["params"]["result"]["value"]["signature"]

                        if signature not in pool_store:

                            log_messages_set = set(
                                response_dict["params"]["result"]["value"]["logs"]
                            )

                            search = "initialize2"
                            if any(search in message for message in log_messages_set):
                                print(f"True, https://solscan.io/tx/{signature}")
                                pool = parse_new_pool(get_transaction(signature))
                                yield signature, pool
                                save_token_data({signature: pool})
                            else:

                                pass

                        # else:
                        #     print("Error in response: ", response_dict['params']['result']['value']['err'])
                        #     pass
                        backoff = 1

            except websockets.ConnectionClosed as e:
                print(f"WebSocket connection closed: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)  # Exponential backoff
                continue
            except Exception as e:
                print(f"An error occurredR: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)  # Exponential backoff


def get_transaction(signature: str, retries: int = 5) -> dict:
    """
    Fetch a transaction by its signature with retry logic.
    """
    print(signature)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            signature,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
        ],
    }
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    try:
        
        response = session.post(SOLANA_RPC_URL, json=payload)
        if response.status_code == 200:
            result = response.json().get("result")
            if result:
                print({"============TRANSACTION DETECTED====================":result})
                pprint.pprint(result["transaction"]["message"]["instructions"])
                return result["transaction"]["message"]["instructions"]
        else:
            print(f"Attempt failed: {response.json().get('error')}")
    except SSLError as e:
        print(f"SSL error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred T: {e}")
    return None


def parse_new_pool(instruction_list: dict) -> dict:
    """
    Parse a transaction instruction to detect new token pools and track volume.
    """
    try:
        for instruction in instruction_list:
            program_id = instruction["programId"]
            print(program_id, "\n")

            if program_id == TOKEN_PROGRAM_ID:
                print("============NEW POOL DETECTED====================")
                pprint.pprint({"instruct": instruction}, "\n")

                return {
                    "Token0": instruction["accounts"][8],
                    "Token1": instruction["accounts"][9],
                    # "account": instruction["parsed"]["info"].get("destination"),
                    # "source": instruction["parsed"]["info"]["source"],
                    # "volume": Decimal(instruction["parsed"]["info"]["tokenAmount"].get("uiAmountString")),
                }
    except KeyError:
        print("KeyError: Instruction not in expected format")
        return None


# def calculate_market_cap(token_data):
#     """
#     Calculate market cap based on circulating supply and token price.
#     """
#     # Fetch circulating supply from Solana token metadata
#     response = requests.get(
#         f"https://api.mainnet-beta.solana.com/token/{token_data['mint']}"
#     )
#     pprint.pprint(response.json(),"\n")
#     circulating_supply = Decimal(response.json()["result"].get("supply"))
#     print(circulating_supply,"\n")

#     # Fetch token price from a price oracle
#     response = requests.get(
#         f"https://api.mainnet-beta.solana.com/token/{token_data['mint']}/price"
#     )
#     price_per_token = Decimal(response.json()["result"].get("price"))
#     print(price_per_token,"\n")

#     return circulating_supply * price_per_token

# def calculate_market_cap(token_data):
#     """
#     Mock market cap calculation based on circulating supply and token price.
#     Replace this with actual token data from price oracles (if needed).
#     """
#     circulating_supply = Decimal(10_000_000)  # Replace with actual supply
#     price_per_token = Decimal(0.05)  # Replace with actual price
#     return circulating_supply * price_per_token


# def check_newly_listed_token_on_raydium():
#     """
#     Check Raydium DEX for newly listed SOL-token pairs and return the token address and deposited SOL amount.
#     """
#     RAYDIUM_API_URL = "https://api.raydium.io/pairs"

#     response = requests.get(RAYDIUM_API_URL)
#     pairs = response.json().get("data", [])

#     for pair in pairs:
#         if pair["baseToken"]["symbol"] == "SOL":
#             token_address = pair["quoteToken"]["mint"]
#             deposited_sol = Decimal(pair["baseToken"]["amount"])
#             return token_address, deposited_sol

#     return None, None


# async def monitor_tokens():
#     """
#     Continuously monitor tokens for market cap and volume thresholds.
#     Yields token data for alerts.
#     """
#     tracked_tokens = load_token_data()

#     while True:
#         # Fetch recent signatures for SPL Token Program
#         signatures = get_recent_signatures()
#         print({"sigs":signatures})

#         for signature in signatures:
#             await asyncio.sleep(6)
#             transaction = get_transaction(signature)

#             if transaction:
#                 token_data = parse_new_token(transaction)
#                 print({"dat":token_data},"\n")

#                 if token_data:
#                     mint = token_data['mint']

#                     # Update market cap/volume for tokens
#                     if mint not in tracked_tokens:
#                         tracked_tokens[mint] = {
#                             "mint": token_data["mint"],
#                             "account": token_data["account"],
#                             "source": token_data["source"],
#                             "volume": Decimal(0),
#                         }

#                     tracked_tokens[mint]["volume"] = str(Decimal(tracked_tokens[mint]["volume"])+ Decimal(token_data["volume"]))
#                     tracked_tokens[mint]["market_cap"] = str(calculate_market_cap(
#                         token_data
#                     ))

#                     # Check if thresholds are exceeded
#                     if (
#                         Decimal(tracked_tokens[mint]["volume"]) >= THRESHOLD_VOLUME
#                         and Decimal(tracked_tokens[mint]["market_cap"])
#                         >= THRESHOLD_MARKET_CAP
#                     ):
#                         save_token_data(tracked_tokens)  # Save updated stats
#                         yield token_data, tracked_tokens[mint]

#         await asyncio.sleep(30)  # Delay between fetches

# def get_recent_signatures_from_after_current_date(date):
#     """
#     Fetch recent transaction signatures for SPL Token Program.
#     """
#     payload = {
#         "jsonrpc": "2.0",
#         "id": 1,
#         "method": "getSignaturesForAddress",
#         "params": [TOKEN_PROGRAM_ID, {"limit": 50, "before": date}],
#     }
#     response = requests.post(SOLANA_RPC_URL, json=payload)
#     print(response.json().get("result", []),"\n")
#     return [sig["signature"] for sig in response.json().get("result", [])]


# def get_recent_signatures(limit=50):
#  """
# Fetch recent transaction signatures for SPL Token Program starting from the last checked block height.
# """
# payload = {
#     "jsonrpc": "2.0",
#     "id": 1,
#     "method": "getSignaturesForAddress",
#     "params": [TOKEN_PROGRAM_ID, {"limit": limit}],
# }
# response = requests.post(SOLANA_RPC_URL, json=payload)
# return [sig["signature"] for sig in response.json().get("result", [])]
