import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Define Swagger API base URL
swagger_base_url = "https://api.example.com"

# List of endpoints to test
api_endpoints = [
    {"method": "GET", "endpoint": "/api/v1/resource1", "params": None, "body": None},
    {"method": "POST", "endpoint": "/api/v1/resource2", "params": None, "body": {"key": "value"}},
    {"method": "GET", "endpoint": "/api/v1/resource3", "params": {"id": 123}, "body": None},
]

# Headers (add Authorization token if needed)
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"  # Replace with a valid token
}

# Function to send API request
def send_api_request(base_url, endpoint_data):
    method = endpoint_data["method"]
    url = f"{base_url}{endpoint_data['endpoint']}"
    params = endpoint_data.get("params")
    body = endpoint_data.get("body")

    try:
        # Send the appropriate request based on the method
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, params=params, json=body)
        else:
            return {"error": f"Unsupported method: {method}"}

        # Raise HTTPError for bad responses
        response.raise_for_status()

        # Return JSON response
        return {"endpoint": endpoint_data["endpoint"], "status": response.status_code, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"endpoint": endpoint_data["endpoint"], "error": str(e)}

# Execute requests in parallel
results = []
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(send_api_request, swagger_base_url, endpoint) for endpoint in api_endpoints]

    for future in as_completed(futures):
        results.append(future.result())

# Print results
for result in results:
    if "error" in result:
        print(f"Error in {result['endpoint']}: {result['error']}")
    else:
        print(f"Success: {result['endpoint']} - Status Code: {result['status']} - Data: {json.dumps(result['data'], indent=2)}")
