
import requests
import json
import random
import datetime
from datetime import timedelta

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
        print(f"Login failed: {res.text}")
        return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def create_partner(token, name, type, gst, city):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": name,
        "type": type,
        "gst_number": gst,
        "address": f"123 Market Road, {city}",
        "credit_limit": 500000,
        "email": f"contact@{name.replace(' ', '').lower()}.com",
        "mobile": "9876543210"
    }
    res = requests.post(f"{BASE_URL}/partners/", json=data, headers=headers)
    if res.status_code in [200, 201]:
        print(f"✅ Created Partner: {name}")
        return res.json()["id"]
    print(f"❌ Failed Partner {name}: {res.text}")
    return None

def create_product(token, seller_id, name, design_no, quality):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": name,
        "seller_id": seller_id,
        "design_number": design_no,
        "quality": quality,
        "base_price": random.randint(500, 5000),
        "category": "Saree",
        "description": f"Premium {quality} Saree pattern {design_no}"
    }
    res = requests.post(f"{BASE_URL}/products/", json=data, headers=headers)
    if res.status_code in [200, 201]:
        print(f"✅ Created Product: {name}")
        return res.json()["id"]
    print(f"❌ Failed Product {name}: {res.text}")
    return None

def run_simulation():
    token = login(ADMIN_USER, ADMIN_PASS)
    if not token:
        return

    print("--- Starting Grand Simulation ---")
    
    # 1. Create Partners
    supplier_id = create_partner(token, "Lakshmi Textiles", "supplier", "24ABCDE1234F1Z5", "Surat")
    customer_id = create_partner(token, "Mumbai Fashion House", "customer", "27VWXYZ9876G1Z2", "Mumbai")
    
    if supplier_id:
        # 2. Create Products (Simulating Strict Schema compliance)
        create_product(token, supplier_id, "Banarasi Silk Saree", "DN-SILK-001", "Pure Silk")
        create_product(token, supplier_id, "Cotton Print Saree", "DN-CTN-882", "Cotton 60-60")
        create_product(token, supplier_id, "Georgette Party Wear", "DN-GEO-999", "Georgette")

    # 3. Create Orders (Optional for now, focusing on catalog)
    
    print("--- Simulation Complete ---")

if __name__ == "__main__":
    run_simulation()
