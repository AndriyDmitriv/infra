from django.urls import path
from .views import login_view, logout_view

app_name = 'authentication'

urlpatterns = [
    path('auth/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]