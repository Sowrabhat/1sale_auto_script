import requests
import pandas as pd
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib3.util.ssl_ import create_urllib3_context
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress only the specific warning for insecure HTTPS requests
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

# API endpoint
api_endpoint = "https://content.fitforcloud.com/api/Products/ParseUrl"

# Load Excel file
file_path = 'api_test.xlsx'
df = pd.read_excel(file_path)

# Add new columns for the data you want to extract
columns_to_add = ['name', 'image', 'brand', 'categories', 'price', 'affiliateUrl', 'description']
for column in columns_to_add:
    if column not in df.columns:
        df[column] = ""

# Function to send the API request and handle responses
def send_request(index, url):
    # Ensure the URL is valid
    if pd.isna(url):
        return index, None  # No URL provided, return None

    # API request body
    payload = {"url": url}
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Send POST request using the session
        response = session.post(api_endpoint, json=payload, headers=headers, verify=False)
        response.raise_for_status()  # Raise exception for HTTP errors
        return index, response.json()  # Parse the JSON response
    except requests.exceptions.RequestException as e:
        # Handle request errors 
        return index, {"error": str(e)}  # Return error in response

# Initialize ThreadPoolExecutor for parallel requests
with ThreadPoolExecutor() as executor:
    futures = []
    for index, row in df.iterrows():
        url = row['API_URL']
        futures.append(executor.submit(send_request, index, url))

    # Process the responses as they complete
    for future in as_completed(futures):
        index, response = future.result()
        if response and 'error' not in response:
            # Extract fields from the response and store in DataFrame
            df.at[index, 'name'] = response.get('name', '')
            df.at[index, 'brand'] = response.get('brand', '')

            # Handle the categories field safely
            categories = response.get('categories', [])
            if isinstance(categories, list):  # Ensure it's a list
                # Filter out None values and convert all items to strings
                df.at[index, 'categories'] = ', '.join(str(cat) for cat in categories if cat is not None)
            else:
                df.at[index, 'categories'] = ''  # Default to an empty string

            df.at[index, 'price'] = response.get('price', {}).get('selling', '')
            df.at[index, 'affiliateUrl'] = response.get('affiliateUrl', '')
            df.at[index, 'description'] = response.get('description', '')
            
            # Handle multiple image URLs
            images = response.get('images', [])
            df.at[index, 'image'] = '{' + ', '.join(images) + '}' if images else ''
        else:
            # If there was an error, log it in a specific column
            df.at[index, 'name'] = 'Error'
            df.at[index, 'price'] = 'Error'

        print(f"Row {index}: Response processed")

# Save results back to Excel
df.to_excel('results.xlsx', index=False)
