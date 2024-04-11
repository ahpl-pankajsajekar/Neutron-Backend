from pyclbr import Class
from urllib import request
from django.http import Http404, JsonResponse
from django.shortcuts import render
import pymongo
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics

from bson import ObjectId, json_util
import json
import datetime
import re
import requests  # type: ignore
import base64

from providerApp.serializers import DCSerializer, DCStatusChangeSerializer, EmpanelmentSerializer, SelfEmpanelmentSerializer
from .models import neutron_collection, person_collection, selfEmpanelment_collection

class home(APIView):
    def get(self, request, *args, **kwargs):
        # person_collection.create_index([("$**", "text")])
        # search_query = "Sajekar"
        # personData = person_collection.find({ "$text": { "$search": search_query } })
        # return JsonResponse(personData, safe=False)
        return Response("hello")
    

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
            # search_tests_inputstring = [ int(d['item_value']) for d in search_tests_inputstring]
            # if search_tests_inputstring:
                # tests_required = search_tests_inputstring.replace(', ', ',').split(',')
                # tests_required = re.split(r',\s*|\s*,\s*|\s+', search_tests_inputstring)

            # Get pagination parameters
            # page_number = int(request.query_params.get('page', 1))
            # page_size = int(request.query_params.get('page_size', 8))

            if search_query_inputstring is None:
                return Response({"error": "Search term not provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize the query dictionary
            query_conditions = []

            # Iterate over the search data list
            for item in search_query_list:
                if isinstance(item, int):
                    # For integer values, construct query conditions for numeric fields
                    query_conditions.append({"$or": [{"DCID": item}, {"Pincode": item},  {"Mobile number 1": item} ]})
                elif isinstance(item, str):
                    # For string values, construct query conditions for string fields
                    query_conditions.append({"$or": [
                        {"DC Name": {"$regex": item, "$options": "i"}},
                        {"City": {"$regex": item, "$options": "i"}},
                        {"State": {"$regex": item, "$options": "i"}},
                        {"DC Registration No": {"$regex": item, "$options": "i"}},
                        {"Accreditation Type": {"$regex": item, "$options": "i"}},
                    ]})

            if search_tests_inputstring:
                # Convert transformations to regular expressions for case-insensitive matching
                # regex_transformations = [re.compile(f'^{re.escape(transform)}$', re.IGNORECASE) for transform in tests_required]
                # test_details_condition = {"AvailableTest": {"$elemMatch": { "$all": regex_transformations}} }
                # Add condition for testDetails field
                test_details_condition = {"AvailableTestCode": { "$all": search_tests_inputstring}}
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
            result = person_collection.insert_one(request.data)
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
        
class EmpanelmentDetailAPIView(APIView):
    def get(self, request):
        try:
            empanelmentID_query = request.query_params.get('id')
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)

            document = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID_query) })

            if document:
                response_data = {
                    "status": "Successful",
                    # "data": serializer.data,
                    "data": json.loads(json_util.dumps(document)),
                    "message": "Document Found Successfully",
                    "serviceName": "EmpanelmentDetails_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found'}, status=404)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class EmpanelmentUpdateAPIView(APIView):
    def put(self, request):
        data = request.data
        try:
            empanelmentID_query = request.query_params.get('id')
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)
            result = person_collection.replace_one({'_id': ObjectId(empanelmentID_query)}, data)
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
            result = person_collection.update_one({'_id': ObjectId(empanelmentID_query)}, {'$set': data})
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

class EmpanelmentDeleteAPIView(APIView):
    def delete(self, request):
        try:
            empanelmentID_query = request.query_params.get('id')
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)

            document = person_collection.delete_one({'_id': ObjectId(empanelmentID_query) })

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
 
        
# Self Emapanelment
class SelfEmpanelmentCreateAPIView(APIView):
    
    def post(self, request):
        try:
            # Get data from request
            serializer = SelfEmpanelmentSerializer(data=request.data)
            if serializer.is_valid():
                empanelment_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
            # Create data in MongoDB
            result = selfEmpanelment_collection.insert_one(request.data)
            response_data = {
                    "status": "Successful",
                    "document_id": str(result.inserted_id),
                    "message": "Document created Successfully",
                    "serviceName": "SelfEmpanelmentCreate_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_201_CREATED,
                    }
            return Response(response_data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class TicketUpdateAPIView(APIView):
    def put(self, request):
        data = request.data
        try:
            ticketId_query = request.query_params.get('ticket_id')
            if ticketId_query is None:
                return Response({"error": "Ticket not Found"}, status=status.HTTP_400_BAD_REQUEST)
            result = person_collection.replace_one({'_id': ObjectId(ticketId_query)}, data)
            if result.modified_count == 1:
                response_data = {
                        "status": "Successful",
                        "message": "Ticket Full Update Successfully",
                        "serviceName": "TicketFullUpdate_Service",
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
            ticketId_query = request.query_params.get('ticket_id')
            if ticketId_query is None:
                return Response({"error": "Ticket not Found"}, status=status.HTTP_400_BAD_REQUEST)
            result = person_collection.update_one({'_id': ObjectId(ticketId_query)}, {'$set': data})
            if result.modified_count == 1:
                response_data = {
                        "status": "Successful",
                        "message": "Ticket Partial Update Successfully",
                        "serviceName": "TicketPartialUpdate_Service",
                        "timeStamp": datetime.datetime.now().isoformat(),
                        "code": status.HTTP_200_OK,
                        }
                return Response(response_data)
            else:
                return Response({'error': 'Document not found or not modified'}, status=404)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# basic authorization 
freshdesk_username = 'p8StXeOUFSoTHBrUyco'
freshdesk_password = 'X'
freshdesk_url = 'https://alineahealthcare.freshdesk.com/'

# Concatenate username and password with a colon
auth_string = f'{freshdesk_username}:{freshdesk_password}'
# Encode the auth string to base64
auth_encoded = base64.b64encode(auth_string.encode()).decode()

# Update Freshdesk Ticket update
def ticketStatusUpdate(ticket_id):
    try:
        url = f"{freshdesk_url}api/v2/tickets/{ticket_id}"
        # update status Resolved 4
        body_data = {
            "status": 2,
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_encoded}'
        }
        response = requests.put(url, json=body_data, headers=headers)
        res = response.json()
        print("----res-----",)
        if response.status_code == 200:
            print("Ticket updated successfully!")
            response_data = {
                "status":  "Successful",
                "message":  "Ticket updated successfully!",
                "serviceName": "ticketStatusUpdate_Function",
                "timeStamp": datetime.datetime.now().isoformat(),
                "code": 200,
            }
        else:
            print("Failed to update ticket. Status code:", response.status_code)
            response_data = {
                "status":  res['code'],
                "message":  res['message'],
                "serviceName": "ticketStatusUpdate_Function",
                "timeStamp": datetime.datetime.now().isoformat(),
                "code": response.status_code,
            }
        # return Response(response_data)
    except requests.exceptions.RequestException as e:
        print("Error making request:", e)
        response_data = {
            "status": "Failed",
            "message": e,
            "serviceName": "ticketStatusUpdate_Function",
            "timeStamp": datetime.datetime.now().isoformat(),
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        # return Response(response_data)
    print(response_data)
    return(response_data)
# ticketStatusUpdate(569752)


# Self Empanelment list view
class SelfEmpanelmentList(generics.ListCreateAPIView):
    serializer_class = SelfEmpanelmentSerializer
    permission_classes = []
    
    def get_queryset(self):
        return selfEmpanelment_collection.find()
    

class FileUploadView(APIView):
    def post(self, request, format=None):
        file = request.data['pan_image']
        dcname = request.data.get('dcname')
        pan_number = request.data.get('pan_number')
        text_field = request.data.get('text_field')
        
        # Store file and additional data in MongoDB
        data = {
            'dcname': dcname,
            'pan_number': pan_number,
            'text_field': text_field,
            'pan_image': file.read()
        }
        selfEmpanelment_collection.insert_one(data)
        return Response(status=status.HTTP_201_CREATED)
    
# SelfEmpanelment
class SelfEmpanelmentCreateAPIView(APIView):
    def post(self, request,id=None, *args, **kwargs):
        ticketId_from_url = id
        if ticketId_from_url == None:
            return Response({"error": "FreshDesk Ticket id Faild"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Get data from request
            serializer = EmpanelmentSerializer(data=request.data)
            if serializer.is_valid():
                dc_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
            # Create data in MongoDB
            result = person_collection.insert_one(request.data)
            # change status in freshdesk
            ticketStatusUpdate(ticketId_from_url)
            response_data = {
                    "status": "Successful",
                    "document_id": str(result.inserted_id),
                    "message": "Self Empanelment document created Successfully",
                    "serviceName": "SelfEmpanelmentCreate_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_201_CREATED,
                    }
            return Response(response_data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Dc Chanage Status 
class DCStatusChangeAPIView(APIView):
    def post(self, request):
        data = request.data
        try:
            dcID_query = int(request.query_params.get('dc', None))
            if dcID_query is None:
                return Response({"error": "DC Details not provided"}, status=status.HTTP_400_BAD_REQUEST)
            # count no of documents return 404
            dc_count = neutron_collection.count_documents({'DCID': dcID_query })
            print(dc_count)
            if dc_count == 0:
                return Response({"error": "No DC Details found for the provided ID"}, status=status.HTTP_404_NOT_FOUND)
            document = neutron_collection.update_one({'DCID': dcID_query}, {'$set': data})
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