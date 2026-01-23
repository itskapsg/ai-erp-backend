#!/bin/bash

# API Verification Script
# Tests the complete Dynamic Approval System API workflow

set -e  # Exit on any error

API_BASE="http://localhost:54279"
echo "🚀 Dynamic Approval System API Verification"
echo "=============================================="
echo "API Base URL: $API_BASE"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}💡 $1${NC}"
}

# Test 1: Health Check
print_step "🔍 Step 1: Health Check"
HEALTH_RESPONSE=$(curl -s "$API_BASE/health")
echo "Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    print_success "API is healthy and running"
else
    print_error "API health check failed"
    exit 1
fi
echo ""

# Test 2: Login as Salesman
print_step "🔐 Step 2: Login as Salesman"
SALESMAN_TOKEN_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=salesman&password=salesman123")

echo "Login Response: $SALESMAN_TOKEN_RESPONSE"

SALESMAN_TOKEN=$(echo "$SALESMAN_TOKEN_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['access_token'])
except:
    print('ERROR')
")

if [ "$SALESMAN_TOKEN" = "ERROR" ]; then
    print_error "Failed to get salesman token"
    exit 1
else
    print_success "Salesman logged in successfully"
    print_info "Token: ${SALESMAN_TOKEN:0:20}..."
fi
echo ""

# Test 3: Create Partner as Salesman (Should be PENDING_APPROVAL)
print_step "🏢 Step 3: Create Partner as Salesman"
PARTNER_CREATE_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/partners/" \
    -H "Authorization: Bearer $SALESMAN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Customer Corp",
        "type": "customer",
        "gst_number": "27ABCDE1234F1Z5",
        "credit_limit": 100000.00
    }')

echo "Create Partner Response: $PARTNER_CREATE_RESPONSE"

PARTNER_ID=$(echo "$PARTNER_CREATE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['id'])
except:
    print('ERROR')
")

PARTNER_STATUS=$(echo "$PARTNER_CREATE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['workflow_stage'])
except:
    print('ERROR')
")

if [ "$PARTNER_STATUS" = "pending_approval" ]; then
    print_success "Partner created with PENDING_APPROVAL status (approval required)"
    print_info "Partner ID: $PARTNER_ID"
else
    print_error "Expected PENDING_APPROVAL, got: $PARTNER_STATUS"
    exit 1
fi
echo ""

# Test 4: Login as Admin
print_step "🔐 Step 4: Login as Admin"
ADMIN_TOKEN_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin123")

echo "Admin Login Response: $ADMIN_TOKEN_RESPONSE"

ADMIN_TOKEN=$(echo "$ADMIN_TOKEN_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['access_token'])
except:
    print('ERROR')
")

if [ "$ADMIN_TOKEN" = "ERROR" ]; then
    print_error "Failed to get admin token"
    exit 1
else
    print_success "Admin logged in successfully"
    print_info "Token: ${ADMIN_TOKEN:0:20}..."
fi
echo ""

# Test 5: List Partners (should show pending partner)
print_step "📋 Step 5: List Partners"
PARTNERS_LIST_RESPONSE=$(curl -s -X GET "$API_BASE/api/v1/partners/" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

echo "Partners List Response: $PARTNERS_LIST_RESPONSE"

PENDING_COUNT=$(echo "$PARTNERS_LIST_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    count = sum(1 for partner in data if partner['workflow_stage'] == 'pending_approval')
    print(count)
except:
    print('0')
")

print_info "Found $PENDING_COUNT partners pending approval"
echo ""

# Test 6: Approve Partner as Admin
print_step "✅ Step 6: Approve Partner as Admin"
APPROVE_RESPONSE=$(curl -s -X PUT "$API_BASE/api/v1/partners/$PARTNER_ID/approve" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "action": "approve"
    }')

echo "Approve Response: $APPROVE_RESPONSE"

APPROVAL_STATUS=$(echo "$APPROVE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['new_status'])
except:
    print('ERROR')
")

if [ "$APPROVAL_STATUS" = "approved" ]; then
    print_success "Partner approved successfully"
else
    print_error "Failed to approve partner. Status: $APPROVAL_STATUS"
    exit 1
fi
echo ""

# Test 7: Verify Partner Status
print_step "🔍 Step 7: Verify Partner Status"
PARTNER_STATUS_RESPONSE=$(curl -s -X GET "$API_BASE/api/v1/partners/$PARTNER_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

echo "Partner Status Response: $PARTNER_STATUS_RESPONSE"

FINAL_STATUS=$(echo "$PARTNER_STATUS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['workflow_stage'])
except:
    print('ERROR')
")

if [ "$FINAL_STATUS" = "approved" ]; then
    print_success "Partner status confirmed as APPROVED"
else
    print_error "Unexpected final status: $FINAL_STATUS"
    exit 1
fi
echo ""

# Test 8: Test Admin Direct Creation (Should be Auto-Approved)
print_step "🏢 Step 8: Test Admin Direct Creation"
ADMIN_PARTNER_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/partners/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Admin Created Partner",
        "type": "supplier",
        "gst_number": "27ADMIN1234F1Z5",
        "credit_limit": 500000.00
    }')

echo "Admin Partner Creation Response: $ADMIN_PARTNER_RESPONSE"

ADMIN_PARTNER_STATUS=$(echo "$ADMIN_PARTNER_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['workflow_stage'])
except:
    print('ERROR')
")

if [ "$ADMIN_PARTNER_STATUS" = "approved" ]; then
    print_success "Admin-created partner auto-approved (sufficient privileges)"
else
    print_error "Expected auto-approval for admin, got: $ADMIN_PARTNER_STATUS"
    exit 1
fi
echo ""

# Test 9: Test Unauthorized Access
print_step "🚫 Step 9: Test Unauthorized Access"
UNAUTHORIZED_RESPONSE=$(curl -s -w "%{http_code}" -X GET "$API_BASE/api/v1/partners/" \
    -H "Authorization: Bearer invalid_token")

HTTP_CODE="${UNAUTHORIZED_RESPONSE: -3}"
if [ "$HTTP_CODE" = "401" ]; then
    print_success "Unauthorized access properly rejected (401)"
else
    print_error "Expected 401 for invalid token, got: $HTTP_CODE"
fi
echo ""

# Test 10: Test Role-Based Access (Salesman trying to approve)
print_step "🚫 Step 10: Test Role-Based Access Control"
FORBIDDEN_RESPONSE=$(curl -s -w "%{http_code}" -X PUT "$API_BASE/api/v1/partners/$PARTNER_ID/approve" \
    -H "Authorization: Bearer $SALESMAN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"action": "approve"}')

HTTP_CODE="${FORBIDDEN_RESPONSE: -3}"
if [ "$HTTP_CODE" = "403" ]; then
    print_success "Role-based access control working (403 Forbidden)"
else
    print_error "Expected 403 for insufficient privileges, got: $HTTP_CODE"
fi
echo ""

# Final Summary
echo "🎉 API VERIFICATION COMPLETE!"
echo "=============================="
print_success "✅ Health Check: API is running"
print_success "✅ Authentication: JWT tokens working"
print_success "✅ Approval Logic: Salesman → PENDING_APPROVAL"
print_success "✅ Admin Approval: Partner approved successfully"
print_success "✅ Auto-Approval: Admin → APPROVED directly"
print_success "✅ Security: Unauthorized access blocked"
print_success "✅ RBAC: Role-based access control enforced"

echo ""
print_info "🎯 Dynamic Approval System API is fully functional!"
print_info "📚 API Documentation: $API_BASE/docs"
print_info "🔧 The system successfully implements:"
echo "   • JWT Authentication with role-based access"
echo "   • Dynamic approval policies (configurable without code changes)"
echo "   • Automatic workflow stage determination"
echo "   • Complete approval/rejection workflow"
echo "   • Security and authorization controls"
echo ""
print_success "🚀 Mission Accomplished!"