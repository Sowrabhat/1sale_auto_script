import requests
import pandas as pd
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib3.util.ssl_ import create_urllib3_context

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

# Loop through each URL in the Excel file
for index, row in df.iterrows():
    url = row['API_URL']
    
    # Ensure the URL is valid
    if pd.isna(url):
        print(f"Row {index}: No URL provided")
        df.at[index, 'Response'] = "No URL provided"
        continue

    # API request body
    payload = {"url": url}
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Send POST request using the session
        response = session.post(api_endpoint, json=payload, headers=headers, verify=False)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Print response or save it to a column
        print(f"Row {index}: Status Code: {response.status_code}, Response: {response.text}")
        df.at[index, 'Response'] = response.text
    except requests.exceptions.RequestException as e:
        # Handle request errors
        print(f"Row {index}: Error - {e}")
        df.at[index, 'Response'] = f"Error: {e}"

# Save results back to Excel
df.to_excel('results.xlsx', index=False)
