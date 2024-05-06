import jwt
import requests
from docusign.ds_config import PRIVATE_KEY
import time    

CURRENT_UNIX_EPOCH_TIME = int(time.time())
DOCSIGN_PRIVATE_KEY = PRIVATE_KEY
DOCSIGN_INTEGRATION_KEY = 'c660dadf-b55d-4025-b75e-806a03dd3404'
DOCSIGN_USER_ID = '2c9e7766-c715-4642-851e-8383484aaa49'


def docusign_JWT_Auth():
    # Create JWT token
    jwt_payload = {
        "iss": DOCSIGN_INTEGRATION_KEY,
        "sub": DOCSIGN_USER_ID,
        "aud": "account-d.docusign.com",
        "iat": CURRENT_UNIX_EPOCH_TIME,
        "exp": CURRENT_UNIX_EPOCH_TIME+6000,
        "scope": "signature impersonation"
    }

    jwt_token = jwt.encode(jwt_payload, DOCSIGN_PRIVATE_KEY, algorithm="RS256")

    # Request access token using JWT grant
    token_url = "https://account-d.docusign.com/oauth/token"
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token
    }
    response = requests.post(token_url, data=data, verify=False)
    
    # Handle the response from DocuSign
    if response.status_code == 200:
        tokens = response.json()
        return tokens
    else:
        return None
        # return HttpResponseBadRequest("Failed to obtain access token from DocuSign.")

