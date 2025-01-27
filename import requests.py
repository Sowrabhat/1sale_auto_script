import requests
import pandas as pd
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib3.util.ssl_ import create_urllib3_context
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

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

# Add columns to store results if they do not exist
columns = ['Name', 'image', 'images', 'videos', 'brand', 'categories', 'retailer', 'summary', 'description', 'affiliateurl', 'rawUrl', 'price', 'selling', 'Original_URL', 'Response']
for column in columns:
    if column not in df.columns:
        df[column] = ""

# Function to make API requests
def make_request(index, url):
    payload = {"url": url}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = session.post(api_endpoint, json=payload, headers=headers, verify=False)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse the response JSON and extract the needed data
        response_data = response.json()
        
        # Extract and store the values in the respective columns
        df.at[index, 'Name'] = response_data.get('Name', '')
        df.at[index, 'image'] = response_data.get('image', '')
        df.at[index, 'images'] = response_data.get('images', '')
        df.at[index, 'videos'] = response_data.get('videos', '')
        df.at[index, 'brand'] = response_data.get('brand', '')
        df.at[index, 'categories'] = response_data.get('categories', '')
        df.at[index, 'retailer'] = response_data.get('retailer', '')
        df.at[index, 'summary'] = response_data.get('summary', '')
        df.at[index, 'description'] = response_data.get('description', '')
        df.at[index, 'affiliateurl'] = response_data.get('affiliateurl', '')
        df.at[index, 'rawUrl'] = response_data.get('rawUrl', '')
        df.at[index, 'price'] = response_data.get('price', '')
        df.at[index, 'selling'] = response_data.get('selling', '')
        
        # Store the original URL
        df.at[index, 'Original_URL'] = url  # Store the original URL in the 'Original_URL' column
        
        return index, "Success", response_data  # Returning the index for tracking
    except requests.exceptions.RequestException as e:
        return index, "Error", str(e)

# List of URLs to process
urls = df['API_URL'].dropna().tolist()

# Initialize ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(make_request, index, url): index for index, url in df.iterrows()}

    # Process results as they come in
    for future in as_completed(futures):
        index, status, response_data = future.result()
        print(f"Row {index}: Status: {status}, Response: {response_data}")

# Save results back to Excel
df.to_excel('results_with_original_url.xlsx', index=False)
