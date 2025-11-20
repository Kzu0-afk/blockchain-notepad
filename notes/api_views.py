# notes/api_views.py

import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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
        try:
            # Blockfrost expects the transaction in hex format
            # The signed_tx_cbor should already be in hex format from the frontend
            tx_hash = api.submit_transaction(signed_tx_cbor)
        except ApiError as e:
            return JsonResponse({
                'error': f'Blockfrost API error: {str(e)}',
                'details': getattr(e, 'body', 'No additional details')
            }, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to submit transaction: {str(e)}'}, status=500)
        
        return JsonResponse({
            'tx_hash': tx_hash
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

