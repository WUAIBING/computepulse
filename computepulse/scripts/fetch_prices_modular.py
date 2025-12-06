#!/usr/bin/env python3
"""
Modular Data Fetcher for ComputePulse.
Uses the ai_core abstraction layer for pluggable AI agents.
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Load .env.local
try:
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.local')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
except Exception as e:
    print(f"Warning: Failed to load .env.local: {e}")

# Add script dir to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_core import AgentFactory

# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'data')
GPU_FILE = os.path.join(DATA_DIR, 'gpu_prices.json')
TOKEN_FILE = os.path.join(DATA_DIR, 'token_prices.json')
GRID_FILE = os.path.join(DATA_DIR, 'grid_load.json')
LOG_FILE = os.path.join(DATA_DIR, 'system_logs.json')
HISTORY_FILE = os.path.join(os.path.dirname(DATA_DIR), '..', 'history_data.json')
INDEX_FILE = os.path.join(DATA_DIR, 'industry_index.json')
INSIGHTS_FILE = os.path.join(DATA_DIR, 'dashboard_insights.json')
EXCHANGE_RATE_FILE = os.path.join(DATA_DIR, 'exchange_rate.json')

# Initialize Agents
print(f"[{datetime.now()}] Initializing AI Consortium Agents...")
architect = AgentFactory.create("qwen")      # Qwen
hunter = AgentFactory.create("deepseek")     # DeepSeek
researcher = AgentFactory.create("kimi")     # Kimi
analyst = AgentFactory.create("glm")         # GLM (The Analyst)
strategist = AgentFactory.create("minimax")  # MiniMax (The Strategist/Auditor)

# --- Helper Functions (Parsing & Validation) ---
# [Reuse the robust parsing logic from optimized script]
def clean_and_parse_json(content: Optional[str]) -> Any:
    if not content: return None
    try:
        # Try direct parse
        return json.loads(content)
    except:
        # Extract JSON block
        match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except: pass
        # Try finding first { or [
        match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except: pass
    return None

def validate_gpu_price(item):
    return isinstance(item, dict) and 'price' in item and isinstance(item['price'], (int, float)) and item['price'] > 0

def validate_token_price(item):
    return isinstance(item, dict) and 'input_price' in item and isinstance(item['input_price'], (int, float))

def validate_grid_data(data):
    return isinstance(data, dict) and 'annual_twh' in data and isinstance(data['annual_twh'], (int, float))

# --- Data Merging Logic ---
def merge_data(sources: List[Any], existing: Any, key_func) -> List[Any]:
    merged_dict = {}
    
    # Load existing
    if isinstance(existing, list):
        for item in existing:
            merged_dict[key_func(item)] = item
            
    # Merge new sources (later sources overwrite earlier ones)
    for source_data in sources:
        if isinstance(source_data, list):
            for item in source_data:
                merged_dict[key_func(item)] = item
                
    return list(merged_dict.values())

# --- Log Management ---
def append_log(agent_name: str, message: str, msg_type: str = "info"):
    log_entry = {
        "id": f"log_{int(time.time())}_{agent_name}",
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "message": message,
        "type": msg_type
    }
    
    try:
        data = {"logs": []}
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data["logs"].append(log_entry)
        # Keep last 50 logs
        if len(data["logs"]) > 50:
            data["logs"] = data["logs"][-50:]
            
        data["last_updated"] = datetime.now().isoformat()
        
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Log Error: {e}")

# --- Main Tasks ---

def fetch_gpu_prices():
    print(f"[{datetime.now()}] Task: Fetch GPU Prices")
    prompt = "Search for latest hourly rental prices for NVIDIA H100, A100, RTX 4090 GPUs on major cloud providers (AWS, Lambda, RunPod, Vast.ai). Return JSON list: [{'provider': 'AWS', 'gpu': 'H100', 'price': 3.5, 'region': 'US'}...]"
    
    # Parallel-like execution (sequential here but agents are independent)
    append_log("Qwen", "Initiating global GPU price scan...", "action")
    qwen_res = architect.search(prompt)
    
    append_log("DeepSeek", "Verifying price consistency...", "action")
    ds_res = hunter.generate(prompt) # DeepSeek might not have search enabled in config, uses reasoning
    
    append_log("Kimi", "Checking market news for hidden price hikes...", "action")
    kimi_res = researcher.search(prompt)
    
    # Parse
    q_data = clean_and_parse_json(qwen_res)
    d_data = clean_and_parse_json(ds_res)
    k_data = clean_and_parse_json(kimi_res)
    
    # Merge
    existing = []
    if os.path.exists(GPU_FILE):
        with open(GPU_FILE, 'r', encoding='utf-8') as f: existing = json.load(f)
        
    key_func = lambda x: f"{x.get('provider')}_{x.get('gpu')}"
    # Priority: Existing < Kimi < Qwen < DeepSeek
    final = merge_data([k_data, q_data, d_data], existing, key_func)
    
    with open(GPU_FILE, 'w', encoding='utf-8') as f: json.dump(final, f, indent=2)
    print(f"GPU Data Saved: {len(final)} records")
    append_log("System", f"GPU Database updated with {len(final)} records.", "success")

def fetch_token_prices():
    print(f"[{datetime.now()}] Task: Fetch Token Prices")
    prompt = "Search official API pricing for GPT-4o, Claude 3.5, Qwen-Max, DeepSeek-V3. Return JSON list: [{'model': 'GPT-4o', 'provider': 'OpenAI', 'input_price': 5.0, 'output_price': 15.0}...]"
    
    append_log("Qwen", "Querying API pricing endpoints...", "action")
    q_data = clean_and_parse_json(architect.search(prompt))
    
    append_log("Kimi", "Cross-referencing with developer docs...", "action")
    k_data = clean_and_parse_json(researcher.search(prompt))
    
    existing = []
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f: existing = json.load(f)
        
    key_func = lambda x: f"{x.get('provider')}_{x.get('model')}"
    final = merge_data([k_data, q_data], existing, key_func)
    
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f: json.dump(final, f, indent=2)
    print(f"Token Data Saved: {len(final)} records")
    append_log("System", f"Token Pricing updated.", "success")

def fetch_grid_load():
    print(f"[{datetime.now()}] Task: Fetch Grid Load")
    prompt = "Search for 2024/2025 global AI data center energy consumption (TWh) and real-time GW estimates. Return JSON: {'annual_twh': 120, 'estimated_gw': 15, 'kwh_price': 0.12}"
    
    append_log("Kimi", "Analyzing global energy reports...", "action")
    k_res = researcher.search(prompt)
    k_data = clean_and_parse_json(k_res)
    
    if validate_grid_data(k_data):
        with open(GRID_FILE, 'w', encoding='utf-8') as f: json.dump(k_data, f, indent=2)
        print("Grid Data Saved")
        append_log("System", "Grid Load metrics synchronized.", "success")
    else:
        print("Grid Data Validation Failed")

def validate_and_fix():
    """Data Quality Check using MiniMax (The Strategist) with Interleaved Thinking"""
    print(f"[{datetime.now()}] Task: Strategic Audit (MiniMax)")
    
    try:
        # Load current data
        with open(GPU_FILE, 'r', encoding='utf-8') as f: gpu_data = json.load(f)
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f: token_data = json.load(f)
        with open(GRID_FILE, 'r', encoding='utf-8') as f: grid_data = json.load(f)
        
        # Safe calculation of averages
        valid_gpu_prices = [d.get('price') for d in gpu_data if isinstance(d.get('price'), (int, float))]
        avg_gpu = sum(valid_gpu_prices)/len(valid_gpu_prices) if valid_gpu_prices else 0
        
        valid_token_prices = [d.get('input_price') for d in token_data if isinstance(d.get('input_price'), (int, float))]
        avg_token = sum(valid_token_prices)/len(valid_token_prices) if valid_token_prices else 0
        
        grid_val = grid_data.get('annual_twh') if grid_data else None
        
        summary_text = f"GPU Prices (Avg): ${avg_gpu:.2f}. " if valid_gpu_prices else "No valid GPU data. "
        summary_text += f"Token Prices (Avg Input): ${avg_token:.2f}. " if valid_token_prices else "No valid Token data. "
        summary_text += f"Grid Load: {grid_val if grid_val is not None else 'N/A'} TWh."
        
        prompt = f"""
        You are the Consortium Strategist (MiniMax).
        
        Review the collected data:
        {summary_text}
        
        Task:
        1. Audit the data for logical inconsistencies (e.g. extremely low GPU price but high energy cost).
        2. Provide a strategic recommendation for the Consortium.
        
        Output format: Just the audit conclusion in one sentence.
        """
        
        append_log("MiniMax", "Initiating deep logic audit...", "action")
        
        # This call generates the <thinking>... response
        response = strategist.generate(prompt)
        
        if response:
            # Parse out thinking vs content
            thinking_match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
            content = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL).strip()
            
            if thinking_match:
                thinking_process = thinking_match.group(1).strip()
                # Log the thinking process!
                # Truncate if too long for UI
                display_thought = thinking_process[:200] + "..." if len(thinking_process) > 200 else thinking_process
                append_log("MiniMax", f"Thinking: {display_thought}", "info")
            
            print(f"MiniMax Audit: {content}")
            append_log("MiniMax", f"Audit Result: {content}", "success")
            
    except Exception as e:
        print(f"Audit Error: {e}")

def generate_market_insight():
    """Generate a daily market summary using DeepSeek (The Analyst Substitute)"""
    print(f"[{datetime.now()}] Task: Market Insight (DeepSeek)")
    
    try:
        # Read collected data to form the context
        with open(GPU_FILE, 'r', encoding='utf-8') as f: gpu_data = json.load(f)
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f: token_data = json.load(f)
        with open(GRID_FILE, 'r', encoding='utf-8') as f: grid_data = json.load(f)
        
        # Load history data for comparison
        history_data = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f: history_data = json.load(f)
            
        # Get previous day's data if available
        prev_gpu_summary = "No history"
        if history_data:
            last_entry = history_data[-1]
            prev_gpu_summary = f"Last run: {last_entry.get('date', 'Unknown')}"

        # Save current run to history (Simple append for now)
        today_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "gpu_count": len(gpu_data) if gpu_data else 0,
            "token_count": len(token_data) if token_data else 0,
            "grid_twh": grid_data.get('annual_twh', 0)
        }
        
        history_data.append(today_entry)
        # Keep last 30 days
        if len(history_data) > 30: history_data = history_data[-30:]
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2)

        # Prepare a summary context
        gpu_summary = f"{len(gpu_data)} GPU records. Avg price example: {gpu_data[0].get('price', 'N/A')}" if gpu_data else "No GPU data"
        
        prompt = f"""
        You are 'The Analyst' (DeepSeek), a cynical but sharp AI market observer in a cyberpunk future.
        
        Current Data:
        - GPU Market: {gpu_summary}
        - AI Grid Load: {grid_data.get('annual_twh', 'N/A')} TWh/year
        
        Historical Context:
        - {prev_gpu_summary}
        
        Task:
        Generate a single, witty, insightful sentence (max 25 words) comparing today's market state with the past.
        If data is flat, complain about the stagnation. If it moves, analyze the 'Pulse'.
        Style: Professional but with a slight futuristic/noir edge.
        """
        
        append_log("DeepSeek", "Synthesizing cross-market data streams...", "action")
        # Use hunter (DeepSeek)
        insight = hunter.generate(prompt)
        
        if insight:
            clean_insight = insight.strip().replace('"', '')
            # Remove thinking block if present
            clean_insight = re.sub(r'<thinking>.*?</thinking>', '', clean_insight, flags=re.DOTALL).strip()
            print(f"DeepSeek Insight: {clean_insight}")
            append_log("DeepSeek", f"Daily Insight: {clean_insight}", "success")
        else:
            print("DeepSeek failed to generate insight")
            
    except Exception as e:
        print(f"Insight Generation Error: {e}")

def generate_industry_index():
    """Generate AI Industry Prosperity Index based on GPU prices and Capex trends using DeepSeek"""
    print(f"[{datetime.now()}] Task: AI Industry Index (DeepSeek)")
    
    try:
        # Context from other data
        with open(GPU_FILE, 'r', encoding='utf-8') as f: gpu_data = json.load(f)
        
        valid_gpu_prices = [d.get('price') for d in gpu_data if isinstance(d.get('price'), (int, float))]
        avg_price = sum(valid_gpu_prices) / len(valid_gpu_prices) if valid_gpu_prices else 0
        
        prompt = f"""
        You are a Chief Financial Analyst for the AI Sector.
        
        Task: Calculate the "AI Industry Prosperity Index" (0-100).
        
        Inputs:
        1. Current Avg H100/A100 Rental Price: ${avg_price:.2f}/hr
        2. External Knowledge: Search for latest 2024/2025 Capex guidance from Hyperscalers (Microsoft, Google, Meta, AWS). Are they increasing or cutting AI spend?
        
        Algorithm:
        - Base Score: 50
        - If Capex is increasing aggressively: +20
        - If GPU rental prices are stable/high (demand > supply): +10
        - If GPU prices are crashing (oversupply): -10
        - If new models (GPT-5, Gemini 2) are rumored/released: +10
        
        Output JSON ONLY:
        {{
            "score": 85,
            "trend": "up",
            "summary": "Capex expansion from Microsoft and Google fuels the index, despite slight spot price softening.",
            "capex_sentiment": "bullish"
        }}
        """
        
        append_log("DeepSeek", "Analyzing Big Tech Capex reports...", "action")
        # Use hunter (DeepSeek)
        res = hunter.generate(prompt)
        data = clean_and_parse_json(res)
        
        if data and 'score' in data:
            data['last_updated'] = datetime.now().isoformat()
            with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Index Saved: {data['score']}")
            append_log("System", f"AI Prosperity Index updated: {data['score']}", "success")
        else:
            print("Failed to generate Index")
            
    except Exception as e:
        print(f"Index Error: {e}")

def generate_dashboard_insights():
    """Generate agent-specific insights for dashboard cards using MiniMax (The Strategist)"""
    print(f"[{datetime.now()}] Task: Dashboard Insights (MiniMax)")
    
    try:
        # Context
        with open(GPU_FILE, 'r', encoding='utf-8') as f: gpu_data = json.load(f)
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f: token_data = json.load(f)
        with open(GRID_FILE, 'r', encoding='utf-8') as f: grid_data = json.load(f)
        
        # Safe calculation of averages
        valid_gpu_prices = [d.get('price') for d in gpu_data if isinstance(d.get('price'), (int, float))]
        avg_gpu = sum(valid_gpu_prices)/len(valid_gpu_prices) if valid_gpu_prices else 0
        
        valid_token_prices = [d.get('input_price') for d in token_data if isinstance(d.get('input_price'), (int, float))]
        avg_token = sum(valid_token_prices)/len(valid_token_prices) if valid_token_prices else 0
        
        grid_val = grid_data.get('annual_twh') if grid_data else None
        
        prompt = f"""
        You are MiniMax, the Strategist. 
        
        Task: Generate 3 distinct, professional one-sentence insights for the dashboard cards, roleplaying as specific agents.
        
        Data Context:
        - Hardware (Qwen): Avg H100 Price ${avg_gpu:.2f}/hr. 
        - Tokens (DeepSeek): Avg Input Price ${avg_token:.2f}/1M.
        - Energy (Kimi): Annual Load {grid_val if grid_val is not None else 'N/A'} TWh.
        
        Requirements:
        1. GCCI (Hardware/Qwen): Focus on supply chain, chip availability, or capex.
        2. GTPI (Tokens/DeepSeek): Focus on API price wars, efficiency, or model competition.
        3. GAGL (Energy/Kimi): Focus on grid strain, nuclear adoption, or carbon footprint.
        4. AIPI (Macro/GLM): Focus on overall industry sentiment, bubble risks, or growth sustainability.
        
        Output JSON ONLY:
        {{
            "gcci": {{ "agent": "Qwen", "text": "H100 supply stabilizes as US-East availability improves." }},
            "gtpi": {{ "agent": "DeepSeek", "text": "Token costs plummeting due to aggressive model distillation." }},
            "gagl": {{ "agent": "Kimi", "text": "Nuclear baseload becoming critical for new GW-scale clusters." }},
            "aipi": {{ "agent": "GLM", "text": "Market consolidation phase indicates a healthy maturation of the AI sector." }}
        }}
        """
        
        append_log("MiniMax", "Coordinating agent insights...", "action")
        res = strategist.generate(prompt)
        
        # Strip <thinking> if present
        if res:
            res = re.sub(r'<thinking>.*?</thinking>', '', res, flags=re.DOTALL).strip()
            
        data = clean_and_parse_json(res)
        
        if data and 'gcci' in data:
            with open(INSIGHTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print("Dashboard Insights Saved")
        else:
            print("Failed to generate Dashboard Insights")
            
    except Exception as e:
        print(f"Insights Error: {e}")

def fetch_exchange_rate():
    """Fetch real-time USD to CNY exchange rate using Kimi (Researcher) with Web Search"""
    print(f"[{datetime.now()}] Task: Fetch Exchange Rate (Kimi)")
    
    try:
        prompt = """
        Please search for the current real-time USD to CNY exchange rate (today).
        
        Output valid JSON ONLY:
        {
            "from": "USD",
            "to": "CNY",
            "rate": 7.28, 
            "timestamp": "2024-..."
        }
        """
        
        append_log("Kimi", "Searching global forex markets...", "action")
        
        # Use researcher (Kimi) which has .search() capability
        # We use .search() to ensure 'enable_search' is True
        res = researcher.search(prompt)
        
        data = clean_and_parse_json(res)
        
        if data and 'rate' in data:
            # Validate rate is reasonable (e.g. 6.0 - 8.0)
            if 6.0 < data['rate'] < 8.0:
                with open(EXCHANGE_RATE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                print(f"Exchange Rate Saved: 1 USD = {data['rate']} CNY")
                append_log("System", f"Exchange rate updated: {data['rate']}", "success")
            else:
                print(f"Rate {data['rate']} seems outlier, ignoring.")
        else:
            print("Failed to fetch exchange rate, using default")
            # Fallback if file doesn't exist or valid
            if not os.path.exists(EXCHANGE_RATE_FILE):
                default_data = {
                    "from": "USD",
                    "to": "CNY", 
                    "rate": 7.25,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Fallback default"
                }
                with open(EXCHANGE_RATE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2)
            
    except Exception as e:
        print(f"Exchange Rate Error: {e}")

if __name__ == "__main__":
    # Ensure data dir exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    try:
        fetch_gpu_prices()
        fetch_token_prices()
        fetch_grid_load()
        fetch_exchange_rate()
        validate_and_fix()
        generate_market_insight()
        generate_industry_index()
        generate_dashboard_insights()
    except Exception as e:
        print(f"Critical Error: {e}")
        append_log("System", f"Critical Failure: {str(e)}", "warning")
        sys.exit(1)
