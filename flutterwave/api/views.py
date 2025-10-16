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
    

######  Customer #########

class CustomerCreateListView(APIView):

    def get(self, request):
        url = f'{settings.FLUTTERWAVE_BASE_URL}/customers'
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()
       
        # encryption_key = settings.FLUTTERWAVE_ENCRYPTION_KEY

        # aes = AESEncryptor(encryption_key)
        # nonce = aes.generate_nonce()

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
    
    def post(self, request):
        url = f'{settings.FLUTTERWAVE_BASE_URL}/customers'
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()

        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payload = {
            "address": request.data.get("address"),
            "email": request.data.get("email"),
            "name": request.data.get("name"),
            "phone": request.data.get("phone")
        }


        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4()),
            "X-Idempotency-Key": str(uuid.uuid4())
        }
    
        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "Customer creation failed",
                        "data": res_data
                    },
                    status=response.status_code
                )

            # --- Success ---
            return Response(
                {
                    "status": True,
                    "message": res_data.get("message", "Customer created successfully."),
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Customer creation failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class CustomerDetailsView(APIView):
    """
    Retrieve or update a specific customer by ID from Flutterwave.
    """

    def get(self, request, id):
        """
        Fetch details of a single customer using the customer ID.
        """
        url = f"{settings.FLUTTERWAVE_BASE_URL}/customers/{id}"
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()

        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4())
        }

        try:
            response = requests.get(url, headers=headers)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": res_data.get("message", "Failed to fetch customer details."),
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": "Customer details fetched successfully.",
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Failed to fetch customer details: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, id):
    
        url = f"{settings.FLUTTERWAVE_BASE_URL}/customers/{id}"
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()

        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "name": request.data.get("name"),
            "email": request.data.get("email"),
            "phone": request.data.get("phone"),
            "address": request.data.get("address")
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4())
        }

        try:
            response = requests.put(url, headers=headers, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": res_data.get("message", "Customer update failed."),
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": res_data.get("message", "Customer updated successfully."),
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Customer update failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomerSearchView(APIView):

    def post(self, request):
        email = request.data.get("email")
        page = request.query_params.get("page", 1)
        size = request.query_params.get("size", 10)

        if not email:
            return Response({
                "status": False,
                "message": "Email is required for search."
            }, status=status.HTTP_400_BAD_REQUEST)

        url = f"{settings.FLUTTERWAVE_BASE_URL}/customers/search"
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()

        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4())
        }

        params = {
            "page": page,
            "size": size
        }

        payload = {
            "email": email
        }

        try:
            response = requests.post(url, headers=headers, params=params, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": res_data.get("message", "Failed to search customers."),
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": "Customer search successful.",
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Customer search failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

########  CHARGES #########

class ChargesCreateListView(APIView):

    def get(self, request):
        url = f'{settings.FLUTTERWAVE_BASE_URL}/charges'
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()


        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        params = {
            "status": request.query_params.get("status"),
            "reference": request.query_params.get("reference"),
            "to": request.query_params.get("to"),
            "from": request.query_params.get("from"),
            "customer_id": request.query_params.get("customer_id"),
            "virtual_account_id": request.query_params.get("virtual_account_id"),
            "payment_method_id": request.query_params.get("payment_method_id"),
            "order_id": request.query_params.get("order_id"),
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
                "message": "Charges fetched successfully",
                "data": response.json()
            }
        )
    
    def post(self, request):
        url = f'{settings.FLUTTERWAVE_BASE_URL}/charges'
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()

        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payload = {
            "amount": request.data.get("amount"),
            "currency": request.data.get("currency"),
            "reference": request.data.get("reference"),
            "customer_id": request.data.get("customer_id"),
            "description": request.data.get("description"),
            "meta": request.data.get("meta", {}),
            "redirect_url": request.data.get("redirect_url"),
            "recurring": request.data.get("recurring", False),
            "order_id": request.data.get("order_id"),
            "billing_details": {
                "email": request.data.get("billing_details", {}).get("email"),
                "name": {
                    "first": request.data.get("billing_details", {}).get("name", {}).get("first"),
                    "middle": request.data.get("billing_details", {}).get("name", {}).get("middle"),
                    "last": request.data.get("billing_details", {}).get("name", {}).get("last"),
                },
                "phone": {
                    "country_code": request.data.get("billing_details", {}).get("phone", {}).get("country_code"),
                    "number": request.data.get("billing_details", {}).get("phone", {}).get("number"),
                }
            },
            "payment_method_details": {
                "type": request.data.get("payment_method_details", {}).get("type"),
                "card": request.data.get("payment_method_details", {}).get("card"),
                "id": request.data.get("payment_method_details", {}).get("id"),
                "meta": request.data.get("payment_method_details", {}).get("meta", {}),
                "device_fingerprint": request.data.get("payment_method_details", {}).get("device_fingerprint"),
                "client_ip": request.data.get("payment_method_details", {}).get("client_ip")
            }
        }

        # --- Validate required fields ---
        required_fields = ["amount", "currency", "reference", "customer_id"]
        missing = [f for f in required_fields if not payload.get(f)]
        if missing:
            return Response({
                "status": False,
                "message": f"Missing required fields: {', '.join(missing)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # --- Validate amount ---
        try:
            amount = float(payload["amount"])
            if amount < 0.01:
                return Response({
                    "status": False,
                    "message": "Amount must be ≥ 0.01"
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                "status": False,
                "message": "Invalid amount value."
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4()),
            "X-Idempotency-Key": str(uuid.uuid4())
        }
    
        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "Charges creation failed",
                        "data": res_data
                    },
                    status=response.status_code
                )

            # --- Success ---
            return Response(
                {
                    "status": True,
                    "message": res_data.get("message", "Charges created successfully."),
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Charges creation failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ChargesDetailsView(APIView):

    def get(self, request, id):
    
        url = f"{settings.FLUTTERWAVE_BASE_URL}/charges/{id}"
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()

        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4())
        }

        try:
            response = requests.get(url, headers=headers)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": res_data.get("message", "Failed to fetch Charges details."),
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": "Charges details fetched successfully.",
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Failed to fetch Charges details: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, id):
    
        url = f"{settings.FLUTTERWAVE_BASE_URL}/charges/{id}"
        auth_manager = AuthManager()
        access_token = auth_manager.get_access_token()

        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "amount": request.data.get("amount"),
            "currency": request.data.get("currency"),
            "reference": request.data.get("reference"),
            "customer_id": id,  # from URL
            "meta": request.data.get("meta", {}),
            "payment_method_id": request.data.get("payment_method_id"),
            "redirect_url": request.data.get("redirect_url"),
            "authorization": request.data.get("authorization"),
            "recurring": request.data.get("recurring", False),
            "order_id": request.data.get("order_id")
        }

        # --- Validation (basic) ---
        required_fields = ["amount", "currency", "reference", "customer_id", "payment_method_id"]
        missing = [f for f in required_fields if not payload.get(f)]
        if missing:
            return Response({
                "status": False,
                "message": f"Missing required fields: {', '.join(missing)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(payload["amount"])
            if amount < 0.01:
                return Response({
                    "status": False,
                    "message": "Amount must be ≥ 0.01"
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                "status": False,
                "message": "Invalid amount value."
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Trace-Id": str(uuid.uuid4())
        }

        try:
            response = requests.put(url, headers=headers, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": res_data.get("message", "Charges update failed."),
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": res_data.get("message", "Charges updated successfully."),
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Charges update failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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