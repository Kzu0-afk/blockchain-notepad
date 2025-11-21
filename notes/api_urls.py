# notes/api_urls.py

from django.urls import path
from . import api_views

urlpatterns = [
    path('save-wallet/', api_views.save_wallet, name='save_wallet'),
    path('build-transaction/', api_views.build_transaction, name='build_transaction'),
    path('submit-transaction/', api_views.submit_transaction, name='submit_transaction'),
    path('transaction-history/', api_views.transaction_history, name='transaction_history'),
    path('wallet-dashboard/', api_views.wallet_dashboard, name='wallet_dashboard'),
]

