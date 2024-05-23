import datetime
import json
from bson import ObjectId, json_util
from django.shortcuts import render

from rest_framework.views import APIView
from Account.permissions import CustomIsAuthenticatedPermission
from Account.serializers import AdminVerifyOnUserRegistrationSerializer, ChangePasswordSerializer, UserRegistrationSerializer, UserLoginSerializer
from Account.signing_via_email import Eg002SigningViaEmailController
from rest_framework_simplejwt.tokens import RefreshToken # type: ignore
from rest_framework import status
from rest_framework.response import Response
from .models import UserMasterCollection

from django.contrib.auth.hashers import make_password
from pymongo.errors import DuplicateKeyError


# Genrate Token manually
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# login user
class loginAPIView(APIView):
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        if valid:
            status_code = status.HTTP_200_OK
            response = {
                'status': "Successful",
                'data': serializer.data,
                'message': 'User logged in successfully',
                "serviceName": "UserLogin_Service",
                "timeStamp": datetime.datetime.now().isoformat(),
                "code": status.HTTP_200_OK,
            }
            return Response(response, status=status_code)


# create user 
class UserRegistrationAPIView(APIView):
    def post(self, request):
        user_data = request.data
        try:
            # Get data from request
            serializer = UserRegistrationSerializer(data=user_data)
            if serializer.is_valid():
                dc_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # delete password2 from body
            del user_data['password2']
            user_data['password'] = make_password(user_data['password'])
            user_data["created_at"] = datetime.datetime.now()
            user_data["updated_at"] = datetime.datetime.now()
            # if apply admin then Do false
            user_data["IsActive"] = True

            # Create data in MongoDB
            result = UserMasterCollection.insert_one(user_data)
            response_data = {
                    "status": "Successful",
                    "document_id": str(result.inserted_id),
                    "message": "User created Successfully",
                    "serviceName": "UserRegistration_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_201_CREATED,
                    }
            return Response(response_data)
        
        except DuplicateKeyError:
            error_detail = "This email is already registered."
            return Response({'error': error_detail}, status=400)   


# Get user for admin verification
class GetUserAPIView(APIView):
    def get(self, request):
        id = request.query_params.get('id', None)
        if id is None:
            return Response({"error": "ID not Provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        userDetail = UserMasterCollection.find({'_id': ObjectId(id)})
        userDetailData = json.loads(json_util.dumps(userDetail))
        serializer_data = {
            "status": "Success",
            "data": userDetailData,
            "message": "User Data Retrieved Successfully",
            "serviceName": "GetUser_Service",
            "timeStamp": datetime.datetime.now().isoformat(),
            "code": status.HTTP_200_OK,
        }
        return Response(serializer_data)

# add Zone and true 
class UpdateUserAPIView(APIView):
    def post(self, request):
        user_data = request.data
        id = user_data['id']
        try:
            serializer = AdminVerifyOnUserRegistrationSerializer(data=user_data)
            if serializer.is_valid():
                dc_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # delete id from body
            del user_data['id']
            user_data['IsActive'] = True
            UserMasterCollection.update_one({"_id":  ObjectId(id)}, {"$set": user_data})
            
            response_data = {
                        "status": "Successful",
                        "message": "User Update Successfully",
                        "serviceName": "UpdateUser_Service",
                        "timeStamp": datetime.datetime.now().isoformat(),
                        "code": status.HTTP_200_OK,
                    }
            return Response(response_data)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordAPIView(APIView):
    permission_classes = [CustomIsAuthenticatedPermission]

    def post(self, request):
        user = request.customMongoUser
        try:
            serializer = ChangePasswordSerializer(data=request.data, context={'user': user})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            # new dataFrame
            newData = {}
            newData['password'] = make_password(str(request.data.get('password')))
            newData["updated_at"] = datetime.datetime.now()
            # update above data in users
            UserMasterCollection.update_one({'email': user['email']}, {'$set': newData})
            response_data = {
                    "status": "Successful",
                    "message": "Change Password Successfully",
                    "serviceName": "ChangePassword_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
            return Response(response_data)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        


# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from docusign_esign import EnvelopesApi, RecipientViewRequest, Document, Signer, EnvelopeDefinition, SignHere, Tabs, \
    Recipients, InPersonSigner
# from .serializers import EnvelopeSerializer


# consts.py
authentication_method = "email"  # Example authentication method
demo_docs_path = "/path/to/demo/docs"  # Example path to demo documents
pattern = None  # Example pattern (for pattern.sub("")) - define according to your needs


from docusign_esign import ApiClient
def create_api_client(base_path, access_token):
    api_client = ApiClient()
    api_client.host = base_path
    api_client.set_default_header("Authorization", f"Bearer {access_token}")
    return api_client

class CreateEnvelopeView(APIView):
    def post(self, request):
        args = {
            "base_path" : "https://demo.docusign.net",
            "access_token" : "8842f65d-951a-4531-8b22-9146dad8f661",
            "signer_email" : "pankaj.sajekar@alineahealthcare.in",
            "signer_name" : "pankaj sajekar",
        }
        Eg002SigningViaEmailController.worker(args=args)
        file_obj = request.FILES['file']
        # serializer = EnvelopeSerializer(data=request.data)
        # if serializer.is_valid():
        if True:
            # signer_name = serializer.validated_data['signer_name']
            signer_name = "Pankaj Sajekar"
            # Get authentication credentials
            account_id = "9926847e-9a52-42a2-9004-73a4053d1b15"
            base_path = "https://demo.docusign.net"
            access_token = "8842f65d-951a-4531-8b22-9146dad8f661"
            ds_return_url = request.build_absolute_uri("/ds/ds_return")

            # Create envelope arguments
            envelope_args = {
                "host_email": "pankaj.sajekar@alineahealthcare.in",  # Assuming you have user authentication
                "host_name": "pankaj",  # Assuming you have user authentication
                "signer_name": signer_name,
                "ds_return_url": ds_return_url,
            }

            # Create envelope
            envelope_definition = self.make_envelope(envelope_args)

            # Call Envelopes::create API method
            api_client = create_api_client(base_path=base_path, access_token=access_token)
            envelope_api = EnvelopesApi(api_client)
            results = envelope_api.create_envelope(account_id=account_id, envelope_definition=envelope_definition)
            envelope_id = results.envelope_id

            # Create the Recipient View request object
            recipient_view_request = RecipientViewRequest(
                authentication_method=authentication_method,
                recipient_id="1",
                return_url=ds_return_url,
                user_name=envelope_args["host_name"],
                email=envelope_args["host_email"]
            )

            # Obtain the recipient_view_url for the embedded signing session
            results = envelope_api.create_recipient_view(
                account_id=account_id,
                envelope_id=envelope_id,
                recipient_view_request=recipient_view_request
            )

            # Return signing URL
            return Response({"redirect_url": results.url}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
