# payments/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
import requests, uuid
from django.conf import settings
from datetime import datetime, timedelta
from .services import AESEncryptor
# class ListCustomersView(APIView):


class AuthManager:
    def __init__(self):
        self.credentials = {
            "client_id": settings.FLUTTERWAVE_CLIENT_ID,
            "client_secret": settings.FLUTTERWAVE_CLIENT_SECRET,
            "access_token": None,
            "expiry": None
        }

    def generate_access_token(self):
        url = "https://idp.flutterwave.com/realms/flutterwave/protocol/openid-connect/token"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "client_id": self.credentials["client_id"],
            "client_secret": self.credentials["client_secret"],
            "grant_type": "client_credentials"
        }

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()

        response_json = response.json()

        # Store token and expiry
        self.credentials["access_token"] = response_json["access_token"]
        self.credentials["expiry"] = datetime.now() + timedelta(seconds=response_json["expires_in"])

        return self.credentials["access_token"]

    def get_access_token(self):
        # If no token or expired -> generate a new one
        if (
            not self.credentials["access_token"]
            or not self.credentials["expiry"]
            or self.credentials["expiry"] < datetime.now() + timedelta(minutes=1)
        ):
            return self.generate_access_token()

        return self.credentials["access_token"]

class CustomerCreateListView(APIView):

    def get(self, request):
        url = f'{settings.FLUTTERWAVE_BASE_URL}/customers'
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()
       
        encryption_key = settings.FLUTTERWAVE_ENCRYPTION_KEY

        aes = AESEncryptor(encryption_key)
        nonce = aes.generate_nonce()

        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        params = {
            "page": request.query_params.get("page"),
            "size": request.query_params.get("size")
        }


        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4()),
            "X-Idempotency-Key": str(uuid.uuid4())
        }

        response = requests.get(url, headers=headers, params=params)

        return Response(
            {
                "status": True,
                "message": "Customers fetched successfully",
                "data": response.json()
            }
        )
        

class FlutterWaveView(APIView):

    def post(self, request):
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()
        reference = f"txn-{uuid.uuid4().hex[:12]}"
        encryption_key = settings.FLUTTERWAVE_ENCRYPTION_KEY

        aes = AESEncryptor(encryption_key)
        nonce = aes.generate_nonce()

        url = "https://api.flutterwave.cloud/developersandbox/orchestration/direct-charges"

        payload = {
            "reference": reference,
            "currency": "AED",
            "amount": 100.50,
            "customer": {
                "email": "johndoe@example.com",
                "name": {
                "first_name": "John",
                "last_name": "Doe"
                },
                "phone": {
                "country_code": "254",
                "number": "712345678"
                },
                "address": {
                "line1": "123 Test St",
                "city": "Dubai",
                "state": "Dubai",
                "postal_code": "00000",
                "country": "AE"
                }
            },
            "payment_method": {
                "type": "card",
                "card": {
                "nonce": nonce,
                "encrypted_card_number": aes.encrypt("4111111111111111", nonce),
                "encrypted_expiry_month": aes.encrypt("09", nonce),
                "encrypted_expiry_year": aes.encrypt("26", nonce),
                "encrypted_cvv": aes.encrypt("123", nonce),
                "billing_address": {
                    "line1": "123 Test St",
                    "city": "Dubai",
                    "state": "Dubai",
                    "postal_code": "00000",
                    "country": "AE"
                },
                "cof": {
                    "enabled": True
                },
                "card_holder_name": "John Doe"
                }
            },
            "redirect_url": "https://webhook.site/58ad6d2f-e64f-4d0e-919b-e82795d8bc7d"
        }


        print("payload", payload)
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4()),
            "X-Idempotency-Key": str(uuid.uuid4())
        }

        response = requests.post(url, json=payload, headers=headers)

        print(response.text)
        
        return Response(response.json(), status=status.HTTP_200_OK)