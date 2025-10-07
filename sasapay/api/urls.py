from django.urls import path
from .views import *

urlpatterns = [
    path("authenticate/", SasapayAuthView.as_view(), name="sasapay-auth"),

    path("c2bpayment/", C2BPaymentRequestView.as_view(), name="c2b"),
    path("process-payment/", ProcessPayment.as_view(), name="process-payment"),
    path("c2b-mobile/", C2BPaymentMobileMoneyRequestView.as_view(), name="c2b-mobile-money"),
    path("c2b-callback/", C2BCallbackView.as_view(), name="c2b-callback"),
    path("sasapay/ipn/", IPNView.as_view(), name="sasapay-ipn"),

    path("b2cpayment/", B2CPaymentRequestView.as_view(), name="b2cpayment"),

    path("b2bpayment/", B2BPaymentRequestView.as_view(), name="b2cpayment"),

    path("channel-codes/", ChannelCodesView.as_view(), name="channel-codes"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("remittance/", RemittancePaymentView.as_view(), name="remittance")


]
