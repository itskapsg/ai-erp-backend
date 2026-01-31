
import requests
import json
import random
from datetime import datetime
import sys

BASE_URL = "http://localhost:54279/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# Role Config
ROLES = ["manager", "accountant", "salesman"]
USERS = {role: {"username": role, "password": role, "role": role} for role in ROLES}

def login(username, password):
    url = f"{BASE_URL}/auth/token"
    payload = {"username": username, "password": password}
    try:
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            return res.json()["access_token"]
        return None
    except:
        return None

def create_users(admin_token):
    print("\n--- Creating Role-Based Users ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    for role, data in USERS.items():
        payload = {
            "username": data["username"],
            "email": f"{role}@erp.com",
            "password": data["password"],
            "role": role  # Enum values are lowercase (admin, manager, etc.)
        }
        res = requests.post(f"{BASE_URL}/users/", json=payload, headers=headers)
        if res.status_code in [200, 201]:
            print(f"✅ Created User: {role}")
        elif res.status_code == 400 and "already registered" in res.text:
            print(f"ℹ️ User {role} already exists.")
        else:
            print(f"❌ Failed to create {role}: {res.text}")

def generate_mass_data(token):
    print("\n--- Generating Mass Data (Targets: ~20 Partners, ~20 Products) ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Partners
    supplier_ids = []
    customer_ids = []
    
    cities = ["Surat", "Mumbai", "Delhi", "Ahmedabad", "Jaipur", "Kolkata", "Chennai", "Bangalore"]
    
    print("Generating Partners...")
    print("Generating Partners...")
    for i in range(1, 101):  # Scale to 100
        ptype = "supplier" if i % 2 == 0 else "customer"
        name = f"Partner {i} {ptype.title()}"
        gst = f"24ABCDE{1000+i}F1Z{i%9}"
        data = {
            "name": name,
            "type": ptype,
            "status": "active",
            "gst_number": gst,
            "address": f"Shop {i}, Textile Market, {random.choice(cities)}",
            "mobile": f"98765{10000+i}",
            "email": f"partner{i}@test.com",
            "credit_limit": random.randint(100000, 1000000)
        }
        res = requests.post(f"{BASE_URL}/partners/", json=data, headers=headers)
        
        pid = None
        if res.status_code in [200, 201, 202]: # Handle Pending
            pid = res.json()["id"]
            if i % 10 == 0: print(f"  Created {i} partners...")
        elif res.status_code == 400 and "already exists" in res.text:
            # Fetch existing partner by GST or Name logic? 
            # Actually easier to just Search by GST
            # But the API lookup by GST isn't trivial without filtering. 
            # Let's just create a unique one or skip?
            # Better: POST to /partners/search?gst=... if available?
            # We'll skip adding to specific lists if we can't get ID easily, 
            # but for mass data, we need IDs to create products.
            # Workaround: Filter /partners/ list by type and just grab 50 IDs.
            pass 
        else:
            print(f"❌ Failed Partner {name}: {res.status_code} - {res.text}")
            
        if pid:
            if ptype == "supplier": supplier_ids.append(pid)
            else: customer_ids.append(pid)

    # If we have too few IDs (due to duplicates), fetch all partners to ensure we have IDs for products
    if len(supplier_ids) < 10:
        print("ℹ️ Fetching existing suppliers for product generation...")
        r = requests.get(f"{BASE_URL}/partners/?type=supplier", headers=headers)
        if r.status_code == 200:
            supplier_ids = [p["id"] for p in r.json()]
    
    print(f"✅ Active Suppliers: {len(supplier_ids)}, Customers: {len(customer_ids)}")
    
    print(f"✅ Created {len(supplier_ids)} Suppliers and {len(customer_ids)} Customers (Total Attempts: {i}).")
    
    # 2. Products
    print("Generating Products...")
    product_ids = []
    fabrics = ["Silk", "Cotton", "Georgette", "Chiffon", "Crepe", "Velvet", "Linen"]
    types = ["Saree", "Suit", "Kurti", "Lehenga"]
    
    # Ensure we have suppliers
    if not supplier_ids:
        print("⚠️ No suppliers created! Skipping Product Generation.")
    else:
        for i in range(1, 51):
            fabric = random.choice(fabrics)
            ptype = random.choice(types)
            seller = random.choice(supplier_ids)
            
            data = {
                "name": f"{fabric} {ptype} Design {i}",
                "seller_id": seller,
                "design_number": f"DN-{fabric[:3].upper()}-{1000+i}",
                "quality": fabric,
                "category": ptype,
                "base_price": random.randint(500, 8000),
                "description": f"High quality {fabric} {ptype} with premium finish."
            }
            res = requests.post(f"{BASE_URL}/products/", json=data, headers=headers)
            if res.status_code in [200, 201]:
                product_ids.append(res.json()["id"])
                if i % 10 == 0: print(f"  Created {i} products...")
            else:
                print(f"❌ Failed Product {i}: {res.text}")
                
    print(f"✅ Created {len(product_ids)} Products.")
    return customer_ids, product_ids

def verify_rbac():
    print("\n--- Verifying RBAC (Role Capabilities) ---")
    
    # Login Users
    sales_token = login("salesman", "salesman")
    mgr_token = login("manager", "manager")
    
    if not sales_token or not mgr_token:
        print("❌ Login failed for rbac users.")
        return

    # 1. Salesman Capability: CAN Create Partner (Pending), CANNOT Approve
    print("\n[Salesman Test]")
    
    # Salesman creates a partner
    p_data = {"name": "Salesman Created Partner", "type": "customer"}
    r = requests.post(f"{BASE_URL}/partners/", json=p_data, headers={"Authorization": f"Bearer {sales_token}"})
    
    if r.status_code in [200, 201]:
        print("✅ Salesman CAN Create Partner.")
        target_partner = r.json()["id"]
        
        # Check status (Should be PENDING_APPROVAL)
        if r.json().get("workflow_stage") == "pending_approval":
             print("✅ Partner is PENDING_APPROVAL (Correct).")
        else:
             print(f"⚠️ Partner status is {r.json().get('workflow_stage')}, expected pending_approval.")
             
        # Salesman tries to approve it
        r_approve = requests.put(
            f"{BASE_URL}/partners/{target_partner}/approve",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {sales_token}"}
        )
        if r_approve.status_code == 403:
            print("✅ Salesman CANNOT Approve Partner (403 Forbidden).")
        else:
            print(f"❌ Salesman WAS ALLOWED to Approve Partner! (Status: {r_approve.status_code})")
            
        # 2. Manager Capability: CAN Approve
        print("\n[Manager Test]")
        # Manager approves the same partner
        r_mgr = requests.put(
            f"{BASE_URL}/partners/{target_partner}/approve",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {mgr_token}"}
        )
        if r_mgr.status_code == 200:
            print("✅ Manager CAN Approve Partner.")
        else:
             print(f"❌ Manager Failed to Approve: {r_mgr.text}")
             
    else:
        print(f"❌ Salesman Failed to Create Partner: {r.text}")

if __name__ == "__main__":
    admin_token = login(ADMIN_USER, ADMIN_PASS)
    if admin_token:
        create_users(admin_token)
        generate_mass_data(admin_token)
        verify_rbac()
    else:
        print("Admin login failed.")
