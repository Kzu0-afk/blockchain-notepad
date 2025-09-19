from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Note

def landing_view(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('notes:note_list')
    return render(request, 'notes/landing.html')

@login_required
def note_edit_view(request, pk):
    note = get_object_or_404(Note, pk=pk, createdBy=request.user, is_deleted=False)
    if request.method == 'POST':
        note.title = request.POST.get('title')
        note.description = request.POST.get('description')
        note.save()
        messages.success(request, "Note updated successfully!")
        return redirect('notes:note_list')
    return render(request, 'notes/note_form.html', {'note': note})

@login_required
def note_delete_view(request, pk):
    note = get_object_or_404(Note, pk=pk, createdBy=request.user, is_deleted=False)
    if request.method in ['POST', 'DELETE']:
        note.is_deleted = True
        note.save()
        messages.info(request, "Note deleted.")
        if request.headers.get('HX-Request'):
            return HttpResponse('')  # HTMX removes the element
        return redirect('notes:note_list')
    return render(request, 'notes/note_confirm_delete.html', {'note': note})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Welcome.")
            return redirect('notes:note_list')
    else:
        form = UserCreationForm()
    return render(request, 'notes/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect('notes:note_list')
    else:
        form = AuthenticationForm()
    return render(request, 'notes/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect('notes:landing')

@login_required
def note_list_view(request):
    notes = Note.objects.filter(createdBy=request.user, is_deleted=False).order_by('-updatedAt')
    return render(request, 'notes/note_list.html', {'notes': notes})

@login_required
def note_create_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        Note.objects.create(title=title, description=description, createdBy=request.user)
        messages.success(request, "Note created successfully!")
        return redirect('notes:note_list')
    return render(request, 'notes/note_form.html')
