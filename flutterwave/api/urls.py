from django.urls import path
from .views import *

urlpatterns = [
   path("customers/", CustomerCreateListView.as_view(), name="customers"),
   path("customer/<str:id>/", CustomerDetailsView.as_view(), name="customer"),
   path("search/", CustomerSearchView.as_view(), name="search-customer"),

   path("charges/", ChargesCreateListView.as_view(), name="charges"),
   path("charges/<str:id>/", ChargesDetailsView.as_view(), name="charge"),
   
]
