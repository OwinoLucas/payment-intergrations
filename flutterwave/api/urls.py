from django.urls import path
from .views import *

urlpatterns = [
   path("customers/", CustomerCreateListView.as_view(), name="customer")
]
