#!/usr/bin/env python3
"""
Deep Verification Script for GLM (ZhipuAI).
Directly tests the GLM-4 model using ZhipuAI SDK.
"""

import os
import sys
import time
from datetime import datetime

# Ensure we can load env
try:
    from dotenv import load_dotenv
    load_dotenv('.env.local')
except ImportError:
    try:
        with open('.env.local', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k] = v
    except: pass

try:
    from zhipuai import ZhipuAI
except ImportError:
    print("Warning: zhipuai package not installed. Switching to OpenAI compatible client.")
    # Fallback to OpenAI client if zhipuai is missing
    try:
        from openai import OpenAI
        ZhipuAI = None # Marker
    except ImportError:
        print("Error: openai package not installed either.")
        sys.exit(1)

API_KEY = os.getenv('ZHIPU_API_KEY')
print(f"Using GLM API Key: {API_KEY[:8]}...{API_KEY[-4:] if API_KEY else 'None'}")

def verify_glm():
    print("\n" + "="*60)
    print("🚀 Starting Verification for GLM (ZhipuAI)")
    print("="*60)
    
    if not API_KEY:
        print("❌ Error: Missing ZHIPU_API_KEY")
        return

    model = "glm-4"
    query = "What is the capital of France?" # Simple knowledge query to test connectivity
    
    print(f"\nModel: {model}")
    print(f"Query: {query}")
    print("\nSending request to ZhipuAI...")
    
    start_time = time.time()
    
    try:
        if ZhipuAI:
            # Use official SDK
            client = ZhipuAI(api_key=API_KEY)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": query}],
                stream=False
            )
            content = response.choices[0].message.content
        else:
            # Use OpenAI compatible client
            # ZhipuAI compatible base URL
            base_url = "https://open.bigmodel.cn/api/paas/v4/"
            client = OpenAI(api_key=API_KEY, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": query}],
                stream=False
            )
            content = response.choices[0].message.content

        duration = time.time() - start_time
        print(f"\n⏱️ Request Duration: {duration:.2f}s")
        
        print("\n" + "-"*60)
        print("📦 Response Content")
        print("-" * 60)
        
        print(f"\n[Content]:\n{content}")
        
        if "Paris" in content:
            print("\n✅ GLM is Online and Responding Correctly.")
        else:
            print("\n❓ GLM Responded but content is unexpected.")

    except Exception as e:
        print(f"❌ Exception: {e}")
        if "401" in str(e):
            print("👉 Hint: API Key might be invalid or expired.")

if __name__ == "__main__":
    verify_glm()
