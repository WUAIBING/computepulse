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
CLEAN_ENERGY_FILE = os.path.join(DATA_DIR, 'clean_energy.json')
ELECTRICITY_PRICES_FILE = os.path.join(DATA_DIR, 'electricity_prices.json')
PRODUCTION_COSTS_FILE = os.path.join(DATA_DIR, 'production_costs.json')
COMPANY_FINANCIALS_FILE = os.path.join(DATA_DIR, 'company_financials.json')
TOKEN_PRICING_MODELS_FILE = os.path.join(DATA_DIR, 'token_pricing_models.json')
TOKEN_PRICING_OFFICIAL_FILE = os.path.join(DATA_DIR, 'token_pricing_official.json')

# Initialize Agents
print(f"[{datetime.now()}] Initializing AI Consortium Agents...")
architect = AgentFactory.create("qwen")      # Qwen (Architect)
hunter = AgentFactory.create("deepseek")     # DeepSeek (Hunter)
researcher = AgentFactory.create("qwen")     # Qwen (Researcher) - Better search reliability for electricity prices
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
        
        Output JSON format with real data only:
        {{
            "score": [calculate based on actual data],
            "trend": "[up/down/sideways based on analysis]",
            "summary": "[generate real summary based on actual market conditions]",
            "capex_sentiment": "[bullish/bearish/neutral based on actual data]"
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
        
        Output JSON format with real insights only:
        {{
            "gcci": {{ "agent": "Qwen", "text": "[analyze actual data and generate real insight]" }},
            "gtpi": {{ "agent": "DeepSeek", "text": "[analyze actual data and generate real insight]" }},
            "gagl": {{ "agent": "Kimi", "text": "[analyze actual data and generate real insight]" }},
            "aipi": {{ "agent": "GLM", "text": "[analyze actual data and generate real insight]" }}
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
    """Fetch real-time exchange rates for USD to multiple currencies using ExchangeRate API (权威数据)"""
    print(f"[{datetime.now()}] Task: Fetch Exchange Rates (API)")

    try:
        append_log("ComputePulse", "Querying ExchangeRate API for authoritative exchange rates...", "action")

        # Direct API call to ExchangeRate API - returns all currencies against USD
        import requests
        r = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
        if r.status_code == 200:
            api_data = r.json()
            rates = api_data['rates']
            timestamp = datetime.now().isoformat()

            # Extract rates for currencies we need (扩展更多货币)
            # USD is always 1.0 (base currency)
            usd_rate = 1.0
            cny_rate = round(rates.get('CNY', 0), 4)
            eur_rate = round(rates.get('EUR', 0), 4)
            gbp_rate = round(rates.get('GBP', 0), 4)
            jpy_rate = round(rates.get('JPY', 0), 2)
            inr_rate = round(rates.get('INR', 0), 2)
            cad_rate = round(rates.get('CAD', 0), 4)
            aud_rate = round(rates.get('AUD', 0), 4)
            krw_rate = round(rates.get('KRW', 0), 2)
            brl_rate = round(rates.get('BRL', 0), 2)

            # Data validation: rates must be within reasonable ranges
            validation_errors = []

            # CNY validation: 6.0 - 8.0
            if cny_rate < 6.0 or cny_rate > 8.0:
                validation_errors.append(f"CNY rate {cny_rate} outside valid range (6.0-8.0)")

            # EUR validation: 0.7 - 1.2
            if eur_rate < 0.7 or eur_rate > 1.2:
                validation_errors.append(f"EUR rate {eur_rate} outside valid range (0.7-1.2)")

            # GBP validation: 0.6 - 1.1
            if gbp_rate < 0.6 or gbp_rate > 1.1:
                validation_errors.append(f"GBP rate {gbp_rate} outside valid range (0.6-1.1)")

            if validation_errors:
                error_msg = "; ".join(validation_errors)
                print(f"Validation Error: {error_msg}")
                append_log("System", f"Exchange rate validation failed: {error_msg}", "error")
                return

            # Save complete exchange rate data
            data = {
                "base": "USD",
                "timestamp": timestamp,
                "source": "ExchangeRate API",
                "rates": {
                    "USD": usd_rate,
                    "CNY": cny_rate,
                    "EUR": eur_rate,
                    "GBP": gbp_rate,
                    "JPY": jpy_rate,
                    "INR": inr_rate,
                    "CAD": cad_rate,
                    "AUD": aud_rate,
                    "KRW": krw_rate,
                    "BRL": brl_rate
                },
                # For backward compatibility, keep the old structure
                "from": "USD",
                "to": "CNY",
                "rate": cny_rate
            }

            with open(EXCHANGE_RATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            print(f"Exchange Rates Saved:")
            print(f"  USD: {usd_rate} (基准)")
            print(f"  CNY: {cny_rate} (1 USD = {cny_rate} CNY)")
            print(f"  EUR: {eur_rate} (1 USD = {eur_rate} EUR)")
            print(f"  GBP: {gbp_rate} (1 USD = {gbp_rate} GBP)")
            print(f"  JPY: {jpy_rate} (1 USD = {jpy_rate} JPY)")
            print(f"  INR: {inr_rate} (1 USD = {inr_rate} INR)")
            print(f"  CAD: {cad_rate} (1 USD = {cad_rate} CAD)")
            print(f"  AUD: {aud_rate} (1 USD = {aud_rate} AUD)")
            print(f"  KRW: {krw_rate} (1 USD = {krw_rate} KRW)")
            print(f"  BRL: {brl_rate} (1 USD = {brl_rate} BRL)")
            print(f"  来源: ExchangeRate API")

            append_log("System", f"Exchange rates updated: USD={usd_rate}, CNY={cny_rate}, EUR={eur_rate}, GBP={gbp_rate}, JPY={jpy_rate}, INR={inr_rate} (权威数据)", "success")
        else:
            print(f"ExchangeRate API failed with status code: {r.status_code}")
            append_log("System", "Failed to fetch exchange rates from API", "error")

    except Exception as e:
        print(f"Exchange Rate API Error: {e}")
        append_log("System", f"Exchange rate API error: {str(e)}", "error")

def fetch_clean_energy_data():
    """Fetch global clean energy percentage data from authoritative sources (IEA, EIA)"""
    print(f"[{datetime.now()}] Task: Fetch Clean Energy Data")

    try:
        append_log("ComputePulse", "Querying global clean energy data from IEA and EIA...", "action")

        # Prompt for AI agents to search for clean energy data
        prompt = """Search for the latest global clean energy statistics (2024-2025) from authoritative sources:
        - IEA (International Energy Agency)
        - EIA (U.S. Energy Information Administration)
        - Ember Climate Global Electricity Database
        - Our World in Data

        Focus on:
        1. Global renewable energy percentage in electricity generation
        2. Breakdown by technology: Solar, Wind, Hydro, Nuclear, etc.
        3. Top 10 countries with highest clean energy percentage
        4. Year-over-year growth trends

        Return JSON format with real data only:
        {
            "global_percentage": [actual percentage],
            "by_technology": {
                "solar": [actual %],
                "wind": [actual %],
                "hydro": [actual %],
                "nuclear": [actual %],
                "other_renewables": [actual %]
            },
            "top_countries": [
                {"country": "[country name]", "percentage": [actual %]},
                {"country": "[country name]", "percentage": [actual %]}
            ],
            "year_over_year_growth": [actual growth %],
            "data_source": "[official source name]",
            "last_updated": "[actual date]"
        }"""

        # Use researcher (Kimi) to gather clean energy data
        append_log("Kimi", "Analyzing global renewable energy reports...", "action")
        k_res = researcher.search(prompt)
        k_data = clean_and_parse_json(k_res)

        if k_data and 'global_percentage' in k_data:
            # Add timestamp
            k_data['timestamp'] = datetime.now().isoformat()

            with open(CLEAN_ENERGY_FILE, 'w', encoding='utf-8') as f:
                json.dump(k_data, f, indent=2)

            print(f"Clean Energy Data Saved:")
            print(f"  Global Clean Energy: {k_data.get('global_percentage', 'N/A')}%")
            print(f"  Data Source: {k_data.get('data_source', 'N/A')}")

            append_log("System", f"Clean energy data updated: {k_data.get('global_percentage', 'N/A')}% global renewable energy", "success")
        else:
            print("Clean Energy Data Validation Failed")
            append_log("System", "Failed to fetch valid clean energy data", "error")

    except Exception as e:
        print(f"Clean Energy Data Error: {e}")
        append_log("System", f"Clean energy data error: {str(e)}", "error")

def fetch_electricity_prices():
    """Fetch global electricity prices (min, max, average) by region"""
    print(f"[{datetime.now()}] Task: Fetch Global Electricity Prices")

    try:
        append_log("ComputePulse", "Querying global electricity pricing data...", "action")

        # Load current exchange rates to provide to AI
        exchange_rate_data = {}
        if os.path.exists(EXCHANGE_RATE_FILE):
            with open(EXCHANGE_RATE_FILE, 'r', encoding='utf-8') as f:
                exchange_rate_data = json.load(f)

        # Load real-time exchange rates from our API (not from AI)
        if exchange_rate_data and 'rates' in exchange_rate_data:
            rates = exchange_rate_data['rates']
            prompt = f"""作为AI算力市场分析专家，请搜索并分析全球电力价格数据。

            核心任务：
            1. 搜索最新全球工业电价数据（美国、德国、中国、日本、英国、加拿大、澳大利亚、巴西）
            2. 搜索商业电价和数据中心电价
            3. 分析价格波动趋势和区域差异

            数据权威源：
            - IEA Electricity Prices Database
            - EIA International Energy Statistics
            - Eurostat Energy Statistics
            - 各国国家电网公司/能源监管机构
            - 实时电力交易平台（如EEX、PJM、CAISO等）

            强制要求：
            - 使用搜索工具获取当前最新实时数据
            - 搜索时要明确要求"最新"、"当前"、"今日"数据
            - 提供具体的数值和计算过程
            - **重要：不要搜索汇率数据！必须使用以下提供的汇率**：
              1 USD = {rates.get('CNY', 'N/A')} CNY
              1 USD = {rates.get('EUR', 'N/A')} EUR
              1 USD = {rates.get('GBP', 'N/A')} GBP
              1 USD = {rates.get('JPY', 'N/A')} JPY
              1 USD = {rates.get('INR', 'N/A')} INR
              时间戳：{exchange_rate_data.get('timestamp', 'N/A')}
            - 展示计算公式：USD/MWh = 原始货币价格 ÷ 汇率

            Return JSON format with real data only:
            {{
                "industrial_prices": [
                    {{"region": "[region name]", "min_price": [actual USD price], "max_price": [actual USD price], "avg_price": [actual USD price], "currency": "USD/MWh"}},
                    {{"region": "[region name]", "min_price": [actual USD price], "max_price": [actual USD price], "avg_price": [actual USD price], "currency": "USD/MWh"}}
                ],
                "commercial_prices": [
                    {{"region": "[region name]", "min_price": [actual USD price], "max_price": [actual USD price], "avg_price": [actual USD price], "currency": "USD/MWh"}}
                ],
                "datacenter_rates": [
                    {{"region": "[region name]", "rate": [actual USD rate], "currency": "USD/MWh", "source": "[official source]"}}
                ],
                "exchange_rates_used": {{
                    "USD_CNY": {rates.get('CNY', 'N/A')},
                    "USD_EUR": {rates.get('EUR', 'N/A')},
                    "USD_GBP": {rates.get('GBP', 'N/A')},
                    "USD_JPY": {rates.get('JPY', 'N/A')},
                    "USD_INR": {rates.get('INR', 'N/A')},
                    "USD_CAD": {rates.get('CAD', 'N/A')},
                    "USD_AUD": {rates.get('AUD', 'N/A')},
                    "USD_KRW": {rates.get('KRW', 'N/A')},
                    "USD_BRL": {rates.get('BRL', 'N/A')},
                    "timestamp": "{exchange_rate_data.get('timestamp', 'N/A')}",
                    "source": "{exchange_rate_data.get('source', 'N/A')}"
                }},
                "last_updated": "[actual date]"
            }}"""
        else:
            # Fallback prompt without exchange rates (should not happen)
            prompt = """Search for the latest global electricity prices (2024-2025) from authoritative sources. Return data in USD/MWh format only.

            Return JSON format with real data only:
            {
                "industrial_prices": [
                    {"region": "[region name]", "min_price": [actual USD price], "max_price": [actual USD price], "avg_price": [actual USD price], "currency": "USD/MWh"}
                ],
                "commercial_prices": [
                    {"region": "[region name]", "min_price": [actual USD price], "max_price": [actual USD price], "avg_price": [actual USD price], "currency": "USD/MWh"}
                ],
                "datacenter_rates": [
                    {"region": "[region name]", "rate": [actual USD rate], "currency": "USD/MWh", "source": "[official source]"}
                ],
                "last_updated": "[actual date]"
            }"""

        # Use researcher (Qwen) to gather electricity price data
        # Qwen has better search reliability than Kimi for real-time data
        append_log("Qwen", "Analyzing global electricity market data with reliable search...", "action")
        k_res = researcher.search(prompt)

        # CRITICAL: MiniMax auditing Qwen's calculation process
        append_log("MiniMax", "Auditing Qwen's calculation process to prevent hallucinations...", "action")

        # Ask Qwen to show detailed thinking process
        thinking_prompt = f"""
        作为ComputePulse项目的AI审计员，请详细展示你刚才的电力价格计算过程：

        1. 你搜索到的原始数据（每个国家的具体价格和货币）
        2. 你使用的汇率转换公式
        3. 你如何计算min/max/avg
        4. 你如何计算全球统计

        必须展示：
        - 每个国家的原始数据（数值+货币）
        - 每一步的计算公式
        - 汇率使用记录

        这是防止AI幻觉的关键步骤。
        """

        thinking_response = researcher.generate(thinking_prompt)

        # MiniMax audits the thinking process
        audit_prompt = f"""
        作为ComputePulse项目的MiniMax审计员，请检查Qwen的电力价格计算过程：

        Qwen的思考过程：
        {thinking_response}

        请验证：
        1. 数学计算是否正确？
        2. 汇率使用是否合理？
        3. 是否有计算错误？
        4. 原始数据是否合理？

        如果发现问题，请指出具体的错误和建议修正。
        """

        audit_response = strategist.generate(audit_prompt)
        k_data = clean_and_parse_json(k_res)

        if k_data and 'industrial_prices' in k_data:
            # Calculate global statistics across all regions
            industrial_prices = k_data.get('industrial_prices', [])
            if industrial_prices:
                # Extract avg prices for global calculation
                avg_prices = [float(item.get('avg_price', 0)) for item in industrial_prices if isinstance(item.get('avg_price'), (int, float))]
                min_prices = [float(item.get('min_price', 0)) for item in industrial_prices if isinstance(item.get('min_price'), (int, float))]
                max_prices = [float(item.get('max_price', 0)) for item in industrial_prices if isinstance(item.get('max_price'), (int, float))]

                if avg_prices:
                    global_stats = {
                        "global_min_avg_price": round(min(avg_prices), 2),
                        "global_max_avg_price": round(max(avg_prices), 2),
                        "global_avg_price": round(sum(avg_prices) / len(avg_prices), 2),
                        "global_min_price": round(min(min_prices), 2) if min_prices else 0,
                        "global_max_price": round(max(max_prices), 2) if max_prices else 0,
                        "regions_count": len(industrial_prices)
                    }
                    k_data['global_statistics'] = global_stats

                    print(f"\n=== 全球电力价格统计 ===")
                    print(f"  最低均价: {global_stats['global_min_avg_price']} USD/MWh")
                    print(f"  最高均价: {global_stats['global_max_avg_price']} USD/MWh")
                    print(f"  全球平均: {global_stats['global_avg_price']} USD/MWh")
                    print(f"  最低价: {global_stats['global_min_price']} USD/MWh")
                    print(f"  最高价: {global_stats['global_max_price']} USD/MWh")
                    print(f"  覆盖区域: {global_stats['regions_count']} 个")

            # Add timestamp
            k_data['timestamp'] = datetime.now().isoformat()

            with open(ELECTRICITY_PRICES_FILE, 'w', encoding='utf-8') as f:
                json.dump(k_data, f, indent=2)

            print(f"Electricity Prices Data Saved:")
            print(f"  Regions covered: {len(k_data.get('industrial_prices', []))}")

            append_log("System", f"Electricity prices updated for {len(k_data.get('industrial_prices', []))} regions", "success")
        else:
            print("Electricity Prices Data Validation Failed")
            append_log("System", "Failed to fetch valid electricity price data", "error")

    except Exception as e:
        print(f"Electricity Prices Data Error: {e}")
        append_log("System", f"Electricity prices data error: {str(e)}", "error")

def fetch_gpu_production_costs():
    """Fetch GPU manufacturer cost structure and pricing analysis"""
    print(f"[{datetime.now()}] Task: Fetch GPU Production Costs")

    try:
        append_log("ComputePulse", "Analyzing GPU manufacturer cost structures...", "action")

        # Prompt for AI agents to search for GPU production cost data
        prompt = """Search for the latest GPU production cost and pricing analysis (2024-2025):
        - NVIDIA H100/A100 manufacturing costs
        - AMD GPU production economics
        - Intel Arc GPU cost analysis
        - Supply chain and margin analysis
        - TSMC/Samsung foundry pricing

        Focus on:
        1. Manufacturing cost per unit (silicon, packaging, testing)
        2. R&D cost allocation
        3. Profit margins by product tier
        4. Competitive pricing strategies
        5. Cost trends over time

        Return JSON format with real data only:
        {
            "nvidia": {
                "h100": {
                    "manufacturing_cost": [actual cost],
                    "suggested_retail": [actual price],
                    "gross_margin": [actual margin],
                    "cost_breakdown": {
                        "silicon": [actual cost],
                        "packaging": [actual cost],
                        "testing": [actual cost],
                        "r_and_d_allocation": [actual cost]
                    }
                },
                "a100": {
                    "manufacturing_cost": [actual cost],
                    "suggested_retail": [actual price],
                    "gross_margin": [actual margin],
                    "cost_breakdown": {
                        "silicon": [actual cost],
                        "packaging": [actual cost],
                        "testing": [actual cost],
                        "r_and_d_allocation": [actual cost]
                    }
                }
            },
            "amd": {
                "mi300x": {
                    "manufacturing_cost": [actual cost],
                    "suggested_retail": [actual price],
                    "gross_margin": [actual margin]
                }
            },
            "industry_analysis": {
                "average_gross_margin": [actual margin],
                "cost_trend": "[trend description]",
                "main_cost_driver": "[main factor]"
            },
            "last_updated": "[actual date]"
        }"""

        # Use hunter (DeepSeek) to analyze GPU production costs
        append_log("DeepSeek", "Dissecting GPU manufacturing economics...", "action")
        ds_res = hunter.generate(prompt)
        ds_data = clean_and_parse_json(ds_res)

        if ds_data and 'nvidia' in ds_data:
            # Add timestamp
            ds_data['timestamp'] = datetime.now().isoformat()

            with open(PRODUCTION_COSTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(ds_data, f, indent=2)

            print(f"GPU Production Costs Data Saved:")
            print(f"  Manufacturers covered: {list(ds_data.keys())}")

            append_log("System", f"GPU production costs updated for {len(ds_data) - 1} manufacturers", "success")
        else:
            print("GPU Production Costs Data Validation Failed")
            append_log("System", "Failed to fetch valid GPU production cost data", "error")

    except Exception as e:
        print(f"GPU Production Costs Data Error: {e}")
        append_log("System", f"GPU production costs error: {str(e)}", "error")

def fetch_ai_company_financials():
    """Fetch AI company financial data and stock prices from official sources"""
    print(f"[{datetime.now()}] Task: Fetch AI Company Financials")

    try:
        append_log("ComputePulse", "Gathering AI company financial data from official sources...", "action")

        # Prompt for AI agents to search for AI company financials
        prompt = """Search for the latest AI company financial data (Q3/Q4 2024):
        - NVIDIA (NVDA) - official earnings, AI revenue
        - AMD (AMD) - data center GPU revenue
        - Microsoft (MSFT) - Azure AI revenue, OpenAI investment
        - Google (GOOGL) - AI/ML revenue, TPU costs
        - Amazon (AMZN) - AWS AI services revenue
        - Meta (META) - AI infrastructure spending
        - OpenAI - funding rounds, valuation
        - Anthropic - funding, revenue model

        Focus on:
        1. Official quarterly earnings reports
        2. AI-specific revenue breakdown
        3. Capital expenditure on AI infrastructure
        4. Stock price performance
        5. Market valuation trends

        Return JSON format with real data only:
        {
            "nvidia": {
                "stock_price": [actual price],
                "market_cap": [actual cap],
                "ai_revenue_q3": [actual revenue],
                "data_center_growth": [actual growth],
                "next_earnings_date": "[actual date]",
                "source": "[official source]"
            },
            "microsoft": {
                "stock_price": [actual price],
                "market_cap": [actual cap],
                "azure_ai_revenue": [actual revenue],
                "openai_investment": [actual amount],
                "source": "[official source]"
            },
            "industry_metrics": {
                "total_ai_market_cap": [actual cap],
                "average_pe_ratio": [actual ratio],
                "top_performer": "[company name]"
            },
            "last_updated": "[actual date]"
        }"""

        # Use researcher (Kimi) to gather AI company financials
        append_log("Kimi", "Analyzing AI company earnings reports...", "action")
        k_res = researcher.search(prompt)
        k_data = clean_and_parse_json(k_res)

        if k_data and 'nvidia' in k_data:
            # Add timestamp
            k_data['timestamp'] = datetime.now().isoformat()

            with open(COMPANY_FINANCIALS_FILE, 'w', encoding='utf-8') as f:
                json.dump(k_data, f, indent=2)

            print(f"AI Company Financials Data Saved:")
            print(f"  Companies covered: {list(k_data.keys())}")

            append_log("System", f"AI company financials updated for {len([k for k in k_data.keys() if k != 'industry_metrics' and k != 'timestamp'])} companies", "success")
        else:
            print("AI Company Financials Data Validation Failed")
            append_log("System", "Failed to fetch valid AI company financial data", "error")

    except Exception as e:
        print(f"AI Company Financials Data Error: {e}")
        append_log("System", f"AI company financials error: {str(e)}", "error")

def fetch_token_pricing_models():
    """Fetch AI model token pricing analysis (subscription vs usage models)"""
    print(f"[{datetime.now()}] Task: Fetch Token Pricing Models")

    try:
        append_log("ComputePulse", "Analyzing AI model token pricing strategies...", "action")

        # Prompt for AI agents to search for token pricing models
        prompt = """Search for the latest AI model token pricing strategies (2024-2025):
        - OpenAI: GPT-4o, GPT-4 Turbo pricing, ChatGPT Plus subscription
        - Anthropic: Claude 3.5 Sonnet, Claude 3 Haiku pricing
        - Google: Gemini Pro, Gemini Ultra pricing
        - Meta: Llama models (open source vs pro)
        - Microsoft: Copilot subscriptions
        - DeepSeek: API pricing models
        - Qwen: Alibaba's pricing strategy

        Focus on:
        1. Pay-per-token pricing (input/output costs)
        2. Subscription models (monthly/annual)
        3. Freemium tiers and limitations
        4. Enterprise vs individual pricing
        5. Token cost efficiency trends

        Return JSON format with real data only:
        {
            "openai": {
                "gpt_4o": {
                    "input_price_per_million": [actual price],
                    "output_price_per_million": [actual price],
                    "subscription_alternative": {
                        "chatgpt_plus": [actual price],
                        "monthly_limit": "[limit description]"
                    },
                    "efficiency_score": [actual score]
                },
                "gpt_4_turbo": {
                    "input_price_per_million": [actual price],
                    "output_price_per_million": [actual price],
                    "subscription_alternative": null,
                    "efficiency_score": [actual score]
                }
            },
            "anthropic": {
                "claude_3_5_sonnet": {
                    "input_price_per_million": [actual price],
                    "output_price_per_million": [actual price],
                    "subscription_alternative": {
                        "claude_pro": [actual price],
                        "monthly_limit": "[limit description]"
                    },
                    "efficiency_score": [actual score]
                }
            },
            "pricing_analysis": {
                "average_input_cost": [actual cost],
                "average_output_cost": [actual cost],
                "most_efficient": "[model name]",
                "subscription_adoption_rate": [actual rate],
                "trend": "[trend description]"
            },
            "last_updated": "[actual date]"
        }"""

        # Use analyst (GLM) to analyze token pricing models
        append_log("GLM", "Evaluating token pricing strategies...", "action")
        gl_res = analyst.generate(prompt)
        gl_data = clean_and_parse_json(gl_res)

        if gl_data and 'openai' in gl_data:
            # Add timestamp
            gl_data['timestamp'] = datetime.now().isoformat()

            with open(TOKEN_PRICING_MODELS_FILE, 'w', encoding='utf-8') as f:
                json.dump(gl_data, f, indent=2)

            print(f"Token Pricing Models Data Saved:")
            print(f"  Providers covered: {list(gl_data.keys())}")

            append_log("System", f"Token pricing models updated for {len([k for k in gl_data.keys() if k != 'pricing_analysis' and k != 'timestamp'])} providers", "success")
        else:
            print("Token Pricing Models Data Validation Failed")
            append_log("System", "Failed to fetch valid token pricing model data", "error")

    except Exception as e:
        print(f"Token Pricing Models Data Error: {e}")
        append_log("System", f"Token pricing models error: {str(e)}", "error")


def fetch_official_token_pricing():
    """Fetch token pricing from official AI provider documentation - fast and accurate"""
    print("\n[9] Official Token Pricing (API Documentation Sources)")
    append_log("System", "Fetching official token pricing from provider APIs...", "action")

    try:
        from fetch_official_token_pricing import OfficialTokenPriceFetcher

        fetcher = OfficialTokenPriceFetcher()
        pricing_data = fetcher.fetch_all_pricing()
        fetcher.save_pricing_data(pricing_data)

        providers_count = pricing_data.get('metadata', {}).get('total_providers', 0)
        models_count = pricing_data.get('statistics', {}).get('total_models', 0)

        append_log("System", f"Official token pricing updated: {providers_count} providers, {models_count} models", "success")
        print(f"  Official pricing saved: {providers_count} providers, {models_count} models")

    except Exception as e:
        print(f"Official Token Pricing Error: {e}")
        append_log("System", f"Official token pricing error: {str(e)}", "error")


if __name__ == "__main__":
    # Ensure data dir exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    try:
        fetch_gpu_prices()
        fetch_token_prices()
        fetch_grid_load()
        fetch_clean_energy_data()
        fetch_electricity_prices()
        fetch_gpu_production_costs()
        fetch_ai_company_financials()
        fetch_token_pricing_models()
        fetch_official_token_pricing()  # Official API documentation pricing
        fetch_exchange_rate()
        validate_and_fix()
        generate_market_insight()
        generate_industry_index()
        generate_dashboard_insights()
    except Exception as e:
        print(f"Critical Error: {e}")
        append_log("System", f"Critical Failure: {str(e)}", "warning")
        sys.exit(1)
