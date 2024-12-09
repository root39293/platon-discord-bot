# Platon Discord Bot

<div align="center">
  <img src="./assets/platon.jpg" alt="Platon Bot" width="400"/>
  
  [![version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/root39293/platon-discord-bot)
</div>

## Introduction
Python based Discord server management and information provider assistant

## Features
- 일일 초기화되는 개인 할일 관리 시스템
- 진행도 추적 주간퀘스트 체크리스트
- 실시간 암호화폐 가격 알림 및 모니터링
- 주요 미디어의 실시간 뉴스 수집
- Google Gemini 기반 명언 생성

## Upcoming Features
- [ ] 일일 할일 초기화 버그 수정
  - [ ] 자정 시점 초기화 오류
  - [ ] 할일 목록 중복 생성 문제
- [ ] 주간 할일 초기화 버그 수정
  - [ ] 주간 리셋 시점 오류
  - [ ] 체크리스트 상태 초기화 문제

## Installation
1. Environment Setup
~~~
BOT_TOKEN=discord_bot_token
GEMINI_API_KEY=google_gemini_api_key
~~~

2. Launch
~~~
docker-compose up -d
~~~

## Commands
- `/할일`: 할일 목록 관리
- `/주간퀘`: 주간퀘스트 체크리스트
- `/코인시세`: 코인 시세 조회
- `/인기코인`: 거래량 기준 TOP 5 코인
- `/뉴스조회`: 실시간 뉴스 확인
- `/명언조회`: AI 명언 생성

## Tech Stack
- discord.py
- Google Gemini AI
- Docker
- GitHub Actions

## Contributing
1. Development Setup
~~~
# virtual environment setup
python -m .venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# configure environment variables
cp .env.example .env
# modify .env file
~~~

2. Run
~~~
python bot.py
~~~


## License
This project is licensed under the MIT License - see the LICENSE file for details.
