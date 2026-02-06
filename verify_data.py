
import requests
import json

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

def verify():
    token = login()
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n--- Verifying Users ---")
    users = requests.get(f"{BASE_URL}/users/", headers=headers).json()
    print(f"Total Users: {len(users)}")

    print("\n--- Verifying Partners ---")
    partners = requests.get(f"{BASE_URL}/partners/", headers=headers).json()
    customers = [p for p in partners if p['type'] == 'customer']
    suppliers = [p for p in partners if p['type'] == 'supplier']
    print(f"Total Partners: {len(partners)} (Customers: {len(customers)}, Suppliers: {len(suppliers)})")

    print("\n--- Verifying Products ---")
    products = requests.get(f"{BASE_URL}/products/", headers=headers).json()
    print(f"Total Products: {len(products)}")
    
    # Check Variants
    variants_count = 0
    for p in products[:5]: # Check first 5
        vs = requests.get(f"{BASE_URL}/products/{p['id']}/variants/", headers=headers).json()
        variants_count += len(vs)
    print(f"Sample Variant Check (first 5 products): found {variants_count} variants.")

    print("\n--- Verifying Orders ---")
    orders = requests.get(f"{BASE_URL}/orders/", headers=headers).json()
    print(f"Total Orders: {len(orders)}")
    if orders:
        print(f"Sample Order ID: {orders[0]['id']}")
        print(f"Sample Order Amount: {orders[0]['total_amount']}")

    print("\n--- Verifying Namaste Visits ---")
    visits = requests.get(f"{BASE_URL}/namaste/", headers=headers).json()
    print(f"Total Visits: {len(visits)}")
    if visits:
        print("Sample Visit Structure Key(s):", visits[0].keys())
        # Check if booking exists
        # endpoint /namaste/{id}/
        # v_detail = requests.get(f"{BASE_URL}/namaste/{visits[0]['id']}", headers=headers).json()
        # print("Visit Detail Keys:", v_detail.keys())

if __name__ == "__main__":
    verify()
