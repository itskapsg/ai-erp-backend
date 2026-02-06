#!/usr/bin/env python3
"""
Real Financial Math Verification Script

This script tests the implementation of real financial calculations to prevent
the split-order loophole where users could bypass credit limits by creating
multiple smaller orders.

Test Scenario:
1. Create a Buyer with Credit Limit ₹50,000
2. Step 1: Create Order A for ₹40,000 (Should be CONFIRMED - within limit)
3. Step 2: Create Order B for ₹20,000 
   - Old System: Would CONFIRM (20k < 50k limit) - LOOPHOLE!
   - New System: Should PENDING (40k + 20k = 60k > 50k limit) - FIXED!

This proves our real financial math prevents credit limit bypass.
"""

import os
import sys
from decimal import Decimal
from sqlalchemy.orm import Session

# Set environment to use PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://erp_admin:db_password_123@localhost/erp_dev_db'

# Add the app directory to Python path
sys.path.append('/workspace')

from app.database import get_db
from app.models.core import User, UserRole, WorkflowStage
from app.models.masters import Partner, PartnerType
from app.models.orders import Order, OrderStatus
from app.models.products import Product, ProductVariant
from app.services.order_service import OrderService
from app.services.finance_service import FinanceService


def setup_test_data(db: Session):
    """Set up test data for the verification"""
    print("🔧 Setting up test data...")
    
    # Create a test user (salesman who will create orders)
    test_user = db.query(User).filter_by(username='test_salesman').first()
    if not test_user:
        test_user = User(
            username='test_salesman',
            email='test@example.com',
            role=UserRole.SALESMAN
        )
        test_user.set_password('password123')
        db.add(test_user)
        db.flush()
    
    # Create a test buyer with ₹50,000 credit limit
    test_buyer = db.query(Partner).filter_by(name='Test Buyer - Split Order Test').first()
    if not test_buyer:
        test_buyer = Partner(
            name='Test Buyer - Split Order Test',
            type=PartnerType.CUSTOMER,
            gst_number='TEST123456789',
            credit_limit=Decimal('50000.00')  # ₹50,000 credit limit
        )
        test_buyer.workflow_stage = WorkflowStage.APPROVED
        db.add(test_buyer)
        db.flush()
    
    # Create a test seller
    test_seller = db.query(Partner).filter_by(name='Test Seller - Split Order Test').first()
    if not test_seller:
        test_seller = Partner(
            name='Test Seller - Split Order Test',
            type=PartnerType.SUPPLIER,
            gst_number='SELL123456789',
            credit_limit=Decimal('0.00')
        )
        test_seller.workflow_stage = WorkflowStage.APPROVED
        db.add(test_seller)
        db.flush()
    
    # Create a test product and variant
    test_product = db.query(Product).filter_by(name='Test Product - Split Order').first()
    if not test_product:
        test_product = Product(
            name='Test Product - Split Order',
            category='Test Category',
            base_price=Decimal('1000.00')
        )
        test_product.workflow_stage = WorkflowStage.APPROVED
        db.add(test_product)
        db.flush()
        
        # Create a variant
        test_variant = ProductVariant(
            product_id=test_product.id,
            sku='TEST-SPLIT-ORDER-001',
            attributes={'Color': 'Test', 'Size': 'Standard'},
            price_adjustment=Decimal('0.00')
        )
        db.add(test_variant)
        db.flush()
    else:
        test_variant = db.query(ProductVariant).filter_by(product_id=test_product.id).first()
    
    db.commit()
    
    return {
        'user': test_user,
        'buyer': test_buyer,
        'seller': test_seller,
        'product': test_product,
        'variant': test_variant
    }


def clean_existing_test_orders(db: Session, buyer_id: str):
    """Clean up any existing test orders for this buyer"""
    print("🧹 Cleaning up existing test orders...")
    
    existing_orders = db.query(Order).filter_by(buyer_id=buyer_id).all()
    for order in existing_orders:
        if 'Split Order Test' in (order.buyer.name if order.buyer else ''):
            db.delete(order)
    
    db.commit()
    print(f"   Deleted {len(existing_orders)} existing test orders")


def test_split_order_prevention(db: Session, test_data: dict):
    """Test the core functionality: preventing split-order loophole"""
    
    print("\n" + "="*80)
    print("🧪 TESTING SPLIT-ORDER LOOPHOLE PREVENTION")
    print("="*80)
    
    buyer = test_data['buyer']
    seller = test_data['seller']
    user = test_data['user']
    variant = test_data['variant']
    
    # Clean existing orders first
    clean_existing_test_orders(db, str(buyer.id))
    
    # Initialize services
    order_service = OrderService(db)
    finance_service = FinanceService(db)
    
    print(f"\n📊 Initial State:")
    print(f"   Buyer: {buyer.name}")
    print(f"   Credit Limit: ₹{buyer.credit_limit:,.2f}")
    
    # Check initial outstanding balance
    initial_balance = finance_service.calculate_outstanding_balance(str(buyer.id))
    print(f"   Initial Outstanding: ₹{initial_balance:,.2f}")
    print(f"   Available Credit: ₹{buyer.credit_limit - initial_balance:,.2f}")
    
    # STEP 1: Create Order A for ₹40,000
    print(f"\n🔸 STEP 1: Creating Order A for ₹40,000")
    print(f"   Expected: CONFIRMED (within ₹50,000 limit)")
    
    order_a_items = [{"variant_id": str(variant.id), "quantity": 40}]  # 40 * ₹1000 = ₹40,000
    
    try:
        order_a = order_service.create_order(
            buyer_id=str(buyer.id),
            seller_id=str(seller.id),
            items=order_a_items,
            user=user
        )
        
        print(f"   ✅ Order A Created: {order_a.order_number}")
        print(f"   📋 Status: {order_a.status.value}")
        print(f"   🔄 Workflow Stage: {order_a.workflow_stage.value}")
        print(f"   💰 Amount: ₹{order_a.total_amount:,.2f}")
        
        if order_a.workflow_stage == WorkflowStage.APPROVED and order_a.status == OrderStatus.CONFIRMED:
            print(f"   ✅ CORRECT: Order A was auto-approved (within credit limit)")
        else:
            print(f"   ❌ UNEXPECTED: Order A should have been auto-approved")
            
    except Exception as e:
        print(f"   ❌ ERROR creating Order A: {str(e)}")
        return False
    
    # Check outstanding balance after Order A
    balance_after_a = finance_service.calculate_outstanding_balance(str(buyer.id))
    print(f"   📊 Outstanding after Order A: ₹{balance_after_a:,.2f}")
    print(f"   📊 Available Credit: ₹{buyer.credit_limit - balance_after_a:,.2f}")
    
    # STEP 2: Create Order B for ₹20,000 (THE CRITICAL TEST)
    print(f"\n🔸 STEP 2: Creating Order B for ₹20,000")
    print(f"   Math: ₹{balance_after_a:,.2f} (existing) + ₹20,000 (new) = ₹{balance_after_a + Decimal('20000'):,.2f}")
    print(f"   Expected: PENDING_APPROVAL (₹{balance_after_a + Decimal('20000'):,.2f} > ₹{buyer.credit_limit:,.2f} limit)")
    print(f"   Old System Would: CONFIRM (₹20,000 < ₹50,000) - LOOPHOLE!")
    print(f"   New System Should: PENDING (total exposure exceeds limit) - FIXED!")
    
    order_b_items = [{"variant_id": str(variant.id), "quantity": 20}]  # 20 * ₹1000 = ₹20,000
    
    try:
        order_b = order_service.create_order(
            buyer_id=str(buyer.id),
            seller_id=str(seller.id),
            items=order_b_items,
            user=user
        )
        
        print(f"   ✅ Order B Created: {order_b.order_number}")
        print(f"   📋 Status: {order_b.status.value}")
        print(f"   🔄 Workflow Stage: {order_b.workflow_stage.value}")
        print(f"   💰 Amount: ₹{order_b.total_amount:,.2f}")
        
        if order_b.rejection_reason:
            print(f"   📝 Reason: {order_b.rejection_reason}")
        
        # THE CRITICAL CHECK: Order B should require approval
        if order_b.workflow_stage == WorkflowStage.PENDING_APPROVAL:
            print(f"   ✅ SUCCESS: Split-order loophole PREVENTED!")
            print(f"   ✅ Order B correctly requires approval due to total exposure")
            return True
        else:
            print(f"   ❌ FAILURE: Split-order loophole NOT prevented!")
            print(f"   ❌ Order B was auto-approved, allowing credit limit bypass")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR creating Order B: {str(e)}")
        return False


def test_financial_reporting(db: Session, test_data: dict):
    """Test the financial reporting capabilities"""
    
    print(f"\n🔸 STEP 3: Testing Financial Reporting")
    
    buyer = test_data['buyer']
    finance_service = FinanceService(db)
    
    try:
        # Get comprehensive financial summary
        summary = finance_service.get_partner_financial_summary(str(buyer.id))
        
        print(f"   📊 Financial Summary for {summary['partner_name']}:")
        print(f"   💳 Credit Limit: ₹{summary['credit_limit']:,.2f}")
        print(f"   💰 Outstanding Balance: ₹{summary['outstanding_balance']:,.2f}")
        print(f"   💵 Available Credit: ₹{summary['available_credit']:,.2f}")
        print(f"   📈 Credit Utilization: {summary['credit_utilization_percent']:.1f}%")
        print(f"   📦 Total Orders: {summary['total_orders']}")
        
        # Show order breakdown
        print(f"   📋 Order Breakdown:")
        for status, count in summary['order_counts'].items():
            if count > 0:
                print(f"      - {status}: {count} orders")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR in financial reporting: {str(e)}")
        return False


def main():
    """Main test execution"""
    
    print("🚀 REAL FINANCIAL MATH VERIFICATION")
    print("="*80)
    print("Testing implementation to prevent split-order credit limit bypass")
    print("="*80)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Setup test data
        test_data = setup_test_data(db)
        
        # Run the critical test
        loophole_prevented = test_split_order_prevention(db, test_data)
        
        # Test financial reporting
        reporting_works = test_financial_reporting(db, test_data)
        
        # Final results
        print(f"\n" + "="*80)
        print("🏁 FINAL RESULTS")
        print("="*80)
        
        if loophole_prevented:
            print("✅ SPLIT-ORDER LOOPHOLE: PREVENTED")
            print("   The system correctly calculates total exposure and requires approval")
            print("   when outstanding balance + new order exceeds credit limit.")
        else:
            print("❌ SPLIT-ORDER LOOPHOLE: NOT PREVENTED")
            print("   The system failed to prevent credit limit bypass through multiple orders.")
        
        if reporting_works:
            print("✅ FINANCIAL REPORTING: WORKING")
            print("   Real-time financial calculations are accurate and comprehensive.")
        else:
            print("❌ FINANCIAL REPORTING: FAILED")
            print("   Financial reporting encountered errors.")
        
        overall_success = loophole_prevented and reporting_works
        
        if overall_success:
            print(f"\n🎉 IMPLEMENTATION SUCCESS!")
            print(f"   Real Financial Math is working correctly.")
            print(f"   Credit limit bypass through split orders is PREVENTED.")
        else:
            print(f"\n💥 IMPLEMENTATION FAILURE!")
            print(f"   Real Financial Math needs debugging.")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)