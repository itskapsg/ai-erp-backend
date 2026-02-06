
import requests
import json
import random
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1" # Internal Port
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def login():
    try:
        res = requests.post(f"{BASE_URL}/auth/token", data={"username": ADMIN_USER, "password": ADMIN_PASS})
        if res.status_code != 200:
            print(f"Login Failed: {res.text}")
            return None
        return res.json()["access_token"]
    except Exception as e:
        print(f"Login Error: {e}")
        return None

def sim_financials():
    token = login()
    if not token: return
    
    headers = {"Authorization": f"Bearer {token}"}
    print("--- Starting Financial Core Simulation ---")
    
    # 1. Setup Data: Order
    print("Getting partners...")
    partners = requests.get(f"{BASE_URL}/partners/", headers=headers).json()
    customers = [p for p in partners if p['type'].lower() == 'customer']
    suppliers = [p for p in partners if p['type'].lower() == 'supplier']
    
    if not customers or not suppliers:
        print("Missing partners.")
        return

    buyer = customers[0]
    seller = suppliers[0]
    
    # Find product of this seller
    products = requests.get(f"{BASE_URL}/products/", headers=headers).json()
    product = next((p for p in products if p['seller_id'] == seller['id']), None)
    
    if not product:
        print("No product found.")
        return

    # Set Commission Rate for Supplier
    print("Setting Supplier Commission Rate...")
    requests.put(f"{BASE_URL}/partners/{seller['id']}", json={"commission_rate": 10.0}, headers=headers)

    # Check variant
    vs = requests.get(f"{BASE_URL}/products/{product['id']}/variants/", headers=headers).json()
    if not vs: 
        requests.post(f"{BASE_URL}/products/{product['id']}/variants/", json={"attributes": {"Size": "X"}, "price_adjustment": 0}, headers=headers)
        vs = requests.get(f"{BASE_URL}/products/{product['id']}/variants/", headers=headers).json()
    variant_id = vs[0]['id']
    
    # 1. Create Order
    print("1. Creating Order...")
    res_ord = requests.post(f"{BASE_URL}/orders/", json={
        "buyer_id": buyer['id'], "seller_id": seller['id'],
        "items": [{"variant_id": variant_id, "quantity": 10}]
    }, headers=headers)
    
    if res_ord.status_code not in [200, 201]:
        print(f"Order FAILED: {res_ord.text}")
        return
    order = res_ord.json()
    print(f"✅ Order Created: {order['order_number']} (Total: {order['total_amount']})")
    
    # 2. Create Invoice
    print("2. Uploading Supplier Invoice...")
    inv_payload = {
        "invoice_number": f"INV-{random.randint(1000,9999)}",
        "supplier_id": seller['id'],
        "date": datetime.now().date().isoformat(),
        "total_amount": float(order['total_amount']), # Parse float
        "order_id": order['id']
    }
    # Removed trailing slash
    res_inv = requests.post(f"{BASE_URL}/accounting/invoices", json=inv_payload, headers=headers)
    if res_inv.status_code != 200:
        print(f"Invoice Upload Failed: {res_inv.text}")
        return
    inv_id = res_inv.json()['id']
    print(f"✅ Invoice Uploaded: ID {inv_id}")
    
    # 3. Reconcile
    print("3. Reconciling Invoice...")
    res_rec = requests.post(f"{BASE_URL}/accounting/invoices/{inv_id}/reconcile", headers=headers)
    print(f"Reconcile Result: {res_rec.json()}")
    
    # 4. Record Payment
    print("4. Recording Payment (Buyer -> Supplier)...")
    pay_payload = {
        "payment_number": f"PAY-{random.randint(1000,9999)}",
        "from_partner_id": buyer['id'],
        "to_partner_id": seller['id'],
        "amount": float(order['total_amount']),
        "payment_date": datetime.now().date().isoformat(),
        "mode": "RTGS", # Try Uppercase if DB expects it
        "reference_number": f"UTR{random.randint(10000,99999)}"
    }
    res_pay = requests.post(f"{BASE_URL}/accounting/payments", json=pay_payload, headers=headers)
    if res_pay.status_code != 200:
        print(f"Payment Record Failed: {res_pay.text}")
        return
    pay_id = res_pay.json()['id']
    print(f"✅ Payment Recorded: ID {pay_id}")
    
    # 5. Process Payment (Commission)
    print("5. Processing Payment & Commission...")
    res_proc = requests.post(f"{BASE_URL}/accounting/payments/{pay_id}/process", headers=headers)
    print(f"Process Result: {res_proc.json()}")
    
    # 6. Verify Reporting
    print("6. Verifying Sales Register...")
    res_rep = requests.get(f"{BASE_URL}/reports/sales-register", headers=headers)
    if res_rep.status_code == 200:
        print(f"Sales Register Entries: {len(res_rep.json())}")
    else:
        print(f"Report Failed: {res_rep.text}")

if __name__ == "__main__":
    sim_financials()
