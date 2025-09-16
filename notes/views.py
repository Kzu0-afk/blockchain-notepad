from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Note

# --- Authentication Views ---

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('note_list') # Redirect to the notes list after signup
    else:
        form = UserCreationForm()
    return render(request, 'notes/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('note_list') # Redirect to the notes list after login
    else:
        form = AuthenticationForm()
    return render(request, 'notes/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login') # Redirect to login page after logout
    
# Add these functions to the bottom of notes/views.py

# --- Note Views ---

@login_required
def note_list_view(request):
    # Get only the notes created by the currently logged-in user
    notes = Note.objects.filter(createdBy=request.user).order_by('-updatedAt')
    return render(request, 'notes/note_list.html', {'notes': notes})

@login_required
def note_create_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        # Create a new note and associate it with the logged-in user
        Note.objects.create(title=title, description=description, createdBy=request.user)
        return redirect('note_list')
    return render(request, 'notes/note_form.html')   