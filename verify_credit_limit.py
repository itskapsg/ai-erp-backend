
import requests
import json
import random

BASE_URL = "http://localhost:54279/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def login():
    res = requests.post(f"{BASE_URL}/auth/token", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    return res.json()["access_token"]

def verify_limit():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get a Customer
    customers = requests.get(f"{BASE_URL}/partners/?type=customer", headers=headers).json()
    customers = [c for c in customers if c['type'].lower() == 'customer']
    if not customers:
        print("No customers found")
        return
        
    buyer = customers[0]
    limit = float(buyer.get('credit_limit') or 0)
    print(f"Buyer: {buyer['name']}, Credit Limit: {limit}")
    
    # Update limit to something small to ensure we exceed it
    # Need to be admin/manager to update? Admin is running this script.
    # PUT /partners/{id} ? No update endpoint in easy view, but let's assume limit is 
    # whatever it is. If it's 0, any order > 0 should trigger approval.
    # If it's large, we order HUGE amount.
    
    target_amount = limit + 1000000 # Force exceed
    
    # 2. Get a Supplier & Product
    suppliers = requests.get(f"{BASE_URL}/partners/?type=supplier", headers=headers).json()
    seller = suppliers[0]
    
    # Find product for seller
    products = requests.get(f"{BASE_URL}/products/", headers=headers).json()
    product = None
    variant_id = None
    
    for p in products:
        if p['seller_id'] == seller['id']:
             # Get variant
             vs = requests.get(f"{BASE_URL}/products/{p['id']}/variants/", headers=headers).json()
             if vs:
                 product = p
                 variant_id = vs[0]['id']
                 break
    
    if not product:
        print("No product found for seller")
        return

    print(f"Ordering Product: {product['name']}, Variant: {variant_id}")
    
    # Create Order
    # Price is likely fixed in variant/product base price.
    # We need Quantity such that Qty * Price > Target Amount.
    price = float(product['base_price'])
    qty = int(target_amount / price) + 10
    
    print(f"Target Amount > {target_amount}. Price: {price}. Qty needed: {qty}")
    
    payload = {
        "buyer_id": buyer['id'],
        "seller_id": seller['id'],
        "items": [
            {"variant_id": variant_id, "quantity": qty}
        ]
    }
    
    res = requests.post(f"{BASE_URL}/orders/", json=payload, headers=headers)
    if res.status_code in [200, 201]:
        order = res.json()
        print(f"Order Created: {order['id']}")
        print(f"Total Amount: {order['total_amount']}")
        print(f"Status: {order['status']}")
        print(f"Workflow Stage: {order['workflow_stage']}")
        
        if order['workflow_stage'] == 'pending_approval':
            print("✅ SUCCESS: Order is Pending Approval (Credit Limit Enforced)")
        else:
            print("❌ FAILURE: Order was Approved despite exceeding limit?")
            print(f"Debug: Credit Limit {limit} vs Order Total {order['total_amount']}")
    else:
        print(f"Failed to create order: {res.text}")

if __name__ == "__main__":
    verify_limit()
