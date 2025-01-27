import requests
import pandas as pd
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib3.util.ssl_ import create_urllib3_context
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress specific warnings for insecure HTTPS requests
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class HostnameIgnoringAdapter(requests.adapters.HTTPAdapter):
    """Adapter to ignore hostname mismatches."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False  # Disable hostname verification
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

# Add the adapter to the session
session = requests.Session()
session.mount('https://', HostnameIgnoringAdapter())

# API endpoints
api_endpoints = {
    "ParseUrl": "https://content.fitforcloud.com/api/Products/ParseUrl",
    "ParseUrlv2": "https://content.fitforcloud.com/api/Products/ParseUrlv2"
}

# Load Excel file
file_path = 'api_test.xlsx'
df = pd.read_excel(file_path)

# Add new columns for the data you want to extract
columns_to_add = [
    'name_api1', 'image_api1', 'brand_api1', 'categories_api1', 'price_api1', 'affiliateUrl_api1', 'description_api1',
    'name_api2', 'image_api2', 'brand_api2', 'categories_api2', 'price_api2', 'affiliateUrl_api2', 'description_api2',
    'error_api1', 'error_api2'
]
for column in columns_to_add:
    if column not in df.columns:
        df[column] = ""

# Function to send the API request and handle responses
def send_request(index, url, endpoint_name, endpoint_url):
    if pd.isna(url):
        return index, endpoint_name, None  # No URL provided, return None

    # API request body
    payload = {"url": url}
    headers = {'Content-Type': 'application/json'}

    try:
        # Send POST request using the session
        response = session.post(endpoint_url, json=payload, headers=headers, verify=False)
        response.raise_for_status()  # Raise exception for HTTP errors
        return index, endpoint_name, response.json()  # Parse the JSON response
    except requests.exceptions.RequestException as e:
        # Handle request errors
        return index, endpoint_name, {"error": str(e)}  # Return error in response

# Initialize ThreadPoolExecutor for parallel requests
with ThreadPoolExecutor() as executor:
    futures = []
    for index, row in df.iterrows():
        url = row.get('API_URL', None)
        for endpoint_name, endpoint_url in api_endpoints.items():
            futures.append(executor.submit(send_request, index, url, endpoint_name, endpoint_url))

    # Process the responses as they complete
    for future in as_completed(futures):
        index, endpoint_name, response = future.result()
        if endpoint_name == "ParseUrl":
            suffix = "_api1"
        elif endpoint_name == "ParseUrlv2":
            suffix = "_api2"
        else:
            continue  # Skip unexpected endpoints

        if response and 'error' not in response:
            # Extract fields from the response and store in DataFrame
            df.at[index, f'name{suffix}'] = response.get('name', '')
            df.at[index, f'brand{suffix}'] = response.get('brand', '')

            # Handle the categories field safely
            categories = response.get('categories', [])
            if isinstance(categories, list):
                df.at[index, f'categories{suffix}'] = ', '.join(str(cat) for cat in categories if cat is not None)
            else:
                df.at[index, f'categories{suffix}'] = ''

            df.at[index, f'price{suffix}'] = response.get('price', {}).get('selling', '')
            df.at[index, f'affiliateUrl{suffix}'] = response.get('affiliateUrl', '')
            df.at[index, f'description{suffix}'] = response.get('description', '')

            # Handle multiple image URLs in JSON format
            images = response.get('images', [])
            if images and isinstance(images, list):
                df.at[index, f'image{suffix}'] = json.dumps(images)
            else:
                df.at[index, f'image{suffix}'] = json.dumps([])
        else:
            # Log error details
            df.at[index, f'error{suffix}'] = response.get('error', 'Unknown error')

        print(f"Row {index}: Response from {endpoint_name} processed")

# Save results back to Excel
df.to_excel('results_both_apis.xlsx', index=False)
#haga