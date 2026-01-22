from django.urls import path
from . import views

app_name = 'django_resend'

urlpatterns = [
    path('webhook/', views.resend_webhook_view, name='webhook'),
]
