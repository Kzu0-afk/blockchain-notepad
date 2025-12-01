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
    path('history/', views.transaction_list_view, name='transaction_list'),
]
