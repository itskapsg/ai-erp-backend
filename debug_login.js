// Debug script to test login functionality
const axios = require('axios');

async function testLogin() {
    console.log('🔍 Testing login functionality...');
    
    try {
        // Test 1: Direct API call
        console.log('\n1. Testing direct API call...');
        const formData = new URLSearchParams();
        formData.append('username', 'admin');
        formData.append('password', 'admin123');
        
        const response = await axios.post('http://localhost:8001/api/v1/auth/token', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        
        console.log('✅ Direct API call successful!');
        console.log('Token:', response.data.access_token.substring(0, 50) + '...');
        console.log('User:', response.data.username);
        console.log('Role:', response.data.role);
        
        // Test 2: Test with token
        console.log('\n2. Testing authenticated request...');
        const authResponse = await axios.get('http://localhost:8001/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${response.data.access_token}`
            }
        });
        
        console.log('✅ Authenticated request successful!');
        console.log('User data:', authResponse.data);
        
        // Test 3: Test CORS preflight
        console.log('\n3. Testing CORS preflight...');
        const corsResponse = await axios.options('http://localhost:8001/api/v1/auth/token', {
            headers: {
                'Origin': 'http://localhost:56000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        });
        
        console.log('✅ CORS preflight successful!');
        console.log('CORS headers:', corsResponse.headers);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        if (error.response) {
            console.error('Status:', error.response.status);
            console.error('Data:', error.response.data);
        }
    }
}

testLogin();