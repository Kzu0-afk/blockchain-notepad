"""
Background tasks for blockchain operations using Django management commands.
These functions can be called from management commands or scheduled via cron.
"""

import logging
from django.conf import settings
from blockfrost import BlockFrostApi, ApiError
from .models import Transaction
from .utils import safe_blockfrost_call

logger = logging.getLogger('blockchain')


def update_transaction_statuses(limit=100):
    """
    Update transaction statuses by polling Blockfrost.
    This function should be run periodically (e.g., every 5-10 minutes).

    Args:
        limit: Maximum number of transactions to process

    Returns:
        dict: Summary of updates
    """
    logger.info("Starting transaction status update task")

    # Get pending and submitted transactions that need status updates
    transactions = Transaction.objects.filter(
        status__in=['pending', 'submitted']
    ).order_by('created_at')[:limit]

    if not transactions:
        logger.info("No transactions need status updates")
        return {'updated': 0, 'errors': 0, 'processed': 0}

    # Get Blockfrost API key
    blockfrost_project_id = settings.BLOCKFROST_PROJECT_ID
    if not blockfrost_project_id or blockfrost_project_id == '':
        logger.error("Blockfrost API key not configured")
        return {'updated': 0, 'errors': 1, 'processed': 0}

    api = BlockFrostApi(project_id=blockfrost_project_id)

    updated_count = 0
    error_count = 0
    processed_count = 0

    logger.info(f"Processing {transactions.count()} transactions")

    for transaction in transactions:
        processed_count += 1
        try:
            # Check transaction status via Blockfrost
            status, details = check_transaction_status(api, transaction.tx_hash)

            if status != transaction.status:
                # Update transaction status
                transaction.status = status
                transaction.updated_at = timezone.now()

                # Add additional details based on status
                if status == 'confirmed' and details:
                    transaction.confirmed_at = timezone.now()
                    transaction.block_height = details.get('block_height')
                    transaction.slot = details.get('slot')

                transaction.save()
                updated_count += 1

                logger.info(f'Updated transaction {transaction.tx_hash}: {transaction.status} → {status}')

        except Exception as e:
            error_count += 1
            logger.error(f'Error processing transaction {transaction.tx_hash}: {str(e)}')

    summary = {
        'updated': updated_count,
        'errors': error_count,
        'processed': processed_count
    }

    logger.info(f'Transaction status update complete: {summary}')
    return summary


def check_transaction_status(api, tx_hash):
    """
    Check transaction status via Blockfrost API.

    Returns:
        tuple: (status, details)
        - status: 'confirmed', 'submitted', 'failed', or 'pending'
        - details: dict with additional info or None
    """
    try:
        # Get transaction details
        tx_details = safe_blockfrost_call(api.transaction, tx_hash)

        # Check if transaction has been confirmed (has block info)
        if tx_details.get('block_height'):
            return 'confirmed', {
                'block_height': tx_details.get('block_height'),
                'slot': tx_details.get('slot'),
            }
        else:
            # Transaction exists but not yet confirmed
            return 'submitted', None

    except ApiError as e:
        if e.status_code == 404:
            # Transaction not found - could be still pending or failed
            return 'pending', None
        else:
            # Other API error - mark as failed
            logger.warning(f'Blockfrost API error for {tx_hash}: {str(e)}')
            return 'failed', {'error': str(e), 'error_code': e.status_code}

    except Exception as e:
        # Unexpected error
        logger.error(f'Unexpected error checking {tx_hash}: {str(e)}')
        return 'failed', {'error': str(e)}


# Import timezone here to avoid circular imports
from django.utils import timezone
