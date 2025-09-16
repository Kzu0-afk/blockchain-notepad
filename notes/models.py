# notes/models.py

from django.db import models
from django.contrib.auth.models import User # Import Django's built-in User model

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

    def __str__(self):
        # This helps identify notes in the admin panel
        return f"{self.title} by {self.createdBy.username}"