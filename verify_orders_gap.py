import requests
import json
import sys

BASE_URL = "http://localhost:54279/api/v1"

def login_admin():
    print("Logging in as admin...")
    response = requests.post(f"{BASE_URL}/auth/token", data={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        sys.exit(1)
    return response.json()["access_token"]

def verify_orders():
    token = login_admin()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get a Supplier
    print("\nFetching Supplier...")
    all_partners = requests.get(f"{BASE_URL}/partners/", headers=headers).json()
    suppliers = [p for p in all_partners if p['type'] == 'supplier' or p['type'] == 'SUPPLIER']
    if not suppliers:
        print("   No suppliers found. Creating one...")
        s_data = {"name": "Auto Verify Supplier 2", "type": "supplier", "email": "sup2@test.com", "mobile": "1122334455"}
        res = requests.post(f"{BASE_URL}/partners/", json=s_data, headers=headers)
        supplier = res.json()
    else:
        supplier = suppliers[0]
    print(f"   Using Supplier: {supplier['name']} (ID: {supplier['id']})")

    # 2. Get a Customer
    print("\nFetching Customer...")
    customers = requests.get(f"{BASE_URL}/partners/?type=customer", headers=headers).json()
    customer = None
    if not customers:
        # Create one
        print("   Creating new Customer...")
        cust_data = {
            "name": "Auto Verified Customer",
            "type": "customer",
            "email": "customer@test.com",
            "mobile": "9876543210",
            "credit_limit": 50000.0
        }
        res = requests.post(f"{BASE_URL}/partners/", json=cust_data, headers=headers)
        if res.status_code == 201:
            customer = res.json()
        else:
            print(f"❌ Failed to create customer: {res.text}")
            return
    else:
        customer = customers[0]
    
    print(f"   Using Customer: {customer['name']} (ID: {customer['id']})")
    
    # 3. Get a Product for this Supplier
    print("\nFetching Product for Supplier...")
    products = requests.get(f"{BASE_URL}/products/", headers=headers).json()
    target_product = None
    for p in products:
        if p.get('seller_id') == supplier['id']:
             target_product = p
             break
    
    if not target_product:
        # Create one
        print("   Creating new Product for Supplier...")
        prod_data = {
            "name": "Order Verification Saree",
            "category": "Sarees",
            "base_price": 2000.0,
            "seller_id": supplier['id'],
            "design_number": "ORD-TEST-001",
            "quality": "Test Quality"
        }
        res = requests.post(f"{BASE_URL}/products/", json=prod_data, headers=headers)
        if res.status_code == 201:
            target_product = res.json()
        else:
            print(f"❌ Failed to create product: {res.text}")
            return
            
    print(f"   Using Product: {target_product['name']} (ID: {target_product['id']})")
    
    # Enable Variant?
    variant_id = None
    if target_product.get('variants') and len(target_product['variants']) > 0:
        variant_id = target_product['variants'][0]['id']
    else:
        # Parse items or re-fetch? Products list might not include variants detail depending on implementation
        # Let's fetch detail
        p_detail = requests.get(f"{BASE_URL}/products/{target_product['id']}", headers=headers).json()
        if p_detail.get('variants'):
            variant_id = p_detail['variants'][0]['id']
        else:
            # Add variant
            print("   Adding Variant...")
            var_data = {
               "attributes": {"Color": "Red"},
               "price_adjustment": 0,
               "stock_quantity": 0
            }
            res = requests.post(f"{BASE_URL}/products/{target_product['id']}/variants/", json=var_data, headers=headers)
            if res.status_code not in [200, 201]:
                print(f"❌ Failed to create variant: {res.text}")
                return
            variant_id = res.json()['id']

    # 4. Create Order with Commission
    print("\nCreating Brokerage Order...")
    order_data = {
        "buyer_id": customer['id'],
        "seller_id": supplier['id'],
        "commission_rate": 5.0, # 5% Commission
        "items": [
            {
                "variant_id": variant_id,
                "quantity": 2
            }
        ]
    }
    
    res = requests.post(f"{BASE_URL}/orders/", json=order_data, headers=headers)
    if res.status_code != 201:
        print(f"❌ Failed to create order: {res.text}")
        return
        
    order = res.json()
    print(f"✅ Order Created: {order['order_number']}")
    print(f"   Total Amount: {order['total_amount']}")
    print(f"   Commission Rate: {order.get('commission_rate')}")
    print(f"   Commission Amount: {order.get('commission_amount')}")
    
    # Verify Commission Math
    # Total = 2 * 2000 = 4000
    # Comm = 4000 * 0.05 = 200
    expected_comm = float(order['total_amount']) * 0.05
    actual_comm = float(order['commission_amount'])
    
    if abs(expected_comm - actual_comm) < 0.1:
         print(f"✅ Commission Calculation Verified: {actual_comm} (Matches Expected)")
    else:
         print(f"❌ Commission Calculation Mismatch: Got {actual_comm}, Expected {expected_comm}")

if __name__ == "__main__":
    verify_orders()
