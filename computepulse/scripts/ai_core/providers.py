import os
import time
from datetime import datetime
from typing import Optional
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    import dashscope
except ImportError:
    dashscope = None

from .base_agent import BaseAgent

class DashScopeAgent(BaseAgent):
    """Agent implementation for Alibaba DashScope (Qwen)."""
    
    def __init__(self, name: str, role: str, model_name: str = "qwen-max"):
        super().__init__(name, role)
        self.model_name = model_name
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            # Try loading from .env.local logic here if needed, or assume environment is set
            pass
            
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        if not dashscope or not self.api_key:
            return None
        
        try:
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            response = dashscope.Generation.call(
                model=self.model_name,
                messages=messages,
                result_format='message',
                api_key=self.api_key
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                print(f"[{datetime.now()}] {self.name} Error: {response.code} - {response.message}")
                return None
        except Exception as e:
            print(f"[{datetime.now()}] {self.name} Exception: {e}")
            return None

    def search(self, query: str) -> Optional[str]:
        if not dashscope or not self.api_key:
            return None
            
        try:
            messages = [{'role': 'user', 'content': query}]
            # Qwen uses 'enable_search' flag in DashScope SDK
            response = dashscope.Generation.call(
                model=self.model_name,
                messages=messages,
                result_format='message',
                enable_search=True, 
                api_key=self.api_key
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                print(f"[{datetime.now()}] {self.name} Search Error: {response.code} - {response.message}")
                return None
        except Exception as e:
            print(f"[{datetime.now()}] {self.name} Search Exception: {e}")
            return None

class DeepSeekAgent(BaseAgent):
    """Agent implementation for DeepSeek (via OpenAI compatible API)."""
    
    def __init__(self, name: str, role: str, model_name: str = "deepseek-r1"):
        super().__init__(name, role)
        self.model_name = model_name
        # DeepSeek might use DASHSCOPE_API_KEY if hosted on Aliyun, or its own DEEPSEEK_API_KEY
        self.api_key = os.getenv('DASHSCOPE_API_KEY') 
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = None
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        if not self.client:
            return None
            
        try:
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[{datetime.now()}] {self.name} Exception: {e}")
            return None

    def search(self, query: str) -> Optional[str]:
        # DeepSeek via DashScope currently doesn't support search flag in standard OpenAI client easily
        # For now, we fallback to standard generation or need specific tool implementation
        return self.generate(query, system_prompt="You are a helpful assistant.")

class KimiAgent(BaseAgent):
    """Agent implementation for Moonshot Kimi (via OpenAI compatible API)."""
    
    def __init__(self, name: str, role: str, model_name: str = "Moonshot-Kimi-K2-Instruct"):
        super().__init__(name, role)
        self.model_name = model_name
        # Kimi uses DASHSCOPE_API_KEY in our current setup
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = None
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        # Kimi basic generation
        if not self.client: return None
        try:
            messages = []
            if system_prompt: messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            completion = self.client.chat.completions.create(
                model=self.model_name, messages=messages, stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[{datetime.now()}] {self.name} Gen Error: {e}")
            return None

    def search(self, query: str) -> Optional[str]:
        # Kimi with Search enabled via extra_body
        if not self.client: return None
        try:
            messages = [
                {"role": "system", "content": "You are Kimi, capable of real-time internet search."},
                {"role": "user", "content": query}
            ]
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                extra_body={"enable_search": True}, # The key parameter for Kimi/DashScope
                stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[{datetime.now()}] {self.name} Search Error: {e}")
            return None

class MiniMaxAgent(BaseAgent):
    """Agent implementation for MiniMax (HaiLuo) via OpenAI compatible API."""
    
    def __init__(self, name: str, role: str, model_name: str = "MiniMax-M2"):
        super().__init__(name, role)
        self.model_name = model_name
        self.api_key = os.getenv('MINIMAX_API_KEY')
        self.base_url = "https://api.minimaxi.com/v1"
        self.client = None
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        if not self.client:
             print(f"[{datetime.now()}] {self.name} Error: Client not initialized (Missing MINIMAX_API_KEY?)")
             return None
        
        try:
            messages = []
            if system_prompt: messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            # Enable reasoning_split to capture the "Interleaved Thinking"
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                extra_body={"reasoning_split": True},
                stream=False
            )
            
            message = completion.choices[0].message
            content = message.content
            
            # Extract reasoning if available
            reasoning = ""
            # Check if reasoning_details exists in the message object
            if hasattr(message, 'reasoning_details') and message.reasoning_details:
                try:
                    # It returns a list of items, usually the first one has the text
                    # We need to handle both object access and dict access depending on SDK version
                    details = message.reasoning_details
                    if isinstance(details, list) and len(details) > 0:
                        first_item = details[0]
                        if hasattr(first_item, 'text'):
                            reasoning = first_item.text
                        elif isinstance(first_item, dict) and 'text' in first_item:
                            reasoning = first_item['text']
                except Exception as parse_err:
                    print(f"[{datetime.now()}] {self.name} Reasoning Parse Error: {parse_err}")
            
            # If reasoning exists, embed it in the output so the caller can extract it
            if reasoning:
                return f"<thinking>{reasoning}</thinking>\n{content}"
            
            return content

        except Exception as e:
            print(f"[{datetime.now()}] {self.name} Gen Error: {e}")
            return None
            
    def search(self, query: str) -> Optional[str]:
        # MiniMax M2 is strong at reasoning, not necessarily web search tool native in this API wrapper
        # We fallback to generate with a specific system prompt
        return self.generate(query, system_prompt="You are a helpful assistant with strong reasoning capabilities.")

class GLMAgent(BaseAgent):
    """Agent implementation for Zhipu GLM-4 (via OpenAI compatible API)."""
    
    def __init__(self, name: str, role: str, model_name: str = "glm-4.6"):
        super().__init__(name, role)
        self.model_name = model_name
        # Use ZHIPU_API_KEY environment variable
        self.api_key = os.getenv('ZHIPU_API_KEY')
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/"
        self.client = None
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        if not self.client: 
            print(f"[{datetime.now()}] {self.name} Error: Client not initialized (Missing ZHIPU_API_KEY?)")
            return None
        try:
            messages = []
            if system_prompt: messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            completion = self.client.chat.completions.create(
                model=self.model_name, messages=messages, stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[{datetime.now()}] {self.name} Gen Error: {e}")
            return None
            
    def search(self, query: str) -> Optional[str]:
        # GLM standalone web search implementation
        if not self.api_key: return None
        try:
            import requests
            import json
            
            url = "https://open.bigmodel.cn/api/paas/v4/web_search"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "search_query": query,
                "search_engine": "search_std",
                "search_intent": False # Optional but good practice
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                
                # The response structure is typically:
                # { "id": "...", "request_id": "...", "search_result": [ { "title": "...", "content": "...", "link": "..." } ] }
                
                items = result.get('search_result', [])
                if not items:
                    return f"No search results found for: {query}"
                
                context = "Search Results:\n"
                for idx, item in enumerate(items):
                    context += f"{idx+1}. {item.get('title', 'No Title')}\n"
                    context += f"   {item.get('content', 'No Content')[:200]}...\n"
                    context += f"   Source: {item.get('link', 'N/A')}\n\n"
                
                # Now use the model to synthesize the answer based on search results
                synthesis_prompt = f"""
                Based on the following search results, answer the user's query: "{query}"
                
                {context}
                
                Synthesize a concise and accurate answer.
                """
                return self.generate(synthesis_prompt)
            else:
                print(f"[{datetime.now()}] {self.name} Web Search API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[{datetime.now()}] {self.name} Search Error: {e}")
            return None
