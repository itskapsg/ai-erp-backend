
import requests
import json
import os

BASE_URL = "http://localhost:54279/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def login():
    try:
        res = requests.post(f"{BASE_URL}/auth/token", data={"username": ADMIN_USER, "password": ADMIN_PASS})
        return res.json()["access_token"]
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def verify_pdf():
    token = login()
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get last order
    orders = requests.get(f"{BASE_URL}/orders/", headers=headers).json()
    if not orders:
        print("No orders found to generate PDF.")
        return

    last_order = orders[-1]
    oid = last_order['id']
    print(f"Testing PDF for Order: {oid} ({last_order['order_number']})")
    
    # Request PDF
    res = requests.get(f"{BASE_URL}/orders/{oid}/pdf", headers=headers)
    
    if res.status_code == 200:
        content_type = res.headers.get("Content-Type")
        print(f"✅ Success! Status: 200, Type: {content_type}")
        if "application/pdf" in content_type:
            # Save it
            filename = f"order_{last_order['order_number']}.pdf"
            with open(filename, "wb") as f:
                f.write(res.content)
            print(f"Saved PDF to {filename} ({len(res.content)} bytes)")
        else:
            print("❌ Content-Type is not PDF!")
    else:
        print(f"❌ Failed: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    verify_pdf()
