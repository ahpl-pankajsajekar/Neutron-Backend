
import requests 
import base64
from providerApp.models import fdticket_collection

# basic authorization 
freshdesk_username = 'p8StXeOUFSoTHBrUyco'
freshdesk_password = 'X'
freshdesk_url = 'https://alineahealthcare.freshdesk.com/'

# Concatenate username and password with a colon
auth_string = f'{freshdesk_username}:{freshdesk_password}'
# Encode the auth string to base64
auth_encoded = base64.b64encode(auth_string.encode()).decode()


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


def CreateTicketFunction(fd_body_data):
    try:
        url = f"{freshdesk_url}api/v2/tickets"
        # update status   
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_encoded}'
        }
        # fd_body_data = fd_body_data
        response = requests.post(url, json=fd_body_data, headers=headers)
        res = response.json()
        if response.status_code == 201:
            ticket = res
            createTicket_data = {
                "Ticket_Id": ticket['id'],
                "Subject": ticket['subject'],
                "Status_ID": ticket['status'],
                "Description": ticket['description_text'],
                "Description_Html": ticket['description'],
                "Priority_ID": ticket['priority'],
                "Group_ID": ticket['group_id'],
                "Source_ID": ticket['source'],
                "Requester_Address": ticket['custom_fields']['cf_customer_address'],
                "DignosticCenter_ProviderName": ticket['custom_fields']['cf_diagnostic_centre_name'],
                "DignosticCenter_Pincode": ticket['custom_fields']['cf_diagnostic_centre_pincode'],
                "DignosticCenter_Zone": ticket['custom_fields']['cf_select_your_zone'],
                "DignosticCenter_State": ticket['custom_fields']['cf_diagnostic_centre_state'],
                "DignosticCenter_City": ticket['custom_fields']['cf_diagnostic_centre_city'],
                "DignosticCenter_presentremark": ticket['custom_fields']['cf_presentremark'],
                "DignosticCenter_EmailId": ticket['custom_fields']['cf_diagnostic_center_email_id'],
                "DignosticCenter_Address": ticket['custom_fields']['cf_diagnostic_centre_address'],
                "DignosticCenter_ContactNumber": ticket['custom_fields']['cf_diagnostic_centre_contact_number'],
                "DignosticCenter_OtherDetailsIfAny": ticket['custom_fields']['cf_other_detailsif_any'],
                "cf_flscontact": ticket['custom_fields']['cf_flscontact'],
                "cf_request_type": ticket['custom_fields']['cf_request_type'],
                "Priority": ticket['custom_fields']['cf_priority'],
                "start_time": ticket['custom_fields']['cf_start_time'],
                "end_time": ticket['custom_fields']['cf_end_time'],
                "tags": ticket['tags'],
                "to_emails": ticket['to_emails'],
                "due_by": ticket['due_by'],
                "created_at": ticket['created_at'],
                "updated_at": ticket['updated_at'],
            }
            if "associated_tickets_list" in ticket:
                createTicket_data.update({"associated_tickets_list": ticket['associated_tickets_list']})
                createTicket_data.update({"association_type": ticket['association_type']})
            if ticket['custom_fields']['cf_provider_id']:
                createTicket_data.update({"DignosticCenter_Provider_ID": int(ticket['custom_fields']['cf_provider_id']) })
            ticket_docu = fdticket_collection.insert_one(createTicket_data)
            print(ticket_docu)
            response_data = {
                "status":  "Success",
                "data":  createTicket_data,
                "message":  "Ticket Created successfully!",
            }
        else:
            response_data = {
                "status":  res['errors'],
                "message":  res['description'],
            }
    except requests.exceptions.RequestException as e:
        response_data = {
            "status": "Failed",
            "message": e,
        }
    print(response_data)
    return(response_data)

fd_create_ticket_body_data = {
    "status": 3,
    "priority": 1,
    # "subject": "Testing from postman for project neutron",
    # "requester_id": 89008796442,
    "cc_emails": ["faraz.khan@alineahealthcare.in"],
}
# CreateTicketFunction(fd_create_ticket_body_data)


# Update Freshdesk Ticket update
def ticketStatusUpdate(ticket_id, fd_ticket_body_data):
    try:
        url = f"{freshdesk_url}api/v2/tickets/{ticket_id}"
        # update status   
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_encoded}'
        }
        response = requests.put(url, json=fd_ticket_body_data, headers=headers)
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
