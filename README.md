# 🏏 Cricket News Notifier

Automated cricket news aggregator that fetches news from multiple sources, analyzes sentiment, and sends daily newsletters via Email and Telegram.

## ✨ Features

- 📰 Fetches news from Twitter, Reddit, and ESPN Cricinfo
- 🔄 LLM-powered deduplication
- 🎭 Sentiment analysis (Positive/Neutral/Negative)
- 📧 Email newsletters
- 📱 Telegram bot notifications
- 💬 RAG-powered Q&A chat
- 📊 Web dashboard

## 🛠️ Tech Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Pipeline:** LangGraph, LangChain
- **AI/ML:** Groq (Llama 3.1), HuggingFace (DistilBERT)
- **Vector DB:** ChromaDB
- **Frontend:** Streamlit
- **Scheduler:** APScheduler

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/cricket-news-notifier.git
cd cricket-news-notifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
```

Required API keys:
- `GROQ_API_KEY` - Get from [Groq](https://console.groq.com)
- `REDDIT_CLIENT_ID` & `REDDIT_CLIENT_SECRET` - Get from [Reddit Apps](https://www.reddit.com/prefs/apps)
- `TWITTER_BEARER_TOKEN` - Get from [Twitter Developer](https://developer.twitter.com)
- `TELEGRAM_BOT_TOKEN` - Get from [@BotFather](https://t.me/botfather)
- `SMTP_EMAIL` & `SMTP_PASSWORD` - Gmail App Password

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Run the Application

**Terminal 1 - Backend API:**
```bash
uvicorn backend.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/app.py
```

**Terminal 3 - Scheduler (Optional):**
```bash
python scheduler/jobs.py
```

### 5. Access the App

- **Frontend:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

## 📖 Usage

### Manual Pipeline Run
```bash
python run_pipeline.py
```

### Cleanup Old Data
```bash
# Clean SQLite (newsletters older than 30 days)
python scripts/cleanup_sqlite.py --days 30

# Clean VectorDB
python scripts/cleanup_vectordb.py
```

## 🌐 Deployment (Render)

1. Push code to GitHub
2. Create new Web Service on Render
3. Set environment variables
4. Add Render Cron Job for daily pipeline at 8 AM IST

## 📁 Project Structure
```
cricket-news-notifier/
├── backend/          # FastAPI backend
├── src/
│   ├── agents/       # Data source agents
│   ├── pipeline/     # LangGraph pipeline
│   ├── tools/        # AI tools
│   ├── notifiers/    # Email & Telegram
│   └── rag/          # Vector DB & Query Engine
├── frontend/         # Streamlit app
├── scheduler/        # APScheduler
└── scripts/          # Cleanup scripts
```

## 📄 License

MIT License