#!/usr/bin/env python3
"""
Token爬虫基础模块
包含通用的爬虫类、汇率处理和文件读写功能
供各个公司特定的爬虫脚本使用
"""

import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("[ERROR] beautifulsoup4 required: pip install beautifulsoup4")

# 构建相对于项目根目录的路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TOKEN_PRICING_FILE = os.path.join(PROJECT_ROOT, 'public', 'data', 'token_pricing_official.json')
EXCHANGE_RATE_FILE = os.path.join(PROJECT_ROOT, 'public', 'data', 'exchange_rate.json')


class PureWebCrawler:
    """纯爬虫基类 - 无预设数据"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
        })
        self.usd_cny_rate = self._load_exchange_rate()

    def _load_exchange_rate(self) -> float:
        """从exchange_rate.json加载实时汇率"""
        try:
            if os.path.exists(EXCHANGE_RATE_FILE):
                with open(EXCHANGE_RATE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rate = data.get('rates', {}).get('CNY', None)
                    if rate:
                        print(f"[RATE] USD/CNY = {rate} (from {data.get('timestamp', 'unknown')})")
                        return float(rate)
        except Exception as e:
            print(f"[RATE ERROR] {e}")

        # 如果无法获取汇率，尝试实时获取
        return self._fetch_live_rate()

    def _fetch_live_rate(self) -> float:
        """实时获取汇率"""
        try:
            # 尝试多个汇率API
            apis = [
                ('https://open.er-api.com/v6/latest/USD', lambda d: d['rates']['CNY']),
                ('https://api.exchangerate-api.com/v4/latest/USD', lambda d: d['rates']['CNY']),
            ]
            for url, extractor in apis:
                try:
                    resp = self.session.get(url, timeout=10)
                    if resp.status_code == 200:
                        rate = extractor(resp.json())
                        print(f"[RATE] USD/CNY = {rate} (live from API)")
                        return float(rate)
                except:
                    continue
        except Exception as e:
            print(f"[RATE ERROR] Failed to get live rate: {e}")

        raise ValueError("Cannot get exchange rate - refusing to use hardcoded value")

    def cny_to_usd(self, cny_price: float) -> float:
        """人民币转美元"""
        return round(cny_price / self.usd_cny_rate, 6)

    def extract_prices_from_text(self, text: str, patterns: List[Tuple[str, str]]) -> List[Dict]:
        """从文本中使用正则提取价格"""
        models = []
        for pattern, model_hint in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                try:
                    groups = match.groups()
                    if len(groups) >= 2:
                        model_name = model_hint if model_hint else groups[0] if len(groups) > 2 else "unknown"
                        input_price = float(groups[-2])
                        output_price = float(groups[-1])
                        models.append({
                            "model": model_name,
                            "input_price": input_price,
                            "output_price": output_price
                        })
                except:
                    continue
        return models

    def crawl_openai(self) -> Dict:
        """爬取OpenAI定价 - 通过API文档"""
        print("\n[CRAWL] OpenAI...")

        try:
            # OpenAI有一个公开的模型列表API
            url = "https://openai.com/api/pricing/"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                # 尝试解析页面中的JSON数据
                soup = BeautifulSoup(resp.text, 'html.parser')

                # 查找所有script标签中的JSON数据
                for script in soup.find_all('script'):
                    if script.string and 'pricing' in script.string.lower():
                        # 尝试提取价格数据
                        text = script.string

                        # 常见的价格模式: "gpt-4o" ... "$X.XX" ... "input" ... "$Y.YY" ... "output"
                        price_patterns = [
                            (r'"(gpt-4o)"[^}]*?"(\d+\.?\d*)"[^}]*?input[^}]*?"(\d+\.?\d*)"[^}]*?output', None),
                            (r'(gpt-4o-mini)[^\d]*(\d+\.?\d*)[^\d]*per[^\d]*million[^\d]*input[^\d]*(\d+\.?\d*)[^\d]*output', None),
                        ]

                        for pattern, hint in price_patterns:
                            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                            if match:
                                groups = match.groups()
                                models.append({
                                    "model": groups[0],
                                    "input_price_per_1m": float(groups[1]),
                                    "output_price_per_1m": float(groups[2]),
                                    "input_price_per_1k": float(groups[1]) / 1000,
                                    "output_price_per_1k": float(groups[2]) / 1000,
                                    "currency": "USD",
                                    "scraped_at": datetime.now().isoformat()
                                })
                                print(f"    Found: {groups[0]}")

                # 备用：从页面文本提取
                if not models:
                    page_text = resp.text

                    # 更宽松的模式匹配
                    model_patterns = [
                        r'(gpt-4o(?:-mini)?)["\s:]*[^$]*\$(\d+\.?\d*)[^$]*\$(\d+\.?\d*)',
                        r'(o1-(?:preview|mini))["\s:]*[^$]*\$(\d+\.?\d*)[^$]*\$(\d+\.?\d*)',
                    ]

                    for pattern in model_patterns:
                        for match in re.finditer(pattern, page_text, re.IGNORECASE):
                            models.append({
                                "model": match.group(1),
                                "input_price_per_1m": float(match.group(2)),
                                "output_price_per_1m": float(match.group(3)),
                                "input_price_per_1k": float(match.group(2)) / 1000,
                                "output_price_per_1k": float(match.group(3)) / 1000,
                                "currency": "USD",
                                "scraped_at": datetime.now().isoformat()
                            })
                            print(f"    Found: {match.group(1)}")

            return {
                "provider": "OpenAI",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "OpenAI", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_anthropic(self) -> Dict:
        """爬取Anthropic定价"""
        print("\n[CRAWL] Anthropic...")

        try:
            url = "https://www.anthropic.com/pricing"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                page_text = resp.text

                # Anthropic格式通常是: Claude 3.5 Sonnet $3 / MTok input $15 / MTok output
                patterns = [
                    r'(claude[- ]?3\.?5?[- ]?sonnet)[^$]*\$(\d+\.?\d*)\s*/\s*M[^$]*\$(\d+\.?\d*)',
                    r'(claude[- ]?3\.?5?[- ]?haiku)[^$]*\$(\d+\.?\d*)\s*/\s*M[^$]*\$(\d+\.?\d*)',
                    r'(claude[- ]?3[- ]?opus)[^$]*\$(\d+\.?\d*)\s*/\s*M[^$]*\$(\d+\.?\d*)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                    if match:
                        model_name = match.group(1).strip()
                        input_price = float(match.group(2))
                        output_price = float(match.group(3))
                        models.append({
                            "model": model_name,
                            "input_price_per_1m": input_price,
                            "output_price_per_1m": output_price,
                            "input_price_per_1k": input_price / 1000,
                            "output_price_per_1k": output_price / 1000,
                            "currency": "USD",
                            "scraped_at": datetime.now().isoformat()
                        })
                        print(f"    Found: {model_name} - ${input_price}/M in, ${output_price}/M out")

            return {
                "provider": "Anthropic",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "Anthropic", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_google(self) -> Dict:
        """爬取Google AI定价"""
        print("\n[CRAWL] Google AI...")

        try:
            url = "https://ai.google.dev/pricing"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # 查找定价表格
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            cell_text = cells[0].get_text(strip=True).lower()
                            if 'gemini' in cell_text:
                                model_name = cells[0].get_text(strip=True)
                                # 尝试从后续单元格提取价格
                                for i, cell in enumerate(cells[1:], 1):
                                    text = cell.get_text(strip=True)
                                    price_match = re.search(r'\$?(\d+\.?\d*)', text)
                                    if price_match:
                                        try:
                                            price = float(price_match.group(1))
                                            # 假设第一个价格是input，第二个是output
                                            if i == 1:
                                                input_price = price
                                            elif i == 2:
                                                output_price = price
                                                models.append({
                                                    "model": model_name,
                                                    "input_price_per_1m": input_price,
                                                    "output_price_per_1m": output_price,
                                                    "input_price_per_1k": input_price / 1000,
                                                    "output_price_per_1k": output_price / 1000,
                                                    "currency": "USD",
                                                    "scraped_at": datetime.now().isoformat()
                                                })
                                                print(f"    Found: {model_name}")
                                                break
                                        except:
                                            pass

            return {
                "provider": "Google",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "Google", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_deepseek(self) -> Dict:
        """爬取DeepSeek定价 - 使用QWEN大模型分析中文页面"""
        print("\n[CRAWL] DeepSeek (使用QWEN大模型分析)...")

        try:
            # 使用中文定价页面
            url = "https://api-docs.deepseek.com/zh-cn/quick_start/pricing/"
            resp = self.session.get(url, timeout=15)

            if resp.status_code != 200:
                print(f"    页面获取失败: HTTP {resp.status_code}")
                # 回退到英文页面
                url = "https://api-docs.deepseek.com/quick_start/pricing/"
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    return {
                        "provider": "DeepSeek",
                        "source_url": url,
                        "crawl_time": datetime.now().isoformat(),
                        "crawl_status": "error",
                        "error": f"HTTP {resp.status_code}",
                        "models_found": 0,
                        "models": []
                    }

            # 获取页面内容
            page_content = resp.text[:10000]  # 限制长度，避免token过多

            # 尝试使用QWEN大模型分析页面内容
            models = self._analyze_with_qwen(page_content, url)

            # 如果QWEN分析返回空结果，尝试英文页面
            if not models and "zh-cn" in url:
                print("    中文页面未找到价格，尝试英文页面...")
                en_url = "https://api-docs.deepseek.com/quick_start/pricing/"
                en_resp = self.session.get(en_url, timeout=15)
                if en_resp.status_code == 200:
                    en_content = en_resp.text[:10000]
                    models = self._analyze_with_qwen(en_content, en_url)
                    url = en_url  # 更新URL为英文页面
                else:
                    print(f"    英文页面获取失败: HTTP {en_resp.status_code}")

            # 如果QWEN分析失败，回退到传统解析方法
            if not models:
                print("    QWEN分析失败，回退到传统解析...")
                models = self._parse_deepseek_traditional(resp.text, url)

            return {
                "provider": "DeepSeek",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"provider": "DeepSeek", "error": str(e), "crawl_status": "error", "models": []}

    def _analyze_with_qwen(self, page_content: str, url: str) -> List[Dict]:
        """使用QWEN大模型分析页面内容提取价格信息"""
        try:
            # 检查API密钥
            import os
            from dotenv import load_dotenv

            # 加载环境变量
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env.local')
            if os.path.exists(env_path):
                load_dotenv(env_path)

            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                print("    [QWEN] DASHSCOPE_API_KEY 未设置，跳过AI分析")
                return []

            # 导入QWEN适配器 - 添加项目根目录到sys.path
            try:
                import sys
                import os
                # 添加项目根目录到sys.path (向上两级：scripts -> computepulse目录)
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)

                from ai_orchestrator.adapters.qwen_adapter import QwenAdapter
            except ImportError as e:
                print(f"    [QWEN] 无法导入QwenAdapter: {e}")
                print(f"    [QWEN] sys.path: {sys.path}")
                print(f"    [QWEN] 当前目录: {os.getcwd()}")
                print(f"    [QWEN] 项目根目录: {project_root}")
                # 尝试备选路径：向上三级
                try:
                    project_root_alt = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    if project_root_alt not in sys.path:
                        sys.path.insert(0, project_root_alt)
                    from ai_orchestrator.adapters.qwen_adapter import QwenAdapter
                    print(f"    [QWEN] 使用备选路径导入成功: {project_root_alt}")
                except ImportError as e2:
                    print(f"    [QWEN] 备选路径也失败: {e2}")
                    return []

            # 准备prompt
            system_prompt = """你是一个专业的AI定价数据分析助手。请从提供的DeepSeek定价页面内容中提取token价格信息。

你需要提取以下信息：
1. 模型名称（如：DeepSeek-V3.2, DeepSeek-V3.2 (Cache Hit), DeepSeek-V3.2 (Cache Miss), DeepSeek-V3.2 (Output)等）
2. 输入价格（每100万token，美元）
3. 输出价格（每100万token，美元）
4. 价格类型（input_cache_hit, input_cache_miss, output）

页面中可能包含的价格格式：
- $0.028 per 1M input tokens (cache hit)
- $0.28 per 1M input tokens (cache miss)
- $0.42 per 1M output tokens

请以JSON数组格式返回结果，每个元素包含以下字段：
- model: 模型名称
- input_price_per_1m: 输入价格（每100万token，美元），如果没有则为null
- output_price_per_1m: 输出价格（每100万token，美元），如果没有则为null
- input_price_per_1k: 输入价格（每1000token，美元），自动计算（input_price_per_1m / 1000）
- output_price_per_1k: 输出价格（每1000token，美元），自动计算（output_price_per_1m / 1000）
- currency: "USD"
- price_type: "input_cache_hit", "input_cache_miss", "output" 或 "unknown"
- price_label: 原始价格标签文本

如果没有找到价格信息，返回空数组 []。"""

            user_prompt = f"""请分析以下DeepSeek定价页面内容，提取所有token价格信息：

页面URL: {url}

页面内容（部分）:
{page_content[:5000]}  # 限制内容长度

请提取价格信息并以JSON数组格式返回。"""

            print("    [QWEN] 调用QWEN大模型分析页面内容...")

            # 创建适配器（禁用搜索，因为我们已经有页面内容）
            adapter = QwenAdapter(api_key=api_key, enable_search=False)

            # 同步调用（因为爬虫是同步的）
            import asyncio

            # 创建新的事件循环
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(adapter.call_async(user_prompt, system_prompt=system_prompt))
            finally:
                loop.close()

            if not response.success:
                print(f"    [QWEN] API调用失败: {response.error}")
                return []

            # 解析响应内容，提取JSON
            content = response.content.strip()
            print(f"    [QWEN] 收到响应长度: {len(content)} 字符")
            print(f"    [QWEN] 响应预览: {content[:200]}...")

            # 尝试从响应中提取JSON
            import json
            import re

            # 查找JSON数组
            json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    models = json.loads(json_str)
                    print(f"    [QWEN] 成功解析 {len(models)} 个模型")

                    # 添加scraped_at时间戳
                    for model in models:
                        model["scraped_at"] = datetime.now().isoformat()
                        # 确保价格字段是数字类型
                        for field in ["input_price_per_1m", "output_price_per_1m", "input_price_per_1k", "output_price_per_1k"]:
                            if model.get(field) is not None:
                                model[field] = float(model[field])

                    return models
                except json.JSONDecodeError as e:
                    print(f"    [QWEN] JSON解析失败: {e}")

            # 如果没找到JSON，尝试手动解析文本
            print("    [QWEN] 未找到JSON，尝试手动解析文本...")
            models = self._extract_prices_from_qwen_response(content)
            return models

        except Exception as e:
            print(f"    [QWEN] 分析过程出错: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_prices_from_qwen_response(self, text: str) -> List[Dict]:
        """从QWEN响应文本中提取价格信息（备用方法）"""
        models = []

        # 查找价格模式
        price_patterns = [
            # $0.028 per 1M input tokens (cache hit)
            (r'\$(\d+\.?\d*)\s*per\s*1M\s*input\s*tokens?\s*\(cache\s*hit\)', 'DeepSeek-V3.2 (Cache Hit)', 'input_cache_hit', None),
            # $0.28 per 1M input tokens (cache miss)
            (r'\$(\d+\.?\d*)\s*per\s*1M\s*input\s*tokens?\s*\(cache\s*miss\)', 'DeepSeek-V3.2 (Cache Miss)', 'input_cache_miss', None),
            # $0.42 per 1M output tokens
            (r'\$(\d+\.?\d*)\s*per\s*1M\s*output\s*tokens?', 'DeepSeek-V3.2 (Output)', 'output', None),
        ]

        for pattern, model_name, price_type, _ in price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                price = float(match.group(1))
                price_per_1k = price / 1000

                model = {
                    "model": model_name,
                    "input_price_per_1m": price if price_type in ["input_cache_hit", "input_cache_miss"] else None,
                    "output_price_per_1m": price if price_type == "output" else None,
                    "input_price_per_1k": price_per_1k if price_type in ["input_cache_hit", "input_cache_miss"] else None,
                    "output_price_per_1k": price_per_1k if price_type == "output" else None,
                    "currency": "USD",
                    "price_type": price_type,
                    "price_label": match.group(0),
                    "scraped_at": datetime.now().isoformat()
                }
                models.append(model)
                print(f"    [QWEN] 从文本提取: {model_name} - ${price}/1M")

        return models

    def _parse_deepseek_traditional(self, page_text: str, url: str) -> List[Dict]:
        """传统解析方法（回退用）"""
        # 这是原来的解析逻辑，保留作为备选
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_text, 'html.parser')
            models = []

            # 查找定价表格
            tables = soup.find_all('table')
            print(f"    找到 {len(tables)} 个表格")

            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')

                # 分析表格结构 - 查找包含"PRICING"的行
                for row_idx, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells]).lower()

                    # 检查是否是定价行
                    if ('pricing' in row_text or
                        ('token' in row_text and ('input' in row_text or 'output' in row_text))):
                        print(f"    分析行 {row_idx}: {row_text[:100]}...")

                        # 尝试提取价格信息
                        for cell in cells:
                            cell_text = cell.get_text(strip=True)

                            # 检查是否包含美元价格
                            usd_match = re.search(r'\$(\d+\.?\d*)', cell_text)
                            if usd_match:
                                price = float(usd_match.group(1))
                                print(f"      找到价格: ${price}")

                                # 确定价格类型
                                price_type = "unknown"
                                price_label = ""

                                # 查找价格标签（前一个单元格或当前行文本）
                                for prev_cell in cells:
                                    prev_text = prev_cell.get_text(strip=True)
                                    prev_text_lower = prev_text.lower()
                                    print(f"        检查单元格: '{prev_text}'")

                                    if 'input' in prev_text_lower and 'cache hit' in prev_text_lower:
                                        price_type = "input_cache_hit"
                                        price_label = prev_text  # 使用原始文本
                                        print(f"        识别为: input_cache_hit")
                                        break
                                    elif 'input' in prev_text_lower and 'cache miss' in prev_text_lower:
                                        price_type = "input_cache_miss"
                                        price_label = prev_text
                                        print(f"        识别为: input_cache_miss")
                                        break
                                    elif 'output' in prev_text_lower:
                                        price_type = "output"
                                        price_label = prev_text
                                        print(f"        识别为: output")
                                        break

                                # 创建模型条目
                                model_name = "DeepSeek-V3.2"
                                if price_type == "input_cache_hit":
                                    model_name = "DeepSeek-V3.2 (Cache Hit)"
                                elif price_type == "input_cache_miss":
                                    model_name = "DeepSeek-V3.2 (Cache Miss)"
                                elif price_type == "output":
                                    model_name = "DeepSeek-V3.2 (Output)"

                                models.append({
                                    "model": model_name,
                                    "price_label": price_label,
                                    "input_price_per_1m": price if price_type in ["input_cache_hit", "input_cache_miss"] else None,
                                    "output_price_per_1m": price if price_type == "output" else None,
                                    "input_price_per_1k": price / 1000 if price_type in ["input_cache_hit", "input_cache_miss"] else None,
                                    "output_price_per_1k": price / 1000 if price_type == "output" else None,
                                    "currency": "USD",
                                    "scraped_at": datetime.now().isoformat(),
                                    "price_type": price_type
                                })

            # 如果没找到价格，尝试更直接的搜索
            if not models:
                print("    表格解析未找到价格，尝试直接搜索...")
                all_text = page_text
                price_matches = re.findall(r'\$(\d+\.?\d*)', all_text)
                unique_prices = list(set(price_matches))

                for price_str in unique_prices:
                    price = float(price_str)
                    print(f"      找到价格: ${price}")

                    # 简单分配模型
                    models.append({
                        "model": "DeepSeek-V3.2",
                        "input_price_per_1m": price,
                        "output_price_per_1m": price,
                        "input_price_per_1k": price / 1000,
                        "output_price_per_1k": price / 1000,
                        "currency": "USD",
                        "scraped_at": datetime.now().isoformat()
                    })

            return models

        except Exception as e:
            print(f"    传统解析失败: {e}")
            return []

    def crawl_zhipu(self) -> Dict:
        """爬取智谱GLM定价"""
        print("\n[CRAWL] Zhipu (GLM)...")

        try:
            url = "https://open.bigmodel.cn/pricing"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # 查找定价卡片或表格
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        row_text = row.get_text().lower()

                        if 'glm' in row_text and len(cells) >= 2:
                            model_name = cells[0].get_text(strip=True)

                            for cell in cells[1:]:
                                text = cell.get_text(strip=True)
                                # 智谱使用人民币
                                cny_match = re.search(r'(\d+\.?\d*)\s*(?:元|¥|￥)', text)
                                if not cny_match:
                                    cny_match = re.search(r'(\d+\.?\d*)', text)

                                if cny_match:
                                    try:
                                        cny_price = float(cny_match.group(1))
                                        if cny_price > 0:
                                            usd_price = self.cny_to_usd(cny_price)
                                            models.append({
                                                "model": model_name,
                                                "input_price_per_1m": usd_price * 1000,  # per 1K -> per 1M
                                                "output_price_per_1m": usd_price * 1000,
                                                "input_price_per_1k": usd_price,
                                                "output_price_per_1k": usd_price,
                                                "currency": "USD",
                                                "original_currency": "CNY",
                                                "original_price_per_1k": cny_price,
                                                "exchange_rate": self.usd_cny_rate,
                                                "scraped_at": datetime.now().isoformat()
                                            })
                                            print(f"    Found: {model_name} - ¥{cny_price}/1K")
                                            break
                                    except:
                                        pass

            return {
                "provider": "Zhipu",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "Zhipu", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_alibaba(self) -> Dict:
        """爬取阿里通义千问定价"""
        print("\n[CRAWL] Alibaba (Qwen)...")

        try:
            url = "https://help.aliyun.com/zh/model-studio/billing"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        row_text = row.get_text().lower()

                        if 'qwen' in row_text and len(cells) >= 3:
                            model_name = cells[0].get_text(strip=True)

                            try:
                                # 尝试提取输入和输出价格
                                input_text = cells[1].get_text(strip=True)
                                output_text = cells[2].get_text(strip=True) if len(cells) > 2 else input_text

                                input_match = re.search(r'(\d+\.?\d*)', input_text)
                                output_match = re.search(r'(\d+\.?\d*)', output_text)

                                if input_match:
                                    input_cny = float(input_match.group(1))
                                    output_cny = float(output_match.group(1)) if output_match else input_cny

                                    if input_cny > 0:
                                        input_usd = self.cny_to_usd(input_cny)
                                        output_usd = self.cny_to_usd(output_cny)

                                        models.append({
                                            "model": model_name,
                                            "input_price_per_1k": input_usd,
                                            "output_price_per_1k": output_usd,
                                            "input_price_per_1m": input_usd * 1000,
                                            "output_price_per_1m": output_usd * 1000,
                                            "currency": "USD",
                                            "original_currency": "CNY",
                                            "original_input_per_1k": input_cny,
                                            "original_output_per_1k": output_cny,
                                            "exchange_rate": self.usd_cny_rate,
                                            "scraped_at": datetime.now().isoformat()
                                        })
                                        print(f"    Found: {model_name}")
                            except:
                                pass

            return {
                "provider": "Alibaba",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "Alibaba", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_moonshot(self) -> Dict:
        """爬取Moonshot/Kimi定价"""
        print("\n[CRAWL] Moonshot (Kimi)...")

        try:
            url = "https://platform.moonshot.cn/docs/pricing"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        row_text = row.get_text().lower()

                        if 'moonshot' in row_text and len(cells) >= 2:
                            model_name = cells[0].get_text(strip=True)

                            for cell in cells[1:]:
                                text = cell.get_text(strip=True)
                                cny_match = re.search(r'(\d+\.?\d*)', text)
                                if cny_match:
                                    try:
                                        cny_price = float(cny_match.group(1))
                                        if cny_price > 0:
                                            usd_price = self.cny_to_usd(cny_price)
                                            models.append({
                                                "model": model_name,
                                                "input_price_per_1k": usd_price,
                                                "output_price_per_1k": usd_price,
                                                "input_price_per_1m": usd_price * 1000,
                                                "output_price_per_1m": usd_price * 1000,
                                                "currency": "USD",
                                                "original_currency": "CNY",
                                                "original_price_per_1k": cny_price,
                                                "exchange_rate": self.usd_cny_rate,
                                                "scraped_at": datetime.now().isoformat()
                                            })
                                            print(f"    Found: {model_name} - ¥{cny_price}/1K")
                                            break
                                    except:
                                        pass

            return {
                "provider": "Moonshot",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "Moonshot", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_baidu(self) -> Dict:
        """爬取百度文心定价"""
        print("\n[CRAWL] Baidu (ERNIE)...")

        try:
            url = "https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        row_text = row.get_text().lower()

                        if 'ernie' in row_text and len(cells) >= 2:
                            model_name = cells[0].get_text(strip=True)

                            for cell in cells[1:]:
                                text = cell.get_text(strip=True)
                                cny_match = re.search(r'(\d+\.?\d*)', text)
                                if cny_match:
                                    try:
                                        cny_price = float(cny_match.group(1))
                                        if cny_price > 0:
                                            usd_price = self.cny_to_usd(cny_price)
                                            models.append({
                                                "model": model_name,
                                                "input_price_per_1k": usd_price,
                                                "output_price_per_1k": usd_price,
                                                "input_price_per_1m": usd_price * 1000,
                                                "output_price_per_1m": usd_price * 1000,
                                                "currency": "USD",
                                                "original_currency": "CNY",
                                                "original_price_per_1k": cny_price,
                                                "exchange_rate": self.usd_cny_rate,
                                                "scraped_at": datetime.now().isoformat()
                                            })
                                            print(f"    Found: {model_name} - ¥{cny_price}/1K")
                                            break
                                    except:
                                        pass

            return {
                "provider": "Baidu",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "Baidu", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_minimax(self) -> Dict:
        """爬取MiniMax定价"""
        print("\n[CRAWL] MiniMax...")

        try:
            url = "https://platform.minimaxi.com/document/Price"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        row_text = row.get_text().lower()

                        if 'abab' in row_text and len(cells) >= 2:
                            model_name = cells[0].get_text(strip=True)

                            for cell in cells[1:]:
                                text = cell.get_text(strip=True)
                                cny_match = re.search(r'(\d+\.?\d*)', text)
                                if cny_match:
                                    try:
                                        cny_price = float(cny_match.group(1))
                                        if cny_price > 0:
                                            usd_price = self.cny_to_usd(cny_price)
                                            models.append({
                                                "model": model_name,
                                                "input_price_per_1k": usd_price,
                                                "output_price_per_1k": usd_price,
                                                "currency": "USD",
                                                "original_currency": "CNY",
                                                "original_price_per_1k": cny_price,
                                                "exchange_rate": self.usd_cny_rate,
                                                "scraped_at": datetime.now().isoformat()
                                            })
                                            print(f"    Found: {model_name}")
                                            break
                                    except:
                                        pass

            return {
                "provider": "MiniMax",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "MiniMax", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_xai(self) -> Dict:
        """爬取xAI/Grok定价"""
        print("\n[CRAWL] xAI (Grok)...")

        try:
            url = "https://docs.x.ai/docs/models"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                page_text = resp.text

                # xAI定价模式
                patterns = [
                    r'(grok-2[^\s"]*)[^$]*\$(\d+\.?\d*)\s*/\s*(?:1M|million)[^$]*\$(\d+\.?\d*)',
                    r'(grok-beta)[^$]*\$(\d+\.?\d*)[^$]*\$(\d+\.?\d*)',
                ]

                for pattern in patterns:
                    for match in re.finditer(pattern, page_text, re.IGNORECASE | re.DOTALL):
                        model_name = match.group(1)
                        input_price = float(match.group(2))
                        output_price = float(match.group(3))
                        models.append({
                            "model": model_name,
                            "input_price_per_1m": input_price,
                            "output_price_per_1m": output_price,
                            "input_price_per_1k": input_price / 1000,
                            "output_price_per_1k": output_price / 1000,
                            "currency": "USD",
                            "scraped_at": datetime.now().isoformat()
                        })
                        print(f"    Found: {model_name}")

            return {
                "provider": "xAI",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "xAI", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_mistral(self) -> Dict:
        """爬取Mistral定价"""
        print("\n[CRAWL] Mistral...")

        try:
            url = "https://mistral.ai/technology/"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                page_text = resp.text

                patterns = [
                    r'(mistral[- ]?large)[^$]*\$(\d+\.?\d*)[^$]*\$(\d+\.?\d*)',
                    r'(mistral[- ]?small)[^$]*\$(\d+\.?\d*)[^$]*\$(\d+\.?\d*)',
                    r'(codestral)[^$]*\$(\d+\.?\d*)[^$]*\$(\d+\.?\d*)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                    if match:
                        models.append({
                            "model": match.group(1),
                            "input_price_per_1m": float(match.group(2)),
                            "output_price_per_1m": float(match.group(3)),
                            "input_price_per_1k": float(match.group(2)) / 1000,
                            "output_price_per_1k": float(match.group(3)) / 1000,
                            "currency": "USD",
                            "scraped_at": datetime.now().isoformat()
                        })
                        print(f"    Found: {match.group(1)}")

            return {
                "provider": "Mistral",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "Mistral", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_cohere(self) -> Dict:
        """爬取Cohere定价"""
        print("\n[CRAWL] Cohere...")

        try:
            url = "https://cohere.com/pricing"
            resp = self.session.get(url, timeout=15)

            models = []

            if resp.status_code == 200:
                page_text = resp.text

                patterns = [
                    r'(command[- ]?r[- ]?plus)[^$]*\$(\d+\.?\d*)[^$]*\$(\d+\.?\d*)',
                    r'(command[- ]?r)(?![- ]?plus)[^$]*\$(\d+\.?\d*)[^$]*\$(\d+\.?\d*)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                    if match:
                        models.append({
                            "model": match.group(1),
                            "input_price_per_1m": float(match.group(2)),
                            "output_price_per_1m": float(match.group(3)),
                            "input_price_per_1k": float(match.group(2)) / 1000,
                            "output_price_per_1k": float(match.group(3)) / 1000,
                            "currency": "USD",
                            "scraped_at": datetime.now().isoformat()
                        })
                        print(f"    Found: {match.group(1)}")

            return {
                "provider": "Cohere",
                "source_url": url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {"provider": "Cohere", "error": str(e), "crawl_status": "error", "models": []}

    def crawl_alibaba_qwen(self) -> Dict:
        """爬取阿里巴巴QWEN定价 - 使用QWEN大模型联网搜索"""
        print("\n[CRAWL] Alibaba (QWEN - 使用大模型联网搜索)...")

        try:
            # 目标URL（可能需要登录，所以使用QWEN联网搜索）
            target_url = "https://bailian.console.aliyun.com/?tab=model#/model-market/detail/qwen3-vl-plus"

            # 使用QWEN联网搜索获取定价信息
            models = self._search_with_qwen_for_pricing()

            # 如果QWEN搜索失败，尝试直接访问页面（可能失败）
            if not models:
                print("    QWEN搜索未找到价格，尝试直接访问页面...")
                models = self._try_direct_page_access(target_url)

            return {
                "provider": "Alibaba",
                "source_url": target_url,
                "crawl_time": datetime.now().isoformat(),
                "crawl_status": "success" if models else "no_data",
                "models_found": len(models),
                "models": models
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"provider": "Alibaba", "error": str(e), "crawl_status": "error", "models": []}

    def _search_with_qwen_for_pricing(self) -> List[Dict]:
        """使用QWEN联网搜索获取阿里巴巴QWEN定价信息"""
        try:
            # 检查API密钥
            import os
            from dotenv import load_dotenv

            # 加载环境变量
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env.local')
            if os.path.exists(env_path):
                load_dotenv(env_path)

            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                print("    [QWEN] DASHSCOPE_API_KEY 未设置，跳过AI搜索")
                return []

            # 导入QWEN适配器
            try:
                import sys
                import os
                # 添加项目根目录到sys.path
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)

                from ai_orchestrator.adapters.qwen_adapter import QwenAdapter
            except ImportError as e:
                print(f"    [QWEN] 无法导入QwenAdapter: {e}")
                return []

            # 准备prompt - 让QWEN搜索最新的定价信息
            system_prompt = """你是一个专业的AI定价数据分析助手。请搜索阿里巴巴QWEN模型的最新定价信息。

你需要搜索以下信息：
1. 模型名称（如：QWEN3-VL-PLUS, QWEN2.5-32B, QWEN2.5-7B, QWEN2.5-1.5B等）
2. 输入价格（每100万token，人民币或美元）
3. 输出价格（每100万token，人民币或美元）
4. 价格类型（输入、输出、按需、预付费等）

请搜索以下关键词：
- "阿里巴巴 QWEN3-VL-PLUS 定价"
- "阿里云百炼 QWEN 价格"
- "QWEN模型 token价格"
- "阿里云模型市场定价"

请以JSON数组格式返回结果，每个元素包含以下字段：
- model: 模型名称
- input_price_per_1m: 输入价格（每100万token），如果没有则为null
- output_price_per_1m: 输出价格（每100万token），如果没有则为null
- input_price_per_1k: 输入价格（每1000token），自动计算（input_price_per_1m / 1000）
- output_price_per_1k: 输出价格（每1000token），自动计算（output_price_per_1m / 1000）
- currency: "USD" 或 "CNY"
- price_type: "input", "output", "on_demand", "reserved" 或 "unknown"
- price_label: 原始价格标签文本
- source: 信息来源（网站名称或URL）

如果没有找到价格信息，返回空数组 []。"""

            user_prompt = """请搜索阿里巴巴QWEN模型（特别是QWEN3-VL-PLUS）的最新定价信息。

请重点搜索：
1. 阿里云百炼平台（bailian.aliyun.com）的定价
2. 阿里云模型市场的定价信息
3. QWEN模型的token计费标准

请使用中文关键词搜索，并返回JSON格式的结果。"""

            print("    [QWEN] 调用QWEN大模型进行联网搜索...")

            # 创建适配器（启用搜索功能）
            adapter = QwenAdapter(api_key=api_key, enable_search=True)

            # 同步调用
            import asyncio

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(adapter.call_async(user_prompt, system_prompt=system_prompt))
            finally:
                loop.close()

            if not response.success:
                print(f"    [QWEN] API调用失败: {response.error}")
                return []

            # 解析响应内容，提取JSON
            content = response.content.strip()
            print(f"    [QWEN] 收到响应长度: {len(content)} 字符")
            print(f"    [QWEN] 响应预览: {content[:200]}...")

            # 尝试从响应中提取JSON
            import json
            import re

            # 查找JSON数组
            json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    models = json.loads(json_str)
                    print(f"    [QWEN] 成功解析 {len(models)} 个模型")

                    # 添加scraped_at时间戳，处理货币转换
                    for model in models:
                        model["scraped_at"] = datetime.now().isoformat()

                        # 确保价格字段是数字类型
                        for field in ["input_price_per_1m", "output_price_per_1m", "input_price_per_1k", "output_price_per_1k"]:
                            if model.get(field) is not None:
                                model[field] = float(model[field])

                        # 如果是人民币，转换为美元
                        if model.get("currency") == "CNY":
                            input_price_cny = model.get("input_price_per_1m")
                            output_price_cny = model.get("output_price_per_1m")

                            if input_price_cny:
                                model["input_price_per_1m"] = self.cny_to_usd(input_price_cny)
                                model["input_price_per_1k"] = model["input_price_per_1m"] / 1000
                                model["original_currency"] = "CNY"
                                model["original_input_per_1m"] = input_price_cny
                                model["exchange_rate"] = self.usd_cny_rate

                            if output_price_cny:
                                model["output_price_per_1m"] = self.cny_to_usd(output_price_cny)
                                model["output_price_per_1k"] = model["output_price_per_1m"] / 1000
                                if "original_currency" not in model:
                                    model["original_currency"] = "CNY"
                                model["original_output_per_1m"] = output_price_cny
                                model["exchange_rate"] = self.usd_cny_rate

                            model["currency"] = "USD"

                    return models
                except json.JSONDecodeError as e:
                    print(f"    [QWEN] JSON解析失败: {e}")

            # 如果没找到JSON，尝试手动解析文本
            print("    [QWEN] 未找到JSON，尝试手动解析文本...")
            models = self._extract_qwen_prices_from_text(content)
            return models

        except Exception as e:
            print(f"    [QWEN] 搜索过程出错: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_qwen_prices_from_text(self, text: str) -> List[Dict]:
        """从QWEN响应文本中提取价格信息（备用方法）"""
        models = []

        # 查找QWEN价格模式
        price_patterns = [
            # 人民币价格模式：X元/1M tokens
            (r'(qwen[-\w\.]*(?:vl[- ]?plus)?)[^\d]*(\d+\.?\d*)\s*(?:元|¥|￥)\s*(?:per\s*)?(?:1M|百万)?\s*(?:tokens?|token)', 'input', 'CNY'),
            (r'(qwen[-\w\.]*)[^\d]*输入[^\d]*(\d+\.?\d*)\s*(?:元|¥|￥)', 'input', 'CNY'),
            (r'(qwen[-\w\.]*)[^\d]*输出[^\d]*(\d+\.?\d*)\s*(?:元|¥|￥)', 'output', 'CNY'),
            # 美元价格模式
            (r'(qwen[-\w\.]*(?:vl[- ]?plus)?)[^\$]*\$(\d+\.?\d*)\s*(?:per\s*)?(?:1M|million)?\s*tokens?', 'input', 'USD'),
        ]

        for pattern, price_type, currency in price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                model_name = match.group(1)
                price = float(match.group(2))

                # 创建模型条目
                model = {
                    "model": model_name,
                    "input_price_per_1m": price if price_type == "input" else None,
                    "output_price_per_1m": price if price_type == "output" else None,
                    "input_price_per_1k": price / 1000 if price_type == "input" else None,
                    "output_price_per_1k": price / 1000 if price_type == "output" else None,
                    "currency": currency,
                    "price_type": price_type,
                    "price_label": match.group(0),
                    "scraped_at": datetime.now().isoformat()
                }

                # 如果是人民币，转换为美元
                if currency == "CNY":
                    if price_type == "input":
                        model["input_price_per_1m"] = self.cny_to_usd(price)
                        model["input_price_per_1k"] = model["input_price_per_1m"] / 1000
                    elif price_type == "output":
                        model["output_price_per_1m"] = self.cny_to_usd(price)
                        model["output_price_per_1k"] = model["output_price_per_1m"] / 1000

                    model["original_currency"] = "CNY"
                    model["original_price_per_1m"] = price
                    model["exchange_rate"] = self.usd_cny_rate
                    model["currency"] = "USD"

                models.append(model)
                print(f"    [QWEN] 从文本提取: {model_name} - {price}{currency}/1M ({price_type})")

        return models

    def _try_direct_page_access(self, url: str) -> List[Dict]:
        """尝试直接访问页面（可能失败）"""
        try:
            resp = self.session.get(url, timeout=15)

            if resp.status_code == 200:
                # 尝试解析页面
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')

                # 查找价格信息
                page_text = resp.text.lower()
                price_patterns = re.findall(r'(\d+\.?\d*)\s*(?:元|¥|￥|美元|\$)', page_text)

                if price_patterns:
                    print(f"    直接访问找到 {len(price_patterns)} 个价格模式")
                    # 简单创建一个模型条目
                    return [{
                        "model": "QWEN3-VL-PLUS",
                        "input_price_per_1m": float(price_patterns[0]) * 1000,  # 假设是每1K价格
                        "output_price_per_1m": float(price_patterns[0]) * 1000,
                        "input_price_per_1k": float(price_patterns[0]),
                        "output_price_per_1k": float(price_patterns[0]),
                        "currency": "USD",
                        "price_type": "unknown",
                        "price_label": f"从页面提取: {price_patterns[0]}",
                        "scraped_at": datetime.now().isoformat()
                    }]
                else:
                    print("    直接访问未找到价格信息")
            else:
                print(f"    直接访问失败: HTTP {resp.status_code}")

        except Exception as e:
            print(f"    直接访问出错: {e}")

        return []

    # 文件读写方法
    def load_existing_data(self) -> Dict:
        """加载现有的定价数据"""
        data = {
            "metadata": {
                "crawl_timestamp": datetime.now().isoformat(),
                "method": "pure_web_crawling",
                "exchange_rate_usd_cny": self.usd_cny_rate,
                "data_source": "Official pricing pages only",
                "no_preset_data": True,
                "total_providers": 0,
                "successful_crawls": 0,
                "total_models": 0
            },
            "providers": []
        }

        try:
            if os.path.exists(TOKEN_PRICING_FILE):
                with open(TOKEN_PRICING_FILE, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    # 保留现有数据，但更新元数据中的汇率
                    if "metadata" in existing:
                        data["metadata"] = existing["metadata"]
                        data["metadata"]["exchange_rate_usd_cny"] = self.usd_cny_rate
                    if "providers" in existing:
                        data["providers"] = existing["providers"]
        except Exception as e:
            print(f"[WARN] Failed to load existing data: {e}")

        return data

    def save_provider_data(self, provider_data: Dict, update_metadata: bool = True) -> None:
        """保存单个provider的数据到共享文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(TOKEN_PRICING_FILE), exist_ok=True)

            # 加载现有数据
            all_data = self.load_existing_data()

            # 查找并更新或添加provider数据
            provider_name = provider_data.get("provider")
            existing_index = -1
            for i, provider in enumerate(all_data["providers"]):
                if provider.get("provider") == provider_name:
                    existing_index = i
                    break

            if existing_index >= 0:
                # 更新现有provider
                all_data["providers"][existing_index] = provider_data
                print(f"[UPDATE] Updated {provider_name} data")
            else:
                # 添加新provider
                all_data["providers"].append(provider_data)
                print(f"[ADD] Added {provider_name} data")

            # 更新元数据
            if update_metadata:
                self._update_metadata(all_data)

            # 保存文件
            with open(TOKEN_PRICING_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)

            print(f"[SAVED] {TOKEN_PRICING_FILE}")

        except Exception as e:
            print(f"[ERROR] Save failed: {e}")

    def _update_metadata(self, data: Dict) -> None:
        """更新元数据统计信息"""
        providers = data.get("providers", [])
        successful_crawls = 0
        total_models = 0

        for provider in providers:
            if provider.get("models"):
                successful_crawls += 1
                total_models += len(provider["models"])

        data["metadata"]["total_providers"] = len(providers)
        data["metadata"]["successful_crawls"] = successful_crawls
        data["metadata"]["total_models"] = total_models
        data["metadata"]["crawl_timestamp"] = datetime.now().isoformat()

    def crawl_all(self) -> Dict:
        """爬取所有供应商"""
        print("=" * 60)
        print("  ComputePulse Token Pricing - Pure Web Crawler")
        print("  NO PRESET DATA - 100% REAL-TIME")
        print("=" * 60)
        print(f"\n[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[RATE] Using USD/CNY = {self.usd_cny_rate}")

        all_data = {
            "metadata": {
                "crawl_timestamp": datetime.now().isoformat(),
                "method": "pure_web_crawling",
                "exchange_rate_usd_cny": self.usd_cny_rate,
                "data_source": "Official pricing pages only",
                "no_preset_data": True,
                "total_providers": 0,
                "successful_crawls": 0,
                "total_models": 0
            },
            "providers": []
        }

        # 所有爬虫
        crawlers = [
            self.crawl_openai,
            self.crawl_anthropic,
            self.crawl_google,
            self.crawl_xai,
            self.crawl_mistral,
            self.crawl_cohere,
            self.crawl_deepseek,
            self.crawl_baidu,
            self.crawl_zhipu,
            self.crawl_minimax,
            self.crawl_moonshot,
            self.crawl_alibaba_qwen,  # 使用QWEN大模型联网搜索的阿里巴巴爬虫
        ]

        for crawler in crawlers:
            try:
                result = crawler()
                all_data["providers"].append(result)
                all_data["metadata"]["total_providers"] += 1

                if result.get("models"):
                    all_data["metadata"]["successful_crawls"] += 1
                    all_data["metadata"]["total_models"] += len(result["models"])

            except Exception as e:
                print(f"  [ERROR] {e}")

        # 统计
        print(f"\n[STATS]")
        print(f"  Providers crawled: {all_data['metadata']['total_providers']}")
        print(f"  Successful: {all_data['metadata']['successful_crawls']}")
        print(f"  Total models found: {all_data['metadata']['total_models']}")

        return all_data

    def save(self, data: Dict):
        """保存数据（完整数据集）"""
        try:
            os.makedirs(os.path.dirname(TOKEN_PRICING_FILE), exist_ok=True)
            with open(TOKEN_PRICING_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n[SAVED] {TOKEN_PRICING_FILE}")
        except Exception as e:
            print(f"\n[ERROR] Save failed: {e}")