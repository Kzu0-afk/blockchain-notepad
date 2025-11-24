# notes/urls.py
from django.urls import include, path
from . import views

app_name = 'notes'

urlpatterns = [
    # Landing page for non-authenticated users
    path('', views.landing_view, name='landing'),

    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Note CRUD URLs
    path('notes/', views.note_list_view, name='note_list'),  # Notes home page
    path('create/', views.note_create_view, name='note_create'),
    path('notes/<int:pk>/edit/', views.note_edit_view, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete_view, name='note_delete'),
    # Profile & Wallet URLs
    path('profile/', views.profile_view, name='profile'),

    # WALLET & API ENDPOINTS
    path('send-ada/', views.wallet_profile_view, name='send_ada'),
    path('wallet/', views.wallet_profile_view, name='wallet_profile'),
    path('api/build-transaction/', views.build_transaction, name='build_transaction'),
    path('api/submit-transaction/', views.submit_transaction, name='submit_transaction'),
    path('api/save-wallet/', views.save_wallet, name='save_wallet'),
]
