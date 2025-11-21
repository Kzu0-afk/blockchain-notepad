# notes/api_views.py

import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.conf import settings
from blockfrost import BlockFrostApi, ApiError
from pycardano import (
    Network,
    TransactionBuilder,
    TransactionOutput,
    Value,
    Address,
    BlockFrostChainContext,
)
from .models import Profile, Transaction
from .exceptions import (
    WalletNotConnectedError,
    InsufficientFundsError,
    InvalidAddressError,
    TransactionBuildError,
    TransactionSubmitError,
    BlockfrostAPIError,
    TransactionNotFoundError,
)
from django.utils import timezone
import logging

# Configure structured logging
logger = logging.getLogger('blockchain')


@login_required
@require_http_methods(["POST"])
def save_wallet(request):
    """
    Save the user's wallet address to their profile.
    
    Expected JSON payload:
    {
        "wallet_address": "addr_test..."
    }
    
    Returns:
    {
        "success": true,
        "wallet_address": "addr_test..."
    }
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        wallet_address = data.get('wallet_address')
        
        # Validate input
        if not wallet_address:
            return JsonResponse({'error': 'wallet_address is required'}, status=400)
        
        # Validate address format (basic check - Cardano addresses are typically 103 chars max)
        if len(wallet_address) > 103:
            return JsonResponse({'error': 'Invalid wallet address format'}, status=400)
        
        # Get or create user profile
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Check if address is already in use by another user
        existing_profile = Profile.objects.filter(wallet_address=wallet_address).exclude(user=request.user).first()
        if existing_profile:
            return JsonResponse({'error': 'This wallet address is already connected to another account'}, status=400)
        
        # Save wallet address
        profile.wallet_address = wallet_address
        profile.save()
        
        return JsonResponse({
            'success': True,
            'wallet_address': profile.wallet_address
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def build_transaction(request):
    """
    Build an unsigned transaction for the Cardano Preview Testnet.
    
    Expected JSON payload:
    {
        "recipient_address": "addr_test...",
        "amount_lovelace": 1000000
    }
    
    Returns:
    {
        "unsigned_tx_cbor": "hex-encoded-cbor-string"
    }
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        recipient_address = data.get('recipient_address')
        amount_lovelace = int(data.get('amount_lovelace', 0))
        
        # Validate input
        if not recipient_address:
            return JsonResponse({'error': 'recipient_address is required'}, status=400)
        
        if amount_lovelace <= 0:
            return JsonResponse({'error': 'amount_lovelace must be greater than 0'}, status=400)
        
        # Check if user has a wallet address
        if not hasattr(request.user, 'profile') or not request.user.profile.wallet_address:
            logger.warning(f"Transaction build attempted without wallet: user={request.user.username}")
            raise WalletNotConnectedError()
        
        sender_address = request.user.profile.wallet_address
        
        # Get Blockfrost API key from settings
        blockfrost_project_id = settings.BLOCKFROST_PROJECT_ID
        if not blockfrost_project_id or blockfrost_project_id == '':
            return JsonResponse({'error': 'Blockfrost API key not configured'}, status=500)
        
        # Initialize Chain Context for Preview Testnet
        network = Network.TESTNET  # Preview Testnet uses TESTNET
        context = BlockFrostChainContext(blockfrost_project_id, network)
        
        # Parse addresses
        try:
            sender_addr = Address.from_primitive(sender_address)
            recipient_addr = Address.from_primitive(recipient_address)
        except Exception as e:
            return JsonResponse({'error': f'Invalid address format: {str(e)}'}, status=400)
        
        # Build transaction using TransactionBuilder
        # The builder will automatically:
        # 1. Fetch UTXOs from Blockfrost for the sender address
        # 2. Select inputs needed to cover the amount + fees
        # 3. Calculate fees
        # 4. Create change output back to sender
        try:
            builder = TransactionBuilder(context)
            
            # Tell the builder which address to use for inputs (sender)
            builder.add_input_address(sender_addr)
            
            # Add output to recipient
            builder.add_output(
                TransactionOutput(
                    address=recipient_addr,
                    amount=Value(coin=amount_lovelace)
                )
            )
            
            # Build transaction with change address
            # This will automatically:
            # - Fetch UTXOs for the input address(es)
            # - Select sufficient inputs
            # - Calculate fees
            # - Create change output back to sender
            transaction = builder.build(change_address=sender_addr)
        except Exception as e:
            return JsonResponse({'error': f'Failed to build transaction: {str(e)}'}, status=500)
        
        # Get transaction CBOR (unsigned) - returns hex string
        unsigned_tx_cbor_hex = transaction.to_cbor()
        
        return JsonResponse({
            'unsigned_tx_cbor': unsigned_tx_cbor_hex
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def submit_transaction(request):
    """
    Submit a signed transaction to the Cardano Preview Testnet.
    
    Expected JSON payload:
    {
        "signed_tx_cbor": "hex-encoded-cbor-string"
    }
    
    Returns:
    {
        "tx_hash": "transaction-hash"
    }
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        signed_tx_cbor = data.get('signed_tx_cbor')
        
        # Validate input
        if not signed_tx_cbor:
            return JsonResponse({'error': 'signed_tx_cbor is required'}, status=400)
        
        # Get Blockfrost API key from settings
        blockfrost_project_id = settings.BLOCKFROST_PROJECT_ID
        if not blockfrost_project_id or blockfrost_project_id == '':
            return JsonResponse({'error': 'Blockfrost API key not configured'}, status=500)
        
        # Initialize Blockfrost API
        api = BlockFrostApi(project_id=blockfrost_project_id)
        
        # Submit transaction to Blockfrost
        transaction_record = None
        try:
            # Blockfrost expects the transaction in hex format
            # The signed_tx_cbor should already be in hex format from the frontend
            tx_hash = api.submit_transaction(signed_tx_cbor)
            
            # Create Transaction record for tracking
            # Note: recipient_address and amount_lovelace will be extracted from CBOR if needed
            # For now, we'll create a basic record and update it later if needed
            logger.info(f"Transaction submitted successfully: user={request.user.username}, tx_hash={tx_hash}")
            transaction_record = Transaction.objects.create(
                user=request.user,
                tx_hash=tx_hash,
                signed_tx_cbor=signed_tx_cbor,
                status='submitted',
                submitted_at=timezone.now(),
                recipient_address='',  # Will be populated from transaction parsing if needed
                amount_lovelace=0,  # Will be populated from transaction parsing if needed
            )
            
        except ApiError as e:
            # Create failed transaction record for audit trail
            error_details = getattr(e, 'body', 'No additional details')
            Transaction.objects.create(
                user=request.user,
                signed_tx_cbor=signed_tx_cbor,
                status='failed',
                error_message=str(e),
                error_code=getattr(e, 'status_code', None),
                recipient_address='',
                amount_lovelace=0,
            )
            return JsonResponse({
                'error': f'Blockfrost API error: {str(e)}',
                'details': error_details
            }, status=400)
        except Exception as e:
            # Create failed transaction record for audit trail
            logger.error(f"Transaction submission failed: user={request.user.username}, error={str(e)}", exc_info=True)
            Transaction.objects.create(
                user=request.user,
                signed_tx_cbor=signed_tx_cbor,
                status='failed',
                error_message=str(e),
                recipient_address='',
                amount_lovelace=0,
            )
            raise TransactionSubmitError(f'Failed to submit transaction: {str(e)}')
        
        return JsonResponse({
            'tx_hash': tx_hash,
            'transaction_id': transaction_record.id if transaction_record else None
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def transaction_history(request):
    """
    Get transaction history for the authenticated user.
    
    Query Parameters:
    - page: Page number for pagination (default: 1)
    - page_size: Number of transactions per page (default: 10, max: 100)
    - status: Filter by status (pending, submitted, confirmed, failed)
    - limit: Limit number of results (alternative to pagination)
    
    Returns:
    {
        "transactions": [...],
        "total": 100,
        "page": 1,
        "page_size": 10,
        "total_pages": 10
    }
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 10)), 100)  # Max 100 per page
        status_filter = request.GET.get('status', None)
        limit = request.GET.get('limit', None)
        
        # Get user's transactions
        transactions = Transaction.objects.filter(user=request.user)
        
        # Apply status filter if provided
        if status_filter:
            transactions = transactions.filter(status=status_filter)
        
        # Order by most recent first
        transactions = transactions.order_by('-created_at')
        
        # Apply limit if specified (alternative to pagination)
        if limit:
            transactions = transactions[:int(limit)]
            return JsonResponse({
                'transactions': [
                    {
                        'id': tx.id,
                        'tx_hash': tx.tx_hash,
                        'recipient_address': tx.recipient_address,
                        'amount_lovelace': tx.amount_lovelace,
                        'amount_ada': tx.get_amount_ada(),
                        'status': tx.status,
                        'created_at': tx.created_at.isoformat() if tx.created_at else None,
                        'submitted_at': tx.submitted_at.isoformat() if tx.submitted_at else None,
                        'confirmed_at': tx.confirmed_at.isoformat() if tx.confirmed_at else None,
                        'error_message': tx.error_message,
                        'block_height': tx.block_height,
                        'cardanoscan_url': f'https://preview.cardanoscan.io/transaction/{tx.tx_hash}' if tx.tx_hash else None,
                    }
                    for tx in transactions
                ],
                'total': transactions.count(),
            })
        
        # Use pagination
        paginator = Paginator(transactions, page_size)
        page_obj = paginator.get_page(page)
        
        return JsonResponse({
            'transactions': [
                {
                    'id': tx.id,
                    'tx_hash': tx.tx_hash,
                    'recipient_address': tx.recipient_address,
                    'amount_lovelace': tx.amount_lovelace,
                    'amount_ada': tx.get_amount_ada(),
                    'status': tx.status,
                    'created_at': tx.created_at.isoformat() if tx.created_at else None,
                    'submitted_at': tx.submitted_at.isoformat() if tx.submitted_at else None,
                    'confirmed_at': tx.confirmed_at.isoformat() if tx.confirmed_at else None,
                    'error_message': tx.error_message,
                    'block_height': tx.block_height,
                    'cardanoscan_url': f'https://preview.cardanoscan.io/transaction/{tx.tx_hash}' if tx.tx_hash else None,
                }
                for tx in page_obj
            ],
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Invalid query parameter: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def wallet_dashboard(request):
    """
    Get comprehensive wallet dashboard data for the authenticated user.
    
    Returns:
    {
        "wallet_address": "addr_test...",
        "connection_status": "connected" | "not_connected",
        "ada_balance": 100.5,
        "balance_lovelace": 100500000,
        "transaction_stats": {
            "total_transactions": 10,
            "pending": 2,
            "confirmed": 7,
            "failed": 1,
            "total_sent_ada": 50.0,
            "total_sent_lovelace": 50000000
        },
        "recent_transactions": [...],
        "last_updated": "2025-11-22T10:00:00Z"
    }
    """
    try:
        # Check if user has connected wallet
        if not hasattr(request.user, 'profile') or not request.user.profile.wallet_address:
            return JsonResponse({
                'wallet_address': None,
                'connection_status': 'not_connected',
                'ada_balance': 0,
                'balance_lovelace': 0,
                'transaction_stats': {
                    'total_transactions': 0,
                    'pending': 0,
                    'confirmed': 0,
                    'failed': 0,
                    'total_sent_ada': 0,
                    'total_sent_lovelace': 0
                },
                'recent_transactions': [],
                'last_updated': timezone.now().isoformat()
            })
        
        wallet_address = request.user.profile.wallet_address
        
        # Get Blockfrost API key from settings
        blockfrost_project_id = settings.BLOCKFROST_PROJECT_ID
        if not blockfrost_project_id or blockfrost_project_id == '':
            return JsonResponse({'error': 'Blockfrost API key not configured'}, status=500)
        
        # Initialize Blockfrost API
        api = BlockFrostApi(project_id=blockfrost_project_id)
        
        # Fetch wallet balance from Blockfrost
        ada_balance = 0
        balance_lovelace = 0
        try:
            # Get address information from Blockfrost
            address_info = api.address(wallet_address)
            # Calculate total balance from UTXOs
            utxos = api.address_utxos(wallet_address)
            balance_lovelace = sum(int(utxo['amount'][0]['quantity']) for utxo in utxos if utxo['amount'])
            ada_balance = balance_lovelace / 1_000_000
        except ApiError as e:
            # If address not found or error, balance remains 0
            pass
        except Exception as e:
            # Log error but continue with 0 balance
            pass
        
        # Get transaction statistics
        transactions = Transaction.objects.filter(user=request.user)
        total_transactions = transactions.count()
        pending_count = transactions.filter(status='pending').count()
        confirmed_count = transactions.filter(status='confirmed').count()
        failed_count = transactions.filter(status='failed').count()
        
        # Calculate total sent amount (only confirmed transactions)
        confirmed_transactions = transactions.filter(status='confirmed')
        total_sent_lovelace = sum(tx.amount_lovelace for tx in confirmed_transactions if tx.amount_lovelace)
        total_sent_ada = total_sent_lovelace / 1_000_000
        
        # Get recent transactions (last 5)
        recent_transactions = transactions.order_by('-created_at')[:5]
        recent_transactions_data = [
            {
                'id': tx.id,
                'tx_hash': tx.tx_hash,
                'recipient_address': tx.recipient_address,
                'amount_lovelace': tx.amount_lovelace,
                'amount_ada': tx.get_amount_ada(),
                'status': tx.status,
                'created_at': tx.created_at.isoformat() if tx.created_at else None,
                'cardanoscan_url': f'https://preview.cardanoscan.io/transaction/{tx.tx_hash}' if tx.tx_hash else None,
            }
            for tx in recent_transactions
        ]
        
        return JsonResponse({
            'wallet_address': wallet_address,
            'connection_status': 'connected',
            'ada_balance': round(ada_balance, 6),
            'balance_lovelace': balance_lovelace,
            'transaction_stats': {
                'total_transactions': total_transactions,
                'pending': pending_count,
                'confirmed': confirmed_count,
                'failed': failed_count,
                'total_sent_ada': round(total_sent_ada, 6),
                'total_sent_lovelace': total_sent_lovelace
            },
            'recent_transactions': recent_transactions_data,
            'last_updated': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

