#!/usr/bin/env python3
"""
Deep Verification Script for Kimi (Moonshot) Search Capability.
Uses DashScope SDK with Moonshot-Kimi-K2-Instruct model.
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
    import dashscope
    from openai import OpenAI
except ImportError:
    print("Error: dashscope/openai package not installed")
    sys.exit(1)

API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('VITE_DASHSCOPE_API_KEY')
print(f"Using API Key: {API_KEY[:8]}...{API_KEY[-4:] if API_KEY else 'None'}")

def verify_kimi_search():
    print("\n" + "="*60)
    print("🚀 Starting Deep Verification for Kimi (Moonshot) Web Search")
    print("="*60)
    
    model = "Moonshot-Kimi-K2-Instruct"
    # Pure, direct query without any pre-injected knowledge
    query = "What is the current real-time exchange rate of 1 USD to CNY? Please provide the exact rate and the current time."
    
    # Base URL for DashScope compatible mode
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    print(f"\nModel: {model}")
    print(f"Query: {query}")
    print(f"Config: extra_body={{'enable_search': True}}")
    print("\nSending request to DashScope (OpenAI Compat)...")
    
    client = OpenAI(api_key=API_KEY, base_url=base_url)
    
    start_time = time.time()
    
    try:
        messages = [
            {"role": "system", "content": "You are Kimi, an AI assistant with real-time internet access. When asked for current information like exchange rates, you MUST use your search tool to find the latest data."},
            {"role": "user", "content": query}
        ]
        
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            extra_body={"enable_search": True}, # The magic switch for Kimi on DashScope
            stream=False
        )
        
        duration = time.time() - start_time
        print(f"\n⏱️ Request Duration: {duration:.2f}s")
        
        print("\n" + "-"*60)
        print("📦 Raw Response Analysis")
        print("-" * 60)
        
        message = completion.choices[0].message
        content = message.content
        
        print(f"\n[Content]:\n{content}")
        
        # Heuristic Check
        print("\n" + "-"*60)
        print("🕵️ Evidence of Search")
        print("-" * 60)
        
        has_price = "7." in content and ("CNY" in content or "RMB" in content)
        has_time = "2024" in content or "2025" in content or "UTC" in content
        
        if has_price:
            print("✅ Found Exchange Rate data")
        else:
            print("⚠️ Missing exchange rate data")
            
        if has_time:
            print("✅ Found Timestamp")
        else:
            print("⚠️ Missing timestamp")
            
        # Kimi often uses <search> tags in its internal thought process if exposed, 
        # or just integrates it naturally.
        if "search" in content.lower():
            print("ℹ️ Content mentions 'search'")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    verify_kimi_search()
