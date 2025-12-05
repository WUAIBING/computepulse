#!/usr/bin/env python3
"""
Diagnose Doubao API configuration issues.
"""

import os
import requests
import json

# Load API Key
volc_api_key = os.getenv('VOLC_API_KEY') or os.getenv('VITE_VOLC_API_KEY')

# Try to load from .env.local
if not volc_api_key:
    try:
        with open('.env.local', 'r') as f:
            for line in f:
                if 'VOLC_API_KEY' in line:
                    volc_api_key = line.split('=')[1].strip()
    except:
        pass

print("=" * 60)
print("Doubao API Diagnostic Tool")
print("=" * 60)

# Check 1: API Key
print("\n[1] Checking API Key...")
if volc_api_key:
    print(f"✓ API Key found: {volc_api_key[:10]}...{volc_api_key[-4:]}")
else:
    print("✗ API Key not found!")
    print("  Please set VOLC_API_KEY environment variable or add to .env.local")
    exit(1)

# Check 2: List available endpoints
print("\n[2] Listing available endpoints...")
try:
    url = "https://ark.cn-beijing.volces.com/api/v3/inference_endpoints?page_num=1&page_size=20"
    headers = {"Authorization": f"Bearer {volc_api_key}"}
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            print(f"✓ Found {len(data['items'])} endpoints:")
            for item in data['items']:
                status = item.get('status', 'Unknown')
                endpoint_id = item.get('id', 'N/A')
                model_ref = item.get('model_reference', {}).get('model_id', 'N/A')
                print(f"  - ID: {endpoint_id}")
                print(f"    Model: {model_ref}")
                print(f"    Status: {status}")
                print()
        else:
            print("✗ No endpoints found")
    else:
        print(f"✗ API Error: {response.status_code}")
        print(f"  Response: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Check 3: Test specific endpoint IDs
print("\n[3] Testing specific endpoint IDs...")
test_endpoints = [
    "doubao-seed-1-6-251015",  # Confirmed working endpoint
    "doubao-seed-1-6",  # Model ID (may not work directly)
]

for endpoint_id in test_endpoints:
    print(f"\nTesting: {endpoint_id}")
    try:
        # Try chat/completions API
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Authorization": f"Bearer {volc_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": endpoint_id,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"  ✓ chat/completions API works!")
        else:
            print(f"  ✗ Status: {response.status_code}")
            if response.status_code == 401:
                print(f"    Reason: Unauthorized (check API key or endpoint access)")
            elif response.status_code == 404:
                print(f"    Reason: Endpoint not found")
            else:
                print(f"    Response: {response.text[:200]}")
                
        # Try responses API with search
        url = "https://ark.cn-beijing.volces.com/api/v3/responses"
        payload = {
            "model": endpoint_id,
            "stream": False,
            "tools": [{"type": "web_search"}],
            "input": [{"role": "user", "content": [{"type": "input_text", "text": "Hello"}]}]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"  ✓ responses API (with search) works!")
        else:
            print(f"  ✗ responses API Status: {response.status_code}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Check 4: Recommendations
print("\n" + "=" * 60)
print("Recommendations:")
print("=" * 60)
print("""
1. Check the endpoint ID in your Volcengine console:
   https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint

2. Verify your API key has access to the endpoint:
   - Go to API Key management
   - Check permissions and quotas

3. Common endpoint ID formats:
   - doubao-seed-1-6 (model ID)
   - ep-20241204xxxxxx-xxxxx (endpoint ID)

4. Update the DOUBAO_ENDPOINT_ID in fetch_prices_optimized.py:
   DOUBAO_ENDPOINT_ID = "your-correct-endpoint-id"

5. If using model ID directly, you may need to use chat/completions API
   instead of responses API.
""")
