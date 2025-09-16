# notes/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Note CRUD URLs
    path('', views.note_list_view, name='note_list'), # Home page
    path('create/', views.note_create_view, name='note_create'),
]