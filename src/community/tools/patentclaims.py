from typing import Any, Dict, List

from community.tools import BaseTool

from dotenv import load_dotenv
import os
import requests

load_dotenv()
client_id_key = os.getenv('PATENT_CLIENT_EPO_API_KEY')
client_secret_key = os.getenv('PATENT_CLIENT_EPO_SECRET')

# OAuth2 Token Endpoint
token_url = 'https://ops.epo.org/3.2/auth/accesstoken'

class PatentClaims(BaseTool):

    @classmethod
    def is_available(cls) -> bool:
        return True

    def call(self, parameters: dict, **kwargs: Any) -> List[Dict[str, Any]]:
        query = parameters.get("patent_number", "")
        
        try:
            auth_response = requests.post(token_url, data={
                'grant_type': 'client_credentials',
            }, auth=(client_id_key, client_secret_key))
        except Exception as e:
            print(f"Failed to obtain access token: {e}")
            data = "Error: Failed to obtain access token"
            auth_response = None
        
        if auth_response.status_code == 200:
            # Extract the access token from the response
            access_token = auth_response.json()['access_token']
            pattype='publication'
            format='epodoc'
            
            # Set the API URL for the data request
            data_url = f'https://ops.epo.org/3.2/rest-services/published-data/{pattype}/{format}/{query}/claims'
            
            # Set the headers for the data request, including the obtained access token
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            # Send a GET request with the access token
            response = requests.get(data_url, headers=headers)
            
                        # Check if the data request was successful
            if response.status_code == 200:
                # Process the response
                data = response.json()  # Assuming the API returns JSON data
                claims = data.get('ops:world-patent-data', {}) \
                .get('ftxt:fulltext-documents', {}) \
                .get('ftxt:fulltext-document', {}) \
                .get('claims', [])

                # Filtering the claims by language
                claims_in_english = [claim for claim in claims if claim.get('@lang') == 'EN']
            else:
                data = "Error: Failed to retrieve data"
        else:
            data = "Error: Failed to obtain access token"
        
        return [{"text":  f"{claims_in_english}"}]