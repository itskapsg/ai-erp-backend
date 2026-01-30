import requests
import json
import sys

BASE_URL = "http://localhost:54279/api/v1"

def login(username, password):
    print(f"Logging in as {username}...")
    try:
        response = requests.post(f"{BASE_URL}/auth/token", data={
            "username": username,
            "password": password
        })
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            sys.exit(1)
        return response.json()["access_token"]
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def verify_product_gap():
    # 1. Login
    token = login("admin", "admin123")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check for Supplier or Create One
    print("\nFetching Suppliers...")
    response = requests.get(f"{BASE_URL}/partners/", headers=headers)
    all_partners = response.json()
    suppliers = [p for p in all_partners if p['type'].upper() == 'SUPPLIER']
    
    if suppliers:
        supplier_id = suppliers[0]['id']
        print(f"   Using Existing Supplier: {suppliers[0]['name']} ({supplier_id})")
    else:
        print("   No Suppliers found. Creating one...")
        supplier_data = {
            "name": "Auto Verified Supplier",
            "type": "supplier",
            "gst_number": "AUTO123SUP",
            "mobile": "9999999999",
            "email": "auto@supplier.com",
            "address": "Auto Generated Address"
        }
        create_resp = requests.post(f"{BASE_URL}/partners/", json=supplier_data, headers=headers)
        if create_resp.status_code == 201:
            supplier_id = create_resp.json()['id']
            print(f"   Created Supplier: Auto Verified Supplier ({supplier_id})")
        else:
             print(f"❌ Failed to create supplier: {create_resp.text}")
             return

    # 3. Create Product with NEW fields
    print("\nCreating Product with Design Number & Quality...")
    product_data = {
        "name": "Verification Silk Saree",
        "category": "Sarees",
        "base_price": 5000.00,
        "seller_id": supplier_id,
        "design_number": "DES-VERIFY-001",
        "quality": "Pure Mysuru Silk",
        "description": "Automated verification product"
    }
    
    response = requests.post(f"{BASE_URL}/products/", json=product_data, headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Product Created Successfully")
        print(f"   ID: {data['id']}")
        print(f"   Design: {data.get('design_number')} (Expected: DES-VERIFY-001)")
        print(f"   Quality: {data.get('quality')} (Expected: Pure Mysuru Silk)")
        print(f"   Seller ID: {data.get('seller_id')} (Expected: {supplier_id})")
        
        if data.get('design_number') == "DES-VERIFY-001" and data.get('seller_id') == supplier_id:
             print("   Verification PASSED: Fields match.")
        else:
             print("   Verification FAILED: Content mismatch.")
    else:
        print(f"❌ Failed to create product: {response.text}")

if __name__ == "__main__":
    verify_product_gap()
