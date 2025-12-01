# notes/exceptions.py

"""
Custom exception classes for blockchain operations.
Provides structured error handling with context-rich information.
"""


class BlockchainAPIError(Exception):
    """Base exception for all blockchain-related errors"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class WalletNotConnectedError(BlockchainAPIError):
    """Raised when user attempts blockchain operation without connected wallet"""
    def __init__(self, message="Wallet not connected. Please connect your wallet first."):
        super().__init__(message, error_code="WALLET_NOT_CONNECTED")


class InsufficientFundsError(BlockchainAPIError):
    """Raised when user doesn't have enough funds for transaction"""
    def __init__(self, available, required, message=None):
        if message is None:
            message = f"Insufficient funds. Available: {available} lovelace, Required: {required} lovelace"
        super().__init__(message, error_code="INSUFFICIENT_FUNDS", details={
            'available': available,
            'required': required
        })


class InvalidAddressError(BlockchainAPIError):
    """Raised when an invalid Cardano address is provided"""
    def __init__(self, address, message=None):
        if message is None:
            message = f"Invalid Cardano address format: {address}"
        super().__init__(message, error_code="INVALID_ADDRESS", details={'address': address})


class BlockfrostAPIError(BlockchainAPIError):
    """Raised when Blockfrost API returns an error"""
    def __init__(self, message, status_code=None, api_response=None):
        super().__init__(message, error_code="BLOCKFROST_API_ERROR", details={
            'status_code': status_code,
            'api_response': api_response
        })


class TransactionNotFoundError(BlockchainAPIError):
    """Raised when a requested transaction is not found"""
    def __init__(self, tx_hash=None, transaction_id=None):
        message = "Transaction not found"
        if tx_hash:
            message = f"Transaction with hash {tx_hash} not found"
        elif transaction_id:
            message = f"Transaction with ID {transaction_id} not found"
        super().__init__(message, error_code="TRANSACTION_NOT_FOUND", details={
            'tx_hash': tx_hash,
            'transaction_id': transaction_id
        })

