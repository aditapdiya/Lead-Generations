from django.urls import path
from .views import show_leads

urlpatterns = [
    path("", show_leads, name="show_leads"),
]
