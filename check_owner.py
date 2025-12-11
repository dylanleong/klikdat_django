import requests
import json

url = "http://localhost:1337/api/vehicles/"
try:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        if results:
            first_vehicle = results[0]
            print("First vehicle fields:")
            print(json.dumps(first_vehicle, indent=2))
            
            if 'owner' in first_vehicle:
                print(f"owner: {first_vehicle['owner']}")
            if 'owner_id' in first_vehicle:
                print(f"owner_id: {first_vehicle['owner_id']}")
        else:
            print("No vehicles found.")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Connection failed: {e}")
