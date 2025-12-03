# 🌍 ComputePulse | Global AI Compute & Energy Index

**Real-time tracker for the pulse of the global AI industry.**

ComputePulse is a dashboard that monitors the vital signs of the AI world:
- **GCCI (Global Compute Cost Index)**: Real-time tracking of GPU rental prices (H100, A100, Ascend 910B, etc.) across global providers.
- **Token Price Index**: Live monitoring of LLM API costs (GPT-4, Claude, Qwen, Doubao, etc.).
- **GAGL (Global AI Grid Load)**: Estimating the real-time energy consumption of the world's AI data centers.

## 🚀 Features

- **Dual-Model Intelligence**: Powered by **Qwen-Max** and **Doubao-Pro** working in tandem to cross-verify data from the open web.
- **Real-Time Updates**: Data is automatically fetched and updated daily via GitHub Actions.
- **Global Coverage**: Tracks both international (AWS, Google, OpenAI) and Chinese (Aliyun, Volcengine, Huawei) providers.
- **Energy Impact**: Visualizes the environmental footprint of AI compute in TWh and nuclear reactor equivalents.

## 🛠️ Tech Stack

- **Frontend**: React, Vite, TailwindCSS, Recharts
- **Backend**: Python (Data Fetching & Processing)
- **AI Agents**: 
  - **Qwen-Max** (Alibaba Cloud) - Web Search & Reasoning
  - **Doubao-Pro** (ByteDance Volcengine) - Web Search & Reasoning
- **Deployment**: GitHub Pages (Automated via GitHub Actions)

## 🏃‍♂️ Run Locally

1. **Clone the repo**
   ```bash
   git clone https://github.com/WUAIBING/computepulse.git
   cd computepulse
   ```

2. **Install Dependencies**
   ```bash
   # Frontend
   npm install
   
   # Backend
   pip install requests dashscope
   ```

3. **Set API Keys**
   Create a `.env.local` file:
   ```
   DASHSCOPE_API_KEY=your_qwen_key
   VOLC_API_KEY=your_doubao_key
   ```

4. **Run**
   ```bash
   # Start data fetcher & web server
   python scripts/server.py
   ```
   Access at `http://localhost:3001`

## 📄 License

MIT
