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

    #soft delete field - notes will be marked as deleted instead of being removed from the database
    is_deleted = models.BooleanField(default=False)


    def __str__(self):
        # This helps identify notes in the admin panel
        return f"{self.title} by {self.createdBy.username}"