# notes/api_urls.py

from django.urls import path
from . import api_views

urlpatterns = [
    path('save-wallet/', api_views.save_wallet, name='save_wallet'),
    path('log-transaction/', api_views.log_transaction, name='log_transaction'),
    path('transaction-history/', api_views.transaction_history, name='transaction_history'),
    path('wallet-dashboard/', api_views.wallet_dashboard, name='wallet_dashboard'),
]

