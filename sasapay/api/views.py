from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from requests.auth import HTTPBasicAuth
from django.conf import settings
import requests



class SasapayAuthView(APIView):

    def post(self, request):
        url = f"{settings.SASAPAY_BASE_URL}/auth/token/"
        params = {"grant_type": "client_credentials"}

        # Use HTTP Basic Authentication
        response = requests.get(
            url,
            auth=HTTPBasicAuth(settings.SASAPAY_CLIENT_ID, settings.SASAPAY_CLIENT_SECRET),
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


class C2BPaymentRequestView(APIView):
    """
    Request payment from a SasaPay user (C2B)
    """
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.SASAPAY_BASE_URL}/payments/request-payment/"

        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build payload
        payload = {
            "MerchantCode": request.data.get("MerchantCode"),
            "NetworkCode": request.data.get("NetworkCode"),
            "Currency": request.data.get("Currency", "KES"),
            "Amount": request.data.get("Amount"),
            "CallBackURL": request.data.get("CallBackURL"),
            "PhoneNumber": request.data.get("PhoneNumber"),
            "TransactionDesc": request.data.get("TransactionDesc"),
            "AccountReference": request.data.get("AccountReference"),
        }

        # Remove empty fields
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Request to SasaPay failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "status": True,
            "message": res_data.get("detail", "Request processed"),
            "data": res_data
        }, status=response.status_code)
    
class ProcessPayment(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.SASAPAY_BASE_URL}/payments/process-payment/"

        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response({
                "status": False,
                "message": "Missing Authorization header (Bearer token required)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payload = {
            "CheckoutRequestID": request.data.get('CheckoutRequestID'),
            "MerchantCode": request.data.get('MerchantCode'),
            "VerificationCode": request.data.get('VerificationCode')
        }

        payload = {k: v for k, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Request to SasaPay failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "status": res_data.get("status", False),
            "message": res_data.get("detail", "Request processed"),
            "data": res_data
        }, status=response.status_code)
    

class C2BPaymentMobileMoneyRequestView(APIView):
    """
    Request payment from a SasaPay user (C2B) for mobile money
    """
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f'{settings.SASAPAY_BASE_URL}/payments/request-payment/'

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
            "TransactionFee": request.data.get("TransactionFee"),
            "Currency": request.data.get("Currency", "KES"),
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


class C2BCallbackView(APIView):
    """
    This endpoint receives transaction results from SasaPay
    after a C2B payment request is processed.
    """

    def post(self, request):
        data = request.data
        print(f"SasaPay C2B Callback received: {data}")

        # Optionally validate or process the payment
        merchant_request_id = data.get("MerchantRequestID")
        result_code = data.get("ResultCode")
        result_desc = data.get("ResultDesc")
        trans_amount = data.get("TransAmount")
        customer_mobile = data.get("CustomerMobile")
        transaction_code = data.get("TransactionCode")

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
    Endpoint to receive Instant Payment Notifications (IPN) from SasaPay.
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

class B2CPaymentRequestView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.SASAPAY_BASE_URL}/payments/b2c/"

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
            "Amount": request.data.get("Amount"),
            "Currency": request.data.get("Currency", "KES"),
            "ReceiverNumber": request.data.get("ReceiverNumber"),
            "Channel": request.data.get("Channel"),
            "Reason": request.data.get("Reason"),
            "CallBackURL": request.data.get("CallBackURL")
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
        url = f"{settings.SASAPAY_BASE_URL}/payments/b2b/"

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
            "Currency": request.data.get("Currency", "KES"),
            "Amount": request.data.get("Amount"),
            "ReceiverMerchantCode": request.data.get("ReceiverMerchantCode"),
            "AccountReference": request.data.get("AccountReference"),
            "ReceiverAccountType": request.data.get("ReceiverAccountType"),
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
        
class ChannelCodesView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        url = f"{settings.SASAPAY_BASE_URL}/payments/channel-codes/"

        access_token = request.headers.get("Authorization")
        if not access_token:
            return Response(
                {
                    "status": False,
                    "message": "Missing Authorization header (Bearer token required)"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        headers = {
            "Authorization": access_token
        }

        response = requests.get(url, headers=headers)

        return Response(
            {
                "status": True,
                "message": "Channel Codes available",
                "data": response.json()
            }, status=status.HTTP_200_OK)
    
class CheckoutView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.SASAPAY_BASE_URL}/payments/card-payments/"

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
            "Amount": request.data.get("Amount"),
            "Reference": request.data.get("Reference"),
            "Description": request.data.get("Description"),
            "Currency": request.data.get("Currency", "KES"),
            "PayerEmail": request.data.get("PayerEmail"),
            "CallbackUrl": request.data.get("CallbackUrl"),
            "SuccessUrl": request.data.get("SuccessUrl"),
            "FailureUrl": request.data.get("FailureUrl"),
            "SasaPayWalletEnabled": request.data.get("SasaPayWalletEnabled"),
            "MpesaEnabled": request.data.get("MpesaEnabled"),
            "CardEnabled": request.data.get("CardEnabled"),
            "AirtelEnabled": request.data.get("AirtelEnabled")
        }  

        payload = {k: v for k, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            # --- Handle SasaPay error responses gracefully ---
            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "Checkout process failed",
                        "data": res_data
                    },
                    status=response.status_code
                )

            # --- Success ---
            return Response(
                {
                    "status": True,
                    "message": res_data.get("message", "Checkout processed successfully."),
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Checkout Request to SasaPay failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RemittancePaymentView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        url = f"{settings.SASAPAY_BASE_URL}/remittances/remittance-payments/"
        access_token = request.headers.get("Authorizaton")
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
            "DestinationChannelCode": request.data.get("DestinationChannelCode"),
            "DestinationChannelName": request.data.get("DestinationChannelName"),
            "Currency": request.data.get("Currency", "KES"),
            "Amount": request.data.get("Amount"),
            "ReceiverPhoneNumber": request.data.get("ReceiverPhoneNumber"),
            "ReceiverAccountNumber": request.data.get("ReceiverAccountNumber"),
            "AccountReference": request.data.get("AccountReference"),
            "ReceiverAccountType": request.data.get("ReceiverAccountType"),
            "ReceiverAccountName": request.data.get("ReceiverAccountName"),
            "ForeignCurrency": request.data.get("ForeignCurrency"),
            "SenderPhoneNumber": request.data.get("SenderPhoneNumber"),
            "SenderName": request.data.get("SenderName"),
            "SenderDOB": request.data.get("SenderDOB"),
            "SenderCountryISO": request.data.get("SenderCountryISO"),
            "SenderNationality": request.data.get("SenderNationality"),
            "SenderIDType": request.data.get("SenderIDType"),
            "SenderIDNumber": request.data.get("SenderIDNumber"),
            "SenderServiceProviderName": request.data.get("SenderServiceProviderName"),
            "RemittancePurpose": request.data.get("RemittancePurpose"),
            "CallbackUrl": request.data.get("CallbackUrl"),
            "Remarks": request.data.get("Remarks")
        }  

        payload = {k: v for k, v in payload.items() if v is not None}

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            res_data = response.json()

            # --- Handle SasaPay error responses gracefully ---
            if not response.ok:
                return Response(
                    {
                        "status": False,
                        "message": "Remittance process failed",
                        "data": res_data
                    },
                    status=response.status_code
                )

            # --- Success ---
            return Response(
                {
                    "status": True,
                    "message": res_data.get("message", "Remittance processed successfully."),
                    "data": res_data
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "status": False,
                    "message": f"Remittance Request to SasaPay failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
