import requests

# pankaj developer account
DOCUSIGN_ACCOUNT_BASE_URL = 'https://demo.docusign.net/restapi'
# DOCUSIGN_ACCOUNT_ID = "9926847e-9a52-42a2-9004-73a4053d1b15"

# anil admin account
# DOCUSIGN_ACCOUNT_BASE_URL = 'https://na4.docusign.net'
# DOCUSIGN_ACCOUNT_ID = "ee9f0b52-abdb-485e-af0a-d6ae6362c82d"

# anil admindemo account
DOCUSIGN_ACCOUNT_ID = "9777bc04-36c8-4382-b4f4-e9103ae0a500"

def docusign_create_and_send_envelope(args, DOCUSIGN_ACCESS_TOKEN):
    # Construct the envelope JSON
    envelope_json = {
        "emailSubject": args['emailSubject'],
        "documents": [
            {
                "documentBase64": args['documentBase64'],
                "name": args['documentName'],
                "fileExtension": args['documentExtension'],
                "documentId": "1"
            }
        ],
        "recipients": {
            "signers": [
                {
                    "email": args['dc_signer_email'],
                    "name": args['dc_signer_name'],
                    "recipientId": "1",
                    "routingOrder": "1",
                    "tabs": {
                        "signHereTabs": [{
                            "anchorString": "On behalf of the SERVICE ",
                            "anchorXOffset": "50",
                            "anchorYOffset": "-52",
                            "anchorIgnoreIfNotPresent": "false",
                            "anchorUnits": "pixels"
                        }]
                    }
                },
                {
                    "email": args['authority_signer_email'],
                    "name": args['authority_signer_name'],
                    "recipientId": "2",
                    "routingOrder": "2",
                    "tabs": {
                        "signHereTabs": [{
                            "anchorString": "On behalf of the Alinea",
                            "anchorXOffset": "50",
                            "anchorYOffset": "-70",
                            "anchorIgnoreIfNotPresent": "false",
                            "anchorUnits": "pixels"
                        }]
                    }
                }
            ]
        },
        "status": args['status'],
    }
    # print("--------------->", envelope_json)
    # Send POST request to create and send envelope
    api_url = "{}/v2/accounts/{}/envelopes".format(DOCUSIGN_ACCOUNT_BASE_URL, DOCUSIGN_ACCOUNT_ID)
    headers = {
        "Authorization": f"Bearer {DOCUSIGN_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(api_url, json=envelope_json, headers=headers)

    print(response.json())
    # Handle the response
    if response.status_code == 201:
        envelope_id = response.json()["envelopeId"]
        return {"message": "Envelope created and sent successfully", "envelopeData": response.json()}
    else:
        return {"error": "Failed to create and send envelope"}



def docusign_get_envelope_status(DOCUSIGN_ACCESS_TOKEN, envelope_id):
    
    # Send GET request to retrieve envelope status
    api_url = "{}/v2/accounts/{}/envelopes/{}".format(DOCUSIGN_ACCOUNT_BASE_URL, DOCUSIGN_ACCOUNT_ID, envelope_id)
    headers = {
        "Authorization": f"Bearer {DOCUSIGN_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(api_url, headers=headers)

    # Handle the response
    if response.status_code == 200:
        envelope_status = response.json()["status"]
        return {"status": envelope_status}
    else:
        return {"error": "Failed to retrieve envelope status"}


# download completed envelope
def docusign_get_Envelope_Documents(DOCUSIGN_ACCESS_TOKEN, envelope_id):
    
    # Send GET request to retrieve envelope status
    documentId = "combined"
    api_url = "{}/v2/accounts/{}/envelopes/{}/documents/{}".format(DOCUSIGN_ACCOUNT_BASE_URL, DOCUSIGN_ACCOUNT_ID, envelope_id, documentId)
    headers = {
        "Authorization": f"Bearer {DOCUSIGN_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(api_url, headers=headers, verify=False)

    # Handle the response
    if response.status_code == 200:
        return response.content
    else:
        return None
    
