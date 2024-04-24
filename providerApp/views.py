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

from providerApp.serializers import DCSerializer, DCStatusChangeSerializer, EmpanelmentSerializer, SelfEmpanelmentSerializer, SelfEmpanelmentVerificationSerializer
from .models import neutron_collection, person_collection, selfEmpanelment_collection

from rest_framework.permissions import IsAuthenticated


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
        # 49 = submited to DC , 4 = Resolved
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
# ticketStatusUpdate(584387, 49)


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
    # permission_classes = [IsAuthenticated]

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
                test_details_condition = {"AvailableTestCode": { "$all": search_tests_inputstring}}  # now search like  eg. [ { "item_value": "100001", "item_label": "2 D Echocardiography" } ]
                # test_details_condition = {"AvailableTestCode": {
                #         "$all": [{"$elemMatch": {"item_value": val}} for val in search_tests_inputstring]
                #     }}   # test_details_condition = {'AvailableTestCode': {'$all': [{'$elemMatch': {'item_value': '100001'}}, {'$elemMatch': {'item_value': '100002'}}]}} and it return value. input comes in " search_tests_inputstring = ["100001", "100002"] "
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
        
# Verify view
class selfEmpanelmentDetailAPIView(APIView):
    def post(self, request):
        try:
            empanelmentID_query = request.data['id']
            if empanelmentID_query is None:
                return Response({"error": "Empanelment Details not provided"}, status=status.HTTP_400_BAD_REQUEST)

            document = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID_query) })

            providerData = {
                        "providerName": document.get("providerName", ""),
                        "PanCard_number" : document.get("PanCard_number", ""),
                        "nameOnPanCard" : document.get("nameOnPanCard", ""),
                        "Adhar_number" : document.get("Adhar_number", ""),
                        "Adhar_name" : document.get("Adhar_name", ""),
                        "Accredation" : document.get("Accredation", ""),
                        # "pan_image": base64.b64encode(document['pan_image']).decode('utf-8'),
                        # 'aadhar_image': base64.b64encode(document['pan_image']).decode('utf-8'),
                        # 'Accreditation_image': base64.b64encode(document['Accreditation_image']).decode('utf-8'),
                        # 'Registration_Number_image': base64.b64encode(document['Registration_Number_image']).decode('utf-8'),
                        # 'Ownership_image': base64.b64encode(document['Ownership_image']).decode('utf-8'),
                        # 'TDS_image': base64.b64encode(document['TDS_image']).decode('utf-8'),
                    }
            
            # Check if image fields exist before accessing
            image_fields = ['pan_image', 'aadhar_image', 'Accreditation_image', 'Registration_Number_image', 'Ownership_image', 'TDS_image']
            for field in image_fields:
                if field in document:
                    providerData[field] = base64.b64encode(document[field]).decode('utf-8')
                else:
                    providerData[field] = "" 

            if document:
                response_data = {
                    "status": "Successful",
                    "data": providerData,
                    # "data": json.loads(json_util.dumps(document)),
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
 


class SelfEmpanelmentSelect(APIView):
    def get(self, request):
        cursor = selfEmpanelment_collection.find()
        providerData = []
        for document in cursor:
                # Filter specific fields here
            filtered_data = {
                "id": str(document["_id"]),  # Convert ObjectId to string if needed
                "providerName": document["providerName"],
            }
            providerData.append(filtered_data)

        return Response(providerData)

class SelfEmpanelmentVerificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        form_data=request.data
        try: 
            serializer = SelfEmpanelmentVerificationSerializer(data=request.data)
            if serializer.is_valid():
                serializer_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            empanelmentID_query = request.data['id']
            
            # get data
            getDocuments = selfEmpanelment_collection.find_one({'_id': ObjectId(empanelmentID_query)})
            # updata Data remaining                                                 
            # document = selfEmpanelment_collection.update_one({'_id': ObjectId(empanelmentID_query) }, {'$set': serializer_data} )
            
            ticket_id = getDocuments['TicketID']
            if request.data['DCVerificationStatus'] == 'verify':
                # verify
                ticket_status_code = 4
            else:
                # partial verify
                ticket_status_code = 3

            ticketStatusUpdate(ticket_id, ticket_status_code)

            if getDocuments:
                response_data = {
                    "status": "Successful",
                    "data": json.loads(json_util.dumps(getDocuments)),
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
                    "serviceName": "EmpanelmentDetails_Service",
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
            form_data = request.data
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
            # pan_image = request.FILES.get('pan_image')
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
        form_data=request.data
        if ticketId_from_url == None:
            return Response({"error": "FreshDesk Ticket id Faild"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Get data from request
            serializer = SelfEmpanelmentSerializer(data=form_data)
            if serializer.is_valid():
                dc_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            TicketID = form_data.get('TicketID')
            DCID = form_data.get('DCID')
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
            Center_name = form_data.get('Center_name')
            Grade = form_data.get('Grade')
            Tier = form_data.get('Tier')
            Accredation = form_data.get('Accredation')
            Station = form_data.get('Station')
            address1 = form_data.get('address1')
            address2 = form_data.get('address2')
            ahplLocation = form_data.get('ahplLocation')
            lcLocation = form_data.get('lcLocation')
            state = form_data.get('state')
            city = form_data.get('city')
            pincode = form_data.get('pincode')
            zone = form_data.get('zone')
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
            paymentToBeMadeInFavorOf = form_data.get('paymentToBeMadeInFavorOf')
            paymentMode = form_data.get('paymentMode')

            # pan_image = form_data.get('pan_image')
            # aadhar_image = form_data.get('aadhar_image')
            # Accreditation_image = form_data.get('Accreditation_image')
            # Registration_Number_image = form_data.get('Registration_Number_image')
            # Ownership_image = form_data.get('Ownership_image')
            # TDS_image = form_data.get('TDS_image')
            ECHOCARDIOGRAPHY = form_data.get('ECHOCARDIOGRAPHY')
            MD_RADIOLOGIST = form_data.get('MD_RADIOLOGIST')
            data = {
                'TicketID': TicketID,
                'DCID': DCID,
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
                'Center_name': Center_name,
                'Grade': Grade,
                'Tier': Tier,
                'Accredation': Accredation,
                'Station': Station,
                'address1': address1,
                'address2': address2,
                'ahplLocation': ahplLocation,
                'lcLocation': lcLocation,
                'state': state,
                'city': city,
                'pincode': pincode,
                'zone': zone,
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
                'paymentToBeMadeInFavorOf': paymentToBeMadeInFavorOf,
                'paymentMode': paymentMode,
                'ECHOCARDIOGRAPHY': ECHOCARDIOGRAPHY,
                'MD_RADIOLOGIST': MD_RADIOLOGIST,
                # 'pan_image': pan_image.read(),
                # 'aadhar_image': aadhar_image.read(),
                # 'Accreditation_image': Accreditation_image.read(),
                # 'Registration_Number_image': Registration_Number_image.read(),
                # 'Ownership_image': Ownership_image.read(),
                # 'TDS_image': TDS_image.read(),
            }

            # Check if image fields exist before accessing
            image_fields = ['pan_image', 'aadhar_image', 'Accreditation_image', 'Registration_Number_image', 'Ownership_image', 'TDS_image']
            for field in image_fields:
                if field in form_data:
                    data[field] = form_data.get(field).read()
                else:
                    pass
                    # data[field] = None
            
            # Create data in MongoDB
            result = selfEmpanelment_collection.insert_one(data)
            # change status in freshdesk
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
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Dc Chanage Status Activate and deactivate, delist
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