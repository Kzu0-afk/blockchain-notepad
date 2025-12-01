# notes/api_views.py

import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from blockfrost import BlockFrostApi, ApiUrls
from .models import Profile, Transaction
import logging

logger = logging.getLogger('blockchain')


@login_required
@require_http_methods(["POST"])
def save_wallet(request):
    """
    Save the user's wallet address to their profile.
    
    Expected JSON payload:
    {
        "wallet_address": "addr_test..." (Bech32 format from CIP-30 wallet)
    }
    
    Returns:
    {
        "success": true,
        "wallet_address": "addr_test..."
    }
    """
    try:
        data = json.loads(request.body)
        wallet_address = data.get('wallet_address')
        
        if not wallet_address:
            return JsonResponse({'error': 'wallet_address is required'}, status=400)
        
        # Validate Bech32 format (must start with 'addr')
        if not wallet_address.startswith('addr'):
            return JsonResponse({'error': 'Invalid wallet address format. Expected Bech32 address (starts with addr).'}, status=400)
        
        # Basic length validation
        if len(wallet_address) > 150:
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
        
        logger.info(f"Wallet address saved for user {request.user.username}: {wallet_address}")
        
        return JsonResponse({
            'success': True,
            'wallet_address': profile.wallet_address
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        logger.error(f"Error saving wallet address: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def log_transaction(request):
    """
    Log transaction metadata after client-side submission via Blaze SDK.
    
    Stores only metadata (tx_hash, recipient, amount).
    The transaction hash is sufficient to query all details from the blockchain.
    
    Expected JSON payload:
    {
        "tx_hash": "transaction-hash",           # From Blaze SDK after submission
        "recipient_address": "addr_test...",      # Where ADA was sent
        "amount_lovelace": 1000000                # Amount sent
    }
    
    Returns:
    {
        "success": true,
        "transaction_id": 123
    }
    """
    try:
        data = json.loads(request.body)
        tx_hash = data.get('tx_hash')
        recipient_address = data.get('recipient_address', '')
        amount_lovelace = int(data.get('amount_lovelace', 0))
        
        if not tx_hash:
            return JsonResponse({'error': 'tx_hash is required'}, status=400)
        
        # Create transaction record
        transaction_record = Transaction.objects.create(
            user=request.user,
            tx_hash=tx_hash,
            recipient_address=recipient_address,
            amount_lovelace=amount_lovelace,
            status='submitted',  # Will be updated by background job
        )
        
        logger.info(f"Transaction logged: tx_hash={tx_hash}, user={request.user.username}")
        
        return JsonResponse({
            'success': True,
            'transaction_id': transaction_record.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        logger.error(f"Failed to record transaction: {str(e)}", exc_info=True)
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


