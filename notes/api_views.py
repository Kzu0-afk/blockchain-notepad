# notes/api_views.py

import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from blockfrost import BlockFrostApi, ApiError, ApiUrls
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
    BlockfrostAPIError,
    TransactionSubmitError,
)
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
        "wallet_address": "addr_test..." (Bech32) OR "00..." (Hex-encoded CBOR)
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
        
        # Convert Hex to Bech32 if necessary
        try:
            # Check if it's likely a hex string (no 'addr' prefix, even length)
            if not wallet_address.startswith('addr') and len(wallet_address) % 2 == 0:
                try:
                    # Try to parse as hex bytes
                    address_bytes = bytes.fromhex(wallet_address)
                    # Convert to PyCardano Address object
                    address_obj = Address.from_primitive(address_bytes)
                    # Encode to Bech32
                    wallet_address = address_obj.encode()
                except ValueError as e:
                    logger.warning(f"Hex conversion failed for {wallet_address}: {e}")
                    return JsonResponse({'error': 'Invalid wallet address format. Please try reconnecting your wallet.'}, status=400)
        except Exception as e:
             logger.warning(f"Failed to convert address format: {e}")
             return JsonResponse({'error': f'Address conversion error: {str(e)}'}, status=400)

        # Validate address format (basic check - Cardano addresses are typically 103 chars max)
        # Note: Bech32 addresses can be longer than 103 chars (e.g. enterprise addresses or extensive headers),
        # but for standard shelley addresses ~103 is typical. We'll relax this slightly or trust the previous step.
        if len(wallet_address) > 150: # Increased limit to be safe
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
            return JsonResponse({'error': 'Wallet not connected. Please connect your wallet first.'}, status=400)
        
        sender_address = request.user.profile.wallet_address
        
        # Get Blockfrost API key from settings
        blockfrost_project_id = settings.BLOCKFROST_PROJECT_ID
        if not blockfrost_project_id or blockfrost_project_id == '':
            return JsonResponse({'error': 'Blockfrost API key not configured'}, status=500)
        
        # Initialize Chain Context for Preview Testnet
        network = Network.TESTNET  # Preview Testnet uses TESTNET
        context = BlockFrostChainContext(
            project_id=blockfrost_project_id,
            network=network,
            base_url=ApiUrls.preview.value
        )
        
        # Parse addresses
        try:
            sender_addr = Address.from_primitive(sender_address)
            recipient_addr = Address.from_primitive(recipient_address)
            logger.info(f"Building transaction from {sender_address} to {recipient_address}")
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
            logger.info(f"Transaction built successfully for user {request.user.username}")
        except Exception as e:
            logger.error(f"Transaction build failed: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Failed to build transaction: {str(e)}'}, status=500)
        
        # Get transaction CBOR (unsigned) - returns bytes, need to convert to hex string
        # Fix for Lace wallet: explicitly send only the transaction body (CBOR Array / Type 4)
        # instead of the full transaction object (CBOR Map / Type 5)
        unsigned_tx_cbor_hex = transaction.transaction_body.to_cbor().hex()
        
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
        api = BlockFrostApi(
            project_id=blockfrost_project_id,
            base_url=ApiUrls.preview.value
        )

        # Submit transaction to Blockfrost
        transaction_record = None
        try:
            # Blockfrost expects the transaction in hex format
            # The signed_tx_cbor should already be in hex format from the frontend
            tx_hash = api.submit_transaction(signed_tx_cbor)

            # Create Transaction record for tracking
            # Note: recipient_address and amount_lovelace will be extracted from CBOR if needed
            # For now, we'll create a basic record and update it later if needed
            transaction_record = Transaction.objects.create(
                user=request.user,
                tx_hash=tx_hash,
                signed_tx_cbor=signed_tx_cbor,
                status='submitted',
                recipient_address='',  # Will be populated from transaction parsing if needed
                amount_lovelace=0,  # Will be populated from transaction parsing if needed
            )

        except ApiError as e:
            # Create failed transaction record for audit trail
            error_details = getattr(e, 'body', 'No additional details')
            status_code = getattr(e, 'status_code', None)
            logger.error(f"Blockfrost API error: user={request.user.username}, status={status_code}, error={str(e)}")

            Transaction.objects.create(
                user=request.user,
                signed_tx_cbor=signed_tx_cbor,
                status='failed',
                error_message=str(e),
                error_code=status_code,
                recipient_address='',
                amount_lovelace=0,
            )
            raise BlockfrostAPIError(
                f'Blockfrost API error: {str(e)}',
                status_code=status_code,
                api_response=error_details
            )
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

    except BlockfrostAPIError as e:
        return JsonResponse({
            'error': e.message,
            'error_code': e.error_code,
            'details': e.details
        }, status=400)
    except TransactionSubmitError as e:
        return JsonResponse({
            'error': e.message,
            'error_code': e.error_code,
            'details': e.details
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in submit_transaction: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@login_required
@require_http_methods(["GET"])
def transaction_history(request):
    """
    Retrieve a list of the user's blockchain transactions.
    Supports pagination and filtering by status.

    Query Parameters:
    - status: Filter by transaction status (pending, submitted, confirmed, failed)
    - page: Page number for pagination
    - page_size: Number of items per page (default: 10)
    - limit: Quick limit without full pagination
    """
    user_transactions = Transaction.objects.filter(user=request.user)

    # Filtering
    status_filter = request.GET.get('status')
    if status_filter and status_filter in [s[0] for s in Transaction.STATUS_CHOICES]:
        user_transactions = user_transactions.filter(status=status_filter)

    # Pagination
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    limit = request.GET.get('limit')  # For quick queries without full pagination

    if limit:
        try:
            limit = int(limit)
            user_transactions = user_transactions[:limit]
        except ValueError:
            return JsonResponse({'error': 'Invalid limit parameter'}, status=400)
    else:
        from django.core.paginator import Paginator
        paginator = Paginator(user_transactions, page_size)
        try:
            page_obj = paginator.page(page_number)
        except Exception:
            page_obj = paginator.page(1)
        user_transactions = page_obj.object_list

    # Serialize transactions
    transactions_data = []
    for tx in user_transactions:
        transactions_data.append({
            'id': tx.id,
            'tx_hash': tx.tx_hash,
            'recipient_address': tx.recipient_address,
            'amount_lovelace': tx.amount_lovelace,
            'amount_ada': tx.amount_lovelace / 1_000_000 if tx.amount_lovelace else 0,
            'status': tx.get_status_display(),
            'created_at': tx.created_at.isoformat(),
            'confirmed_at': tx.confirmed_at.isoformat() if tx.confirmed_at else None,
            'error_message': tx.error_message,
            'cardanoscan_link': f"https://preview.cardanoscan.io/transaction/{tx.tx_hash}" if tx.tx_hash else None
        })

    response_data = {
        'count': user_transactions.count(),
        'results': transactions_data
    }

    if not limit:
        response_data.update({
            'next': None,  # Simplified pagination
            'previous': None,
        })

    return JsonResponse(response_data)


@login_required
@require_http_methods(["GET"])
def wallet_dashboard(request):
    """
    Get comprehensive wallet dashboard data including balance and transaction statistics.
    """
    try:
        # Get wallet balance from Blockfrost
        ada_balance = 0
        balance_lovelace = 0

        if hasattr(request.user, 'profile') and request.user.profile.wallet_address:
            wallet_address = request.user.profile.wallet_address

            # Get Blockfrost API key from settings
            blockfrost_project_id = settings.BLOCKFROST_PROJECT_ID
            if blockfrost_project_id:
                api = BlockFrostApi(
                    project_id=blockfrost_project_id,
                    base_url=ApiUrls.preview.value
                )
                try:
                    utxos = api.address_utxos(wallet_address)
                    balance_lovelace = sum(int(utxo['amount'][0]['quantity']) for utxo in utxos if utxo['amount'])
                    ada_balance = balance_lovelace / 1_000_000
                except Exception as e:
                    logger.warning(f'Could not fetch balance for {wallet_address}: {str(e)}')

        # Get transaction statistics
        transactions = Transaction.objects.filter(user=request.user)
        total_transactions = transactions.count()
        pending_count = transactions.filter(status='pending').count()
        confirmed_count = transactions.filter(status='confirmed').count()
        failed_count = transactions.filter(status='failed').count()

        # Calculate total amounts
        confirmed_transactions = transactions.filter(status='confirmed')
        total_sent_lovelace = sum(tx.amount_lovelace for tx in confirmed_transactions if tx.amount_lovelace)
        total_sent_ada = total_sent_lovelace / 1_000_000

        # Get recent transactions (last 5)
        recent_transactions = []
        for tx in transactions.order_by('-created_at')[:5]:
            recent_transactions.append({
                'id': tx.id,
                'tx_hash': tx.tx_hash,
                'status': tx.get_status_display(),
                'amount_lovelace': tx.amount_lovelace,
                'amount_ada': tx.amount_lovelace / 1_000_000 if tx.amount_lovelace else 0,
                'created_at': tx.created_at.isoformat(),
                'cardanoscan_link': f"https://preview.cardanoscan.io/transaction/{tx.tx_hash}" if tx.tx_hash else None
            })

        dashboard_data = {
            'wallet_address': getattr(request.user.profile, 'wallet_address', None) if hasattr(request.user, 'profile') else None,
            'balance': {
                'ada': ada_balance,
                'lovelace': balance_lovelace
            },
            'statistics': {
                'total_transactions': total_transactions,
                'pending_transactions': pending_count,
                'confirmed_transactions': confirmed_count,
                'failed_transactions': failed_count,
                'total_sent_ada': total_sent_ada,
                'total_sent_lovelace': total_sent_lovelace
            },
            'recent_transactions': recent_transactions
        }

        return JsonResponse(dashboard_data)

    except Exception as e:
        logger.error(f"Dashboard error for user {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Failed to load dashboard: {str(e)}'}, status=500)


