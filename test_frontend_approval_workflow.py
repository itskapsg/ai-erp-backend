#!/usr/bin/env python3
"""
Frontend Approval Workflow Verification Script

This script tests the complete approval workflow:
1. Creates test users (Salesman, Manager, Admin)
2. Salesman creates a partner (should be PENDING_APPROVAL)
3. Tests API endpoints that the frontend uses
4. Simulates Manager approval process

Usage: python test_frontend_approval_workflow.py
"""

import os
import sys
import requests
import json
import time
from decimal import Decimal

# Add the workspace to the Python path
sys.path.append('/workspace')

# API Configuration
API_BASE_URL = 'http://95.111.253.134:54279/api/v1'
FRONTEND_URL = 'http://95.111.253.134:56000'

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        
    def login(self, username, password):
        """Login and get JWT token"""
        try:
            response = self.session.post(
                f'{API_BASE_URL}/auth/token',
                data={'username': username, 'password': password},
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data['access_token']
                self.tokens[username] = token
                self.session.headers.update({'Authorization': f'Bearer {token}'})
                return data
            else:
                print(f"❌ Login failed for {username}: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Login error for {username}: {e}")
            return None
    
    def set_token(self, username):
        """Set authorization header for a specific user"""
        if username in self.tokens:
            self.session.headers.update({'Authorization': f'Bearer {self.tokens[username]}'})
            return True
        return False
    
    def create_partner(self, partner_data):
        """Create a new partner"""
        try:
            headers = self.session.headers.copy()
            headers['Content-Type'] = 'application/json'
            
            response = self.session.post(
                f'{API_BASE_URL}/partners/',
                json=partner_data,
                headers=headers,
                timeout=10
            )
            
            return response
        except Exception as e:
            print(f"❌ Error creating partner: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_pending_approvals(self):
        """Get pending approvals (frontend API call)"""
        try:
            response = self.session.get(f'{API_BASE_URL}/partners/?workflow_stage=pending_approval', timeout=10)
            return response
        except Exception as e:
            print(f"❌ Error getting pending approvals: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def approve_partner(self, partner_id):
        """Approve a partner (frontend API call)"""
        try:
            headers = self.session.headers.copy()
            headers['Content-Type'] = 'application/json'
            
            response = self.session.put(
                f'{API_BASE_URL}/partners/{partner_id}/approve',
                json={'action': 'approve'},
                headers=headers,
                timeout=10
            )
            return response
        except Exception as e:
            print(f"❌ Error approving partner: {e}")
            return None
    
    def reject_partner(self, partner_id, reason):
        """Reject a partner (frontend API call)"""
        try:
            headers = self.session.headers.copy()
            headers['Content-Type'] = 'application/json'
            
            response = self.session.put(
                f'{API_BASE_URL}/partners/{partner_id}/approve',
                json={'action': 'reject', 'reason': reason},
                headers=headers,
                timeout=10
            )
            return response
        except Exception as e:
            print(f"❌ Error rejecting partner: {e}")
            return None

def test_approval_workflow():
    """Test the complete approval workflow"""
    
    print("🧪 FRONTEND APPROVAL WORKFLOW VERIFICATION")
    print("=" * 60)
    
    tester = APITester()
    
    # Test users (these should exist from our previous tests)
    test_users = [
        {'username': 'test_salesman', 'password': 'password123', 'role': 'salesman'},
        {'username': 'test_admin', 'password': 'password123', 'role': 'admin'}
    ]
    
    # Step 1: Login all test users
    print("👤 STEP 1: User Authentication")
    print("-" * 30)
    
    for user in test_users:
        print(f"🔐 Logging in {user['username']} ({user['role']})...")
        login_result = tester.login(user['username'], user['password'])
        if login_result:
            print(f"✅ {user['username']} logged in successfully")
        else:
            print(f"❌ Failed to login {user['username']}")
            return False
    
    print()
    
    # Step 2: Salesman creates a partner (should be PENDING_APPROVAL)
    print("📝 STEP 2: Salesman Creates Partner")
    print("-" * 30)
    
    tester.set_token('test_salesman')
    
    # Generate unique GST number using timestamp
    unique_suffix = str(int(time.time()))[-9:]  # Last 9 digits of timestamp
    
    partner_data = {
        'name': 'Frontend Test Vendor',
        'type': 'supplier',
        'gst_number': f'FRONT{unique_suffix}',
        'credit_limit': 25000.00
    }
    
    print(f"🏭 Creating partner: {partner_data['name']}")
    create_response = tester.create_partner(partner_data)
    
    if create_response:
        if create_response.status_code == 201:
            partner = create_response.json()
            print(f"✅ Partner created successfully!")
            print(f"   📊 ID: {partner['id']}")
            print(f"   📊 Status: {partner['workflow_stage']}")
            
            if partner['workflow_stage'] == 'pending_approval':
                print("✅ CORRECT: Partner is pending approval (as expected)")
            else:
                print(f"❌ UNEXPECTED: Partner status is {partner['workflow_stage']}, expected 'pending_approval'")
                return False
        else:
            print(f"❌ Failed to create partner: Status {create_response.status_code}")
            print(f"   Response: {create_response.text}")
            return False
    else:
        print(f"❌ Failed to create partner: No response")
        return False
    
    print()
    
    # Step 3: Test Frontend API - Get Pending Approvals
    print("📋 STEP 3: Frontend API - Get Pending Approvals")
    print("-" * 30)
    
    tester.set_token('test_admin')  # Switch to admin user
    
    print("🔍 Fetching pending approvals (as Admin)...")
    pending_response = tester.get_pending_approvals()
    
    if pending_response and pending_response.status_code == 200:
        pending_approvals = pending_response.json()
        print(f"✅ Found {len(pending_approvals)} pending approvals")
        
        # Find our test partner
        test_partner = None
        for approval in pending_approvals:
            if approval['name'] == 'Frontend Test Vendor':
                test_partner = approval
                break
        
        if test_partner:
            print(f"✅ Found our test partner in pending approvals")
            print(f"   📊 Name: {test_partner['name']}")
            print(f"   📊 Type: {test_partner['type']}")
            print(f"   📊 Status: {test_partner['workflow_stage']}")
        else:
            print("❌ Test partner not found in pending approvals")
            return False
    else:
        print(f"❌ Failed to get pending approvals: {pending_response.text if pending_response else 'No response'}")
        return False
    
    print()
    
    # Step 4: Test Frontend API - Approve Partner
    print("✅ STEP 4: Frontend API - Approve Partner")
    print("-" * 30)
    
    print(f"👍 Approving partner: {test_partner['name']}")
    approve_response = tester.approve_partner(test_partner['id'])
    
    if approve_response and approve_response.status_code == 200:
        approval_result = approve_response.json()
        print(f"✅ Partner approved successfully!")
        print(f"   📊 Message: {approval_result['message']}")
        print(f"   📊 New Status: {approval_result['new_status']}")
        print(f"   📊 Approved By: {approval_result['approved_by']}")
        
        if approval_result['new_status'] == 'approved':
            print("✅ CORRECT: Partner is now approved")
        else:
            print(f"❌ UNEXPECTED: Partner status is {approval_result['new_status']}, expected 'approved'")
            return False
    else:
        print(f"❌ Failed to approve partner: {approve_response.text if approve_response else 'No response'}")
        return False
    
    print()
    
    # Step 5: Verify partner is no longer in pending approvals
    print("🔍 STEP 5: Verify Approval Workflow")
    print("-" * 30)
    
    print("🔍 Checking pending approvals again...")
    final_pending_response = tester.get_pending_approvals()
    
    if final_pending_response and final_pending_response.status_code == 200:
        final_pending = final_pending_response.json()
        
        # Check if our specific test partner is still in pending
        still_pending = any(p['id'] == test_partner['id'] for p in final_pending)
        
        if not still_pending:
            print("✅ CORRECT: Partner is no longer in pending approvals")
            print(f"📊 Current pending count: {len(final_pending)}")
        else:
            print("❌ UNEXPECTED: Partner is still in pending approvals")
            return False
    else:
        print(f"❌ Failed to verify final state: {final_pending_response.text if final_pending_response else 'No response'}")
        return False
    
    print()
    
    # Step 6: Test Rejection Workflow
    print("❌ STEP 6: Test Rejection Workflow")
    print("-" * 30)
    
    # Create another partner to test rejection
    tester.set_token('test_salesman')
    
    # Generate unique GST number for rejection test
    reject_suffix = str(int(time.time()) + 1)[-9:]  # Different timestamp
    
    reject_partner_data = {
        'name': 'Rejection Test Vendor',
        'type': 'customer',
        'gst_number': f'REJCT{reject_suffix}',
        'credit_limit': 15000.00
    }
    
    print(f"🏭 Creating partner for rejection test: {reject_partner_data['name']}")
    reject_create_response = tester.create_partner(reject_partner_data)
    
    if reject_create_response and reject_create_response.status_code == 201:
        reject_partner = reject_create_response.json()
        print(f"✅ Partner created for rejection test")
        
        # Switch to admin and reject
        tester.set_token('test_admin')
        
        rejection_reason = "Incomplete documentation provided"
        print(f"👎 Rejecting partner with reason: {rejection_reason}")
        
        reject_response = tester.reject_partner(reject_partner['id'], rejection_reason)
        
        if reject_response and reject_response.status_code == 200:
            rejection_result = reject_response.json()
            print(f"✅ Partner rejected successfully!")
            print(f"   📊 Message: {rejection_result['message']}")
            print(f"   📊 New Status: {rejection_result['new_status']}")
            
            if rejection_result['new_status'] == 'rejected':
                print("✅ CORRECT: Partner is now rejected")
            else:
                print(f"❌ UNEXPECTED: Partner status is {rejection_result['new_status']}, expected 'rejected'")
                return False
        else:
            print(f"❌ Failed to reject partner: {reject_response.text if reject_response else 'No response'}")
            return False
    else:
        print(f"❌ Failed to create partner for rejection test")
        return False
    
    print()
    
    # Final Summary
    print("=" * 60)
    print("🎉 FRONTEND APPROVAL WORKFLOW VERIFICATION COMPLETE!")
    print("=" * 60)
    print("✅ All tests passed successfully!")
    print()
    print("📋 VERIFIED FUNCTIONALITY:")
    print("   • User authentication (Salesman, Admin)")
    print("   • Partner creation with approval workflow")
    print("   • Pending approvals API endpoint")
    print("   • Partner approval API endpoint")
    print("   • Partner rejection API endpoint")
    print("   • Workflow state transitions")
    print()
    print("🌐 FRONTEND ACCESS:")
    print(f"   • Application: {FRONTEND_URL}")
    print(f"   • API Documentation: {API_BASE_URL.replace('/api/v1', '')}/docs")
    print()
    print("🧪 NEXT STEPS:")
    print("   1. Login to frontend as 'test_salesman' / 'password123'")
    print("   2. Create a new partner (should be pending)")
    print("   3. Logout and login as 'test_admin' / 'password123'")
    print("   4. Go to Approvals page and approve/reject partners")
    
    return True

if __name__ == "__main__":
    success = test_approval_workflow()
    sys.exit(0 if success else 1)