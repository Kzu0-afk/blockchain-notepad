from xmlrpc import client
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Note, Profile
# from blockfrost import Blockfrost, ApiError
from blockfrost import BlockFrostApi, ApiError, ApiUrls
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import cbor2

from blockfrost import BlockFrostApi, ApiUrls

client = BlockFrostApi(
    project_id=settings.BLOCKFROST_PROJECT_ID,
    base_url=ApiUrls.preview.value
)

@csrf_exempt
@require_POST
def build_transaction(request):
    try:
        data = json.loads(request.body)

        # FIXED: Extract variables properly
        sender_address = data.get('sender_address')
        recipient_address = data.get('recipient_address')
        amount_lovelace = data.get('amount_lovelace')

        # Validate
        if not all([sender_address, recipient_address, amount_lovelace]):
            return JsonResponse({"error": "Missing data"}, status=400)

    

        # NOW IT WORKS — both are proper Shelley addresses
        if not sender_address or not sender_address.startswith('addr_test1p'):
            return JsonResponse({"error": "Sender must be Preview Shelley address (addr_test1p...)"}, status=400)
        if not recipient_address or not recipient_address.startswith('addr_test1p'):
            return JsonResponse({"error": "Recipient must be addr_test1p..."}, status=400)
        # if not (sender_address.startswith('addr_test1') or (len(sender_address) == 128 and sender_address.startswith('00'))):
        #     return JsonResponse({"error": "Invalid sender address for Preview testnet"}, status=400)
        # if not recipient_address.startswith('addr_test1p'):
        #     return JsonResponse({"error": "Recipient must be Preview testnet address (addr_test1p...)"}, status=400)
        # if amount_lovelace < 1000000:
        #     return JsonResponse({"error": "Minimum 1 ADA"}, status=400)

        # Get UTXOs
        utxos = client.address_utxos(sender_address)
        if not utxos:
            return JsonResponse({"error": "No funds. Fund from https://docs.cardano.org/cardano-testnet/tools/faucet"}, status=400)

        total = 0
        inputs = []
        for utxo in utxos:
            lovelace = next((a.quantity for a in utxo.amount if a.unit == 'lovelace'), 0)
            total += int(lovelace)
            inputs.append((utxo.tx_hash, utxo.output_index))
            if total >= amount_lovelace + 2000000:
                break

        if total < amount_lovelace + 1000000:
            return JsonResponse({"error": "Insufficient balance"}, status=400)

        change = total - amount_lovelace - 180000
        outputs = {recipient_address: amount_lovelace}
        if change > 500000:
            outputs[sender_address] = change

        tx_body = {
            0: [[bytes.fromhex(h), i] for h, i in inputs],
            1: {addr: {"lovelace": amt} for addr, amt in outputs.items()},
            2: 180000,
            3: client.block_latest().slot + 36000
        }

        return JsonResponse({
            "unsigned_tx_cbor": cbor2.dumps(tx_body).hex()
        })

    except Exception as e:
        return JsonResponse({"error": f"Error: {str(e)}"}, status=500)


@csrf_exempt
@require_POST
def submit_transaction(request):
    try:
        data = json.loads(request.body)
        signed_cbor = data.get('signed_tx_cbor')
        if not signed_cbor:
            return JsonResponse({"error": "No signed transaction"}, status=400)

        tx_hash = client.tx_submit(signed_cbor)
        return JsonResponse({"tx_hash": tx_hash})

    except Exception as e:
        return JsonResponse({"error": f"Submit failed: {str(e)}"}, status=500)
    
def landing_view(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('notes:note_list')
    return render(request, 'notes/landing.html')


def send_ada_view(request):
    return render(request, 'notes/send_ada.html')


def wallet_profile_view(request):
    return render(request, 'notes/profile.html')

@csrf_exempt
@require_POST
def save_wallet(request):
    try:
        data = json.loads(request.body)
        request.session['wallet_address'] = data.get('wallet_address')
        return JsonResponse({"success": True})
    except:
        return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
@require_POST
def save_wallet(request):
    try:
        data = json.loads(request.body)
        request.session['wallet_address'] = data.get('wallet_address')
        return JsonResponse({"success": True})
    except:
        return JsonResponse({"error": "Invalid request"}, status=400)
    
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

@login_required
def profile_view(request):
    """User profile page with wallet connection and transaction form"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'notes/profile.html', {'profile': profile})
