import requests
import os
import json

volc_api_key = os.getenv('VOLC_API_KEY') or os.getenv('VITE_VOLC_API_KEY')
if not volc_api_key:
    try:
        with open('.env.local', 'r') as f:
            for line in f:
                if 'VOLC_API_KEY' in line:
                    volc_api_key = line.split('=')[1].strip()
    except:
        pass

ENDPOINT_ID = "doubao-seed-1-6-251015"

print(f"Retrying Doubao Search (Plugin Enabled Check)...")
# User's URL
url = "https://ark.cn-beijing.volces.com/api/v3/responses" 

headers = {
    "Authorization": f"Bearer {volc_api_key}",
    "Content-Type": "application/json"
}

# User's Payload Structure
payload = {
    "model": ENDPOINT_ID,
    "stream": False,
    "tools": [
        {"type": "web_search"}
    ],
    "input": [ 
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "What is the NVIDIA (NVDA) stock price right now? Please include the time."
                }
            ]
        }
    ]
}

print(f"Requesting {url}...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        res_json = response.json()
        # Print full response for analysis
        # print(json.dumps(res_json, indent=2, ensure_ascii=False))
        
        # Extract content
        if 'output' in res_json:
            for item in res_json['output']:
                if item.get('type') == 'message' and item.get('content'):
                    print("\n[Response Content]:")
                    print(item['content'][0]['text'])
                elif item.get('type') == 'reasoning':
                    print("\n[Reasoning Summary]:")
                    if 'summary' in item:
                        for s in item['summary']:
                            print(s.get('text', ''))
    else:
        print(f"Error Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
