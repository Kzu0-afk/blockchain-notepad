from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # Import for pagination
from .models import Note, Profile, Transaction

def landing_view(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('notes:note_list')
    return render(request, 'notes/landing.html')


def wallet_profile_view(request):
    return render(request, 'notes/profile.html')
@login_required
def note_edit_view(request, pk):
    note = get_object_or_404(Note, pk=pk, createdBy=request.user, is_deleted=False)
    if request.method == 'POST':
        note.title = request.POST.get('title')
        note.description = request.POST.get('description')
        note.save()
        messages.success(request, "Note updated successfully!")
        return redirect('notes:note_list')
    context = {
        'note': note,
        'blockfrost_api_key': settings.BLOCKFROST_PROJECT_ID
    }
    return render(request, 'notes/note_form.html', context)

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
    context = {
        'note': note,
        'blockfrost_api_key': settings.BLOCKFROST_PROJECT_ID
    }
    return render(request, 'notes/note_confirm_delete.html', context)

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
    context = {
        'form': form,
        'blockfrost_api_key': settings.BLOCKFROST_PROJECT_ID
    }
    return render(request, 'notes/signup.html', context)

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
    context = {
        'form': form,
        'blockfrost_api_key': settings.BLOCKFROST_PROJECT_ID
    }
    return render(request, 'notes/login.html', context)

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect('notes:landing')

@login_required
def note_list_view(request):
    all_notes = Note.objects.filter(createdBy=request.user, is_deleted=False).order_by('-updatedAt')
    
    # Pagination
    paginator = Paginator(all_notes, 9) # Show 9 notes per page
    page_number = request.GET.get('page')
    try:
        notes_page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        notes_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        notes_page = paginator.page(paginator.num_pages)

    context = {
        'page_obj': notes_page,
        'is_paginated': notes_page.has_other_pages(),
        'blockfrost_api_key': settings.BLOCKFROST_PROJECT_ID
    }
    return render(request, 'notes/note_list.html', context)

@login_required
def note_create_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        tx_hash = request.POST.get('tx_hash')

        transaction = None
        if tx_hash:
            recipient = request.POST.get('recipient_address') # Matches name in form
            amount = request.POST.get('amount') # Matches name in form
            
            # Create Transaction record
            if recipient and amount:
                transaction = Transaction.objects.create(
                    user=request.user,
                    tx_hash=tx_hash,
                    recipient_address=recipient,
                    amount_lovelace=int(amount),
                    status='submitted' # Client already confirmed submission
                )

        # Create Note, optionally linked to Transaction
        Note.objects.create(
            title=title, 
            description=description, 
            createdBy=request.user,
            transaction=transaction
        )
        
        msg = "Note created successfully!"
        if transaction:
            msg += " (Blockchain Transaction Linked 🔗)"
        
        messages.success(request, msg)
        return redirect('notes:note_list')
    
    context = {
        'blockfrost_api_key': settings.BLOCKFROST_PROJECT_ID
    }
    return render(request, 'notes/note_form.html', context)

@login_required
def profile_view(request):
    """User profile page with wallet connection and transaction form"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    context = {
        'profile': profile,
        'blockfrost_api_key': settings.BLOCKFROST_PROJECT_ID
    }
    return render(request, 'notes/profile.html', context)

@login_required
def transaction_list_view(request):
    """List all blockchain transactions for the current user"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'transactions': transactions,
        'blockfrost_api_key': settings.BLOCKFROST_PROJECT_ID
    }
    return render(request, 'notes/transaction_list.html', context)