
import requests
import json
import traceback

BASE_URL = "http://localhost:54279/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def login(username, password):
    url = f"{BASE_URL}/auth/token"
    payload = {
        "username": username,
        "password": password
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return None
        return response.json()["access_token"]
    except Exception:
        traceback.print_exc()
        return None

def check_products(token):
    url = f"{BASE_URL}/products/"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response Text: {response.text}")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    token = login(ADMIN_USER, ADMIN_PASS)
    if token:
        check_products(token)
    else:
        print("Could not get token, aborting.")
