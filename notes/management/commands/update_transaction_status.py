"""
Management command to update transaction statuses by polling Blockfrost.
This command should be run periodically (e.g., every 5-10 minutes) to check
for transaction confirmations.

Usage:
    python manage.py update_transaction_status --dry-run
    python manage.py update_transaction_status --limit=50
"""

from django.core.management.base import BaseCommand
from notes.tasks import update_transaction_statuses


class Command(BaseCommand):
    help = 'Update transaction statuses by polling Blockfrost API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of transactions to process (default: 100)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made to the database')
            )

        # Call the task function
        summary = update_transaction_statuses(limit=limit)

        # Display results
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'Dry run complete. Would process {summary["processed"]} transactions'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Processed {summary["processed"]} transactions: '
                f'{summary["updated"]} updated, {summary["errors"]} errors'
            ))