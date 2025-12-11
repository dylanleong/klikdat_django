import requests
import json

url = "http://localhost:1337/api/vehicles/"
try:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'facets' in data:
            print("Facets found:")
            print(json.dumps(list(data['facets'].keys()), indent=2))
        else:
            print("No facets key found in response")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Connection failed: {e}")
