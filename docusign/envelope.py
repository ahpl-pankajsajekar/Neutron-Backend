import requests

DOCUSIGN_ACCOUNT_BASE_URL = 'https://demo.docusign.net/restapi'
DOCUSIGN_ACCOUNT_ID = "9926847e-9a52-42a2-9004-73a4053d1b15"

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
                },
                {
                    "email": args['authority_signer_email'],
                    "name": args['authority_signer_name'],
                    "recipientId": "2",
                    "routingOrder": "2",
                }
            ]
        },
        "status": args['status'],
    }
    # Send POST request to create and send envelope
    api_url = "{}/v2/accounts/{}/envelopes".format(DOCUSIGN_ACCOUNT_BASE_URL, DOCUSIGN_ACCOUNT_ID)
    headers = {
        "Authorization": f"Bearer {DOCUSIGN_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(api_url, json=envelope_json, headers=headers)

    # Handle the response
    if response.status_code == 201:
        envelope_id = response.json()["envelopeId"]
        return {"message": "Envelope created and sent successfully", "envelope_id": envelope_id}
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
        return {"envelope_id": envelope_id, "status": envelope_status}
    else:
        return {"error": "Failed to retrieve envelope status"}

