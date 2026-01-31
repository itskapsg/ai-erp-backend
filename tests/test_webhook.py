import requests
import os

BASE_URL = "http://localhost:8000"
FILE_PATH = "test_invoice.txt"

# Create a dummy file
with open(FILE_PATH, "w") as f:
    f.write("This is a test invoice content.")

try:
    url = f"{BASE_URL}/webhook/whatsapp"
    files = {'file': open(FILE_PATH, 'rb')}
    data = {'from_number': '+1234567890', 'body': 'Please process this invoice'}
    
    print(f"Sending POST request to {url}...")
    response = requests.post(url, files=files, data=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        print("✅ Webhook Success!")
    else:
        print("❌ Webhook Failed!")

except Exception as e:
    print(f"❌ Exception: {e}")

finally:
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
