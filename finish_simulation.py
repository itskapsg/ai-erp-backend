import requests
import json

BASE_URL = "http://localhost:54279/api/v1"

def login(username, password):
    url = f"{BASE_URL}/auth/token"
    payload = {"username": username, "password": password}
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        return res.json()["access_token"]
    print(f"Login failed: {res.text}")
    return None

def get_partner_id(token, name):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/partners/?partner_type=CUSTOMER", headers=headers)
    if res.status_code == 200:
        partners = res.json()
        for p in partners:
            if p["name"] == name:
                return p["id"]
    print(f"Partner {name} not found")
    return None

def create_visit(token, partner_id):
    headers = {"Authorization": f"Bearer {token}"}
    # Check availability first
    res = requests.get(f"{BASE_URL}/namaste/beds/availability?check_date=2026-01-29", headers=headers)
    beds = res.json()
    print(f"Beds Response: {beds}")
    available = beds.get('available_beds', [])
    if not available:
        print("No availability")
        return

    bed_id = available[0]
    print(f"Booking Bed ID: {bed_id}")
    
    # Create Visit
    payload = {
        "customer_id": partner_id,
        "accommodation_type": "OFFICE_GUEST_HOUSE",
        "preferred_bed": bed_id,
        "start_date": "2026-01-29T10:00:00",
        "end_date": "2026-01-30T10:00:00",
        "visit_mode": "ACCOMPANIED",
        "arrival_details": "Train 1234"
    }
    
    res = requests.post(f"{BASE_URL}/namaste/", json=payload, headers=headers)
    if res.status_code == 200:
        print("Visit Created Successfully!")
        print(res.json())
    else:
        print(f"Failed to create visit: {res.text}")

token = login("admin", "admin123")
if token:
    pid = get_partner_id(token, "Final Buyer")
    if pid:
        create_visit(token, pid)
