# notes/models.py

from django.db import models
from django.contrib.auth.models import User # Import Django's built-in User model
from django.db.models.signals import post_save
from django.dispatch import receiver

# Profile model to extend User with wallet functionality
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    wallet_address = models.CharField(max_length=103, unique=True, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to automatically create Profile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# This is the model for your 'NOTE' table.
class Note(models.Model):
    # NoteID is created automatically by Django as 'id' (Primary Key)
    title = models.CharField(max_length=255)
    description = models.TextField() # TextField is better for long descriptions
    
    # auto_now_add=True sets this only when the note is first created
    createdAt = models.DateTimeField(auto_now_add=True)
    
    # auto_now=True updates this every time the note is saved
    updatedAt = models.DateTimeField(auto_now=True)
    
    # This is your Foreign Key relationship.
    # Each note is linked to one User.
    # If a User is deleted, all their notes are also deleted (CASCADE).
    createdBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")

    # Link to a blockchain transaction (optional)
    transaction = models.OneToOneField(
        'Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='note'
    )

    #soft delete field - notes will be marked as deleted instead of being removed from the database
    is_deleted = models.BooleanField(default=False)


    def __str__(self):
        # This helps identify notes in the admin panel
        return f"{self.title} by {self.createdBy.username}"


# Transaction model to track blockchain transactions
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ]
    
    # User who initiated the transaction
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction hash from blockchain (unique identifier)
    tx_hash = models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True)
    
    # Transaction details
    recipient_address = models.CharField(max_length=103)
    amount_lovelace = models.BigIntegerField()
    
    # Transaction status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Note: CBOR fields (unsigned_tx_cbor, signed_tx_cbor) are deprecated
    # Transactions are now built client-side via Blaze SDK
    # Fields kept for backwards compatibility with existing data
    
    # Blockchain metadata
    block_height = models.IntegerField(null=True, blank=True)
    slot = models.BigIntegerField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(null=True, blank=True)
    error_code = models.CharField(max_length=50, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            # User-specific queries (most common)
            models.Index(fields=['user', '-created_at'], name='tx_user_created_idx'),
            models.Index(fields=['user', 'status'], name='tx_user_status_idx'),

            # Status-based queries for background updates
            models.Index(fields=['status', 'created_at'], name='tx_status_created_idx'),
            models.Index(fields=['status', 'updated_at'], name='tx_status_updated_idx'),

            # Transaction hash lookups
            models.Index(fields=['tx_hash'], name='tx_hash_idx'),

            # Composite indexes for complex queries
            models.Index(fields=['user', 'status', '-created_at'], name='tx_user_status_created_idx'),
            models.Index(fields=['created_at', 'status'], name='tx_created_status_idx'),
        ]
    
    def __str__(self):
        if self.tx_hash:
            return f"Transaction {self.tx_hash[:16]}... ({self.status})"
        return f"Transaction #{self.id} - {self.status}"
    
    def get_amount_ada(self):
        """Convert lovelace to ADA for display"""
        return self.amount_lovelace / 1_000_000 if self.amount_lovelace else 0
    
    def is_final(self):
        """Check if transaction is in a final state"""
        return self.status in ['confirmed', 'failed']