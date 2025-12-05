# 🌍 ComputePulse | Global AI Compute & Energy Index

<div align="center">

**Real-time tracker for the pulse of the global AI industry**

[![Data Quality](https://img.shields.io/badge/Data%20Quality-Good-brightgreen)](public/data/validation_report_gpu.json)
[![Records](https://img.shields.io/badge/Records-114-blue)](public/data/)
[![Update](https://img.shields.io/badge/Update-Daily-orange)](https://github.com/WUAIBING/computepulse/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

## 📈 What is ComputePulse?

ComputePulse is an intelligent dashboard that monitors the vital signs of the AI world:

### 💰 GCCI (Global Compute Cost Index)
Real-time tracking of GPU rental prices across 77 data points:
- **NVIDIA GPUs**: H100, H200, A100, L40S, Blackwell GB200
- **Chinese AI Chips**: Huawei Ascend 910B, Cambricon MLU370, Hygon DCU
- **Global Providers**: AWS, Azure, Google Cloud, Lambda Labs, RunPod, CoreWeave, Vast.ai
- **Chinese Providers**: Aliyun, Tencent Cloud, Baidu, Volcengine, Huawei Cloud

### 🤖 Token Price Index
Live monitoring of LLM API costs across 37 models:
- **International**: GPT-4o, Claude 3.5 Sonnet, Gemini 2.0, Llama 3
- **Chinese**: Qwen, Ernie, GLM-4, Kimi, Doubao, MiniMax, DeepSeek

### ⚡ GAGL (Global AI Grid Load)
Estimating real-time energy consumption of AI data centers:
- **Annual Consumption**: 415 TWh
- **Real-time Power**: 47.37 GW
- **Active GPUs**: ~4 million worldwide
- **Environmental Impact**: Equivalent to multiple nuclear reactors

## 🚀 Features

### 🤖 Quad-AI Intelligence Consortium
A self-evolving AI team that collaborates to gather, verify, and analyze market data:

- **🧠 Qwen (The Architect)**: Plannig & Orchestration. Defines search strategies and coordinates the team.
- **🎯 DeepSeek (The Hunter)**: Deep Web Mining. Uses reasoning capabilities to extract precise pricing data from complex sources.
- **🔎 Kimi (The Researcher)**: Verification & Fact-Checking. Cross-references data with news and official docs to ensure accuracy.
- **📊 GLM-4 (The Analyst)**: Market Insight & Synthesis. Uses **standalone web search** to analyze trends and generate "Cyberpunk-style" market briefings.

### 🛡️ Modular & Resilient Architecture
- **Dependency Inversion**: Abstract `BaseAgent` interface allows hot-swapping AI models like changing players in a game.
- **Factory Pattern**: `AgentFactory` dynamically instantiates agents (Qwen, DeepSeek, Kimi, GLM) without coupling.
- **Robust Validation**: Multi-layer data quality checks (Type → Range → Deduplication).
- **Auto-Healing**: Automatic retry and failover mechanisms for API calls.

### 🌐 Comprehensive Coverage
- **114+ Total Records**: GPU prices + Token prices + Energy metrics
- **Global & Local**: Covers both Western and Chinese markets seamlessly.
- **Real-Time Updates**: Automated daily updates via GitHub Actions.

### 🎨 Professional UI/UX
- **Holographic Dashboard**: Dynamic visual representation of the AI Consortium.
- **Mobile Optimized**: Perfect rendering on all devices.
- **Internationalization**: Full English/Chinese support for UI and dynamic logs.
- **Theme Support**: High-contrast Dark Mode & Clean Light Mode.

## 🛠️ Tech Stack

### Frontend
- **React** + **TypeScript**: Modern UI framework
- **Vite**: Lightning-fast build tool
- **TailwindCSS**: Utility-first styling
- **Recharts**: Data visualization

### Backend & AI Core
- **Python 3.x**: Data processing and orchestration
- **AI Providers**:
  - **Alibaba Cloud DashScope**: Qwen-Max, DeepSeek-R1
  - **Moonshot AI**: Kimi
  - **Zhipu AI**: GLM-4.6 (with Web Search)

### Data Architecture
```
┌─────────────────────────────────────────┐
│         AI Consortium Layer             │
│  Qwen + DeepSeek + Kimi + GLM           │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      Data Integration Layer             │
│  Smart Merging + Deduplication          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│   Market Insight Generation             │
│  GLM-4 Analyst (Web Search Enabled)     │
└─────────────────────────────────────────┘
```

### Deployment
- **GitHub Pages**: Static site hosting
- **GitHub Actions**: Automated daily data updates

## 🏃‍♂️ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/WUAIBING/computepulse.git
cd computepulse
```

### 2. Install Dependencies
```bash
# Frontend dependencies
npm install

# Backend dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env.local` file in the root directory or export env vars:
```bash
# Required: DashScope API Key (for Qwen + DeepSeek + Kimi via DashScope)
DASHSCOPE_API_KEY=sk-your-dashscope-key-here

# Required: Zhipu AI API Key (for GLM Analyst)
ZHIPU_API_KEY=your-zhipu-key-here
```

### 4. Run the Application

**Option A: Development Mode**
```bash
# Start frontend dev server
npm run dev

# In another terminal, fetch latest data
python scripts/fetch_prices_modular.py
```

**Option B: Production Build**
```bash
# Build frontend
npm run build

# Serve built files
npm run preview
```

Access the dashboard at `http://localhost:5173` (dev) or `http://localhost:4173` (preview)

## 📊 Data Management

### Fetch Latest Data
```bash
# Run the modular data fetcher
python scripts/fetch_prices_modular.py
```

### View Data Quality Reports
```bash
# GPU price validation report
cat public/data/validation_report_gpu.json
```

## 🔧 Configuration

### Data Source Settings
Edit `scripts/fetch_prices_modular.py` to adjust search queries or validation thresholds.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
