# Project Folder Structure 📂

**Generated:** 2026-02-04

This document shows the top-level and key subfolders/files for the project.

---

```
cricket-news-notifier/
├── init_db.py
├── README.md
├── requirements_basic.txt
├── requirements.txt
├── run_pipeline.py
├── telegram_bot.py
├── test_duckduckgo.py
├── backend/
│   ├── __init__.py
│   ├── auth.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── routers/
│       ├── __init__.py
│       ├── chat.py
│       ├── newsletters.py
│       ├── pipeline.py
│       └── subscribers.py
├── data/
│   └── vectordb/
│       ├── chroma.sqlite3
│       └── d4d0a94e-55ad-4755-9367-9503a8724511/
├── frontend/
│   ├── app.py
│   └── pages/
│       ├── admin.py
│       ├── archive.py
│       ├── chat.py
│       ├── home.py
│       └── subscribe.py
├── scheduler/
│   ├── __init__.py
│   └── jobs.py
├── scripts/
│   ├── cleanup_sqlite.py
│   └── cleanup_vectordb.py
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── reddit_agent.py
│   │   ├── rss_agent.py
│   │   └── twitter_agent.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── notifiers/
│   │   ├── __init__.py
│   │   ├── email_agent.py
│   │   └── telegram_agent.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── graph.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── query_engine.py
│   │   └── vectordb.py
│   └── tools/
│       ├── __init__.py
│       ├── sentiment/
│       │   └── sentiment_agent.py
│       ├── summarizer/
│       │   └── summarizer_agent.py
│       └── websearch/
│           └── duckduckgo_agent.py
└── templates/
    └── email_template.html
```

---

Highlights:

- **Backend API**: `backend/` (routers in `backend/routers/`) ✅
- **Agents & Tools**: `src/agents/`, `src/tools/`, `src/notifiers/` 🔧
- **Data store**: `data/vectordb/` where vector DB files live 💾

> Tip: Use `tree` (Windows) or `ls -R` to regenerate a more detailed view when files change.
