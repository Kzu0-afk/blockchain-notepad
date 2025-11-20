# notes/api_urls.py

from django.urls import path
from . import api_views

urlpatterns = [
    path('build-transaction/', api_views.build_transaction, name='build_transaction'),
    path('submit-transaction/', api_views.submit_transaction, name='submit_transaction'),
]

