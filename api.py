import os
from typing import Any
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from datetime import datetime
from bot.storage import save_token_data, load_token_data
from bot.telegram_bot import send_server_telegram_alert

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


@app.route("/")
def health():
    return jsonify({"status": "healthy"}),200


@app.route("/", methods=["POST"])
def process_pool():
    key = request.headers.get("Authorization")
    if key != app.secret_key:
        print("fail")
        return jsonify({"status": "unauthorized"}, 401)
    pool_data: list[dict[str, Any]] = request.get_json()
    tracked_tokens = load_token_data()
    token_details = pool_data[0]["tokenTransfers"]

    new_pool = {
        "exchange":pool_data[0]["source"],
        "token0": token_details[0]["mint"],
        "token0_volume": token_details[0]["tokenAmount"],
        "token1": token_details[1]["mint"],
        "token1_volume": token_details[1]["tokenAmount"],
        "time_stamp": pool_data[0]["timestamp"],
    }
    if new_pool["token0_volume"] > 200 and new_pool["token1_volume"] > 200:
        send_server_telegram_alert(pool_data[0]["signature"], new_pool)
        tracked_tokens[pool_data[0]["signature"]] = {**new_pool,"time_stamp":str(datetime.fromtimestamp(pool_data[0]["timestamp"]))}
        save_token_data(tracked_tokens)

    return jsonify({"status": "success"}),200



if __name__ == "__main__":
    app.run(debug=False)
