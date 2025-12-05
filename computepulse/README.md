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

### 🤖 Triple-AI Intelligence System
- **DeepSeek-v3.2**: Reasoning mode for deep analysis and high-quality data (41 GPU + 25 Token records)
- **Qwen-Max**: Fast web search with stable reliability (12 GPU + 4 Token records)
- **Doubao-Pro**: Data validation and auto-fix with web search capabilities

### 📊 Data Quality Assurance
- **4-Layer Validation**: Type checking → Range validation → Deduplication → AI deep validation
- **Auto-Fix System**: Doubao automatically detects and fixes data anomalies
  - 🔴 High severity: Auto-remove invalid records
  - 🟡 Medium severity: Flag for manual review
  - 🟢 Low severity: Keep with notes
- **Smart Merging**: Priority-based data integration (DeepSeek > Qwen > Doubao > Existing)

### 🌐 Comprehensive Coverage
- **114 Total Records**: 77 GPU prices + 37 Token prices
- **Global Providers**: AWS, Azure, Google Cloud, Lambda Labs, RunPod, CoreWeave, Vast.ai
- **Chinese Providers**: Aliyun, Tencent Cloud, Baidu, Volcengine, Huawei Cloud
- **Real-Time Updates**: Automated daily updates via GitHub Actions (3-minute fetch time)

### 📈 Advanced Features
- **Historical Tracking**: 90-day price history with trend analysis
- **Energy Impact**: Visualizes AI compute's environmental footprint
- **Validation Reports**: Detailed data quality reports with anomaly detection
- **Multi-language Support**: English and Chinese UI

## 🛠️ Tech Stack

### Frontend
- **React** + **TypeScript**: Modern UI framework
- **Vite**: Lightning-fast build tool
- **TailwindCSS**: Utility-first styling
- **Recharts**: Data visualization

### Backend & AI
- **Python 3.x**: Data processing and orchestration
- **DeepSeek-v3.2-exp**: Reasoning mode via Alibaba Cloud DashScope
- **Qwen-Max**: Web search via DashScope
- **Doubao-Pro**: Validation & auto-fix via Volcengine ARK

### Data Architecture
```
┌─────────────────────────────────────────┐
│         Data Collection Layer           │
│  Qwen + DeepSeek + Doubao (optional)    │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      Data Integration Layer             │
│  Smart Merging + Deduplication          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│   Data Validation & Auto-Fix Layer      │
│  Doubao AI Auditor + Fixer              │
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
Create a `.env.local` file in the root directory:
```bash
# Required: DashScope API Key (for Qwen + DeepSeek)
DASHSCOPE_API_KEY=sk-your-dashscope-key-here

# Optional: Volcengine API Key (for Doubao validation)
VOLC_API_KEY=your-volcengine-key-here
```

**Get API Keys:**
- DashScope (Qwen + DeepSeek): https://dashscope.console.aliyun.com/
- Volcengine (Doubao): https://console.volcengine.com/ark

### 4. Run the Application

**Option A: Development Mode**
```bash
# Start frontend dev server
npm run dev

# In another terminal, fetch latest data
python scripts/fetch_prices_optimized.py --once
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
# Single fetch (recommended for testing)
python scripts/fetch_prices_optimized.py --once

# Continuous mode (runs daily at midnight)
python scripts/fetch_prices_optimized.py
```

### Test Individual Components
```bash
# Test DeepSeek integration
python scripts/test_deepseek.py

# Test Doubao validation
python scripts/test_doubao_validator.py

# Test auto-fix functionality
python scripts/test_auto_fix.py

# Diagnose Doubao API issues
python scripts/diagnose_doubao.py
```

### View Data Quality Reports
```bash
# GPU price validation report
cat public/data/validation_report_gpu.json

# Token price validation report
cat public/data/validation_report_token.json
```

## 🔧 Configuration

### Data Source Settings
Edit `scripts/fetch_prices_optimized.py`:

```python
# Enable/disable Doubao for data collection (default: False, too slow)
ENABLE_DOUBAO = False

# Data validation thresholds
GPU_PRICE_MIN = 0.1      # Minimum GPU price (USD/hour)
GPU_PRICE_MAX = 50.0     # Maximum GPU price (USD/hour)
TOKEN_PRICE_MIN = 0.001  # Minimum token price (USD/1M tokens)
TOKEN_PRICE_MAX = 100.0  # Maximum token price (USD/1M tokens)
```

### Auto-Fix Strategy
Edit `scripts/data_validator.py` to customize fix behavior:

```python
# High severity: remove invalid records
# Medium severity: flag for manual review
# Low severity: keep with notes
```

## 📚 Documentation

Detailed documentation available in the repository:

- **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)**: Complete system overview
- **[DATA_INTEGRATION_AND_VALIDATION.md](DATA_INTEGRATION_AND_VALIDATION.md)**: Data architecture details
- **[DOUBAO_AUTO_FIX.md](DOUBAO_AUTO_FIX.md)**: Auto-fix mechanism guide
- **[DEEPSEEK_INTEGRATION_SUCCESS.md](DEEPSEEK_INTEGRATION_SUCCESS.md)**: DeepSeek integration report
- **[TEST_REPORT.md](TEST_REPORT.md)**: Testing and validation results

## 🎯 System Performance

| Metric | Value |
|--------|-------|
| Total Data Records | 114 (77 GPU + 37 Token) |
| Data Fetch Time | ~3 minutes |
| Data Quality | Good (AI-validated) |
| Update Frequency | Daily (automated) |
| Auto-Fix Success Rate | 60% |
| Data Sources | 3 AI models |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### API Connection Issues
```bash
# Diagnose Doubao API configuration
python scripts/diagnose_doubao.py

# Check if API keys are loaded
python -c "import os; print('DashScope:', bool(os.getenv('DASHSCOPE_API_KEY'))); print('Volcengine:', bool(os.getenv('VOLC_API_KEY')))"
```

### Data Quality Issues
```bash
# Clean invalid data
python scripts/clean_data.py

# Re-run validation
python scripts/test_doubao_validator.py
```

### Build Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

## 📊 Data Coverage

### GPU Models
- **NVIDIA**: H100, H200, A100, L40S, Blackwell GB200
- **Chinese AI Chips**: Huawei Ascend 910B, Cambricon MLU370, Hygon DCU

### LLM Models
- **International**: GPT-4o, GPT-4o-mini, o1, Claude 3.5 Sonnet, Gemini 2.0, Llama 3
- **Chinese**: Qwen, Ernie, GLM-4, Kimi, Doubao, MiniMax, DeepSeek

### Cloud Providers
- **International**: AWS, Azure, Google Cloud, Lambda Labs, RunPod, CoreWeave, Vast.ai
- **Chinese**: Aliyun, Tencent Cloud, Baidu AI Cloud, Volcengine, Huawei Cloud

## 🌟 Acknowledgments

- **Alibaba Cloud DashScope**: For Qwen and DeepSeek API access
- **ByteDance Volcengine**: For Doubao API and ARK platform
- **Open Source Community**: For the amazing tools and libraries

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

**Built with ❤️ by SilentCopilot**


