from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from requests.auth import HTTPBasicAuth
from django.conf import settings
import requests



class SasapayTZAuthView(APIView):

    def post(self, request):
        url = f"{settings.SASAPAY_TZ_BASE_URL}/auth/token/"
        params = {"grant_type": "client_credentials"}

        # Use HTTP Basic Authentication
        response = requests.get(
            url,
            auth=HTTPBasicAuth(settings.SASAPAY_TZ_CLIENT_ID, settings.SASAPAY_TZ_CLIENT_SECRET),
            params=params,
        )

        try:
            res_data = response.json()
        except ValueError:
            res_data = {"detail": "Invalid JSON response from SasaPay."}

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
        
class C2BTZRequestView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f'{settings.SASAPAY_TZ_BASE_URL}/payments/request-payment/'

        # --- Check token ---
        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payload = {
            "MerchantCode": request.data.get("MerchantCode"),
            "NetworkCode": request.data.get("NetworkCode"),
            "TransactionFee": request.data.get("Transaction Fee"),
            "Currency": request.data.get("Currency", "TZS"),
            "Amount": request.data.get("Amount"),
            "CallBackURL": request.data.get("CallBackURL"),
            "PhoneNumber": request.data.get("PhoneNumber"),
            "TransactionDesc": request.data.get("TransactionDesc"),
            "AccountReference": request.data.get("AccountReference"),
        }

        # remove null/None fields
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            # --- Handle SasaPay error responses gracefully ---
            if not response.ok or not res_data.get("status", True):
                message = res_data.get("message") or res_data.get("detail") or "Payment request failed."
                return Response(
                    {
                        "status": False,
                        "message": message,
                        "data": res_data
                    },
                    status=response.status_code
                )

            # --- Success ---
            return Response(
                {
                    "status": True,
                    "message": res_data.get("message", "Payment request sent successfully."),
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Request to SasaPay failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class C2BTZCallbackView(APIView):
    """
    This endpoint receives transaction results from SasaPay TZ
    after a C2B payment request is processed.
    """

    def post(self, request):
        data = request.data
        print(f"SasaPay C2B Callback received: {data}")

        # Optionally validate or process the payment
        merchant_request_id = data.get("MerchantRequestID")
        customer_mobile = data.get("CustomerMobile")
        result_code = data.get("ResultCode")
        result_desc = data.get("ResultDesc")
        checkout_request_id = data.get("CheckoutRequestID")
        bill_ref_number = data.get("BillRefNumber")
        trans_amount = data.get("TransAmount")
        trans_date = data.get("TransactionDate")
        third_party_transaction_id = data.get("ThirdPartyTransID")

        # Example logic: mark transaction as complete if successful
        if result_code == "0":
            # TODO: update your database, mark payment successful, etc.
            message = "Transaction processed successfully."
        else:
            # TODO: log or flag failed transaction
            message = f"Transaction failed: {result_desc}"

        return Response(
            {"status": True, "message": message, "data": data},
            status=status.HTTP_200_OK,
        )

class IPNView(APIView):
    """
    Endpoint to receive Instant Payment Notifications (IPN) from SasaPay TZ.
    """

    def post(self, request):
        data = request.data

        print("Received SasaPay IPN: %s", data)

        required_fields = [
            "MerchantCode", "PaymentMethod", "TransID", "TransAmount", "TransactionType",
            "MSISDN", "TransTime", "BillRefNumber"
        ]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return Response(
                {"status": False, "message": f"Missing fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Example: Save or update transaction record
        try:
            # Example pseudo-code
            # transaction = Transaction.objects.filter(bill_ref=data["BillRefNumber"]).first()
            # if transaction:
            #     transaction.status = "COMPLETED"
            #     transaction.amount = data["TransAmount"]
            #     transaction.transaction_id = data["TransID"]
            #     transaction.payment_method = data["PaymentMethod"]
            #     transaction.save()

            print("Processed IPN for BillRefNumber %s", data["BillRefNumber"])
        except Exception as e:
            print("Error processing IPN: %s", str(e))
            return Response(
                {"status": False, "message": "Error processing IPN"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"status": True, "message": "IPN received successfully", "data": data},
            status=status.HTTP_200_OK
        )

class InternalFundMovement(APIView):

    def post(self, request):
        url = f'{settings.SASAPAY_TZ_BASE_URL}/transactions/fund-movement/'
        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payload = {
            "merchantCode": request.data.get("merchantCode"),
            "amount": request.data.get("amount"),
        }

        # remove null/None fields
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            # --- Handle SasaPay error responses gracefully ---
            if not response.ok or not res_data.get("status", True):
                message = res_data.get("message") or res_data.get("detail") or "Transaction failed."
                return Response(
                    {
                        "status": False,
                        "message": message,
                        "data": res_data
                    },
                    status=response.status_code
                )

            # --- Success ---
            return Response(
                {
                    "status": True,
                    "message": res_data.get("message", "Transaction completed successfully."),
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Transaction failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class B2CPaymentRequestView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.SASAPAY_TZ_BASE_URL}/payments/b2c/"

        access_token = request.headers.get("Authorization")
        print("TOKEN: ", access_token)
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        payload = {
            "MerchantCode": request.data.get("MerchantCode"),
            "MerchantTransactionReference": request.data.get("MerchantTransactionReference"),
            "Amount": request.data.get("Amount"),
            "Currency": request.data.get("Currency", "TZS"),
            "ReceiverNumber": request.data.get("ReceiverNumber"),
            "Channel": request.data.get("Channel"),
            "Reason": request.data.get("Reason"),
            "CallBackURL": request.data.get("CallBackURL")
        } 

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        print("URL:", url)
        print("HEADERS:", headers)
        print("PAYLOAD:", payload)

        try:
            response = requests.post(url, headers=headers, json=payload)
            print("RAW RESPONSE:", response.text)
            resp_data = response.json()
             
            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "B2C Transaction Failed",
                        "data": resp_data
                    },
                    status=response.status_code
                )
            return Response(
                {
                    "status": True,
                    "message": "B2C Payment request sent successfully.",
                    "data": resp_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"B2C request failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class B2BPaymentRequestView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.SASAPAY_TZ_BASE_URL}/payments/b2b/"

        access_token = request.headers.get("Authorization")
        
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        payload = {
            "MerchantCode": request.data.get("MerchantCode"),
            "MerchantTransactionReference": request.data.get("MerchantTransactionReference"),
            "Currency": request.data.get("Currency", "TZS"),
            "Amount": request.data.get("Amount"),
            "ReceiverMerchantCode": request.data.get("ReceiverMerchantCode"),
            "AccountReference": request.data.get("AccountReference"),
            "ReceiverAccountType": request.data.get("ReceiverAccountType"), #PAYBILL/TILL PAYBILL requires AccountReference
            "NetworkCode": request.data.get("NetworkCode"),
            "CallBackURL": request.data.get("CallBackURL"),
            "Reason": request.data.get("Reason")
        }  

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            resp_data = response.json()
             
            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "B2B Transaction Failed",
                        "data": resp_data
                    },
                    status=response.status_code
                )
            return Response(
                {
                    "status": True,
                    "message": "B2B Payment request sent successfully.",
                    "data": resp_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"B2B request failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


