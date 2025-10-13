from django.urls import path
from .views import *

urlpatterns = [
    path("auth/", SasapayTZAuthView.as_view(), name="sasapay-auth-tz"),

    path("c2b-tz/", C2BTZRequestView.as_view(), name="c2b-tz"),
    path("c2b-tz/callback/", C2BTZCallbackView.as_view(), name="c2b-callback"),
    path("c2b-tz/ipn/", IPNView.as_view(), name="ipn"),

    path("ifm/", InternalFundMovement.as_view(), name="ifm"),

    path("b2c-tz/", B2CPaymentRequestView.as_view(), name="b2c"),
    path("b2b-tz/", B2BPaymentRequestView.as_view(), name="b2b")

  


]
