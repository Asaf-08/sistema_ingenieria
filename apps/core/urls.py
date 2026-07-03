from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_principal, name='home'),
]