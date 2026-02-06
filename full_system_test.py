
import requests
import json
import random
from datetime import datetime, timedelta
import sys

BASE_URL = "http://localhost:54279/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

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

def get_ids(token, endpoint):
    res = requests.get(f"{BASE_URL}/{endpoint}/", headers={"Authorization": f"Bearer {token}"})
    if res.status_code == 200:
        return [item["id"] for item in res.json()]
    return []

def generate_orders(token, customer_ids, product_ids, variant_map, product_owner_map):
    print("\n--- Generating Mass Orders (Target: 50+) ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    order_ids = []
    
    if not customer_ids or not product_ids:
        print("❌ Missing Customers or Products. skipping Orders.")
        return []
    
    # Fetch Suppliers manually since filter param is broken
    all_partners = requests.get(f"{BASE_URL}/partners/", headers=headers).json()
    supplier_ids = [p["id"] for p in all_partners if p["type"].lower() == "supplier"]
    
    if not supplier_ids:
        print("❌ No suppliers found.")
        return []
        
    print(f"Found {len(supplier_ids)} Suppliers. Starting Order Generation...")
    
    success_count = 0
    for i in range(1, 61):
        seller = random.choice(supplier_ids)
        buyer = random.choice(customer_ids)
        
        # Filter products belonging to this seller
        seller_products = [pid for pid in product_ids if pid in product_owner_map and product_owner_map[pid] == seller]
        
        if not seller_products:
            # Try another seller
            continue
            
        # Pick 1-5 items from this seller's products
        items = []
        for _ in range(random.randint(1, 4)):
            pid = random.choice(seller_products)
            vid = variant_map.get(pid)
            if vid:
                items.append({
                    "variant_id": vid,
                    "quantity": random.randint(5, 50)
                })
        
        if not items: continue

        payload = {
            "buyer_id": buyer,
            "seller_id": seller,
            "items": items
        }
        
        res = requests.post(f"{BASE_URL}/orders/", json=payload, headers=headers)
        if res.status_code in [200, 201]:
            success_count += 1
            order_ids.append(res.json()["id"])
            if i % 10 == 0: print(f"  Created {i} orders...")
        else:
            print(f"❌ Failed Order {i}: {res.status_code} - {res.text}")

    print(f"✅ Created {success_count} Orders.")
    return order_ids

def generate_namaste_visits(token, customer_ids):
    print("\n--- Generating Namaste Visits (Target: 50+) ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    visit_ids = []
    
    if not customer_ids:
        print("❌ Missing Customers.")
        return []

    for i in range(1, 51):
        customer = random.choice(customer_ids)
        start_date = datetime.now() + timedelta(days=random.randint(1, 30))
        end_date = start_date + timedelta(days=random.randint(2, 7))
        
        payload = {
            "customer_id": customer,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "visit_mode": random.choice(["ACCOMPANIED", "SOLO", "MIXED"]),
            "status": "planned"
        }
        
        res = requests.post(f"{BASE_URL}/namaste/", json=payload, headers=headers)
        if res.status_code in [200, 201]:
            try:
                # Response structure: {'visit': {'id': ...}, ...}
                visit_data = res.json()
                if 'visit' in visit_data:
                    vid = visit_data['visit']['id']
                elif 'id' in visit_data:
                    vid = visit_data['id']
                else:
                    # Fallback or error
                    print(f"  ⚠️ Could not find ID in response keys: {visit_data.keys()}")
                    continue

                visit_ids.append(vid)
                if i % 10 == 0: print(f"  Created {i} visits...")
                
                # Add Bed Booking?
                if i % 2 == 0:
                    bed_payload = {
                         "type": "OFFICE_GUEST_HOUSE",
                         "preferred_bed": random.randint(1, 10),
                         "check_in": start_date.isoformat(),
                         "check_out": end_date.isoformat()
                    }
                    # /namaste/{id}/accommodation/
                    r_bed = requests.post(f"{BASE_URL}/namaste/{vid}/accommodation/", json=bed_payload, headers=headers)
                    if r_bed.status_code not in [200, 201]:
                        # print(f"  ⚠️ Bed Booking Failed: {r_bed.text}")
                        pass
            except Exception as e:
                print(f"Error parsing response: {e}")




def ensure_variants(token, product_ids):
    print(f"\n--- Ensuring Variants for {len(product_ids)} Products ---")
    headers = {"Authorization": f"Bearer {token}"}
    variant_map = {} # product_id -> variant_id
    
    count = 0
    for pid in product_ids:
        # Check existing variants
        res = requests.get(f"{BASE_URL}/products/{pid}/variants/", headers=headers)
        if res.status_code == 200:
            variants = res.json()
            if variants:
                variant_map[pid] = variants[0]["id"]
                continue
        
        # Create default variant
        payload = {
            "attributes": {"Size": "Standard", "Color": "Multi"},
            "stock_quantity": 100,
            "price_adjustment": 0
        }
        res = requests.post(f"{BASE_URL}/products/{pid}/variants/", json=payload, headers=headers)
        if res.status_code in [200, 201]:
            variant_map[pid] = res.json()["id"]
            count += 1
            if count % 10 == 0: print(f"  Created variants for {count} products...")
        else:
            print(f"❌ Failed to create variant for {pid}: {res.text}")
            
    print(f"✅ Variants ready mapping for {len(variant_map)} products.")
    return variant_map

if __name__ == "__main__":
    admin_token = login(ADMIN_USER, ADMIN_PASS)
    if admin_token:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Fetch all partners and filter manually
        all_partners = requests.get(f"{BASE_URL}/partners/", headers=headers).json()
        cust_ids = [p["id"] for p in all_partners if p["type"].lower() == "customer"]
        # Supplier filtering needed for orders? logic inside generate_orders fetches suppliers again.
        
        # Fetch products and build owner map
        all_products = requests.get(f"{BASE_URL}/products/", headers=headers).json()
        prod_ids = [p["id"] for p in all_products]
        product_owner_map = {p["id"]: p["seller_id"] for p in all_products}
        
        # Ensure variants exist
        variant_map = ensure_variants(admin_token, prod_ids)
        
        # Pass variant_map and product_owner_map
        generate_orders(admin_token, cust_ids, list(variant_map.keys()), variant_map, product_owner_map)
        generate_namaste_visits(admin_token, cust_ids)
    else:
        print("Login failed.")
