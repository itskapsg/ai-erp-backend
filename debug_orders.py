
import requests
import json
import random

BASE_URL = "http://localhost:54279/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def login():
    res = requests.post(f"{BASE_URL}/auth/token", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    return res.json()["access_token"]

def debug_order():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get a Customer
    customers = requests.get(f"{BASE_URL}/partners/", headers=headers).json()
    customers = [p for p in customers if p['type'].lower() == 'customer']
    if not customers:
        print("No customers found")
        return
    buyer = customers[0]
    
    # 2. Get a Supplier
    suppliers = requests.get(f"{BASE_URL}/partners/", headers=headers).json()
    suppliers = [p for p in suppliers if p['type'].lower() == 'supplier']
    if not suppliers:
        print("No suppliers found")
        return
    seller = suppliers[0]
    
    # 3. Get a Product with Variant
    products = requests.get(f"{BASE_URL}/products/", headers=headers).json()
    product = None
    variant_id = None
    
    for p in products:
        vs = requests.get(f"{BASE_URL}/products/{p['id']}/variants/", headers=headers).json()
        if vs:
            product = p
            variant_id = vs[0]['id']
            break
            
    if not product:
        print("No product with variants found")
        return
        
    print(f"Computed Payload Data:")
    print(f"Buyer: {buyer['id']} ({buyer['name']})")
    print(f"Seller: {seller['id']} ({seller['name']})")
    print(f"Product: {product['id']} ({product['name']})")
    print(f"Variant: {variant_id}")
    
    payload = {
        "buyer_id": buyer['id'],
        "seller_id": seller['id'],
        "items": [
            {
                "variant_id": variant_id,
                "quantity": 10
            }
        ]
    }
    
    print("\nSending Payload:", json.dumps(payload, indent=2))
    
    res = requests.post(f"{BASE_URL}/orders/", json=payload, headers=headers)
    print(f"\nResponse Code: {res.status_code}")
    print("Response Body:", res.text)

if __name__ == "__main__":
    debug_order()
