import os
from typing import Any
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from bot.storage import save_token_data, load_token_data
from bot.telegram_bot import send_server_telegram_alert

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


@app.route("/")
def health():
    return jsonify({"status": "healthy"}, 200)


@app.route("/", method=["POST"])
def process_pool():
    key = request.headers.get("X-API-KEY")
    if key != "my_secret_key":
        return jsonify({"status": "unauthorized"}, 401)
    pool_data: dict[str, Any] = request.get_json()
    tracked_tokens = load_token_data()
    token_details = pool_data["tokenTransfers"]

    new_pool = {
        "token0": token_details[0]["mint"],
        "token0_volume": token_details[0]["tokenAmount"],
        "token1": token_details[1]["mint"],
        "token1_volume": token_details[1]["tokenAmount"],
        "time_stamp": pool_data["timestamp"],
    }
    tracked_tokens[pool_data["signature"]] = new_pool
    # if new_pool["token0_volume"] > 1000 or new_pool["token1_volume"] > 1000:
    save_token_data(tracked_tokens)
    send_server_telegram_alert(pool_data["signature"], new_pool)

    return jsonify({"status": "success"}, 200)
