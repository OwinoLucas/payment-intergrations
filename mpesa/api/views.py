# payments/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
import requests
from .services import generate_auth, generate_STKpassword, generate_timestamp

class AuthView(APIView):

    def post(self, request):
        url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate"
        params = {"grant_type": "client_credentials"}

        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET

        headers = generate_auth(consumer_key, consumer_secret)

        response = requests.get(url, params=params, headers=headers)

        try:
            res_data = response.json()
        except ValueError:
            res_data = {"detail": "Invalid JSON response from Mpesa."}

        if response.status_code == 200:
            return Response({
                "status": True,
                "message": "Token retrieved successfully",
                "data": res_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": False,
                "message": f"Failed to retrieve token (status {response.status_code})",
                "data": res_data
            }, status=response.status_code)
        
class DynamicQR(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.MPESA_BASE_URL}/mpesa/qrcode/v1/generate"
        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        payload = {
            "MerchantName": request.data.get("MerchantName"),
            "RefNo": request.data.get("RefNo"),
            "Amount": request.data.get("Amount"),
            "TrxCode": request.data.get("TrxCode"),
            "CPI": request.data.get("CPI"),
            "Size": request.data.get("Size")
        }

        payload = {k: v for k, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "QR Code not generated",
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": "QR Code generated successfully.",
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"QR Code generation failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class MpesaExpressView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"

        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        timestamp = generate_timestamp()
        password = generate_STKpassword(
            shortcode=settings.SHORT_CODE,
            passkey=settings.MPESA_PASSKEY,
            timestamp=timestamp
        )
       
        
        payload = {
            "BusinessShortCode": settings.SHORT_CODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": request.data.get("TransactionType"),
            "Amount": request.data.get("Amount"),
            "PartyA": request.data.get("PartyA"),
            "PartyB": request.data.get("PartyB"),
            "PhoneNumber": request.data.get("PhoneNumber"),
            "CallBackURL": request.data.get("CallBackURL"),
            "AccountReference": request.data.get("AccountReference"),
            "TransactionDesc": request.data.get("TransactionDesc")
        }

        payload = {x: v for x, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "STK Push unsuccessful",
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": "STK Push sent successfully.",
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"STK Push failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class C2BRegisterUrlView(APIView):

    def post(self, request):
        url =f"{settings.MPESA_BASE_URL}/mpesa/c2b/v1/registerurl"

        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        payload = {
            "ShortCode": request.data.get("ShortCode"),
            "ResponseType": request.data.get("ResponseType"),
            "ConfirmationURL": request.data.get("ConfirmationURL"),
            "ValidationURL": request.data.get("ValidationURL")
        }

        payload = {x: v for x, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "C2B transaction unsuccessful",
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": "C2B transaction successfully.",
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"C2B transaction failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class B2CPaymentView(APIView):

    def post(self, request):
        url =f"{settings.MPESA_BASE_URL}/mpesa/c2b/v1/registerurl"

        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        payload = {
            "OriginatorConversationID": request.data.get("OriginatorConversationID"),
            "InitiatorName": request.data.get("InitiatorName"),
            "SecurityCredential": request.data.get("SecurityCredential"),
            "CommandID": request.data.get("CommandID"),
            "Amount": request.data.get("Amount"),
            "PartyA": request.data.get("PartyA"),
            "PartyB": request.data.get("PartyB"),
            "Remarks": request.data.get("Remarks"),
            "QueueTimeOutURL": request.data.get("QueueTimeOutURL"),
            "ResultURL": request.data.get("ResultURL"),
            "Occassion": request.data.get("Occassion")
        }

        payload = {x: v for x, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "B2C transaction unsuccessful",
                        "data": res_data
                    },
                    status=response.status_code
                )

            return Response(
                {
                    "status": True,
                    "message": "B2C transaction successfully.",
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"B2C transaction failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
