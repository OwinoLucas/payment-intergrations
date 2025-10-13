from django.urls import path
from .views import *

urlpatterns = [
   path("auth/", AuthView.as_view(), name="auth"),
   path("QR-Code/", DynamicQR.as_view(), name="QR"),
   path("stk-push/", MpesaExpressView.as_view(), name="stk"),
   path("c2b/", C2BRegisterUrlView.as_view(), name="c2b"),
   path("b2c/", B2CPaymentView.as_view(), name="b2c"),
   path("transaction-status/", TransactionStatusView.as_view(), name="transaction-check")
]
