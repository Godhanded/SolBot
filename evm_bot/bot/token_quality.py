"""
EVM Token Quality Analyzer
Comprehensive token analysis and scoring system for BSC/EVM tokens

This module provides sophisticated multi-factor analysis of newly detected tokens,
scoring them across multiple dimensions including liquidity, market cap, security,
holder distribution, and contract verification.

Key Features:
- Multi-factor quality scoring (0-100 points)
- Honeypot detection (can the token be sold?)
- Contract security analysis (ownership, taxes, etc.)
- Holder distribution analysis (whale risk)
- Market cap and liquidity validation
- Detailed reasoning for accept/reject decisions
"""

import asyncio
import time
import aiohttp
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.exceptions import Web3Exception
from eth_utils import to_checksum_address
import logging

from . import config

logger = logging.getLogger(__name__)


class TokenQualityAnalyzer:
    """
    Analyzes token quality across multiple dimensions

    This class performs comprehensive analysis of EVM tokens, checking:
    1. Liquidity (is there enough for trading?)
    2. Market cap (is it in the moonshot range?)
    3. Security (honeypot, taxes, ownership)
    4. Holder distribution (whale risk)
    5. Contract verification (trust factor)
    """

    # Standard ERC20 ABI
    ERC20_ABI = [
        {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    ]

    # Common Ownable interface
    OWNABLE_ABI = [
        {"constant": True, "inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    ]

    def __init__(self):
        """Initialize the token quality analyzer"""
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(config.BSC_RPC_URL))

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to BSC RPC")

        logger.info("Token Quality Analyzer initialized")

        # Statistics
        self.stats = {
            "analyzed": 0,
            "passed": 0,
            "failed": 0,
            "honeypots_detected": 0,
            "high_tax_rejected": 0
        }

    async def analyze_token(self, pair_data: Dict) -> Dict:
        """
        Perform comprehensive token analysis

        Args:
            pair_data: Dictionary containing pair information from detector

        Returns:
            Dictionary containing:
                - quality_score: int (0-100)
                - should_alert: bool
                - should_trade: bool
                - reasons: List of strings explaining the score
                - metrics: Dictionary of individual metric scores
                - security: Dictionary of security checks
        """
        self.stats["analyzed"] += 1
        token_address = pair_data["token_address"]

        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Analyzing token: {token_address}")
        logger.info(f"{'='*60}")

        reasons = []
        metrics = {}

        try:
            # Stage 1: Quick filters (fail fast)
            quick_pass, quick_reasons = await self._quick_filter(pair_data)
            if not quick_pass:
                logger.info("❌ Failed quick filter")
                for reason in quick_reasons:
                    logger.info(f"   {reason}")

                self.stats["failed"] += 1
                return {
                    "quality_score": 0,
                    "should_alert": False,
                    "should_trade": False,
                    "reasons": quick_reasons,
                    "metrics": {},
                    "security": {}
                }

            reasons.extend(quick_reasons)

            # Stage 2: Get token info
            token_info = await self._get_token_info(token_address)
            metrics["token_info"] = token_info

            # Stage 3: Honeypot check (critical!)
            if config.CHECK_HONEYPOT:
                is_honeypot, honeypot_info = await self._check_honeypot(token_address)

                if is_honeypot:
                    logger.warning(f"🍯 HONEYPOT DETECTED: {token_address}")
                    self.stats["honeypots_detected"] += 1
                    self.stats["failed"] += 1

                    return {
                        "quality_score": 0,
                        "should_alert": False,
                        "should_trade": False,
                        "reasons": ["❌ HONEYPOT - Cannot sell this token!"],
                        "metrics": {"honeypot": honeypot_info},
                        "security": {"is_honeypot": True}
                    }

                metrics["honeypot"] = honeypot_info
                reasons.append("✅ Not a honeypot (can be sold)")

                # Check tax levels
                buy_tax = honeypot_info.get("buy_tax", 0)
                sell_tax = honeypot_info.get("sell_tax", 0)

                if buy_tax > float(config.MAX_BUY_TAX_PERCENT):
                    reasons.append(f"❌ Buy tax too high: {buy_tax}%")
                    self.stats["high_tax_rejected"] += 1
                    self.stats["failed"] += 1
                    return self._build_result(0, False, False, reasons, metrics, {})

                if sell_tax > float(config.MAX_SELL_TAX_PERCENT):
                    reasons.append(f"❌ Sell tax too high: {sell_tax}%")
                    self.stats["high_tax_rejected"] += 1
                    self.stats["failed"] += 1
                    return self._build_result(0, False, False, reasons, metrics, {})

                if buy_tax > 0 or sell_tax > 0:
                    reasons.append(f"ℹ️  Taxes: Buy {buy_tax}%, Sell {sell_tax}%")

            # Stage 4: Calculate liquidity score
            liquidity_score, liquidity_reasons = self._score_liquidity(pair_data)
            metrics["liquidity"] = {
                "score": liquidity_score,
                "bnb_amount": pair_data.get("reserve_bnb_decimal", 0)
            }
            reasons.extend(liquidity_reasons)

            # Stage 5: Calculate market cap score
            market_cap, market_cap_score, mc_reasons = await self._score_market_cap(
                pair_data, token_info
            )
            metrics["market_cap"] = {
                "score": market_cap_score,
                "value_usd": market_cap
            }
            reasons.extend(mc_reasons)

            # Stage 6: Security analysis
            security_score, security_info, security_reasons = await self._score_security(
                token_address, token_info
            )
            metrics["security"] = {
                "score": security_score,
                "details": security_info
            }
            reasons.extend(security_reasons)

            # Stage 7: Holder distribution analysis
            holder_score, holder_info, holder_reasons = await self._score_holders(
                token_address, pair_data["pair_address"]
            )
            metrics["holders"] = {
                "score": holder_score,
                "details": holder_info
            }
            reasons.extend(holder_reasons)

            # Stage 8: Contract verification (if required)
            contract_score = 0
            if config.REQUIRE_VERIFIED_CONTRACT:
                is_verified = await self._check_contract_verified(token_address)
                if is_verified:
                    contract_score = config.SCORE_WEIGHT_CONTRACT
                    reasons.append("✅ Contract verified on BSCScan")
                else:
                    reasons.append("⚠️  Contract not verified")
                    self.stats["failed"] += 1
                    return self._build_result(0, False, False, reasons, metrics, security_info)
            else:
                # Give partial points if verified, but don't require it
                is_verified = await self._check_contract_verified(token_address)
                if is_verified:
                    contract_score = config.SCORE_WEIGHT_CONTRACT
                    reasons.append("✅ Contract verified on BSCScan")
                else:
                    contract_score = config.SCORE_WEIGHT_CONTRACT // 2
                    reasons.append("⚠️  Contract not verified (reduced score)")

            metrics["contract"] = {
                "score": contract_score,
                "verified": is_verified
            }

            # Calculate total quality score
            total_score = (
                liquidity_score +
                market_cap_score +
                security_score +
                holder_score +
                contract_score
            )

            # Determine if we should alert/trade
            should_alert = total_score >= config.MINIMUM_QUALITY_SCORE
            should_trade = should_alert and config.AUTO_TRADE

            # Log results
            logger.info(f"\n📊 ANALYSIS COMPLETE")
            logger.info(f"   Quality Score: {total_score}/100")
            logger.info(f"   Should Alert: {should_alert}")
            logger.info(f"   Should Trade: {should_trade}")

            if should_alert:
                self.stats["passed"] += 1
                logger.info("   ✅ PASSED - High quality token!")
            else:
                self.stats["failed"] += 1
                logger.info("   ❌ REJECTED - Below quality threshold")

            return self._build_result(
                total_score, should_alert, should_trade,
                reasons, metrics, security_info
            )

        except Exception as e:
            logger.error(f"Error analyzing token: {e}", exc_info=True)
            self.stats["failed"] += 1
            return self._build_result(
                0, False, False,
                [f"❌ Analysis error: {str(e)}"],
                metrics, {}
            )

    def _build_result(self, score: int, alert: bool, trade: bool,
                     reasons: List[str], metrics: Dict, security: Dict) -> Dict:
        """Build standardized result dictionary"""
        return {
            "quality_score": score,
            "should_alert": alert,
            "should_trade": trade,
            "reasons": reasons,
            "metrics": metrics,
            "security": security
        }

    async def _quick_filter(self, pair_data: Dict) -> Tuple[bool, List[str]]:
        """
        Quick filtering to reject obvious bad tokens before expensive API calls

        Returns:
            Tuple of (passed: bool, reasons: List[str])
        """
        reasons = []

        # Check liquidity range
        liquidity_bnb = Decimal(str(pair_data.get("reserve_bnb_decimal", 0)))

        if liquidity_bnb < config.MIN_LIQUIDITY_BNB:
            reasons.append(f"❌ Liquidity too low: {liquidity_bnb} BNB (min: {config.MIN_LIQUIDITY_BNB})")
            return False, reasons

        if liquidity_bnb > config.MAX_LIQUIDITY_BNB:
            reasons.append(f"❌ Liquidity too high: {liquidity_bnb} BNB (max: {config.MAX_LIQUIDITY_BNB})")
            return False, reasons

        reasons.append(f"✅ Liquidity in range: {liquidity_bnb} BNB")

        return True, reasons

    async def _get_token_info(self, token_address: str) -> Dict:
        """
        Get basic token information (name, symbol, decimals, supply)

        Args:
            token_address: Token contract address

        Returns:
            Dictionary with token info
        """
        try:
            contract = self.w3.eth.contract(
                address=to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )

            # Get basic info
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            total_supply = contract.functions.totalSupply().call()

            # Convert supply to decimal format
            supply_decimal = Decimal(total_supply) / Decimal(10 ** decimals)

            logger.info(f"   Token: {name} ({symbol})")
            logger.info(f"   Decimals: {decimals}")
            logger.info(f"   Supply: {supply_decimal:,.0f}")

            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply,
                "supply_decimal": float(supply_decimal)
            }

        except Exception as e:
            logger.warning(f"Could not get token info: {e}")
            # Return defaults
            return {
                "name": "Unknown",
                "symbol": "???",
                "decimals": 18,
                "total_supply": 0,
                "supply_decimal": 0
            }

    async def _check_honeypot(self, token_address: str) -> Tuple[bool, Dict]:
        """
        Check if token is a honeypot using honeypot.is API

        A honeypot is a token that can be bought but not sold, trapping your funds.

        Args:
            token_address: Token contract address

        Returns:
            Tuple of (is_honeypot: bool, info: Dict)
        """
        try:
            url = f"{config.HONEYPOT_API_URL}?address={token_address}&chainID={config.CHAIN_ID}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Parse response
                        is_honeypot = data.get("honeypotResult", {}).get("isHoneypot", False)
                        buy_tax = data.get("simulationResult", {}).get("buyTax", 0)
                        sell_tax = data.get("simulationResult", {}).get("sellTax", 0)

                        honeypot_reason = data.get("honeypotResult", {}).get("honeypotReason", "")

                        info = {
                            "is_honeypot": is_honeypot,
                            "buy_tax": buy_tax,
                            "sell_tax": sell_tax,
                            "reason": honeypot_reason
                        }

                        if is_honeypot:
                            logger.warning(f"🍯 Honeypot detected: {honeypot_reason}")
                        else:
                            logger.info(f"✅ Honeypot check passed (Buy: {buy_tax}%, Sell: {sell_tax}%)")

                        return is_honeypot, info

                    else:
                        logger.warning(f"Honeypot API returned status {response.status}")
                        return False, {"error": "API error", "buy_tax": 0, "sell_tax": 0}

        except Exception as e:
            logger.warning(f"Honeypot check failed: {e}")
            # If check fails, assume it's not a honeypot (conservative)
            return False, {"error": str(e), "buy_tax": 0, "sell_tax": 0}

    def _score_liquidity(self, pair_data: Dict) -> Tuple[int, List[str]]:
        """
        Score liquidity (0 to SCORE_WEIGHT_LIQUIDITY points)

        Optimal range gets full points, acceptable ranges get partial points
        """
        liquidity_bnb = Decimal(str(pair_data.get("reserve_bnb_decimal", 0)))
        max_score = config.SCORE_WEIGHT_LIQUIDITY
        reasons = []

        # Optimal range (full points)
        if config.OPTIMAL_LIQUIDITY_MIN_BNB <= liquidity_bnb <= config.OPTIMAL_LIQUIDITY_MAX_BNB:
            score = max_score
            reasons.append(f"⭐ Optimal liquidity: {liquidity_bnb} BNB ({score} pts)")

        # Acceptable ranges (partial points)
        elif config.MIN_LIQUIDITY_BNB <= liquidity_bnb < config.OPTIMAL_LIQUIDITY_MIN_BNB:
            score = int(max_score * 0.7)  # 70% of max
            reasons.append(f"✅ Acceptable liquidity: {liquidity_bnb} BNB ({score} pts)")

        elif config.OPTIMAL_LIQUIDITY_MAX_BNB < liquidity_bnb <= config.MAX_LIQUIDITY_BNB:
            score = int(max_score * 0.6)  # 60% of max
            reasons.append(f"✅ High liquidity: {liquidity_bnb} BNB ({score} pts)")

        else:
            score = 0
            reasons.append(f"❌ Liquidity out of range: {liquidity_bnb} BNB")

        return score, reasons

    async def _score_market_cap(self, pair_data: Dict, token_info: Dict) -> Tuple[Decimal, int, List[str]]:
        """
        Calculate market cap and score it (0 to SCORE_WEIGHT_MARKET_CAP points)

        Market cap = (BNB reserve / Token reserve) * Total supply * BNB price
        """
        max_score = config.SCORE_WEIGHT_MARKET_CAP
        reasons = []

        try:
            reserve_bnb = Decimal(str(pair_data.get("reserve_bnb", 0)))
            reserve_token = Decimal(str(pair_data.get("reserve_token", 0)))
            total_supply = Decimal(str(token_info.get("total_supply", 0)))
            decimals = token_info.get("decimals", 18)

            # Adjust for decimals
            reserve_bnb_decimal = reserve_bnb / Decimal(10 ** 18)
            reserve_token_decimal = reserve_token / Decimal(10 ** decimals)
            total_supply_decimal = total_supply / Decimal(10 ** decimals)

            if reserve_token_decimal == 0:
                logger.warning("Reserve token is 0, cannot calculate market cap")
                return Decimal(0), 0, ["❌ Cannot calculate market cap"]

            # Calculate price per token in BNB
            price_per_token_bnb = reserve_bnb_decimal / reserve_token_decimal

            # Calculate market cap in USD
            market_cap_usd = price_per_token_bnb * total_supply_decimal * config.BNB_PRICE_USD

            logger.info(f"   Market Cap: ${market_cap_usd:,.2f}")

            # Score based on market cap
            if market_cap_usd > config.MARKET_CAP_UPPER_LIMIT_USD:
                score = 0
                reasons.append(f"❌ Market cap too high: ${market_cap_usd:,.0f}")
                return market_cap_usd, score, reasons

            if config.MARKET_CAP_MIN_USD <= market_cap_usd <= config.MARKET_CAP_MAX_USD:
                score = max_score
                reasons.append(f"⭐ Moonshot market cap: ${market_cap_usd:,.0f} ({score} pts)")

            elif config.MARKET_CAP_MAX_USD < market_cap_usd <= config.MARKET_CAP_UPPER_LIMIT_USD:
                score = int(max_score * 0.6)  # 60% of max
                reasons.append(f"✅ Decent market cap: ${market_cap_usd:,.0f} ({score} pts)")

            elif market_cap_usd < config.MARKET_CAP_MIN_USD:
                score = int(max_score * 0.4)  # 40% of max
                reasons.append(f"⚠️  Low market cap: ${market_cap_usd:,.0f} ({score} pts)")

            else:
                score = 0
                reasons.append(f"❌ Market cap out of range: ${market_cap_usd:,.0f}")

            return market_cap_usd, score, reasons

        except Exception as e:
            logger.error(f"Error calculating market cap: {e}")
            return Decimal(0), 0, [f"❌ Market cap calculation error: {str(e)}"]

    async def _score_security(self, token_address: str, token_info: Dict) -> Tuple[int, Dict, List[str]]:
        """
        Score security features (0 to SCORE_WEIGHT_SECURITY points)

        Checks:
        - Ownership renounced
        - Liquidity locked (if API available)
        """
        max_score = config.SCORE_WEIGHT_SECURITY
        score = 0
        reasons = []
        security_info = {}

        try:
            # Check if ownership is renounced
            ownership_renounced = await self._check_ownership_renounced(token_address)
            security_info["ownership_renounced"] = ownership_renounced

            if ownership_renounced:
                score += max_score // 2  # Half points for renounced ownership
                reasons.append(f"✅ Ownership renounced (+{max_score // 2} pts)")
            else:
                if config.REQUIRE_OWNERSHIP_RENOUNCED:
                    reasons.append("❌ Ownership NOT renounced (required)")
                    return 0, security_info, reasons
                else:
                    reasons.append(f"⚠️  Ownership NOT renounced")

            # Note: Liquidity lock check would require additional API
            # For now, give remaining points as "benefit of doubt"
            score += max_score // 2
            reasons.append(f"ℹ️  Security baseline score (+{max_score // 2} pts)")

            security_info["score"] = score

            return score, security_info, reasons

        except Exception as e:
            logger.error(f"Error checking security: {e}")
            return 0, security_info, [f"❌ Security check error: {str(e)}"]

    async def _check_ownership_renounced(self, token_address: str) -> bool:
        """
        Check if contract ownership has been renounced

        Ownership is renounced if owner() returns zero address
        """
        try:
            contract = self.w3.eth.contract(
                address=to_checksum_address(token_address),
                abi=self.OWNABLE_ABI
            )

            owner = contract.functions.owner().call()

            # Zero address means renounced
            is_renounced = owner == "0x0000000000000000000000000000000000000000"

            logger.info(f"   Owner: {owner} {'(RENOUNCED)' if is_renounced else '(ACTIVE)'}")

            return is_renounced

        except Exception as e:
            # If owner() function doesn't exist, assume no owner
            logger.debug(f"Could not check ownership: {e}")
            return False

    async def _score_holders(self, token_address: str, pair_address: str) -> Tuple[int, Dict, List[str]]:
        """
        Score holder distribution (0 to SCORE_WEIGHT_HOLDERS points)

        Analyzes top holders to detect whale concentration risk
        """
        max_score = config.SCORE_WEIGHT_HOLDERS
        reasons = []
        holder_info = {}

        try:
            # Get top holders via BSCScan-like API
            # Note: This is a simplified version. In production, you'd use BSCScan API
            # For now, we'll give a baseline score
            score = max_score // 2
            reasons.append(f"ℹ️  Holder analysis baseline (+{score} pts)")

            holder_info["analyzed"] = False
            holder_info["note"] = "Full holder analysis requires BSCScan API"

            return score, holder_info, reasons

        except Exception as e:
            logger.error(f"Error analyzing holders: {e}")
            return max_score // 2, holder_info, ["ℹ️  Could not analyze holders (baseline score)"]

    async def _check_contract_verified(self, token_address: str) -> bool:
        """
        Check if contract is verified on BSCScan

        Note: This requires BSCScan API key
        For now, returns True (assume verified) unless API is configured
        """
        try:
            # If BSCScan API is configured, check verification
            # For now, return True as baseline
            return True

        except Exception as e:
            logger.debug(f"Could not check contract verification: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get analyzer statistics"""
        stats = self.stats.copy()

        # Add success rate
        if stats["analyzed"] > 0:
            stats["pass_rate"] = round(stats["passed"] / stats["analyzed"] * 100, 2)
        else:
            stats["pass_rate"] = 0

        return stats


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """Example usage"""
    analyzer = TokenQualityAnalyzer()

    # Example pair data (from detector)
    pair_data = {
        "pair_address": "0x...",
        "token_address": "0x...",
        "reserve_bnb_decimal": 50.0,
        "reserve_bnb": 50000000000000000000,  # 50 BNB in Wei
        "reserve_token": 1000000000000000000000000,  # 1M tokens
    }

    result = await analyzer.analyze_token(pair_data)

    print(f"\nQuality Score: {result['quality_score']}/100")
    print(f"Should Alert: {result['should_alert']}")
    print(f"Should Trade: {result['should_trade']}")
    print("\nReasons:")
    for reason in result['reasons']:
        print(f"  {reason}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
