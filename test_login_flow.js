// Test login flow using the same API configuration as the frontend
const API_BASE_URL = 'http://95.111.253.134:54279/api/v1';

console.log('🔗 Testing API Base URL:', API_BASE_URL);

// Test login
async function testLogin() {
    try {
        console.log('🧪 Testing login with admin/admin123...');
        
        const formData = new URLSearchParams();
        formData.append('username', 'admin');
        formData.append('password', 'admin123');
        
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Login successful!');
        console.log('📋 Response:', {
            token_type: data.token_type,
            user_id: data.user_id,
            username: data.username,
            role: data.role,
            token_preview: data.access_token.substring(0, 50) + '...'
        });
        
        // Test authenticated request
        console.log('🧪 Testing authenticated request...');
        const authResponse = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${data.access_token}`
            }
        });
        
        if (!authResponse.ok) {
            throw new Error(`Auth test failed! status: ${authResponse.status}`);
        }
        
        const authData = await authResponse.json();
        console.log('✅ Authenticated request successful!');
        console.log('👤 User info:', authData);
        
        return true;
        
    } catch (error) {
        console.error('❌ Login test failed:', error.message);
        return false;
    }
}

// Run the test
testLogin().then(success => {
    if (success) {
        console.log('\n🎉 LOGIN FLOW TEST PASSED! The backend API is working correctly.');
        console.log('📝 Frontend should be able to login using the same configuration.');
    } else {
        console.log('\n💥 LOGIN FLOW TEST FAILED! There may be an issue with the backend.');
    }
});