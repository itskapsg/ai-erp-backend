#!/bin/bash

echo "Testing demo user login..."
for user in admin manager accountant salesman; do
  echo -n "Testing $user:${user}123... "
  response=$(curl -s -X POST http://localhost:54279/api/v1/auth/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$user&password=${user}123")
  
  if echo "$response" | grep -q "access_token"; then
    token=$(echo "$response" | jq -r '.access_token')
    echo "✅ SUCCESS (Token: ${token:0:20}...)"
  else
    echo "❌ FAILED"
    echo "Response: $response"
  fi
done
