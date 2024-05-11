from django.shortcuts import render
import pymongo
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from bson import ObjectId, json_util
import json
import datetime
import re
import requests  # type: ignore
import base64

from Account.models import UserMasterCollection
from Account.permissions import CustomIsAuthenticatedPermission, IsLegalUserPermission, IsNetworkUserPermission
from docusign.ds_jwt_auth import docusign_JWT_Auth
from docusign.envelope import docusign_create_and_send_envelope, docusign_get_Envelope_Documents, docusign_get_envelope_status
from providerApp.serializers import DCStatusChangeSerializer, EmpanelmentSerializer, SelfEmpanelmentSerializer, SelfEmpanelmentVerificationSerializer, SelfEmpanelmentVerificationbyLegalSerializer, docusignAgreementFileSerializer
from .models import neutron_collection, selfEmpanelment_collection, testName_collection

from rest_framework.permissions import IsAuthenticated
from pymongo.errors import DuplicateKeyError

from providerApp.tests import CreateDictsinList
# update in mongodb
def MongodbCRUD():
    # dictsinListData get from test.py
    dictsinListData = CreateDictsinList()
    # set filter and queary
    filter = {
        }
    queary = {
        "$set": {
           "availableTests" : dictsinListData
        },
    }

    try:
        result = testName_collection.insert_many(dictsinListData)
        # result = neutron_collection.update_many(filter, queary )
        print(result)
        return result
    except Exception:
        print("Exception : ", Exception)
# MongodbCRUD()


# basic authorization 
freshdesk_username = 'p8StXeOUFSoTHBrUyco'
freshdesk_password = 'X'
freshdesk_url = 'https://alineahealthcare.freshdesk.com/'

# Concatenate username and password with a colon
auth_string = f'{freshdesk_username}:{freshdesk_password}'
# Encode the auth string to base64
auth_encoded = base64.b64encode(auth_string.encode()).decode()

# Update Freshdesk Ticket update
def ticketStatusUpdate(ticket_id, ticket_status_code):
    try:
        url = f"{freshdesk_url}api/v2/tickets/{ticket_id}"
        # update status   
        body_data = {
            "status": ticket_status_code,
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_encoded}'
        }
        response = requests.put(url, json=body_data, headers=headers)
        res = response.json()
        if response.status_code == 200:
            response_data = {
                "status":  "Successful",
                "message":  "Ticket updated successfully!",
            }
        else:
            response_data = {
                "status":  res['code'],
                "message":  res['message'],
            }
    except requests.exceptions.RequestException as e:
        response_data = {
            "status": "Failed",
            "message": e,
        }
    print(response_data)
    return(response_data)
# ticketStatusUpdate(584387, 49)

# view Ticket 
def ViewTicketFunction(ticket_id):
    try:
        url = f"{freshdesk_url}api/v2/tickets/{ticket_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_encoded}'
        }
        response = requests.get(url, headers=headers)
        res = response.json()
        if response.status_code == 200:
           return response.json()
        else:
            response_data = {
                "status":  res['code'],
                "message":  res['message'],
            }
    except requests.exceptions.RequestException as e:
        response_data = {
            "status": "Failed",
            "message": e,
        }
    return response_data
# ViewTicketFunction(584387)
    

# Search in this fields [Pincode, Test Available] that documents show for API
class ADD_DC_APIIntegrations(APIView):
    def get(self, request, format=None):
        search_pincode_query = int(request.query_params.get('pincode'))
        search_tests_query = request.query_params.get('tests')
        if not search_pincode_query or not search_tests_query:
            return Response({"error": "Search term not provided"}, status=status.HTTP_400_BAD_REQUEST)

        if search_tests_query:
            tests_required = search_tests_query.replace(', ', ',').split(',')
        
        # Initialize the query dictionary
        query_conditions = []
        if search_pincode_query:
            query_conditions.append({"Pincode": search_pincode_query})

        if tests_required:
            # Convert transformations to regular expressions for case-insensitive matching
            regex_transformations = [re.compile(f'^{re.escape(transform)}$', re.IGNORECASE) for transform in tests_required]
            # Add condition for testDetails field
            test_details_condition = {"AvailableTest": {"$all": regex_transformations}}
            query_conditions.append(test_details_condition)

        # Combine all conditions using the $and operator
        query = {"$and": query_conditions}

        # Perform search using the constructed query
        cursor = neutron_collection.find(query).sort("Priority", pymongo.DESCENDING)

        # Convert MongoDB cursor to list of dictionaries
        # providerData = [json.loads(json_util.dumps(doc)) for doc in cursor]

        providerData = []
        for document in cursor:
            # Filter specific fields here
            filtered_data = {
                "DCID": document["DCID"],
                "DC Name": document["DC Name"],
                "Date of Empanelment": document["Date of Empanelment"],
                "Address": document["Address"],
                "State": document["State"],
                "City": document["City"],
                "Pincode": document["Pincode"],
                "E_Mail": document["E_Mail"],
                "Contact Person Name 1": document["Contact Person Name 1"],
                "Mobile number 1": document["Mobile number 1"],
                "AvailableTest": document["AvailableTest"],
                "Priority": document["Priority"],
            }
            providerData.append(filtered_data)

        # Prepare serializer data
        serializer_data = {
            "status": "Successful",
            "data": providerData,
            "message": "Result Found Successfully",
            "serviceName": "ADD_DC_APIIntegrations_Service",
            "timeStamp": datetime.datetime.now().isoformat(),
            "totalResult": len(providerData),
            "code": status.HTTP_200_OK,
        }
        # Return the search results
        return Response(serializer_data)
    

# Search in this fields q params [DCID, Pincode, DC Name, City] and t params [AvailableTest]. where that data matched that documents (records) will show
class SearchDCAPIView(APIView):
    permission_classes = [CustomIsAuthenticatedPermission]

    def post(self, request, format=None):
        try:
            data = json.loads(request.body) 
            # Access the value of the 't' key
            search_query_inputstring = data.get('q', None)
            search_tests_inputstring = data.get('t', [])
            # search_query_inputstring = request.query_params.get('q', None)
            # search_tests_inputstring = request.query_params.get('t', None)
            
            # Clean and split search queries
            # search_query_list = [int(i) if i.isdigit() else i for i in search_query_inputstring.replace(', ', ',').split(',')]
            search_query_list = [int(i) if i.isdigit() else i for i in re.split(r',\s*|\s*,\s*|\s+', search_query_inputstring) ]

            # Clean and split Tests inpute
            search_tests_inputstring = [ int(d['item_value']) for d in search_tests_inputstring]
            # if search_tests_inputstring:
                # tests_required = search_tests_inputstring.replace(', ', ',').split(',')
                # tests_required = re.split(r',\s*|\s*,\s*|\s+', search_tests_inputstring)

            # Get pagination parameters
            # page_number = int(request.query_params.get('page', 1))
            # page_size = int(request.query_params.get('page_size', 8))

            if search_query_inputstring is None or (search_query_inputstring == '' and search_tests_inputstring == []):
                return Response({"error": "Search term not provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize the query dictionary
            query_conditions = []

            # Iterate over the search data list
            for item in search_query_list:
                if isinstance(item, int):
                    # For integer values, construct query conditions for numeric fields
                    query_conditions.append({"$or": [{"DCID": item}, {"Pincode": item} ]})
                elif isinstance(item, str):
                    # For string values, construct query conditions for string fields
                    query_conditions.append({"$or": [
                        {"DC Name": {"$regex": item, "$options": "i"}},
                        {"City":{"$regex": "^" + re.escape(item), "$options": "i"}},  # (like operator '^') item match should starting not
                        {"State": {"$regex": "^" + re.escape(item), "$options": "i"}},
                        {"DC Registration No": {"$regex": item, "$options": "i"}},
                        {"Accreditation Type": {"$regex": item, "$options": "i"}},
                    ]})

            if search_tests_inputstring:
                # Convert transformations to regular expressions for case-insensitive matching
                # regex_transformations = [re.compile(f'^{re.escape(transform)}$', re.IGNORECASE) for transform in tests_required]
                # test_details_condition = {"AvailableTest": {"$elemMatch": { "$all": regex_transformations}} }
                # Add condition for testDetails field
                # test_details_condition = {"AvailableTestCode": { "$all": search_tests_inputstring}}  # now search like  eg. [ { "item_value": "100001", "item_label": "2 D Echocardiography" } ]
                test_details_condition = {"availableTests": {
                        "$all": [{"$elemMatch": {"item_Standard_Code": val}} for val in search_tests_inputstring]
                    }}   # test_details_condition = {'AvailableTestCode': {'$all': [{'$elemMatch': {'item_value': '100001'}}, {'$elemMatch': {'item_value': '100002'}}]}} and it return value. input comes in " search_tests_inputstring = ["100001", "100002"] "
                query_conditions.append(test_details_condition)

            # Combine all conditions using the $and operator
            query = {"$and": query_conditions}

            # Perform search using the constructed query
            cursor = neutron_collection.find(query).sort("Priority", pymongo.DESCENDING)
            
            # Convert MongoDB cursor to list of dictionaries
            # providerData = [json.loads(json_util.dumps(doc)) for doc in cursor]
            
            providerData = []
            for document in cursor:
                # Filter specific fields here
                filtered_data = {
                    "DCID": document["DCID"],
                    "DC Name": document["DC Name"],
                    "Date of Empanelment": document["Date of Empanelment"],
                    "Address": document["Address"],
                    "State": document["State"],
                    "City": document["City"],
                    "Pincode": document["Pincode"],
                    "E_Mail": document["E_Mail"],
                    "Contact Person Name 1": document["Contact Person Name 1"],
                    "Mobile number 1": document["Mobile number 1"],
                    "Accreditation Type": document["Accreditation Type"],
                    "DC Registration No": document["DC Registration No"],
                    "Home Visit Facility": document["Home Visit Facility"],
                    "VisitFacility": document["VisitFacility"],
                }
                providerData.append(filtered_data)

            # Get the total count of results
            total_results = len(providerData)

            # Calculate the total number of pages
            # total_pages = (total_results + page_size - 1) // page_size

            # Paginate the results
            # providerData = providerData[(page_number - 1) * page_size: page_number * page_size]
            if len(providerData) == 0:
                serializer_data = {
                    "status": "Successful",
                    "message": "The requested resource was not found",
                    "serviceName": "DCSearchService_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_404_NOT_FOUND,
                }
                return Response(serializer_data)

            # Prepare serializer data
            serializer_data = {
                "status": "Successful",
                "data": providerData,
                "message": "Result Found Successfully",
                "serviceName": "DCSearchService_Service",
                "timeStamp": datetime.datetime.now().isoformat(),
                # "page": page_number,
                # "totalPages": total_pages,
                "totalResult": total_results,
                # "noOfResult": len(providerData),
                "code": status.HTTP_200_OK,
            }

            # Add previous and next URLs
            # if page_number > 1:
            #     serializer_data["previous"] = request.build_absolute_uri(request.path_info + f"?q={search_query_inputstring}&t={search_tests_inputstring}&page={page_number - 1}&page_size={page_size}")
            # if page_number < int(total_pages):
            #     serializer_data["next"] = request.build_absolute_uri(request.path_info + f"?q={search_query_inputstring}&t={search_tests_inputstring}&page={page_number + 1}&page_size={page_size}")

            # Return the search results
            return Response(serializer_data)
        
        except Exception as e:
            serializer_data = {
                "status": "Error",
                "error": str(e),
                "message": "Something went to wrong",
                "serviceName": "DCSearchService_Service",
                "timeStamp": datetime.datetime.now().isoformat(),
                "code": 500,
            }
            return Response(serializer_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Dc Analytics API
class DCAnalyticsAPIView(APIView):
    def get(self, request, formate=None):
        
        dc_status_activate_count = neutron_collection.count_documents({'DCStatus': 'activate'})
        dc_status_deactivate_count = neutron_collection.count_documents({'DCStatus': 'deactivate'})
        dc_status_delist_count = neutron_collection.count_documents({'DCStatus': 'delist'})

        response_data = {
            'activateDC' : dc_status_activate_count,
            'deactivateDC' : dc_status_deactivate_count,
            'delistDC' : dc_status_delist_count,
        }

        serializer_data = {
            "status": "Success",
            "data": response_data,
            "message": "DC analytics Retrieved Successfully",
            "serviceName": "DCAnalytics_Service",
            "timeStamp": datetime.datetime.now().isoformat(),
            "code": status.HTTP_200_OK,
        }
        return Response(serializer_data)



# Get Dc documents in Details
class DCDetailAPIView(APIView):
    def get(self, request, formate=None):
        dcID_query = int(request.query_params.get('dc', None))
        if dcID_query is None:
            return Response({"error": "DC Details not provided"}, status=status.HTTP_400_BAD_REQUEST)
         
        # count no of documents return 404
        dc_count = neutron_collection.count_documents({'DCID': dcID_query })
        if dc_count == 0:
            return Response({"error": "No DC Details found for the provided ID"}, status=status.HTTP_404_NOT_FOUND)
        
        dcDetail = neutron_collection.find({'DCID': dcID_query })
        dcDetailData = json.loads(json_util.dumps(dcDetail))
        serializer_data = {
            "status": "Success",
            "data": dcDetailData,
            "message": "DC Details Retrieved Successfully",
            "serviceName": "DCDetails_Service",
            "timeStamp": datetime.datetime.now().isoformat(),
            "code": status.HTTP_200_OK,
        }
        return Response(serializer_data)

# Update DC
class DCUpdateAPIView(APIView):
    def put(self, request):
        data = request.data
        try:
            empanelmentID_query = request.query_params.get('id')
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)
            result = neutron_collection.replace_one({'_id': ObjectId(empanelmentID_query)}, data)
            if result.modified_count == 1:
                response_data = {
                        "status": "Successful",
                        "message": "Document Full Update Successfully",
                        "serviceName": "EmpanelmentUpdate_Service",
                        "timeStamp": datetime.datetime.now().isoformat(),
                        "code": status.HTTP_200_OK,
                        }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found or not modified'}, status=404)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request):
        data = request.data
        try:
            empanelmentID_query = request.query_params.get('id')
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)
            result = neutron_collection.update_one({'_id': ObjectId(empanelmentID_query)}, {'$set': data})
            if result.modified_count == 1:
                response_data = {
                        "status": "Successful",
                        "message": "Document Partial Update Successfully",
                        "serviceName": "EmpanelmentUpdate_Service",
                        "timeStamp": datetime.datetime.now().isoformat(),
                        "code": status.HTTP_200_OK,
                        }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found or not modified'}, status=404)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# empanelment
class EmpanelmentCreateAPIView(APIView):
    def post(self, request):
        try:
            # Get data from request
            serializer = EmpanelmentSerializer(data=request.data)
            if serializer.is_valid():
                dc_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
            # Create data in MongoDB
            result = selfEmpanelment_collection.insert_one(request.data)
            response_data = {
                    "status": "Successful",
                    "document_id": str(result.inserted_id),
                    "message": "Document created Successfully",
                    "serviceName": "EmpanelmentCreate_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_201_CREATED,
                    }
            return Response(response_data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# Verify view get data 
class selfEmpanelmentDetailAPIView(APIView):
    def post(self, request):
        try:
            empanelmentID_query = request.data['id']
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)

            document = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID_query) })

            providerData = {
                        "providerName": document.get("providerName", ""),
                        "FirmType": document.get("FirmType", ""),
                        "PanCard_number" : document.get("PanCard_number", ""),
                        "nameOnPanCard" : document.get("nameOnPanCard", ""),
                        "Adhar_number" : document.get("Adhar_number", ""),
                        "Adhar_name" : document.get("Adhar_name", ""),
                        "Accredation" : document.get("Accredation", ""),
                    }
            
            # Check if image fields exist before accessing
            # image_fields = ['pan_image', 'aadhar_image', 'Accreditation_image', 'Registration_Number_image', 'Ownership_image', 'TDS_image']
            image_fields = ['pan_image', 'aadhar_image','Accreditation_image','Current_Bank_Statement_image','Shop_Establishment_Certificate_image','Authority_Letter_image', 'LLP_Partnership_Agreement_image', 'stamp_paper_image']
            for field in image_fields:
                if field in document:
                    providerData[field] = base64.b64encode(document[field]).decode('utf-8')
                else:
                    providerData[field] = "" 

            # gives data if user have verified document status
            documentVerifiedStatusByNetwork = {}
            if "verifiedByNetworkDate" in document:
                verified_document_list = ['isPanVerified', "isAadharVerified", "isAccreditationVerified" , "isCurrentBankStatementVerified", "isEstablishmentCertificateVerified",  'isAuthorityLetterVerfied', 'isStampPaperVerified', 'isPartnershipAgreementVerfied']
                for field in verified_document_list:
                    if field in document:
                        documentVerifiedStatusByNetwork[field] = document[field]
                    else:
                        documentVerifiedStatusByNetwork[field] = False
                providerData['documentVerifiedStatus'] = documentVerifiedStatusByNetwork

            if document:
                response_data = {
                    "status": "Successful",
                    "data": providerData,
                    # "data": json.loads(json_util.dumps(document)),
                    "message": "Document Found Successfully",
                    "serviceName": "selfEmpanelmentDetails_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found'}, status=404)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class selfEmpanelmentDetailForLegalAPIView(APIView):
    def post(self, request):
        try:
            empanelmentID_query = request.data['id']
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)

            document = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID_query) })
            _user = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})
            providerData = {
                        "providerName": document.get("providerName", ""),
                        "FirmType": document.get("FirmType", ""),
                        "PanCard_number" : document.get("PanCard_number", ""),
                        "nameOnPanCard" : document.get("nameOnPanCard", ""),
                        "Adhar_number" : document.get("Adhar_number", ""),
                        "Adhar_name" : document.get("Adhar_name", ""),
                        "Accredation" : document.get("Accredation", ""),
                        "verifiedByNetworkUser": {"name": _user['name'], "email": _user['email']},  # give only id
                        "DCVerificationStatus": document.get("DCVerificationStatus", ""),
                    }
            if "verifiedByNetworkDate" in document:
                providerData['verifiedByNetworkDate'] = document['verifiedByNetworkDate']
            
            # Check if image fields exist before accessing
            image_fields = ['pan_image', 'aadhar_image','Accreditation_image','Current_Bank_Statement_image','Shop_Establishment_Certificate_image','Authority_Letter_image', 'LLP_Partnership_Agreement_image', 'stamp_paper_image']
            for field in image_fields:
                if field in document:
                    providerData[field] = base64.b64encode(document[field]).decode('utf-8')
                else:
                    providerData[field] = "" 

            
            # gives data if user have verified document status
            documentVerifiedStatusBylegal = {}
            if "verifiedByNetworkDate" in document:
                verified_document_list = ['isPanVerified', "isAadharVerified", "isAccreditationVerified" , "isCurrentBankStatementVerified", "isEstablishmentCertificateVerified",  'isAuthorityLetterVerfied', 'isStampPaperVerified', 'isPartnershipAgreementVerfied']
                for field in verified_document_list:
                    if field in document:
                        documentVerifiedStatusBylegal[field] = document[field]
                    else:
                        documentVerifiedStatusBylegal[field] = False
                providerData['documentVerifiedStatus'] = documentVerifiedStatusBylegal

            if document:
                response_data = {
                    "status": "Successful",
                    "data": providerData,
                    # "data": json.loads(json_util.dumps(document)),
                    "message": "Document Found Successfully",
                    "serviceName": "selfEmpanelmentDetailForLegal_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found'}, status=404)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class EmpanelmentDeleteAPIView(APIView):
    def delete(self, request):
        try:
            empanelmentID_query = request.query_params.get('id')
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)

            document = selfEmpanelment_collection.delete_one({'_id': ObjectId(empanelmentID_query) })

            if document.deleted_count == 1:
                response_data = {
                    "status": "Successful",
                    "message": "Document Delete Successfully",
                    "serviceName": "EmpanelmentDelete_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found'}, status=404)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 

# for network team role 1
class SelfEmpanelmentSelect(APIView):
    permission_classes = [CustomIsAuthenticatedPermission, IsNetworkUserPermission]

    def get(self, request):
        _user = request.customMongoUser
        user_zone  = _user['zone']
        
        filter_query_by_user = "DCVerificationStatus"

        cursor = selfEmpanelment_collection.find({"zone": user_zone})
        # total_selfEmpanelment = selfEmpanelment_collection.count_documents({filter_query_by_user: { '$exists': True}})
        total_selfEmpanelment_pending_cursor = selfEmpanelment_collection.find({filter_query_by_user: { '$exists': True},  filter_query_by_user: "pending", "zone": user_zone })
        total_selfEmpanelment_verify_cursor = selfEmpanelment_collection.find({filter_query_by_user: { '$exists': True}, filter_query_by_user: "verify", "zone": user_zone })
        total_selfEmpanelment_partialVerify_cursor = selfEmpanelment_collection.find({filter_query_by_user: { '$exists': True}, filter_query_by_user: "partialVerify", "zone": user_zone })
        
        total_selfEmpanelment_pending_list = []
        for document in total_selfEmpanelment_pending_cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
                "pincode": document["pincode"],
                "address": document["address1"],
            }
            if 'verifiedByNetworkUser' in document:
                filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            if 'updated_at' in document:
                filtered_data["updated_at"] = document['updated_at']
            if 'verifiedByNetworkDate' in document:
                filtered_data["verifiedByNetworkDate"] = document['verifiedByNetworkDate']
            total_selfEmpanelment_pending_list.append(filtered_data)
        total_selfEmpanelment_verify_list = []
        for document in total_selfEmpanelment_verify_cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
                "pincode": document["pincode"],
                "address": document["address1"],
            }
            if 'verifiedByNetworkUser' in document:
                filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            if 'updated_at' in document:
                filtered_data["updated_at"] = document['updated_at']
            if 'verifiedByNetworkDate' in document:
                filtered_data["verifiedByNetworkDate"] = document['verifiedByNetworkDate']
            total_selfEmpanelment_verify_list.append(filtered_data)
        total_selfEmpanelment_partialVerify_list = []
        for document in total_selfEmpanelment_partialVerify_cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
                "pincode": document["pincode"],
                "address": document["address1"],
            }
            if 'verifiedByNetworkUser' in document:
                filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            if 'updated_at' in document:
                filtered_data["updated_at"] = document['updated_at']
            if 'verifiedByNetworkDate' in document:
                filtered_data["verifiedByNetworkDate"] = document['verifiedByNetworkDate']
            total_selfEmpanelment_partialVerify_list.append(filtered_data)

        network_analytics = {
            # "total" : total_selfEmpanelment,
            "pending" : total_selfEmpanelment_pending_list,
            "verify" : total_selfEmpanelment_verify_list,
            "partialVerify": total_selfEmpanelment_partialVerify_list, 
        }
        providerData = []
        for document in cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
            }
            if 'verifiedByNetworkUser' in document:
                filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            providerData.append(filtered_data)

        response={
            "selectDropdown": providerData,
            "networkAnalyticsData": network_analytics
        }
        return Response(response)
    
# 
class SelfEmpanelmentSelectForLegal(APIView):
    permission_classes = [CustomIsAuthenticatedPermission, IsLegalUserPermission]

    def get(self, request):
        _user = request.customMongoUser
        user_zone =  _user['zone'] 
        # if _user['role'] == 1:
        #     filter_query_by_user = "DCVerificationStatus"
        # else:
        #     filter_query_by_user = "DCVerificationStatusByLegal"

        filter_query_by_user = "DCVerificationStatusByLegal"

        cursor = selfEmpanelment_collection.find({filter_query_by_user: { '$exists': True}, "DCVerificationStatus": "verify",})
        # total_selfEmpanelment = selfEmpanelment_collection.count_documents({filter_query_by_user: { '$exists': True}})
        total_selfEmpanelment_pending_cursor = selfEmpanelment_collection.find({filter_query_by_user: { '$exists': True},  filter_query_by_user: "pending", "DCVerificationStatus": "verify", })
        total_selfEmpanelment_verify_cursor = selfEmpanelment_collection.find({filter_query_by_user: { '$exists': True}, filter_query_by_user: "verify", "DCVerificationStatus": "verify", })
        total_selfEmpanelment_partialVerify_cursor = selfEmpanelment_collection.find({filter_query_by_user: { '$exists': True}, filter_query_by_user: "partialVerify", "DCVerificationStatus": "verify",  })
        
        total_selfEmpanelment_pending_list = []
        for document in total_selfEmpanelment_pending_cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
                "pincode": document["pincode"],
                "address": document["address1"],
            }
            if 'verifiedByNetworkUser' in document:
                filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            if 'updated_at' in document:
                filtered_data["updated_at"] = document['updated_at']
            if 'verifiedByNetworkDate' in document:
                filtered_data["verifiedByNetworkDate"] = document['verifiedByNetworkDate']
            total_selfEmpanelment_pending_list.append(filtered_data)
        total_selfEmpanelment_verify_list = []
        for document in total_selfEmpanelment_verify_cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
                "pincode": document["pincode"],
                "address": document["address1"],
            }
            
            if 'verifiedByNetworkDate' in document:
                filtered_data["verifiedByNetworkDate"] = document['verifiedByNetworkDate']
            if 'verifiedByNetworkUser' in document:
                    filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            if 'verifiedByLegalDate' in document:
                filtered_data["verifiedByLegalDate"] = document['verifiedByLegalDate']
            if 'verifiedByLegalUser' in document:
                filtered_data["verifiedByLegalUser"] = UserMasterCollection.find_one({"_id":document["verifiedByLegalUser"]})['name']
            if 'updated_at' in document:
                filtered_data["updated_at"] = document['updated_at']

            if 'ds_envelope_status' in document:
                filtered_data["ds_envelope_status"] = document['ds_envelope_status']
            if 'ds_envelope_envelopeId' in document:
                filtered_data["ds_envelope_envelopeId"] = document['ds_envelope_envelopeId']

            total_selfEmpanelment_verify_list.append(filtered_data)
        total_selfEmpanelment_partialVerify_list = []
        for document in total_selfEmpanelment_partialVerify_cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
                "pincode": document["pincode"],
                "address": document["address1"],
            }
            if 'verifiedByNetworkDate' in document:
                filtered_data["verifiedByNetworkDate"] = document['verifiedByNetworkDate']
            if 'verifiedByNetworkUser' in document:
                filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            if 'verifiedByLegalDate' in document:
                filtered_data["verifiedByLegalDate"] = document['verifiedByLegalDate']
            if 'verifiedByLegalUser' in document:
                filtered_data["verifiedByLegalUser"] = UserMasterCollection.find_one({"_id":document["verifiedByLegalUser"]})['name']
            
            if 'updated_at' in document:
                filtered_data["updated_at"] = document['updated_at']
            total_selfEmpanelment_partialVerify_list.append(filtered_data)

        network_analytics = {
            # "total" : total_selfEmpanelment,
            "pending" : total_selfEmpanelment_pending_list,
            "verify" : total_selfEmpanelment_verify_list,
            "partialVerify": total_selfEmpanelment_partialVerify_list, 
        }
        providerData = []
        for document in cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
            }
            if 'verifiedByNetworkUser' in document:
                filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            providerData.append(filtered_data)

        response={
            "selectDropdown": providerData,
            "networkAnalyticsData": network_analytics
        }
        return Response(response)
    

#  list self empanelment in docusign after legal verifed
class SelfEmpanelmentSelectForDocusign(APIView):
    permission_classes = [CustomIsAuthenticatedPermission, IsLegalUserPermission]

    def get(self, request):
        _user = request.customMongoUser
        user_zone =  _user['zone'] 
        # if _user['role'] == 1:
        #     filter_query_by_user = "DCVerificationStatus"
        # else:
        #     filter_query_by_user = "DCVerificationStatusByLegal"

        # after legal verified (field name)
        filter_query_by_user = "DCVerificationStatusByLegal"

        total_selfEmpanelment_verify_cursor = selfEmpanelment_collection.find({filter_query_by_user: { '$exists': True}, "DCVerificationStatusByLegal": "verify", "DCVerificationStatus": "verify", "zone": user_zone })
        
        total_selfEmpanelment_verify_list = []
        for document in total_selfEmpanelment_verify_cursor:
            # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
                "DCID": document["DCID"],
                "pincode": document["pincode"],
                "address": document["address1"],
            }
            
            if 'verifiedByNetworkDate' in document:
                filtered_data["verifiedByNetworkDate"] = document['verifiedByNetworkDate']
            if 'verifiedByNetworkUser' in document:
                filtered_data["verifiedByNetworkUser"] = UserMasterCollection.find_one({"_id":document["verifiedByNetworkUser"]})['name']
            if 'verifiedByLegalDate' in document:
                filtered_data["verifiedByLegalDate"] = document['verifiedByLegalDate']
            if 'verifiedByLegalUser' in document:
                filtered_data["verifiedByLegalUser"] = UserMasterCollection.find_one({"_id":document["verifiedByLegalUser"]})['name']
            if 'updated_at' in document:
                filtered_data["updated_at"] = document['updated_at']
            total_selfEmpanelment_verify_list.append(filtered_data)
        
        response={
            "selectDropdown": total_selfEmpanelment_verify_list,
        }
        return Response(response)


class SelfEmpanelmentVerificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        _user = request.customMongoUser
        form_data=request.data
        try: 
            serializer = SelfEmpanelmentVerificationSerializer(data=form_data)
            if serializer.is_valid():
                serializer_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            empanelmentID_query = form_data['id']
            
            # get data
            getDocuments = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID_query)})
            # removes id data
            del form_data['id']
            form_data['verifiedByNetworkUser'] = _user['_id']
            form_data['verifiedByNetworkDate'] = datetime.datetime.now()
            data = {
                "verificationRemark" : form_data['verificationRemark'],
                "DCVerificationStatus" : form_data['DCVerificationStatus'],
                "isPanVerify": form_data['isPanVerify'],
            }    
            # update data in existing documents                            
            selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID_query) }, {'$set': form_data} )
            ticket_id = getDocuments['TicketID']
            if form_data['DCVerificationStatus'] == 'verify':
                # verify
                # 50 Forwarded to legal after QC1
                ticket_status_code = 50
            elif form_data['DCVerificationStatus'] == 'partialVerify':
                # partial verify
	            # 52 Issue In Document
                ticket_status_code = 52

            ticketStatusUpdate(ticket_id, ticket_status_code)

            if getDocuments:
                response_data = {
                    "status": "Successful",
                    "data": json.loads(json_util.dumps(getDocuments)),
                    "message": "Document Found Successfully",
                    "serviceName": "SelfEmpanelmentVerification_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found'}, status=404)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class SelfEmpanelmentVerificationByLegalAPIView(APIView):
    def post(self, request, *args, **kwargs):
        _user = request.customMongoUser
        form_data=request.data
        try: 
            serializer = SelfEmpanelmentVerificationbyLegalSerializer(data=form_data)
            if serializer.is_valid():
                serializer_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            empanelmentID_query = form_data['id']
            
            # get data
            getDocuments = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID_query)})
            form_data['verifiedByLegalUser'] = _user['_id']
            form_data['verifiedByLegalDate'] = datetime.datetime.now()
            form_data['ds_envelope_status'] = ['waiting']
            del form_data['id']
            print("form_data", form_data)   
            # update data in existing documents                            
            selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID_query) }, {'$set': form_data} )
            ticket_id = getDocuments['TicketID']
            if form_data['DCVerificationStatusByLegal'] == 'verify':
                # verify
	            # 51 Document verified by legal
                ticket_status_code = 51
            else:
                # partial verify
	            # 52 Issue In Document
                ticket_status_code = 52

            ticketStatusUpdate(ticket_id, ticket_status_code)

            if getDocuments:
                response_data = {
                    "status": "Successful",
                    "data": json.loads(json_util.dumps(getDocuments)),
                    "message": "Document Found Successfully",
                    "serviceName": "SelfEmpanelmentVerificationByLegal_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found'}, status=404)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# self empanelment for dc verifycation    
class SelfEmpanelmentList(APIView):
    def get(self, request):
        cursor = selfEmpanelment_collection.find()
        providerData = []
        for document in cursor:
                # Filter specific fields here
                filtered_data = {
                    "_id": str(document["_id"]),
                    "providerName": document["providerName"],
                    "pan_image": base64.b64encode(document['pan_image']).decode('utf-8'),
                }
                providerData.append(filtered_data)

        if providerData:
                response_data = {
                    "status": "Successful",
                    "data": providerData,
                    "message": "Document Found Successfully",
                    "serviceName": "SelfEmpanelmentList_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
                return Response(response_data)
        else:
                return Response({'error': 'Document not found'}, status=404)
    

class SelfEmpanelmentAPIView(APIView):
    def get(self, request, formate=None):
        dcID_query = int(request.query_params.get('dc', None))
        if dcID_query is None:
            return Response({"error": "DC Details not provided"}, status=status.HTTP_400_BAD_REQUEST)
         
        # count no of documents return 404
        dc_count = selfEmpanelment_collection.count_documents({'DCID': dcID_query })
        if dc_count == 0:
            return Response({"error": "No DC Details found for the provided ID"}, status=status.HTTP_404_NOT_FOUND)
        
        dcDetail = selfEmpanelment_collection.find({'DCID': dcID_query })
        dcDetailData = json.loads(json_util.dumps(dcDetail))
        serializer_data = {
            "status": "Success",
            "data": dcDetailData,
            "message": "DC Details Retrieved Successfully",
            "serviceName": "SelfEmpanelment_Service",
            "timeStamp": datetime.datetime.now().isoformat(),
            "code": status.HTTP_200_OK,
        }
        return Response(serializer_data)

class SelfEmpanelmentUpdateAPIView(APIView):
    def patch(self, request):
        data = request.data
        try:
            empanelmentID_query = request.query_params.get('id')
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)
            result = selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID_query)}, {'$set': data})
            if result.modified_count == 1:
                response_data = {
                        "status": "Successful",
                        "message": "Document Partial Update Successfully",
                        "serviceName": "SelfEmpanelmentUpdate_Service",
                        "timeStamp": datetime.datetime.now().isoformat(),
                        "code": status.HTTP_200_OK,
                        }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found or not modified'}, status=404)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
# testing
class FileUploadView(APIView):
    def post(self, request, format=None):
        try:
            form_data = request.data.copy()
            # Get data from request
            # serializer = SelfEmpanelmentSerializer(data=form_data)
            # if serializer.is_valid():
            #     dc_data = serializer.data
            # else:
            #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            pan_image = form_data.get('pan_image')
            dcname = form_data.get('dcName')
            pan_number = form_data.get('pan_number')
            aadhar_number = form_data.get('aadhar_number')
            # Check if file was provided
            if not pan_image:
                return Response({'error': 'Pan image is required'}, status=400)
            # Store file and additional data in MongoDB
            data = {
                'dcname': dcname,
                'pan_number': pan_number,
                'aadhar_number': aadhar_number,
                'pan_image': pan_image.read()
            }
            # print(data)
            result = selfEmpanelment_collection.insert_one(data)
            response_data = {
                        "status": "Successful",
                        "document_id": str(result.inserted_id),
                        "message": "testing created Successfully",
                        "serviceName": "FileUploadView_Service",
                        "timeStamp": datetime.datetime.now().isoformat(),
                        "code": 201,
                        }
            print(response_data)
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# SelfEmpanelment
class SelfEmpanelmentCreateAPIView(APIView):
    def post(self, request, id=None, *args, **kwargs):
        ticketId_from_url = id
        print("------", id, request.data )
        if ticketId_from_url == None:
            return Response({"error": "FreshDesk Ticket id Faild"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            form_data=request.data
            ticketDetails = ViewTicketFunction(ticketId_from_url)
            dc_zone_from_ticket = ticketDetails['custom_fields']['cf_select_your_zone']
            serializer = SelfEmpanelmentSerializer(data=form_data)
            if serializer.is_valid():
                dc_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            print(dc_zone_from_ticket, form_data)
            FirmType = form_data.get('FirmType')
            providerName = form_data.get('providerName')
            providerType = form_data.get('providerType')
            DC_Chain = form_data.get('DC_Chain')
            Regi_number = form_data.get('Regi_number')
            Inception = form_data.get('Inception')
            Owner_name = form_data.get('Owner_name')
            PanCard_number = form_data.get('PanCard_number')
            nameOnPanCard = form_data.get('nameOnPanCard')
            Adhar_number = form_data.get('Adhar_number')
            Adhar_name = form_data.get('Adhar_name')
            Owner_name_asper_document = form_data.get('Owner_name_asper_document')
            Center_name = form_data.get('Center_name')
            Accredation = form_data.get('Accredation')
            address1 = form_data.get('address1')
            address2 = form_data.get('address2')
            state = form_data.get('state')
            city = form_data.get('city')
            pincode = form_data.get('pincode')
            emailId = form_data.get('emailId')
            emailId2 = form_data.get('emailId2')
            Cantact_person1 = form_data.get('Cantact_person1')
            Cantact_person2 = form_data.get('Cantact_person2')
            fax = form_data.get('fax')
            accountNumber = form_data.get('accountNumber')
            accountName = form_data.get('accountName')
            bankName = form_data.get('bankName')
            ifscCode = form_data.get('ifscCode')
            branchName = form_data.get('branchName')
            accountType = form_data.get('accountType')
            
            availableTests = form_data.get('availableTests')

            Opthlmologya = form_data.get('Opthlmologya')
            MBBS_PHYSICIAN = form_data.get('MBBS_PHYSICIAN')
            GYNECOLOGY = form_data.get('GYNECOLOGY')
            OPHTHALMOLOGY = form_data.get('OPHTHALMOLOGY')
            MD_RADIOLOGIST = form_data.get('MD_RADIOLOGIST')
            
            CARDIOLOGY_OUTSOURCED_CENTRE = form_data.get('CARDIOLOGY_OUTSOURCED_CENTRE')
            PATHOLOGY_OUTSOURCED_CENTR = form_data.get('PATHOLOGY_OUTSOURCED_CENTR')

            data = {
                'TicketID': str(ticketId_from_url),
                'DCID': str(ticketId_from_url),
                'providerName': providerName,
                'providerType': providerType,
                'DC_Chain': DC_Chain,
                'Regi_number': Regi_number,
                'Inception': Inception,
                'Owner_name': Owner_name,
                'PanCard_number': PanCard_number,
                'nameOnPanCard': nameOnPanCard,
                'Adhar_number': Adhar_number,
                'Adhar_name': Adhar_name,
                'Owner_name_asper_document': Owner_name_asper_document,
                'Center_name': Center_name,
                'Accredation': Accredation,
                'address1': address1,
                'address2': address2,
                'state': state,
                'city': city,
                'pincode': pincode,
                'zone': dc_zone_from_ticket,  # set zone from ticket
                'emailId': emailId,
                'emailId2': emailId2,
                'Cantact_person1': Cantact_person1,
                'Cantact_person2': Cantact_person2,
                'fax': fax,
                'accountNumber': accountNumber,
                'accountName': accountName,
                'bankName': bankName,
                'ifscCode': ifscCode,
                'branchName': branchName,
                'accountType': accountType,
        
                'Opthlmologya': Opthlmologya,
                'MBBS_PHYSICIAN': MBBS_PHYSICIAN,
                'GYNECOLOGY': GYNECOLOGY,
                'OPHTHALMOLOGY': OPHTHALMOLOGY,
                'MD_RADIOLOGIST': MD_RADIOLOGIST,

                'availableTests': availableTests,

                'CARDIOLOGY_OUTSOURCED_CENTRE': CARDIOLOGY_OUTSOURCED_CENTRE,
                'PATHOLOGY_OUTSOURCED_CENTR': PATHOLOGY_OUTSOURCED_CENTR,
                'FirmType': FirmType,
            }

            # Check if image fields exist before accessing
            image_fields = ['pan_image', 'aadhar_image','Accreditation_image','Current_Bank_Statement_image','Shop_Establishment_Certificate_image','Authority_Letter_image', 'LLP_Partnership_Agreement_image', 'stamp_paper_image']
            for field in image_fields:
                if field in form_data:
                    data[field] = form_data.get(field).read()
                else:
                    pass
                    # data[field] = None
            
            data['DCVerificationStatus'] = 'pending'
            data['DCVerificationStatusByLegal'] = 'pending'
            data["created_at"] = datetime.datetime.now()
            data["updated_at"] = datetime.datetime.now()
            # Create data in MongoDB
            result = selfEmpanelment_collection.insert_one(data)
            # change the status in freshdesk
            # 49 = submited to DC
            ticketStatusUpdate(ticketId_from_url, 49)
            response_data = {
                    "status": "Successful",
                    "document_id": str(result.inserted_id),
                    "message": "Self Empanelment document created Successfully",
                    "serviceName": "SelfEmpanelmentCreate_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_201_CREATED,
                    }
            return Response(response_data)
        
        except DuplicateKeyError:
            error_detail = "Duplicate key error: This Ticket is already Exits."
            return Response({'error': error_detail}, status=400) 
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Dc Chanage Status Activate and deactivate, delist
class DCStatusChangeAPIView(APIView):
    def post(self, request):
        fromdata = request.data
        try:
            DCStatusChangeSerializer(data=fromdata).is_valid()
            dcID_query = int(request.query_params.get('dc', None))
            if dcID_query is None:
                return Response({"error": "DC Details not provided"}, status=status.HTTP_400_BAD_REQUEST)
            # count no of documents return 404
            dc_count = neutron_collection.count_documents({'DCID': dcID_query })
            print(dc_count)
            if dc_count == 0:
                return Response({"error": "No DC Details found for the provided ID"}, status=status.HTTP_404_NOT_FOUND)
            document = neutron_collection.update_one({'DCID': dcID_query}, {'$set': fromdata})
             # Check if the update was successful
            if document.modified_count > 0:
                response_data = {
                    "status": "Successful",
                    "data": {
                        "matched_count": document.matched_count,
                        "modified_count": document.modified_count
                    },
                    "message": "Document Update Successfully",
                    "serviceName": "DCStatusChange_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


from django.template.loader import render_to_string
import tempfile

# send to dc by docusign
class docusignAgreementSentAPIView(APIView):
    def post(self, request):
        empanelmentID = request.data['id']
        if empanelmentID:
            empanelment_docu = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID)})    
            dc_email = empanelment_docu['emailId']
            dc_name = empanelment_docu['Owner_name']
            dc_DCID = empanelment_docu['DCID']
        else:
            return Response({"status": "error", "message": "Id not Provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        DC_data = {
            'providerName' : empanelment_docu['providerName'],
            'providerType' : empanelment_docu['providerType'],
            'Regi_number' : empanelment_docu['Regi_number'],
            'Owner_name' : empanelment_docu['Owner_name'],
            'address1' : empanelment_docu['address1'],
            'pincode' : empanelment_docu['pincode'],
            'emailId' : empanelment_docu['emailId'],
            'FirmType' : empanelment_docu['FirmType'],
            }
        html_content = render_to_string('template.html', DC_data)
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write(html_content)
        BASE64_ENCODED_DOCUMENT_CONTENT =base64.b64encode(html_content.encode()).decode(),

        args = {
            'emailSubject' : 'Please Sign on document',
            'documentBase64' : BASE64_ENCODED_DOCUMENT_CONTENT[0], # tupple
            'documentName' : dc_name,
            'documentExtension' : 'html',
            'dc_signer_email' : dc_email,
            'dc_signer_name' : dc_name,
            'authority_signer_email' : 'pankaj.sajekar@alineahealthcare.in',
            'authority_signer_name' : 'Pankaj Sajekar',
            # 'authority_signer_email' : 'rupali.jadhav@alineahealthcare.in',
            # 'authority_signer_name' : 'rupali jadhav',
            'status' : 'sent',
        }
        token = docusign_JWT_Auth()
        if not token:
            return Response({"status": "error", "message": "Failed to obtain access token from DocuSign."}, status=status.HTTP_403_FORBIDDEN)
        
        access_token = token.get('access_token')

        # send for envelope
        envelope_res = docusign_create_and_send_envelope(args, access_token)

        update_data = {
            # "ds_envelope_status": envelope_res['envelopeData']['status'],
            "ds_envelope_envelopeId": envelope_res['envelopeData']['envelopeId'],
            "ds_envelope_statusDateTime": envelope_res['envelopeData']['statusDateTime'],
            "ds_envelope_uri": envelope_res['envelopeData']['uri'],
        }
        empanelment_docu_result = selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID)}, {"$set": update_data})

        #  insert into array field using push method
        empanelment_docu_result = selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID)}, {'$push': {'ds_envelope_status': envelope_res['envelopeData']['status']}}) 

        if empanelment_docu_result.modified_count == 1:
                response_data = {
                        "status": "Successful",
                        "data": envelope_res['envelopeData'],
                        "message": "",
                        "serviceName": "docusignAgreementFile_Service",
                        "timeStamp": datetime.datetime.now().isoformat(),
                        "code": status.HTTP_200_OK,
                        }
                return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(response_data, status=status.HTTP_200_OK)


# Not needed 
class docusignAgreementFileAPIView(APIView):
    def post(self, request):
        empanelmentID = request.data['id']
        if empanelmentID:
            empanelment_docu = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID)})    
            dc_email = empanelment_docu['emailId']
            dc_name = empanelment_docu['Owner_name']
            dc_DCID = empanelment_docu['DCID']

        serializer = docusignAgreementFileSerializer(data=request.data)

        if serializer.is_valid():   
            BASE64_ENCODED_DOCUMENT_CONTENT = serializer.validated_data['base64_content']
            documentExtension = serializer.validated_data['file_extension']
            documentName = serializer.validated_data['file_name']
     
        args = {
            'emailSubject' : 'Please Sign on document',
            'documentBase64' : BASE64_ENCODED_DOCUMENT_CONTENT,
            'documentName' : documentName,
            'documentExtension' : documentExtension,
            # 'dc_signer_email' : 'navnit.bhoir@alineahealthcare.in',
            # 'dc_signer_name' : 'Navnit bhoir',
            'dc_signer_email' : dc_email,
            'dc_signer_name' : dc_name,
            'authority_signer_email' : 'pankaj.sajekar@alineahealthcare.in',
            'authority_signer_name' : 'Pankaj Sajekar',
            # 'authority_signer_email' : 'rupali.jadhav@alineahealthcare.in',
            # 'authority_signer_name' : 'rupali jadhav',
            'status' : 'sent',
        }

        # goes for access token (JWT Auth)
        token = docusign_JWT_Auth()
        if not token:
            return Response({"status": "error", "message": "Failed to obtain access token from DocuSign."}, status=status.HTTP_403_FORBIDDEN)
        
        access_token = token.get('access_token')

        # send for envelope
        envelope_res = docusign_create_and_send_envelope(args, access_token)

        update_data = {
            "ds_envelope_status": envelope_res['envelopeData']['status'],
            "ds_envelope_envelopeId": envelope_res['envelopeData']['envelopeId'],
            "ds_envelope_statusDateTime": envelope_res['envelopeData']['statusDateTime'],
            "ds_envelope_uri": envelope_res['envelopeData']['uri'],
        }
        empanelment_docu_result = selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID)}, {"$set": update_data}) 
        
        if empanelment_docu_result.modified_count == 1:
                response_data = {
                        "status": "Successful",
                        "data": envelope_res['envelopeData'],
                        "message": "",
                        "serviceName": "docusignAgreementFile_Service",
                        "timeStamp": datetime.datetime.now().isoformat(),
                        "code": status.HTTP_200_OK,
                        }
                return Response(response_data, status=status.HTTP_200_OK)
        
        # ticketStatusUpdate(dc_DCID, 49)
        return Response(response_data, status=status.HTTP_200_OK)
        

# update in mongodb by docusign status 
class docusignCheckStatusAPIView(APIView):
    def get(self, request):
        empanelmentID = request.query_params.get('id')
        if empanelmentID:
            # get document
            empanelment_docu = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID)})
            dc_TicketID = empanelment_docu['TicketID']
            ds_envelope_envelopeId = empanelment_docu['ds_envelope_envelopeId']
            
            token = docusign_JWT_Auth()
            envelopeStatusRes = docusign_get_envelope_status(token.get('access_token'), ds_envelope_envelopeId)
            # get_envelope_res_pdf_content = docusign_get_Envelope_Documents(token.get('access_token'), ds_envelope_envelopeId)
            # print(get_envelope_res_pdf_content)
            if envelopeStatusRes['status'] == 'completed':
                # upadate status closed
                ticketStatusUpdate(dc_TicketID, 5)
            
            # add evelope status if last status not matching with current status and after envelope send
            if empanelment_docu['ds_envelope_status'][-1] != envelopeStatusRes['status'] and empanelment_docu['ds_envelope_status'][0] == 'waiting' :
                insert_data = { "ds_envelope_status": envelopeStatusRes['status'], }
                empanelment_docu = selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID)}, {"$push": insert_data}) 
            else:
                print("status not added")
        
        serializer_data = {
            "status": "Success",
            "data": {
                "envelopeId":ds_envelope_envelopeId,
                "status":envelopeStatusRes['status'],
            },
            "message": "checkStatus",
            "serviceName": "docusignCheckStatusAPIView_Service",
            "timeStamp": datetime.datetime.now().isoformat(),
            "code": status.HTTP_200_OK,
        }
        return Response(serializer_data, status=status.HTTP_200_OK)
    

class SaveToMongoDocusignDocumentContentAPIView(APIView):
    def get(self, request):
        empanelmentID = request.query_params.get('id')
        if empanelmentID:
            # get document
            empanelment_docu = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID)})
            ds_envelope_envelopeId = empanelment_docu['ds_envelope_envelopeId']
            
            token = docusign_JWT_Auth()
            get_envelope_res_pdf_content = docusign_get_Envelope_Documents(token.get('access_token'), ds_envelope_envelopeId)
            
            # update document
            update_data = {
                "ds_envelope_document_content": get_envelope_res_pdf_content
            }
            empanelment_docu = selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID)}, {"$set": update_data}) 

        serializer_data = {
            "status": "Success",
            "data": {
                "envelopeId":ds_envelope_envelopeId,
            },
            "message": "Save PDF in MongoDB",
            "serviceName": "SaveToMongoDocusignDocumentContent_Service",
            "timeStamp": datetime.datetime.now().isoformat(),
            "code": status.HTTP_200_OK,
        }
        return Response(serializer_data, status=status.HTTP_200_OK)
    


class SaveIntoDBAndViewDocusignDocumentContentAPIView(APIView):
    def get(self, request):
        empanelmentID = request.query_params.get('id')
        if empanelmentID:
            # get document
            empanelment_docu = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID)})
            ds_envelope_envelopeId = empanelment_docu['ds_envelope_envelopeId']
            DC_providerName = empanelment_docu['providerName']
            # document signed by docusign and stored in db then provide document in pdf
            if 'ds_envelope_document_content' in empanelment_docu:
                ds_envelope_document_content = empanelment_docu['ds_envelope_document_content']
                pdf_content = base64.b64encode(ds_envelope_document_content).decode('utf-8')
                return Response({'pdf_content':pdf_content, "DC_name": DC_providerName }, status=status.HTTP_200_OK)
            else:
                # store document in db and provide pdf
                token = docusign_JWT_Auth()
                get_envelope_res_pdf_content = docusign_get_Envelope_Documents(token.get('access_token'), ds_envelope_envelopeId)
                
                update_data = { "ds_envelope_document_content": get_envelope_res_pdf_content, 'DC_Empanelment_Status': "Registered" }
                empanelment_docu = selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID)}, {"$set": update_data}) 
                pdf_content = base64.b64encode(get_envelope_res_pdf_content).decode('utf-8')
                return Response({'pdf_content':pdf_content, "DC_name": DC_providerName}, status=status.HTTP_200_OK)
            


           
