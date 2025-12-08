#!/usr/bin/env python3
"""
官方Token价格爬虫 - Playwright版本
使用Playwright实现JavaScript渲染，从AI公司官方定价页面抓取最新数据
适用于GitHub Actions自动化运行
"""

import asyncio
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional

# Playwright导入
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[WARN] Playwright not installed. Run: pip install playwright && playwright install chromium")

# 文件路径
TOKEN_PRICING_FILE = 'public/data/token_pricing_official.json'


class PlaywrightTokenPriceFetcher:
    """使用Playwright爬取官方Token定价"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.results = []

    async def init_browser(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        print("[BROWSER] Chromium launched in headless mode")

    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            print("[BROWSER] Closed")
        except Exception as e:
            print(f"[BROWSER] Close error (ignored): {e}")

    def parse_price(self, text: str) -> Optional[float]:
        """从文本解析价格"""
        if not text:
            return None
        text = text.replace('$', '').replace(',', '').replace('￥', '').strip()
        match = re.search(r'(\d+\.?\d*)', text)
        return float(match.group(1)) if match else None

    async def fetch_openai_pricing(self) -> Dict:
        """爬取OpenAI定价页面"""
        print("\n[CRAWL] OpenAI pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://openai.com/api/pricing/", wait_until="networkidle", timeout=30000)

            # 等待页面加载
            await page.wait_for_timeout(3000)

            models = []

            # 获取页面内容
            content = await page.content()

            # OpenAI定价模式匹配 - 他们用 /1M tokens 格式
            patterns = [
                (r'gpt-4o(?!-mini)[^\d]*\$(\d+\.?\d*)\s*/\s*1M[^\$]*\$(\d+\.?\d*)\s*/\s*1M', 'gpt-4o'),
                (r'gpt-4o-mini[^\d]*\$(\d+\.?\d*)\s*/\s*1M[^\$]*\$(\d+\.?\d*)\s*/\s*1M', 'gpt-4o-mini'),
                (r'gpt-4-turbo[^\d]*\$(\d+\.?\d*)\s*/\s*1M[^\$]*\$(\d+\.?\d*)\s*/\s*1M', 'gpt-4-turbo'),
                (r'o1-preview[^\d]*\$(\d+\.?\d*)\s*/\s*1M[^\$]*\$(\d+\.?\d*)\s*/\s*1M', 'o1-preview'),
                (r'o1-mini[^\d]*\$(\d+\.?\d*)\s*/\s*1M[^\$]*\$(\d+\.?\d*)\s*/\s*1M', 'o1-mini'),
            ]

            for pattern, model_name in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    input_price = float(match.group(1))
                    output_price = float(match.group(2))
                    models.append({
                        "model": model_name,
                        "input_price_per_1m": input_price,
                        "output_price_per_1m": output_price,
                        "input_price_per_1k": input_price / 1000,
                        "output_price_per_1k": output_price / 1000,
                        "currency": "USD",
                        "scraped": True,
                        "last_updated": datetime.now().isoformat()
                    })
                    print(f"  Found {model_name}: ${input_price}/1M input, ${output_price}/1M output")

            await page.close()

            return {
                "provider": "OpenAI",
                "source": "https://openai.com/api/pricing/",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "OpenAI", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_anthropic_pricing(self) -> Dict:
        """爬取Anthropic定价页面"""
        print("\n[CRAWL] Anthropic pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://www.anthropic.com/pricing", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []
            content = await page.content()

            # Claude定价模式 - 通常是 $X / MTok
            patterns = [
                (r'claude[- ]?3\.?5[- ]?sonnet[^\d]*\$(\d+\.?\d*)\s*/\s*M[^\$]*\$(\d+\.?\d*)', 'claude-3.5-sonnet'),
                (r'claude[- ]?3\.?5[- ]?haiku[^\d]*\$(\d+\.?\d*)\s*/\s*M[^\$]*\$(\d+\.?\d*)', 'claude-3.5-haiku'),
                (r'claude[- ]?3[- ]?opus[^\d]*\$(\d+\.?\d*)\s*/\s*M[^\$]*\$(\d+\.?\d*)', 'claude-3-opus'),
            ]

            for pattern, model_name in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    input_price = float(match.group(1))
                    output_price = float(match.group(2))
                    models.append({
                        "model": model_name,
                        "input_price_per_1m": input_price,
                        "output_price_per_1m": output_price,
                        "input_price_per_1k": input_price / 1000,
                        "output_price_per_1k": output_price / 1000,
                        "currency": "USD",
                        "scraped": True,
                        "last_updated": datetime.now().isoformat()
                    })
                    print(f"  Found {model_name}: ${input_price}/M input, ${output_price}/M output")

            await page.close()

            return {
                "provider": "Anthropic",
                "source": "https://www.anthropic.com/pricing",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "Anthropic", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_google_pricing(self) -> Dict:
        """爬取Google AI定价页面"""
        print("\n[CRAWL] Google AI pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://ai.google.dev/pricing", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []
            content = await page.content()

            # Google定价表格解析
            # 尝试从表格中提取
            tables = await page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    if len(cells) >= 3:
                        model_text = await cells[0].inner_text()
                        if 'gemini' in model_text.lower():
                            try:
                                input_text = await cells[1].inner_text()
                                output_text = await cells[2].inner_text()
                                input_price = self.parse_price(input_text)
                                output_price = self.parse_price(output_text)
                                if input_price:
                                    models.append({
                                        "model": model_text.strip(),
                                        "input_price_per_1k": input_price,
                                        "output_price_per_1k": output_price or input_price,
                                        "currency": "USD",
                                        "scraped": True,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    print(f"  Found {model_text.strip()}")
                            except:
                                pass

            await page.close()

            return {
                "provider": "Google",
                "source": "https://ai.google.dev/pricing",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "Google", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_deepseek_pricing(self) -> Dict:
        """爬取DeepSeek定价"""
        print("\n[CRAWL] DeepSeek pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://platform.deepseek.com/api-docs/pricing", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []
            content = await page.content()

            # DeepSeek定价解析
            tables = await page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    row_text = await row.inner_text()
                    if 'deepseek' in row_text.lower():
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 2:
                            try:
                                model_name = await cells[0].inner_text()
                                price_text = await cells[1].inner_text()
                                price = self.parse_price(price_text)
                                if price:
                                    # DeepSeek用人民币计价
                                    models.append({
                                        "model": model_name.strip(),
                                        "input_price_per_1k": price / 7.1,
                                        "output_price_per_1k": price / 7.1,
                                        "original_price_cny": price,
                                        "currency": "USD",
                                        "scraped": True,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    print(f"  Found {model_name.strip()}")
                            except:
                                pass

            await page.close()

            return {
                "provider": "DeepSeek",
                "source": "https://platform.deepseek.com/api-docs/pricing",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "DeepSeek", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_zhipu_pricing(self) -> Dict:
        """爬取智谱GLM定价"""
        print("\n[CRAWL] Zhipu (GLM) pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://open.bigmodel.cn/pricing", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []

            # 智谱定价表格解析
            tables = await page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    row_text = await row.inner_text()
                    if 'glm' in row_text.lower():
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 2:
                            try:
                                model_name = await cells[0].inner_text()
                                price_text = await cells[1].inner_text()
                                price = self.parse_price(price_text)
                                if price:
                                    models.append({
                                        "model": model_name.strip(),
                                        "input_price_per_1k": price / 7.1,
                                        "output_price_per_1k": price / 7.1,
                                        "original_price_cny": price,
                                        "currency": "USD",
                                        "scraped": True,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    print(f"  Found {model_name.strip()}")
                            except:
                                pass

            await page.close()

            return {
                "provider": "Zhipu",
                "source": "https://open.bigmodel.cn/pricing",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "Zhipu", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_alibaba_pricing(self) -> Dict:
        """爬取阿里通义千问定价"""
        print("\n[CRAWL] Alibaba (Qwen) pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://help.aliyun.com/zh/model-studio/billing", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []

            tables = await page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    row_text = await row.inner_text()
                    if 'qwen' in row_text.lower():
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 3:
                            try:
                                model_name = await cells[0].inner_text()
                                input_text = await cells[1].inner_text()
                                output_text = await cells[2].inner_text()
                                input_price = self.parse_price(input_text)
                                output_price = self.parse_price(output_text)
                                if input_price:
                                    models.append({
                                        "model": model_name.strip(),
                                        "input_price_per_1k": input_price / 7.1,
                                        "output_price_per_1k": (output_price or input_price) / 7.1,
                                        "original_input_cny": input_price,
                                        "original_output_cny": output_price,
                                        "currency": "USD",
                                        "scraped": True,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    print(f"  Found {model_name.strip()}")
                            except:
                                pass

            await page.close()

            return {
                "provider": "Alibaba",
                "source": "https://help.aliyun.com/zh/model-studio/billing",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "Alibaba", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_moonshot_pricing(self) -> Dict:
        """爬取Moonshot/Kimi定价"""
        print("\n[CRAWL] Moonshot (Kimi) pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://platform.moonshot.cn/docs/pricing", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []

            tables = await page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    row_text = await row.inner_text()
                    if 'moonshot' in row_text.lower():
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 2:
                            try:
                                model_name = await cells[0].inner_text()
                                price_text = await cells[1].inner_text()
                                price = self.parse_price(price_text)
                                if price:
                                    models.append({
                                        "model": model_name.strip(),
                                        "input_price_per_1k": price / 7.1,
                                        "output_price_per_1k": price / 7.1,
                                        "original_price_cny": price,
                                        "currency": "USD",
                                        "scraped": True,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    print(f"  Found {model_name.strip()}")
                            except:
                                pass

            await page.close()

            return {
                "provider": "Moonshot",
                "source": "https://platform.moonshot.cn/docs/pricing",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "Moonshot", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_baidu_pricing(self) -> Dict:
        """爬取百度文心定价"""
        print("\n[CRAWL] Baidu (ERNIE) pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []

            tables = await page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    row_text = await row.inner_text()
                    if 'ernie' in row_text.lower():
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 2:
                            try:
                                model_name = await cells[0].inner_text()
                                price_text = await cells[1].inner_text()
                                price = self.parse_price(price_text)
                                if price:
                                    models.append({
                                        "model": model_name.strip(),
                                        "input_price_per_1k": price / 7.1,
                                        "output_price_per_1k": price / 7.1,
                                        "original_price_cny": price,
                                        "currency": "USD",
                                        "scraped": True,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    print(f"  Found {model_name.strip()}")
                            except:
                                pass

            await page.close()

            return {
                "provider": "Baidu",
                "source": "https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "Baidu", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_minimax_pricing(self) -> Dict:
        """爬取MiniMax定价"""
        print("\n[CRAWL] MiniMax pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://platform.minimaxi.com/document/Price", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []

            tables = await page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    row_text = await row.inner_text()
                    if 'abab' in row_text.lower():
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 2:
                            try:
                                model_name = await cells[0].inner_text()
                                price_text = await cells[1].inner_text()
                                price = self.parse_price(price_text)
                                if price:
                                    models.append({
                                        "model": model_name.strip(),
                                        "input_price_per_1k": price / 7.1,
                                        "output_price_per_1k": price / 7.1,
                                        "original_price_cny": price,
                                        "currency": "USD",
                                        "scraped": True,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    print(f"  Found {model_name.strip()}")
                            except:
                                pass

            await page.close()

            return {
                "provider": "MiniMax",
                "source": "https://platform.minimaxi.com/document/Price",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "MiniMax", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_xai_pricing(self) -> Dict:
        """爬取xAI/Grok定价"""
        print("\n[CRAWL] xAI (Grok) pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://docs.x.ai/docs/models", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []
            content = await page.content()

            # xAI Grok定价模式
            patterns = [
                (r'grok-2[^\d]*\$(\d+\.?\d*)\s*/\s*(?:1M|million)[^\$]*\$(\d+\.?\d*)', 'grok-2'),
                (r'grok-beta[^\d]*\$(\d+\.?\d*)\s*/\s*(?:1M|million)[^\$]*\$(\d+\.?\d*)', 'grok-beta'),
            ]

            for pattern, model_name in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    input_price = float(match.group(1))
                    output_price = float(match.group(2))
                    models.append({
                        "model": model_name,
                        "input_price_per_1m": input_price,
                        "output_price_per_1m": output_price,
                        "input_price_per_1k": input_price / 1000,
                        "output_price_per_1k": output_price / 1000,
                        "currency": "USD",
                        "scraped": True,
                        "last_updated": datetime.now().isoformat()
                    })
                    print(f"  Found {model_name}")

            await page.close()

            return {
                "provider": "xAI",
                "source": "https://docs.x.ai/docs/models",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "xAI", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_mistral_pricing(self) -> Dict:
        """爬取Mistral定价"""
        print("\n[CRAWL] Mistral pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://mistral.ai/technology/", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []
            content = await page.content()

            # Mistral定价模式
            patterns = [
                (r'mistral[- ]?large[^\d]*\$(\d+\.?\d*)\s*/[^\$]*\$(\d+\.?\d*)', 'mistral-large'),
                (r'mistral[- ]?medium[^\d]*\$(\d+\.?\d*)\s*/[^\$]*\$(\d+\.?\d*)', 'mistral-medium'),
                (r'mistral[- ]?small[^\d]*\$(\d+\.?\d*)\s*/[^\$]*\$(\d+\.?\d*)', 'mistral-small'),
            ]

            for pattern, model_name in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    models.append({
                        "model": model_name,
                        "input_price_per_1k": float(match.group(1)),
                        "output_price_per_1k": float(match.group(2)),
                        "currency": "USD",
                        "scraped": True,
                        "last_updated": datetime.now().isoformat()
                    })
                    print(f"  Found {model_name}")

            await page.close()

            return {
                "provider": "Mistral",
                "source": "https://mistral.ai/technology/",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "Mistral", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_cohere_pricing(self) -> Dict:
        """爬取Cohere定价"""
        print("\n[CRAWL] Cohere pricing...")

        try:
            page = await self.browser.new_page()
            await page.goto("https://cohere.com/pricing", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            models = []
            content = await page.content()

            patterns = [
                (r'command[- ]?r[- ]?plus[^\d]*\$(\d+\.?\d*)\s*/[^\$]*\$(\d+\.?\d*)', 'command-r-plus'),
                (r'command[- ]?r(?![- ]?plus)[^\d]*\$(\d+\.?\d*)\s*/[^\$]*\$(\d+\.?\d*)', 'command-r'),
            ]

            for pattern, model_name in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    models.append({
                        "model": model_name,
                        "input_price_per_1k": float(match.group(1)),
                        "output_price_per_1k": float(match.group(2)),
                        "currency": "USD",
                        "scraped": True,
                        "last_updated": datetime.now().isoformat()
                    })
                    print(f"  Found {model_name}")

            await page.close()

            return {
                "provider": "Cohere",
                "source": "https://cohere.com/pricing",
                "crawl_status": "success" if models else "partial",
                "crawl_time": datetime.now().isoformat(),
                "models": models
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {"provider": "Cohere", "error": str(e), "crawl_status": "error", "models": []}

    async def fetch_all_pricing(self) -> Dict:
        """爬取所有供应商定价"""
        print("=" * 60)
        print("  ComputePulse Token Pricing Crawler (Playwright)")
        print("=" * 60)
        print(f"\n[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        await self.init_browser()

        all_pricing = {
            "metadata": {
                "fetch_timestamp": datetime.now().isoformat(),
                "source": "Official pricing pages (Playwright web crawling)",
                "data_type": "token_pricing_official",
                "method": "playwright_headless",
                "total_providers": 0,
                "successful_crawls": 0,
                "partial_crawls": 0,
                "failed_crawls": 0
            },
            "providers": []
        }

        # 所有爬虫任务
        crawlers = [
            self.fetch_openai_pricing,
            self.fetch_anthropic_pricing,
            self.fetch_google_pricing,
            self.fetch_xai_pricing,
            self.fetch_mistral_pricing,
            self.fetch_cohere_pricing,
            self.fetch_deepseek_pricing,
            self.fetch_baidu_pricing,
            self.fetch_zhipu_pricing,
            self.fetch_minimax_pricing,
            self.fetch_moonshot_pricing,
            self.fetch_alibaba_pricing,
        ]

        for crawler in crawlers:
            try:
                result = await crawler()
                all_pricing["providers"].append(result)
                all_pricing["metadata"]["total_providers"] += 1

                status = result.get("crawl_status", "unknown")
                if status == "success":
                    all_pricing["metadata"]["successful_crawls"] += 1
                elif status == "partial":
                    all_pricing["metadata"]["partial_crawls"] += 1
                else:
                    all_pricing["metadata"]["failed_crawls"] += 1

            except Exception as e:
                print(f"  [ERROR] Crawler exception: {e}")
                all_pricing["metadata"]["failed_crawls"] += 1

        await self.close_browser()

        # 统计
        all_models = []
        for provider in all_pricing["providers"]:
            if "models" in provider:
                all_models.extend(provider["models"])

        if all_models:
            input_prices = [m.get("input_price_per_1k", 0) for m in all_models if m.get("input_price_per_1k", 0) > 0]
            output_prices = [m.get("output_price_per_1k", 0) for m in all_models if m.get("output_price_per_1k", 0) > 0]

            all_pricing["statistics"] = {
                "total_models_scraped": len(all_models),
                "input_price_range": {
                    "min": min(input_prices) if input_prices else 0,
                    "max": max(input_prices) if input_prices else 0,
                    "avg": sum(input_prices) / len(input_prices) if input_prices else 0
                },
                "output_price_range": {
                    "min": min(output_prices) if output_prices else 0,
                    "max": max(output_prices) if output_prices else 0,
                    "avg": sum(output_prices) / len(output_prices) if output_prices else 0
                }
            }

        print(f"\n[STATS] Crawl Statistics:")
        print(f"  Total providers: {all_pricing['metadata']['total_providers']}")
        print(f"  Successful: {all_pricing['metadata']['successful_crawls']}")
        print(f"  Partial: {all_pricing['metadata']['partial_crawls']}")
        print(f"  Failed: {all_pricing['metadata']['failed_crawls']}")
        print(f"  Total models: {len(all_models)}")

        return all_pricing

    def save_pricing_data(self, data: Dict) -> None:
        """保存数据"""
        try:
            os.makedirs(os.path.dirname(TOKEN_PRICING_FILE), exist_ok=True)

            with open(TOKEN_PRICING_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"\n[SAVE] Data saved to: {TOKEN_PRICING_FILE}")

            if data.get("providers"):
                print(f"\n[SUMMARY]")
                for provider in data["providers"]:
                    model_count = len(provider.get('models', []))
                    status = provider.get('crawl_status', 'unknown')
                    print(f"  - {provider['provider']}: {model_count} models [{status}]")

        except Exception as e:
            print(f"\n[ERROR] Save failed: {e}")


async def main():
    """主函数"""
    if not PLAYWRIGHT_AVAILABLE:
        print("[ERROR] Playwright not available. Install with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return

    fetcher = PlaywrightTokenPriceFetcher()
    pricing_data = await fetcher.fetch_all_pricing()
    fetcher.save_pricing_data(pricing_data)

    print("\n" + "=" * 60)
    print("  [DONE] Playwright Crawling Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
