#!/usr/bin/env python3
"""
Setup Verification Script
Checks if your EVM Bot configuration is correct before running

Usage:
    python check_setup.py
"""

import sys
from pathlib import Path

# Add bot to path
sys.path.insert(0, str(Path(__file__).parent))

def check_setup():
    """Check if setup is correct"""
    print("🔍 Checking EVM Bot Setup...\n")

    errors = []
    warnings = []
    success = []

    # 1. Check .env file exists
    print("1️⃣  Checking .env file...")
    env_file = Path(".env")
    if not env_file.exists():
        errors.append(".env file not found. Copy .env.example to .env")
        print("   ❌ .env file not found\n")
    else:
        success.append(".env file exists")
        print("   ✅ .env file found\n")

    # 2. Check dependencies
    print("2️⃣  Checking dependencies...")
    missing_deps = []

    try:
        import web3
        success.append("web3 installed")
    except ImportError:
        missing_deps.append("web3")

    try:
        import aiohttp
        success.append("aiohttp installed")
    except ImportError:
        missing_deps.append("aiohttp")

    try:
        import dotenv
        success.append("python-dotenv installed")
    except ImportError:
        missing_deps.append("python-dotenv")

    if missing_deps:
        errors.append(f"Missing dependencies: {', '.join(missing_deps)}")
        errors.append("Run: pip install -r requirements.txt")
        print(f"   ❌ Missing: {', '.join(missing_deps)}\n")
    else:
        print("   ✅ All dependencies installed\n")

    # 3. Check configuration
    if env_file.exists():
        print("3️⃣  Checking configuration...")

        from dotenv import load_dotenv
        import os
        load_dotenv()

        # Telegram
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")

        if not telegram_token or "your_bot_token" in telegram_token:
            errors.append("TELEGRAM_BOT_TOKEN not configured in .env")
            print("   ❌ Telegram bot token missing")
        else:
            success.append("Telegram bot token configured")
            print("   ✅ Telegram bot token configured")

        if not telegram_chat or "your_chat_id" in telegram_chat:
            errors.append("TELEGRAM_CHAT_ID not configured in .env")
            print("   ❌ Telegram chat ID missing")
        else:
            success.append("Telegram chat ID configured")
            print("   ✅ Telegram chat ID configured")

        print()

        # RPC
        rpc_url = os.getenv("BSC_RPC_URL")
        if rpc_url:
            success.append("BSC RPC URL configured")
            print(f"   ✅ BSC RPC: {rpc_url[:50]}...")
        else:
            errors.append("BSC_RPC_URL not configured")
            print("   ❌ BSC RPC URL missing")

        print()

        # Auto-trade
        auto_trade = os.getenv("AUTO_TRADE", "false").lower() == "true"
        private_key = os.getenv("PRIVATE_KEY")

        if auto_trade:
            print("   ⚠️  AUTO_TRADE is ENABLED")
            if not private_key or "your_private_key" in private_key:
                errors.append("AUTO_TRADE enabled but PRIVATE_KEY not configured")
                print("   ❌ Private key required for auto-trading")
            else:
                warnings.append("Auto-trading enabled - ensure you understand the risks")
                print("   ✅ Private key configured")
                print("   ⚠️  Make sure this is a dedicated wallet!")
        else:
            success.append("Running in signal-only mode (safe)")
            print("   ✅ Running in signal-only mode (safe)")

        print()

    # 4. Check network connectivity
    print("4️⃣  Checking network connectivity...")

    if env_file.exists() and 'web3' in sys.modules:
        from web3 import Web3
        import os

        rpc_url = os.getenv("BSC_RPC_URL", "https://bsc-dataseed1.binance.org")

        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                chain_id = w3.eth.chain_id
                block = w3.eth.block_number
                success.append(f"Connected to BSC (Chain {chain_id}, Block {block})")
                print(f"   ✅ Connected to BSC")
                print(f"   ✅ Chain ID: {chain_id}")
                print(f"   ✅ Latest block: {block}")
            else:
                errors.append("Could not connect to BSC RPC")
                print("   ❌ Could not connect to BSC RPC")
        except Exception as e:
            errors.append(f"BSC connection error: {e}")
            print(f"   ❌ Connection error: {e}")

        print()

    # 5. Check directory structure
    print("5️⃣  Checking directory structure...")

    required_dirs = ["bot", "data", "logs"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            success.append(f"{dir_name}/ directory exists")
            print(f"   ✅ {dir_name}/ exists")
        else:
            warnings.append(f"{dir_name}/ directory missing (will be created)")
            print(f"   ⚠️  {dir_name}/ missing (will be created)")

    print()

    # Summary
    print("="*60)
    print("📊 SUMMARY")
    print("="*60)

    if success:
        print(f"\n✅ {len(success)} checks passed:")
        for item in success[:5]:  # Show first 5
            print(f"   • {item}")
        if len(success) > 5:
            print(f"   • ... and {len(success) - 5} more")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warnings:")
        for warning in warnings:
            print(f"   • {warning}")

    if errors:
        print(f"\n❌ {len(errors)} errors:")
        for error in errors:
            print(f"   • {error}")
        print("\n" + "="*60)
        print("❌ SETUP INCOMPLETE")
        print("="*60)
        print("\nPlease fix the errors above before running the bot.")
        print("\nQuick fixes:")
        print("  1. Copy .env.example to .env")
        print("  2. Edit .env with your Telegram bot token and chat ID")
        print("  3. Run: pip install -r requirements.txt")
        print("\nSee QUICKSTART.md for detailed instructions.")
        return False

    print("\n" + "="*60)
    print("✅ SETUP COMPLETE")
    print("="*60)

    if warnings:
        print("\n⚠️  Note the warnings above")

    print("\n🚀 You're ready to run the bot!")
    print("\nTo start:")
    print("  python -m bot.main")
    print("\nFor more info:")
    print("  • QUICKSTART.md - Quick start guide")
    print("  • README.md - Full documentation")
    print("  • .env - Configuration file")

    return True


if __name__ == "__main__":
    try:
        success = check_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCheck cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
