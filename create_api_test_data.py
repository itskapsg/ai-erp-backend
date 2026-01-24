#!/usr/bin/env python3
"""
Create test data for API testing
"""

import sys
import os
from decimal import Decimal
from uuid import uuid4

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.masters import Partner, PartnerType
from app.models.products import Product, ProductVariant

def create_test_data():
    """Create test partners and products for API testing."""
    db = SessionLocal()
    
    try:
        # Create test buyer partner
        buyer = Partner(
            id=uuid4(),
            name="API Test Buyer",
            type=PartnerType.CUSTOMER,
            gst_number="29API1234F1Z5",  # 15 chars max
            credit_limit=Decimal("50000.00")
        )
        db.add(buyer)
        
        # Create test seller partner
        seller = Partner(
            id=uuid4(),
            name="API Test Seller",
            type=PartnerType.SUPPLIER,
            gst_number="27API5678G2H6",  # 15 chars max
            credit_limit=Decimal("100000.00")
        )
        db.add(seller)
        
        # Create test product
        product = Product(
            id=uuid4(),
            name="API Test Smartphone",
            description="Test product for API verification",
            category="Electronics",
            base_price=Decimal("25000.00")
        )
        db.add(product)
        
        # Create product variant
        variant = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            sku="API-TEST-PHONE",
            attributes={"Storage": "128GB", "Color": "Black"},
            price_adjustment=Decimal("0.00"),
            stock_quantity=100
        )
        db.add(variant)
        
        db.commit()
        
        print(f"✅ Created Buyer: {buyer.name} (ID: {buyer.id})")
        print(f"✅ Created Seller: {seller.name} (ID: {seller.id})")
        print(f"✅ Created Product: {product.name} (ID: {product.id})")
        print(f"✅ Created Variant: {variant.sku} (ID: {variant.id})")
        
        return {
            'buyer_id': str(buyer.id),
            'seller_id': str(seller.id),
            'variant_id': str(variant.id)
        }
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()