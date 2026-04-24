#!/bin/bash
# Quick API test script

echo "Testing backend health..."
curl -s https://lux-beyond-production.up.railway.app/health | jq

echo -e "\n\nTesting expenses endpoint (should require auth)..."
curl -s https://lux-beyond-production.up.railway.app/expenses

echo -e "\n\nTo test with authentication, you need to:"
echo "1. Sign in to https://lux-beyond-homes.firebaseapp.com/"
echo "2. Open browser console"
echo "3. Run: firebase.auth().currentUser.getIdToken().then(token => console.log(token))"
echo "4. Copy the token and run:"
echo "   curl -H 'Authorization: Bearer YOUR_TOKEN' https://lux-beyond-production.up.railway.app/expenses"
