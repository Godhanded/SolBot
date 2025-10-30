import os
from typing import Any
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from datetime import datetime
from bot.storage import save_token_data, load_token_data
from bot.telegram_bot import send_server_telegram_alert
from bot.token_quality import TokenQualityAnalyzer, quick_filter

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# Initialize quality analyzer
quality_analyzer = TokenQualityAnalyzer()


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
    signature = pool_data[0]["signature"]

    # Extract pool information
    token0 = token_details[0]["mint"]
    token0_volume = token_details[0]["tokenAmount"]
    token1 = token_details[1]["mint"]
    token1_volume = token_details[1]["tokenAmount"]
    exchange = pool_data[0]["source"]
    timestamp = pool_data[0]["timestamp"]

    # Get the AMM address if available (pool address)
    amm_address = pool_data[0].get("accountData", [{}])[0].get("account", "")

    print(f"\n[WEBHOOK] New pool detected: {signature[:8]}...")

    # Step 1: Quick pre-filter (saves API calls)
    if not quick_filter(token0_volume, token1_volume, token0, token1):
        print(f"[WEBHOOK] ❌ Quick filter rejected - Bad liquidity or pump.fun")
        return jsonify({"status": "filtered", "reason": "quick_filter"}), 200

    print(f"[WEBHOOK] ✓ Passed quick filter - Running full analysis...")

    # Step 2: Full quality analysis
    analysis = quality_analyzer.analyze_token(
        amm_address or token0,  # Use AMM address or fallback to token0
        token0_volume,
        token1_volume,
        token0,
        token1
    )

    # Print analysis summary
    print(f"[WEBHOOK] Quality Score: {analysis['quality_score']}/100")
    for reason in analysis['reasons']:
        print(f"[WEBHOOK]   {reason}")

    # Step 3: Only alert on high-quality tokens
    if analysis['should_alert']:
        # Determine which token is SOL and which is the new token
        SOLANA_MINT_ADDRESS = "So11111111111111111111111111111111111111112"

        if token0 == SOLANA_MINT_ADDRESS:
            token_address = token1
            token_volume = token1_volume
        else:
            token_address = token0
            token_volume = token0_volume

        # Create enhanced alert with quality metrics
        alert_message = (
            f"🚀 *HIGH QUALITY GEM DETECTED!* (Webhook)\n\n"
            f"⭐ *Quality Score:* {analysis['quality_score']}/100\n"
            f"💰 *Market Cap:* ${analysis['market_cap']:,.0f}\n"
            f"💧 *Liquidity:* {analysis['liquidity_sol']:.2f} SOL\n\n"
            f"🪙 *Token:* `{token_address}`\n"
            f"📊 *Supply in Pool:* {token_volume:,.0f}\n"
            f"🏪 *Exchange:* {exchange}\n\n"
            f"🔒 *Security:*\n"
            f"{'✅' if analysis['security_checks'].get('mint_authority_revoked') else '❌'} Mint Authority Revoked\n"
            f"{'✅' if analysis['security_checks'].get('freeze_authority_revoked') else '❌'} Freeze Authority Revoked\n\n"
            f"📈 *Analysis:*\n"
        )

        # Add top analysis reasons
        for reason in analysis['reasons'][:5]:  # Top 5 reasons
            alert_message += f"• {reason}\n"

        alert_message += (
            f"\n🔗 *Links:*\n"
            f"[Solscan](https://solscan.io/token/{token_address}) | "
            f"[DexScreener](https://dexscreener.com/solana/{amm_address or token_address}) | "
            f"[Swap](https://raydium.io/swap/?inputMint=So11111111111111111111111111111111111111112&outputMint={token_address})\n\n"
            f"🧾 *Tx:* https://solscan.io/tx/{signature}"
        )

        print(f"[WEBHOOK] 🚀 SENDING ALERT! Quality score: {analysis['quality_score']}/100")
        send_server_telegram_alert(signature, {
            "exchange": exchange,
            "token0": token0,
            "token0_volume": token0_volume,
            "token1": token1,
            "token1_volume": token1_volume,
            "time_stamp": timestamp,
            "quality_score": analysis['quality_score'],
            "market_cap": analysis['market_cap'],
            "liquidity_sol": analysis['liquidity_sol']
        }, custom_message=alert_message)

        # Track this token
        tracked_tokens[signature] = {
            "exchange": exchange,
            "token0": token0,
            "token0_volume": token0_volume,
            "token1": token1,
            "token1_volume": token1_volume,
            "time_stamp": str(datetime.fromtimestamp(timestamp)),
            "quality_score": analysis['quality_score'],
            "market_cap": analysis['market_cap'],
            "liquidity_sol": analysis['liquidity_sol']
        }
        save_token_data(tracked_tokens)
        print(f"[WEBHOOK] ✅ Alert sent and token tracked!")

        return jsonify({
            "status": "success",
            "action": "alerted",
            "quality_score": analysis['quality_score']
        }), 200
    else:
        print(f"[WEBHOOK] ❌ Quality score too low: {analysis['quality_score']}/100")
        return jsonify({
            "status": "success",
            "action": "filtered",
            "quality_score": analysis['quality_score']
        }), 200



if __name__ == "__main__":
    app.run(debug=False)
