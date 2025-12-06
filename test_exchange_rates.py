import os
import sys
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Add script dir to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'computepulse/scripts'))

try:
    from computepulse.scripts.ai_core.factory import AgentFactory
except ImportError:
    # Fallback if running from root
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
    from ai_core.factory import AgentFactory

def clean_and_parse_json(text):
    """Clean markdown JSON blocks and parse"""
    if not text: return None
    try:
        # Remove code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```', '', text)
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                return None
        return None

def test_agent_exchange_rate(agent_name, agent_instance):
    print(f"\n--- Testing Agent: {agent_name} ---")
    
    prompt = """
    Please search for the current real-time USD to CNY exchange rate (today).
    
    Output valid JSON ONLY:
    {
        "from": "USD",
        "to": "CNY",
        "rate": 7.25, 
        "timestamp": "2024-..."
    }
    """
    
    try:
        start_time = datetime.now()
        
        # Try search first if available, otherwise generate
        if hasattr(agent_instance, 'search'):
            print(f"Attempting .search() method...")
            response = agent_instance.search(prompt)
        else:
            print(f"Using .generate() method...")
            response = agent_instance.generate(prompt)
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"Response time: {duration:.2f}s")
        # Truncate response for display
        display_response = (response[:100] + '...') if response and len(response) > 100 else response
        print(f"Raw Response: {display_response}")
        
        data = clean_and_parse_json(response)
        
        if data and 'rate' in data:
            print(f"✅ SUCCESS: Rate = {data['rate']}")
            return True, data['rate']
        else:
            print(f"❌ FAILED: Could not parse rate from response")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False, None

def main():
    print("Starting AI Exchange Rate Capability Test...")
    print(f"Time: {datetime.now()}")
    
    # We will test all available agents to see who can fetch real rates
    agents_to_test = [
        ("Qwen (Architect)", "qwen"),
        ("DeepSeek (Hunter)", "deepseek"),
        ("Kimi (Researcher)", "kimi"),
        ("GLM (Analyst)", "glm"),
        # MiniMax might fail if key is invalid, but we test it anyway
        ("MiniMax (Strategist)", "minimax")
    ]
    
    results = []
    
    for name, key in agents_to_test:
        try:
            print(f"\nInitializing {name}...")
            agent = AgentFactory.create(key)
            success, rate = test_agent_exchange_rate(name, agent)
            results.append({
                "agent": name,
                "success": success,
                "rate": rate
            })
        except Exception as e:
            print(f"Could not initialize {name}: {e}")
            results.append({
                "agent": name,
                "success": False,
                "rate": None,
                "error": str(e)
            })

    print("\n\n=== TEST SUMMARY ===")
    print(f"{'Agent':<20} | {'Status':<10} | {'Rate':<10}")
    print("-" * 45)
    for res in results:
        status = "PASS" if res['success'] else "FAIL"
        rate_str = str(res['rate']) if res['rate'] else "N/A"
        print(f"{res['agent']:<20} | {status:<10} | {rate_str:<10}")

if __name__ == "__main__":
    main()