# 📝 Note + Blockchain Integration Feature Plan

## 🎯 Objective
Enable global wallet persistence across the application and integrate blockchain transactions directly into the Note creation process. This ensures that creating a note can optionally trigger a real on-chain transaction, with the record permanently linked to the note.

## 🛠 Implementation Plan

### 1. 🌍 Global Wallet Persistence
**Goal:** Connect wallet once on Profile, remain connected on all pages, with accurate UI feedback everywhere.

**Strategy:**
- `autoConnect()` runs on EVERY page load via `base.html` -> `wallet-connection.js`.
- It checks `localStorage` for `connectedWalletName`.
- If found, it reconnects and updates `global-wallet-status` in the navbar.
- `updateConnectedUI()` is responsible for updating both the global header status and the profile-specific wallet status (hiding connect elements and showing disconnect button).
- **New `updateDisconnectedUI()`:** A dedicated function ensures consistent UI updates when no wallet is connected or a connection attempt fails. It makes the `wallet-select` and `connectWalletBtn` visible on the profile page and resets the header status.
- **Fix `BLOCKFROST_API_KEY` scope:** Ensure `window.BLOCKFROST_API_KEY` is always populated correctly by passing `settings.BLOCKFROST_PROJECT_ID` to the context of ALL views that render `base.html`. This prevents `initProvider()` from failing on non-profile pages.

**Files to Modify:**
- `frontend/src/wallet-connection.js`:
    - Refined `updateConnectedUI` to safely handle missing elements.
    - Added `updateDisconnectedUI` for consistent disconnected UI state.
    - Updated `autoConnect` and `connectWallet` to call `updateDisconnectedUI` on failure.
    - Replaced emojis in template literals with HTML entities to prevent build errors.
- `notes/templates/notes/base.html`:
    - The wallet status indicator now has the correct ID `global-wallet-status`.
- `notes/views.py`:
    - All views rendering `base.html` (`note_list_view`, `note_create_view`, `note_edit_view`, `note_delete_view`, `signup_view`, `login_view`, `transaction_list_view`) now pass `blockfrost_api_key` to their contexts.

### 2. 🔗 Link Notes to Transactions (Backend)
**Goal:** Database association between a `Note` and a `Transaction`.

**Strategy:**
- Add a `OneToOneField` to the `Note` model pointing to `Transaction`.
- This allows accessing transaction data directly from the note template (e.g., `note.transaction.tx_hash`).

**Schema Change (`notes/models.py`):**
```python
class Note(models.Model):
    # ... existing fields ...
    transaction = models.OneToOneField(
        'Transaction', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='note'
    )
```

### 3. 💸 Transaction-Enabled Note Form
**Goal:** User fills out Note + Payment details -> TX sent -> Note saved with TX link.

**Frontend Flow (`note_form.html`):**
1.  Add fields: `Recipient Address` and `Amount (ADA)`.
2.  Add a **Hidden Input**: `<input type="hidden" name="tx_hash" id="tx_hash">`.
3.  **Intercept Form Submit:**
    - If payment fields are empty: Submit normally (Note only).
    - If payment fields are filled:
        - Prevent default submit.
        - Call `blaze.sendAda(recipient, amount)`.
        - On success: Get `txHash`, set `value` of hidden input.
        - Programmatically submit the form.
        - On error: Alert user, do not submit.

**Backend Flow (`notes/views.py`):**
- In `NoteCreateView.form_valid()`:
    - Save the `Note` object.
    - Check `request.POST.get('tx_hash')`.
    - If present:
        - Create a new `Transaction` object with `tx_hash`, `amount`, `recipient`, `status='submitted'`.
        - Assign `note.transaction = new_transaction`.
        - Save `Note`.

### 4. 📜 Updated Note List UI
**Goal:** Visual indication of blockchain-verified notes with detailed info.

**Changes (`note_list.html`):**
- Check `{% if note.transaction %}`.
- If true, display a "Blockchain Verified ⛓️" badge.
- Show `TX Hash` (truncated) linking to CardanoScan.
- Show `Amount` sent.
- **Enhanced Details:** Display full Recipient Address and Status when available.

### 5. 📊 Transaction History Page (New)
**Goal:** Dedicated page for user's transaction history.

**Strategy:**
- Create a new view `transaction_list_view` in `views.py`.
- Create `transaction_list.html` template.
- Fetch all transactions for `request.user`.
- Display table/cards with: Date, TX Hash, Recipient, Amount, Status, Linked Note (if any).
- Add link to this page in the main navigation header.

## ✅ Step-by-Step Execution Guide (Completed)

1.  **Backend:** Update `Note` model and run migrations. ✅
2.  **Frontend Logic:** Update `wallet-connection.js` to handle global persistence, `autoConnect()`, `disconnectWallet()`, `updateConnectedUI()`, and `updateDisconnectedUI()`. ✅
3.  **Frontend Build:** Rebuild with Vite. ✅
4.  **Views:** Update Django views to handle the atomic creation of Note + Transaction and pass `blockfrost_api_key` to all necessary contexts. ✅
5.  **Templates:**
    - Update `note_form.html` with payment inputs and JS handler. ✅
    - Update `note_list.html` to display transaction metadata. ✅
    - Update `notes/templates/notes/base.html` for global wallet status. ✅
    - Create `notes/templates/notes/transaction_list.html`. ✅
6.  **Bug Fixes:**
    - Fixed `LOGIN_URL` reverse match error. ✅
    - Added Disconnect button to profile UI. ✅
    - Fixed global header wallet status persistence. ✅
    - Implemented `transaction_list.html` and view. ✅
    - Enhanced `note_list.html` details. ✅
    - **New:** Fixed wallet select issue on profile by ensuring `blockfrost_api_key` is passed globally and refining UI state functions (`updateDisconnectedUI`). ✅

---
**Reference:** Based on `@FINAL_REFACTOR_IMPLEMENTATION.md` architecture using Blaze SDK + Blockfrost.
