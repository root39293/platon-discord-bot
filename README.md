<h1 align="center">Platon Discord Bot</h1>
<div align="center">
  <img src="./assets/platon.jpg" alt="Platon Bot" width="400"/>
  
  [![version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/root39293/platon-discord-bot)
</div>

<h2 align="left">Introduction</h2>
Python based Discord server management and information provider assistant

<h2 align="left">Features</h2>

- Daily resetting personal task management system
- Progress tracking weekly quest checklist
- Real-time cryptocurrency price alerts and monitoring
- Real-time news collection from major media
- Google Gemini based quote generation

<h2 align="left">Installation</h2>

1. Environment Setup
```
BOT_TOKEN=discord_bot_token
GEMINI_API_KEY=google_gemini_api_key
```
2. Launch
```
docker-compose up -d
```

<h2 align="left">Commands</h2>

- `/할일`: Manage task list
- `/주간퀘`: Weekly quest checklist
- `/코인시세`: Check cryptocurrency prices
- `/인기코인`: View TOP 5 coins by trading volume
- `/뉴스조회`: Check real-time news
- `/명언조회`: Generate AI quotes

<h2 align="left">Tech Stack</h2>

- discord.py
- Google Gemini AI
- Docker
- GitHub Actions

<h2 align="left">Contributing</h2>

1. Development Setup
```
# virtual environment setup
python -m .venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
# install dependencies
pip install -r requirements.txt
# configure environment variables
cp .env.example .env
# modify .env file
```
2. Run
```
python bot.py
```

<h2 align="left">License</h2>

This project is licensed under the MIT License - see the LICENSE file for details.
