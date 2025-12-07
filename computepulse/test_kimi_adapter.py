import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.local')
load_dotenv(env_path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_orchestrator.adapters.kimi_adapter import KimiAdapter

async def test():
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print('No API key')
        return

    adapter = KimiAdapter(api_key=api_key, enable_search=True)
    print(f'Testing Kimi adapter with model: {adapter.model_name}')

    response = await adapter.call_async('你好')
    print(f'Success: {response.success}')
    print(f'Error: {response.error}')
    if response.content:
        print(f'Content length: {len(response.content)}')
        print(f'Content: {response.content[:100]}...')

if __name__ == '__main__':
    asyncio.run(test())