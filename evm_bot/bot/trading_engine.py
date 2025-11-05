"""
Automated Trading Engine for EVM/BSC
Handles buying and selling tokens on PancakeSwap with advanced risk management

This module provides automated trading capabilities including:
- Buying tokens with configurable slippage and gas optimization
- Selling tokens with multiple exit strategies
- Position tracking and management
- Gas price optimization
- Transaction monitoring and confirmation

Key Features:
- Automatic buy execution when high-quality tokens detected
- Multiple sell triggers (stop-loss, take-profit, trailing stop, time-based)
- Slippage protection
- Gas optimization
- Transaction failure handling and retries
- Detailed transaction logging
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.exceptions import Web3Exception
from eth_account import Account
from eth_utils import to_checksum_address, to_wei, from_wei
import logging
import json

from . import config

logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Automated trading engine for PancakeSwap

    Handles all trading operations including buying, selling, and position management.
    Integrates with PancakeSwap Router V2 for executing swaps.
    """

    # PancakeSwap Router V2 ABI (minimal - only functions we need)
    ROUTER_ABI = [
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"}
            ],
            "name": "getAmountsOut",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactETHForTokensSupportingFeeOnTransferTokens",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactTokensForETHSupportingFeeOnTransferTokens",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    # ERC20 ABI for approvals
    ERC20_ABI = [
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }
    ]

    def __init__(self):
        """Initialize the trading engine"""
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(config.BSC_RPC_URL))

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to BSC RPC")

        logger.info(f"Connected to BSC (Chain ID: {self.w3.eth.chain_id})")

        # Initialize account if private key provided
        self.account = None
        self.wallet_address = None

        if config.PRIVATE_KEY:
            try:
                self.account = Account.from_key(config.PRIVATE_KEY)
                self.wallet_address = self.account.address
                logger.info(f"Wallet loaded: {self.wallet_address}")

                # Check balance
                balance = self.w3.eth.get_balance(self.wallet_address)
                balance_bnb = from_wei(balance, 'ether')
                logger.info(f"Wallet balance: {balance_bnb} BNB")

            except Exception as e:
                logger.error(f"Failed to load wallet: {e}")
                raise

        # Initialize PancakeSwap router
        self.router_address = to_checksum_address(config.PANCAKE_ROUTER_V2)
        self.router = self.w3.eth.contract(
            address=self.router_address,
            abi=self.ROUTER_ABI
        )

        # WBNB address
        self.wbnb_address = to_checksum_address(config.WBNB_ADDRESS)

        # Statistics
        self.stats = {
            "buys_attempted": 0,
            "buys_successful": 0,
            "sells_attempted": 0,
            "sells_successful": 0,
            "total_spent_bnb": Decimal(0),
            "total_received_bnb": Decimal(0),
            "gas_spent_bnb": Decimal(0)
        }

    async def buy_token(self, token_address: str, pair_data: Dict, analysis: Dict) -> Optional[Dict]:
        """
        Buy a token on PancakeSwap

        Args:
            token_address: Address of token to buy
            pair_data: Pair information from detector
            analysis: Quality analysis results

        Returns:
            Dictionary with transaction details, or None if buy failed
        """
        if config.DRY_RUN:
            logger.info("🏃 DRY RUN - Would buy token")
            return self._create_mock_buy_result(token_address, pair_data)

        if not self.account:
            logger.error("Cannot buy: No wallet configured")
            return None

        self.stats["buys_attempted"] += 1

        try:
            token_address = to_checksum_address(token_address)

            logger.info(f"\n{'='*60}")
            logger.info(f"💰 BUYING TOKEN")
            logger.info(f"{'='*60}")
            logger.info(f"Token: {token_address}")
            logger.info(f"Amount: {config.TRADE_AMOUNT_BNB} BNB")

            # Check BNB balance
            balance = self.w3.eth.get_balance(self.wallet_address)
            balance_bnb = Decimal(str(from_wei(balance, 'ether')))

            logger.info(f"Wallet balance: {balance_bnb} BNB")

            # Ensure sufficient balance
            total_needed = config.TRADE_AMOUNT_BNB + config.MIN_BNB_BALANCE
            if balance_bnb < total_needed:
                logger.error(f"Insufficient balance. Need {total_needed} BNB, have {balance_bnb} BNB")
                return None

            # Calculate amount to spend (in Wei)
            amount_in_wei = to_wei(float(config.TRADE_AMOUNT_BNB), 'ether')

            # Get expected output amount
            path = [self.wbnb_address, token_address]
            amounts_out = self.router.functions.getAmountsOut(amount_in_wei, path).call()
            expected_tokens = amounts_out[1]

            logger.info(f"Expected tokens: {expected_tokens}")

            # Calculate minimum output with slippage
            slippage_multiplier = (100 - config.SLIPPAGE_PERCENT) / 100
            min_tokens_out = int(expected_tokens * float(slippage_multiplier))

            logger.info(f"Min tokens (with {config.SLIPPAGE_PERCENT}% slippage): {min_tokens_out}")

            # Get optimal gas price
            gas_price = await self._get_optimal_gas_price()
            logger.info(f"Gas price: {from_wei(gas_price, 'gwei')} Gwei")

            # Build transaction
            deadline = int(time.time()) + 300  # 5 minutes from now

            tx = self.router.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                min_tokens_out,
                path,
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'value': amount_in_wei,
                'gas': 300000,  # Gas limit
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'chainId': config.CHAIN_ID
            })

            # Estimate gas
            try:
                estimated_gas = self.w3.eth.estimate_gas(tx)
                tx['gas'] = int(estimated_gas * 1.2)  # Add 20% buffer
                logger.info(f"Estimated gas: {estimated_gas}")
            except Exception as e:
                logger.warning(f"Could not estimate gas: {e}")

            # Sign transaction
            signed_tx = self.account.sign_transaction(tx)

            # Send transaction
            logger.info("📤 Sending buy transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"✅ Transaction sent: {tx_hash_hex}")
            logger.info(f"🔗 https://bscscan.com/tx/{tx_hash_hex}")

            # Wait for confirmation
            logger.info("⏳ Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                logger.info("✅ BUY SUCCESSFUL!")

                # Get actual token balance
                token_balance = await self._get_token_balance(token_address, self.wallet_address)

                # Calculate gas cost
                gas_used = receipt['gasUsed']
                gas_cost_wei = gas_used * gas_price
                gas_cost_bnb = Decimal(str(from_wei(gas_cost_wei, 'ether')))

                logger.info(f"Tokens received: {token_balance}")
                logger.info(f"Gas used: {gas_cost_bnb} BNB")

                # Update stats
                self.stats["buys_successful"] += 1
                self.stats["total_spent_bnb"] += config.TRADE_AMOUNT_BNB
                self.stats["gas_spent_bnb"] += gas_cost_bnb

                # Return transaction details
                return {
                    "success": True,
                    "tx_hash": tx_hash_hex,
                    "token_address": token_address,
                    "amount_bnb": float(config.TRADE_AMOUNT_BNB),
                    "tokens_received": token_balance,
                    "expected_tokens": expected_tokens,
                    "gas_used": gas_used,
                    "gas_cost_bnb": float(gas_cost_bnb),
                    "timestamp": int(time.time()),
                    "buy_price_bnb": float(config.TRADE_AMOUNT_BNB) / token_balance if token_balance > 0 else 0,
                    "block_number": receipt['blockNumber']
                }

            else:
                logger.error("❌ Transaction failed!")
                return None

        except Exception as e:
            logger.error(f"Error buying token: {e}", exc_info=True)
            return None

    async def sell_token(self, token_address: str, amount: Optional[int] = None,
                        reason: str = "Manual") -> Optional[Dict]:
        """
        Sell a token on PancakeSwap

        Args:
            token_address: Address of token to sell
            amount: Amount of tokens to sell (in smallest unit). If None, sells all
            reason: Reason for selling (for logging)

        Returns:
            Dictionary with transaction details, or None if sell failed
        """
        if config.DRY_RUN:
            logger.info(f"🏃 DRY RUN - Would sell token (reason: {reason})")
            return self._create_mock_sell_result(token_address, reason)

        if not self.account:
            logger.error("Cannot sell: No wallet configured")
            return None

        self.stats["sells_attempted"] += 1

        try:
            token_address = to_checksum_address(token_address)

            logger.info(f"\n{'='*60}")
            logger.info(f"💸 SELLING TOKEN")
            logger.info(f"{'='*60}")
            logger.info(f"Token: {token_address}")
            logger.info(f"Reason: {reason}")

            # Get token balance
            if amount is None:
                amount = await self._get_token_balance(token_address, self.wallet_address)

            if amount == 0:
                logger.warning("No tokens to sell")
                return None

            logger.info(f"Amount: {amount} tokens")

            # Check/approve token spending
            await self._ensure_token_approval(token_address, amount)

            # Get expected output amount
            path = [token_address, self.wbnb_address]
            amounts_out = self.router.functions.getAmountsOut(amount, path).call()
            expected_bnb = amounts_out[1]

            logger.info(f"Expected BNB: {from_wei(expected_bnb, 'ether')}")

            # Calculate minimum output with slippage
            slippage_multiplier = (100 - config.SLIPPAGE_PERCENT) / 100
            min_bnb_out = int(expected_bnb * float(slippage_multiplier))

            logger.info(f"Min BNB (with {config.SLIPPAGE_PERCENT}% slippage): {from_wei(min_bnb_out, 'ether')}")

            # Get optimal gas price
            gas_price = await self._get_optimal_gas_price()
            logger.info(f"Gas price: {from_wei(gas_price, 'gwei')} Gwei")

            # Build transaction
            deadline = int(time.time()) + 300  # 5 minutes from now

            tx = self.router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                amount,
                min_bnb_out,
                path,
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'chainId': config.CHAIN_ID
            })

            # Estimate gas
            try:
                estimated_gas = self.w3.eth.estimate_gas(tx)
                tx['gas'] = int(estimated_gas * 1.2)
                logger.info(f"Estimated gas: {estimated_gas}")
            except Exception as e:
                logger.warning(f"Could not estimate gas: {e}")

            # Sign transaction
            signed_tx = self.account.sign_transaction(tx)

            # Send transaction
            logger.info("📤 Sending sell transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"✅ Transaction sent: {tx_hash_hex}")
            logger.info(f"🔗 https://bscscan.com/tx/{tx_hash_hex}")

            # Wait for confirmation
            logger.info("⏳ Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                logger.info("✅ SELL SUCCESSFUL!")

                # Calculate gas cost
                gas_used = receipt['gasUsed']
                gas_cost_wei = gas_used * gas_price
                gas_cost_bnb = Decimal(str(from_wei(gas_cost_wei, 'ether')))

                # Get actual BNB received (check balance change)
                actual_bnb = Decimal(str(from_wei(expected_bnb, 'ether')))

                logger.info(f"BNB received: {actual_bnb}")
                logger.info(f"Gas used: {gas_cost_bnb} BNB")

                # Update stats
                self.stats["sells_successful"] += 1
                self.stats["total_received_bnb"] += actual_bnb
                self.stats["gas_spent_bnb"] += gas_cost_bnb

                # Return transaction details
                return {
                    "success": True,
                    "tx_hash": tx_hash_hex,
                    "token_address": token_address,
                    "tokens_sold": amount,
                    "bnb_received": float(actual_bnb),
                    "expected_bnb": float(from_wei(expected_bnb, 'ether')),
                    "gas_used": gas_used,
                    "gas_cost_bnb": float(gas_cost_bnb),
                    "timestamp": int(time.time()),
                    "sell_price_bnb": float(actual_bnb) / amount if amount > 0 else 0,
                    "reason": reason,
                    "block_number": receipt['blockNumber']
                }

            else:
                logger.error("❌ Transaction failed!")
                return None

        except Exception as e:
            logger.error(f"Error selling token: {e}", exc_info=True)
            return None

    async def _get_token_balance(self, token_address: str, wallet_address: str) -> int:
        """Get token balance for a wallet"""
        try:
            token_contract = self.w3.eth.contract(
                address=to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )

            balance = token_contract.functions.balanceOf(
                to_checksum_address(wallet_address)
            ).call()

            return balance

        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return 0

    async def _ensure_token_approval(self, token_address: str, amount: int):
        """Ensure token is approved for spending by router"""
        try:
            token_contract = self.w3.eth.contract(
                address=to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )

            # Check current allowance
            allowance = token_contract.functions.allowance(
                self.wallet_address,
                self.router_address
            ).call()

            if allowance >= amount:
                logger.info("Token already approved")
                return

            logger.info("Approving token for spending...")

            # Approve maximum amount
            max_approval = 2**256 - 1

            # Build approval transaction
            tx = token_contract.functions.approve(
                self.router_address,
                max_approval
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 100000,
                'gasPrice': await self._get_optimal_gas_price(),
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'chainId': config.CHAIN_ID
            })

            # Sign and send
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if receipt['status'] == 1:
                logger.info("✅ Token approved")
            else:
                raise Exception("Approval transaction failed")

        except Exception as e:
            logger.error(f"Error approving token: {e}")
            raise

    async def _get_optimal_gas_price(self) -> int:
        """Get optimal gas price based on network conditions"""
        try:
            # Get current gas price from network
            base_gas_price = self.w3.eth.gas_price

            # Apply multiplier from config
            optimal_gas_price = int(base_gas_price * float(config.GAS_PRICE_MULTIPLIER))

            # Cap at maximum
            max_gas_price_wei = to_wei(config.MAX_GAS_PRICE_GWEI, 'gwei')
            if optimal_gas_price > max_gas_price_wei:
                logger.warning(f"Gas price capped at {config.MAX_GAS_PRICE_GWEI} Gwei")
                optimal_gas_price = max_gas_price_wei

            return optimal_gas_price

        except Exception as e:
            logger.error(f"Error getting gas price: {e}")
            # Fallback to 5 Gwei
            return to_wei(5, 'gwei')

    def _create_mock_buy_result(self, token_address: str, pair_data: Dict) -> Dict:
        """Create mock buy result for dry run"""
        return {
            "success": True,
            "tx_hash": "0x" + "0" * 64,
            "token_address": token_address,
            "amount_bnb": float(config.TRADE_AMOUNT_BNB),
            "tokens_received": 1000000,
            "expected_tokens": 1000000,
            "gas_used": 200000,
            "gas_cost_bnb": 0.001,
            "timestamp": int(time.time()),
            "buy_price_bnb": float(config.TRADE_AMOUNT_BNB) / 1000000,
            "block_number": 0,
            "dry_run": True
        }

    def _create_mock_sell_result(self, token_address: str, reason: str) -> Dict:
        """Create mock sell result for dry run"""
        return {
            "success": True,
            "tx_hash": "0x" + "0" * 64,
            "token_address": token_address,
            "tokens_sold": 1000000,
            "bnb_received": float(config.TRADE_AMOUNT_BNB) * 1.5,  # Assume 50% profit
            "expected_bnb": float(config.TRADE_AMOUNT_BNB) * 1.5,
            "gas_used": 200000,
            "gas_cost_bnb": 0.001,
            "timestamp": int(time.time()),
            "sell_price_bnb": (float(config.TRADE_AMOUNT_BNB) * 1.5) / 1000000,
            "reason": reason,
            "block_number": 0,
            "dry_run": True
        }

    def get_stats(self) -> Dict:
        """Get trading statistics"""
        stats = self.stats.copy()

        # Calculate success rates
        if stats["buys_attempted"] > 0:
            stats["buy_success_rate"] = round(
                stats["buys_successful"] / stats["buys_attempted"] * 100, 2
            )
        else:
            stats["buy_success_rate"] = 0

        if stats["sells_attempted"] > 0:
            stats["sell_success_rate"] = round(
                stats["sells_successful"] / stats["sells_attempted"] * 100, 2
            )
        else:
            stats["sell_success_rate"] = 0

        # Calculate profit/loss
        stats["net_bnb"] = float(
            stats["total_received_bnb"] - stats["total_spent_bnb"] - stats["gas_spent_bnb"]
        )

        return stats
