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

# Add a new column to store responses
if 'Response' not in df.columns:
    df['Response'] = ""

# Function to send the API request and handle responses
def send_request(index, url):
    # Ensure the URL is valid
    if pd.isna(url):
        return index, "No URL provided"

    # API request body
    payload = {"url": url}
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Send POST request using the session
        response = session.post(api_endpoint, json=payload, headers=headers, verify=False)
        response.raise_for_status()  # Raise exception for HTTP errors
        return index, response.text
    except requests.exceptions.RequestException as e:
        # Handle request errors
        return index, f"Error: {e}"

# Initialize ThreadPoolExecutor for parallel requests
with ThreadPoolExecutor() as executor:
    futures = []
    for index, row in df.iterrows():
        url = row['API_URL']
        futures.append(executor.submit(send_request, index, url))

    # Process the responses as they complete
    for future in as_completed(futures):
        index, response = future.result()
        print(f"Row {index}: Response: {response}")
        df.at[index, 'Response'] = response

# Save results back to Excel
df.to_excel('results.xlsx', index=False)
