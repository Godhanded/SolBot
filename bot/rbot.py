import json
import requests
import time

from storage import load_token_data, save_token_data

# Configuration
RPC_URL = ""  # Replace with your Solana RPC HTTP URL
SIGNIFICANT_AMOUNT_SOL = 1000 * 10**9  # SOL (1 SOL = 10^9 lamports)
RAYDIUM_PROGRAM_ID = (
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"  # Raydium AMM program ID
)


# Function to fetch balance of a given token account
def fetch_balance(account_pubkey):
    try:
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountBalance",
            "params": [account_pubkey],
        }
        response = requests.post(RPC_URL, json=body)
        response.raise_for_status()
        data = response.json()
        return int(data["result"]["value"]["amount"]) if "result" in data else 0
    except Exception as e:
        print(f"Error fetching balance for {account_pubkey}: {e}")
        return 0


# Function to fetch recent transaction signatures
def fetch_recent_transactions():
    try:
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                RAYDIUM_PROGRAM_ID,
                {"limit": 50},
            ],  # Fetch the latest 10 transactions
        }
        response = requests.post(RPC_URL, json=body)
        response.raise_for_status()
        data = response.json()
        if "result" in data:
            return [tx["signature"] for tx in data["result"]]
        else:
            return []
    except Exception as e:
        print(f"Error fetching recent transactions: {e}")
        return []


# Function to fetch the details of a transaction using its signature
def fetch_transaction_details(signature):
    try:
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
            ],  # Detailed info
        }
        response = requests.post(RPC_URL, json=body)
        response.raise_for_status()
        data = response.json()
        return data["result"] if "result" in data else None
    except Exception as e:
        print(f"Error fetching transaction details for {signature}: {e}")
        return None


# Function to extract relevant instructions for new pair listing
def extract_involved_account_pubkeys_for_new_pair(transaction):
    involved_accounts = []
    if transaction:
        for instruction in transaction["transaction"]["message"]["instructions"]:
            # Check for instructions related to the creation of a liquidity pool or token pair
            # For example, look for instruction programs that involve `createAccount` or `initializePool` logic
            # These are common in the context of new pair listings
            if instruction.get("programId", "") == RAYDIUM_PROGRAM_ID:
                if "createAccount" in instruction.get("parsed", {}).get("type", ""):
                    involved_accounts.extend(
                        instruction.get("accounts", [])
                    )  # Collect involved accounts
                if "initializePool" in instruction.get("parsed", {}).get("type", ""):
                    involved_accounts.extend(instruction.get("accounts", []))
    return involved_accounts


# Function to process the recent transactions
def process_transactions():
    print("Fetching recent transactions...")
    signatures = fetch_recent_transactions()

    for signature in signatures:
        print(f"Processing transaction with signature: {signature}")
        transaction = fetch_transaction_details(signature)

        # Extract token accounts involved in new pair creation
        involved_accounts = extract_involved_account_pubkeys_for_new_pair(transaction)

        if not involved_accounts:
            print(f"No new pair detected for transaction {signature}. Skipping.")
            continue
        results: list = load_token_data()
        # For each involved account, check its balance
        for account in involved_accounts:
            print(f"Checking account balance: {account}")
            balance = fetch_balance(account)
            print(f"Balance: {balance / 10**9} SOL")

            # Check if the account balance exceeds the threshold
            if balance >= SIGNIFICANT_AMOUNT_SOL:
                results.append({account: balance})
                save_token_data(results)
                print(
                    f"New pair with large SOL balance detected: {account}, Balance: {balance / 10**9} SOL"
                )


# Periodically fetch and process transactions every 10 seconds
def monitor_transactions():
    while True:
        process_transactions()
        time.sleep(30)  # Poll every 30 seconds (adjust as needed)


if __name__ == "__main__":
    monitor_transactions()
