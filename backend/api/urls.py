"""
backend/api/urls.py
URL patterns for the api app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
]
