import requests
import json
import sys

BASE_URL = "http://localhost:54279/api/v1"

def login(username, password):
    print(f"Logging in as {username}...")
    response = requests.post(f"{BASE_URL}/auth/token", data={
        "username": username,
        "password": password
    })
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        sys.exit(1)
    return response.json()["access_token"]

def verify_gap_analysis():
    # 1. Login as Admin
    token = login("admin", "admin123")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Partner with NEW fields
    print("\nCreating Partner with new fields...")
    partner_data = {
        "name": "Gap Analysis Corp",
        "type": "supplier",
        "gst_number": "GAP123456789",
        "mobile": "9876543210",
        "email": "contact@gap.com",
        "address": "123 Textile Lane, Fabric City",
        "commission_rate": 5.5,
        "credit_limit": 50000.00
    }
    
    response = requests.post(f"{BASE_URL}/partners/", json=partner_data, headers=headers)
    if response.status_code == 201:
        print("✅ Partner Created Successfully")
        data = response.json()
        print(f"   ID: {data['id']}")
        print(f"   Mobile: {data.get('mobile')} (Expected: 9876543210)")
        print(f"   Commission: {data.get('commission_rate')} (Expected: 5.5)")
        print(f"   Status: {data.get('status')} (Expected: ACTIVE)")
        partner_id = data['id']
    else:
        print(f"❌ Failed to create partner: {response.text}")
        return

    # 3. Update Status to BLACKLISTED
    print(f"\nUpdating Status for {partner_id} to BLACKLISTED...")
    response = requests.put(
        f"{BASE_URL}/partners/{partner_id}/status?status=BLACKLISTED",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status Updated: {data.get('status')}")
        if data.get('status') == 'BLACKLISTED':
            print("   Verification PASSED: Status is BLACKLISTED")
        else:
            print("   Verification FAILED: Status mismatch")
    else:
        print(f"❌ Failed to update status: {response.text}")

if __name__ == "__main__":
    try:
        verify_gap_analysis()
    except Exception as e:
        print(f"Verification crashed: {e}")
