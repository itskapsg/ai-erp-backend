
import requests
import json
import sys

BASE_URL = "http://localhost:54279/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def login():
    res = requests.post(f"{BASE_URL}/auth/token", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    return res.json()["access_token"]

def inspect():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Inspect Product
    print("\n--- Product Structure ---")
    products = requests.get(f"{BASE_URL}/products/", headers=headers).json()
    if products:
        p = products[0]
        print(json.dumps(p, indent=2))
        
        # Check if we need to fetch details to see variants
        p_detail = requests.get(f"{BASE_URL}/products/{p['id']}", headers=headers).json()
        print("\n--- Product Detail ---")
        print(json.dumps(p_detail, indent=2))
    else:
        print("No products found.")

    # 2. Inspect Visit Creation Response
    print("\n--- Visit Creation Response ---")
    # Need a customer
    partners = requests.get(f"{BASE_URL}/partners/?type=customer", headers=headers).json()
    if partners:
        cid = partners[0]["id"]
        payload = {
            "customer_id": cid,
            "start_date": "2026-02-01T10:00:00",
            "end_date": "2026-02-05T10:00:00",
            "visit_mode": "SOLO",
            "status": "planned"
        }
        res = requests.post(f"{BASE_URL}/namaste/", json=payload, headers=headers)
        print(f"Status: {res.status_code}")
        try:
            print(json.dumps(res.json(), indent=2))
        except:
            print(res.text)

if __name__ == "__main__":
    inspect()
