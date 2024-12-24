import requests
import time

# Solscan API endpoint for Raydium DEX
<<<<<<< HEAD
SOLSCAN_API_URL = ""
=======
SOLSCAN_API_URL = "https://api.solscan.io/amm/pools?dex=raydium"
>>>>>>> b4968a9 (update token monitoring logic and add liquidity pool tracking)

# Volume threshold
VOLUME_THRESHOLD = 100000  # Example threshold


# Function to fetch liquidity pools from Solscan API
def fetch_liquidity_pools():
    response = requests.get(SOLSCAN_API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return []


# Function to monitor and store liquidity pools
def monitor_liquidity_pools():
    while True:
        pools = fetch_liquidity_pools()
        for pool in pools:
            volume = pool.get("volume", 0)
            if volume > VOLUME_THRESHOLD:
                store_pool_details(pool)
        time.sleep(60)  # Check every 60 seconds


# Function to store pool details
def store_pool_details(pool):
    with open("liquidity_pools.txt", "a") as file:
        file.write(f"Pool ID: {pool['pool_id']}\n")
        file.write(f"Volume: {pool['volume']}\n")
        file.write(f"Token A: {pool['token_a']['symbol']}\n")
        file.write(f"Token B: {pool['token_b']['symbol']}\n")
        file.write(f"Timestamp: {pool['timestamp']}\n")
        file.write("\n")


if __name__ == "__main__":
    monitor_liquidity_pools()
