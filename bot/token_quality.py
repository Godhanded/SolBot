"""
Token Quality Analyzer for finding high-potential gems
Filters out scams, rug pulls, and low-quality tokens
"""
import requests
from decimal import Decimal
from typing import Optional, Dict, Any
from config import (
    SOLANA_RPC_URL,
    MIN_LIQUIDITY_SOL,
    MAX_LIQUIDITY_SOL,
    OPTIMAL_LIQUIDITY_MIN,
    OPTIMAL_LIQUIDITY_MAX,
    MARKET_CAP_MIN,
    MARKET_CAP_MAX,
    MARKET_CAP_UPPER_LIMIT,
    MAX_TOP_HOLDER_PERCENTAGE,
    SOL_PRICE_USD,
    FILTER_PUMP_FUN_TOKENS,
    REQUIRE_MINT_REVOKED,
    REQUIRE_FREEZE_REVOKED,
    MINIMUM_QUALITY_SCORE
)

# Wrapped SOL address (used in most pairs)
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"

# Pump.fun program ID (filter these out - mostly scams)
PUMP_FUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"


class TokenQualityAnalyzer:
    """Analyzes token quality and calculates a quality score (0-100)"""

    def __init__(self, rpc_url: str | None = SOLANA_RPC_URL):
        if not rpc_url:
            raise ValueError("SOLANA_RPC_URL must be set in environment variables")
        self.rpc_url = rpc_url

    def analyze_token(self, token_address: str, token0_volume: float, token1_volume: float,
                     token0_address: str, token1_address: str) -> Dict[str, Any]:
        """
        Comprehensive token quality analysis

        Returns:
            dict with keys: quality_score, should_alert, liquidity_sol, market_cap,
                           holder_concentration, security_checks, reasons
        """
        result = {
            "quality_score": 0,
            "should_alert": False,
            "liquidity_sol": 0,
            "market_cap": 0,
            "holder_concentration": 0,
            "security_checks": {},
            "reasons": []
        }

        # Determine which token is SOL and which is the new token
        if token0_address == WSOL_ADDRESS:
            sol_volume = token0_volume
            token_volume = token1_volume
            new_token_address = token1_address
        elif token1_address == WSOL_ADDRESS:
            sol_volume = token1_volume
            token_volume = token0_volume
            new_token_address = token0_address
        else:
            # Neither token is SOL - skip these exotic pairs
            result["reasons"].append("No SOL pair - exotic pair")
            return result

        result["liquidity_sol"] = sol_volume

        # CRITICAL FILTER 1: Minimum Liquidity
        if sol_volume < MIN_LIQUIDITY_SOL:
            result["reasons"].append(f"Insufficient liquidity: {sol_volume:.2f} SOL < {MIN_LIQUIDITY_SOL} SOL minimum")
            return result

        # CRITICAL FILTER 2: Maximum Liquidity (too high = hard to pump)
        if sol_volume > MAX_LIQUIDITY_SOL:
            result["reasons"].append(f"Liquidity too high for moonshot: {sol_volume:.2f} SOL > {MAX_LIQUIDITY_SOL} SOL")
            return result

        # CRITICAL FILTER 3: Check if pump.fun token (filter by address pattern)
        if FILTER_PUMP_FUN_TOKENS and self._is_pump_fun_token(new_token_address):
            result["reasons"].append("Pump.fun token detected - high scam risk")
            return result

        # Start calculating quality score
        score = 0

        # SCORE COMPONENT 1: Liquidity (0-30 points)
        # Sweet spot: configured optimal range
        if OPTIMAL_LIQUIDITY_MIN <= sol_volume <= OPTIMAL_LIQUIDITY_MAX:
            score += 30
            result["reasons"].append(f"✓ Optimal liquidity: {sol_volume:.2f} SOL")
        elif MIN_LIQUIDITY_SOL <= sol_volume < OPTIMAL_LIQUIDITY_MIN:
            score += 20
            result["reasons"].append(f"✓ Decent liquidity: {sol_volume:.2f} SOL")
        elif OPTIMAL_LIQUIDITY_MAX < sol_volume <= (OPTIMAL_LIQUIDITY_MAX * 2):
            score += 20
            result["reasons"].append(f"✓ Good liquidity: {sol_volume:.2f} SOL")
        else:
            score += 10
            result["reasons"].append(f"✓ Acceptable liquidity: {sol_volume:.2f} SOL")

        # SCORE COMPONENT 2: Market Cap (0-25 points)
        # Estimate market cap based on pool ratio
        try:
            market_cap = self._estimate_market_cap(sol_volume, token_volume, new_token_address)
            result["market_cap"] = market_cap

            # Sweet spot: configured range for moonshot potential
            if MARKET_CAP_MIN <= market_cap <= MARKET_CAP_MAX:
                score += 25
                result["reasons"].append(f"✓ Moonshot market cap: ${market_cap:,.0f}")
            elif MARKET_CAP_MAX < market_cap <= MARKET_CAP_UPPER_LIMIT:
                score += 15
                result["reasons"].append(f"✓ Decent market cap: ${market_cap:,.0f}")
            elif market_cap < MARKET_CAP_MIN:
                score += 5
                result["reasons"].append(f"⚠ Very low market cap: ${market_cap:,.0f} (high risk)")
            else:
                result["reasons"].append(f"⚠ High market cap: ${market_cap:,.0f} (limited upside)")
        except Exception as e:
            result["reasons"].append(f"⚠ Could not calculate market cap: {e}")

        # SCORE COMPONENT 3: Token Security (0-30 points)
        security = self._check_token_security(new_token_address)
        result["security_checks"] = security

        if security.get("mint_authority_revoked"):
            score += 15
            result["reasons"].append("✓ Mint authority revoked (immutable supply)")
        else:
            result["reasons"].append("⚠ Mint authority NOT revoked (can create infinite tokens)")
            if REQUIRE_MINT_REVOKED:
                result["reasons"].append("❌ REJECTED: Mint authority required to be revoked")
                return result

        if security.get("freeze_authority_revoked"):
            score += 15
            result["reasons"].append("✓ Freeze authority revoked (not a honeypot)")
        else:
            result["reasons"].append("⚠ Freeze authority NOT revoked (potential honeypot)")
            if REQUIRE_FREEZE_REVOKED:
                result["reasons"].append("❌ REJECTED: Freeze authority required to be revoked")
                return result

        # SCORE COMPONENT 4: Holder Distribution (0-15 points)
        holder_data = self._check_holder_distribution(new_token_address)
        if holder_data:
            top_holder_pct = holder_data.get("top_holder_percentage", 100)
            result["holder_concentration"] = top_holder_pct

            # Check against configured maximum
            if top_holder_pct > MAX_TOP_HOLDER_PERCENTAGE:
                result["reasons"].append(f"❌ High concentration: Top holder {top_holder_pct:.1f}% > {MAX_TOP_HOLDER_PERCENTAGE}% (rug risk)")
                return result

            if top_holder_pct < 30:
                score += 15
                result["reasons"].append(f"✓ Great distribution: Top holder {top_holder_pct:.1f}%")
            elif top_holder_pct < 50:
                score += 10
                result["reasons"].append(f"✓ Good distribution: Top holder {top_holder_pct:.1f}%")
            elif top_holder_pct <= MAX_TOP_HOLDER_PERCENTAGE:
                score += 5
                result["reasons"].append(f"⚠ Moderate concentration: Top holder {top_holder_pct:.1f}%")
        else:
            score += 5  # Give benefit of doubt if we can't check
            result["reasons"].append("⚠ Could not verify holder distribution")

        result["quality_score"] = score

        # Use configured minimum quality score
        if score >= MINIMUM_QUALITY_SCORE:
            result["should_alert"] = True
            result["reasons"].append(f"🚀 HIGH QUALITY GEM: Score {score}/100")
        elif score >= 50:
            result["reasons"].append(f"⚠ MODERATE QUALITY: Score {score}/100 (below threshold of {MINIMUM_QUALITY_SCORE})")
        else:
            result["reasons"].append(f"❌ LOW QUALITY: Score {score}/100 (rejected)")

        return result

    def _is_pump_fun_token(self, token_address: str) -> bool:
        """
        Check if token is from pump.fun (usually ends with 'pump')
        These are typically low-quality meme coins
        """
        # Most pump.fun tokens have 'pump' at the end of their address
        if token_address.endswith("pump"):
            return True

        # Additional check: Query token metadata to see if it's a pump.fun token
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    token_address,
                    {"encoding": "jsonParsed"}
                ]
            }
            response = requests.post(self.rpc_url, json=payload, timeout=5)
            data = response.json()

            # Check if the program owner is pump.fun
            if data.get("result", {}).get("value", {}).get("owner") == PUMP_FUN_PROGRAM:
                return True

        except Exception:
            pass

        return False

    def _estimate_market_cap(self, sol_amount: float, token_amount: float,
                            token_address: str) -> float:
        """
        Estimate market cap based on initial liquidity pool ratio
        Uses SOL_PRICE_USD from config
        """
        if token_amount == 0:
            return 0

        # Get token total supply
        try:
            supply_info = self._get_token_supply(token_address)
            total_supply = supply_info.get("total_supply", 0)

            if total_supply == 0:
                return 0

            # Calculate price per token in SOL
            token_price_in_sol = sol_amount / token_amount

            # Calculate market cap
            market_cap_sol = token_price_in_sol * total_supply
            market_cap_usd = market_cap_sol * SOL_PRICE_USD

            return market_cap_usd

        except Exception as e:
            # Fallback: estimate based on pool ratio only
            # Assume circulating supply = token amount in pool * 10
            estimated_supply = token_amount * 10
            token_price_in_sol = sol_amount / token_amount
            market_cap_sol = token_price_in_sol * estimated_supply
            return market_cap_sol * SOL_PRICE_USD

    def _get_token_supply(self, token_address: str) -> Dict[str, float]:
        """Get token total supply from blockchain"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenSupply",
                "params": [token_address]
            }
            response = requests.post(self.rpc_url, json=payload, timeout=5)
            data = response.json()

            if "result" in data:
                ui_amount = data["result"]["value"]["uiAmount"]
                return {"total_supply": ui_amount}

        except Exception as e:
            print(f"Error fetching token supply: {e}")

        return {"total_supply": 0}

    def _check_token_security(self, token_address: str) -> Dict[str, bool]:
        """
        Check critical security parameters:
        - Mint authority (should be revoked/null)
        - Freeze authority (should be revoked/null)
        """
        result = {
            "mint_authority_revoked": False,
            "freeze_authority_revoked": False
        }

        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    token_address,
                    {"encoding": "jsonParsed"}
                ]
            }
            response = requests.post(self.rpc_url, json=payload, timeout=5)
            data = response.json()

            if "result" in data and data["result"]:
                parsed_data = data["result"]["value"]["data"]["parsed"]["info"]

                # Check mint authority
                mint_authority = parsed_data.get("mintAuthority")
                if mint_authority is None:
                    result["mint_authority_revoked"] = True

                # Check freeze authority
                freeze_authority = parsed_data.get("freezeAuthority")
                if freeze_authority is None:
                    result["freeze_authority_revoked"] = True

        except Exception as e:
            print(f"Error checking token security: {e}")

        return result

    def _check_holder_distribution(self, token_address: str) -> Optional[Dict[str, float]]:
        """
        Check holder distribution to detect potential rug pulls
        Returns top holder percentage
        """
        try:
            # Get largest token holders
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenLargestAccounts",
                "params": [token_address]
            }
            response = requests.post(self.rpc_url, json=payload, timeout=5)
            data = response.json()

            if "result" in data and data["result"]["value"]:
                accounts = data["result"]["value"]

                # Get total supply
                supply_info = self._get_token_supply(token_address)
                total_supply = supply_info.get("total_supply", 0)

                if total_supply > 0 and len(accounts) > 0:
                    # Calculate top holder percentage
                    top_holder_amount = accounts[0]["uiAmount"]
                    top_holder_pct = (top_holder_amount / total_supply) * 100

                    return {
                        "top_holder_percentage": top_holder_pct,
                        "total_holders": len(accounts)
                    }

        except Exception as e:
            print(f"Error checking holder distribution: {e}")

        return None


def quick_filter(token0_volume: float, token1_volume: float,
                 token0_address: str, token1_address: str) -> bool:
    """
    Quick pre-filter before full analysis (saves API calls)
    Returns True if token passes basic checks
    Uses configured thresholds from config.py
    """
    # Determine SOL volume
    if token0_address == WSOL_ADDRESS:
        sol_volume = token0_volume
        new_token = token1_address
    elif token1_address == WSOL_ADDRESS:
        sol_volume = token1_volume
        new_token = token0_address
    else:
        return False  # Not a SOL pair

    # Basic liquidity check using configured values
    if sol_volume < MIN_LIQUIDITY_SOL or sol_volume > MAX_LIQUIDITY_SOL:
        return False

    # Filter pump.fun tokens by address pattern (if enabled)
    if FILTER_PUMP_FUN_TOKENS and new_token.endswith("pump"):
        return False

    return True
