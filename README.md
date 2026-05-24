# 🕷️ OsintHAM — OSINT Investigation Constructor

[![GitHub](https://img.shields.io/badge/GitHub-RaphailRu%2Fosintham-blue)](https://github.com/RaphailRu/osintham)
[![Live Demo](https://img.shields.io/badge/Live-Demo-green)](https://raphailru.github.io/osintham/)
[![Version](https://img.shields.io/badge/version-0.5.1-orange)](https://github.com/RaphailRu/osintham/releases)

## 📋 Описание

**OsintHAM** — это конструктор OSINT-расследований с веб-интерфейсом. Инструмент для построения графов взаимосвязей, сбора информации из источников и генерации отчётов.

### Возможности

- 🕸️ **Интерактивный граф** — Cytoscape.js с перетаскиванием, зумом, стилизацией узлов
- 🔗 **Связи между узлами** — типы отношений, уровень доверия, направление
- 🔍 **OSINT Scanner** — 25+ интеграций (Sherlock, Maigret, Holehe, Shodan, Censys, HIBP...)
- 💻 **Веб-терминал** — 20+ команд (whois, dns, ssl, ghdb, scan...)
- 📋 **Отчёты** — экспорт в JSON, HTML, Markdown
- 🔔 **Уведомления** — toast-уведомления с автоудалением
- 🌙 **Тёмная тема** — полный dark mode
- 💾 **LocalStorage** — данные сохраняются между сессиями

### Типы узлов

| Тип | Иконка | Цвет |
|-----|--------|------|
| Person | 👤 | Фиолетовый |
| Email | 📧 | Красный |
| Phone | 📱 | Оранжевый |
| Social Account | 🌐 | Зелёный |
| Organization | 🏢 | Голубой |
| Domain | 🔗 | Жёлтый |
| IP Address | 📍 | Розовый |
| Event | 📅 | Индиго |
| Document | 📄 | Серый |

## 🚀 Быстрый старт

### GitHub Pages (Demo)

Откройте [raphailru.github.io/osintham](https://raphailru.github.io/osintham/) — работает без сервера, данные в LocalStorage.

### Docker

```bash
git clone https://github.com/RaphailRu/osintham.git
cd osintham
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev      # разработка
npm run build    # сборка
npm run preview  # просмотр сборки
```

## 📡 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/health` | Проверка работоспособности |
| GET | `/api` | Список всех endpoints |
| GET | `/api/investigations` | Список расследований |
| POST | `/api/investigations` | Создать расследование |
| GET | `/api/investigations/{id}` | Получить расследование |
| PUT | `/api/investigations/{id}` | Обновить расследование |
| DELETE | `/api/investigations/{id}` | Удалить расследование |
| POST | `/api/investigations/{id}/nodes` | Добавить узел |
| PUT | `/api/nodes/{id}` | Обновить узел |
| DELETE | `/api/nodes/{id}` | Удалить узел |
| POST | `/api/investigations/{id}/edges` | Добавить связь |
| PUT | `/api/edges/{id}` | Обновить связь |
| DELETE | `/api/edges/{id}` | Удалить связь |
| GET | `/api/investigations/{id}/graph` | Полный граф |
| GET | `/api/investigations/{id}/report` | Генерация отчёта |
| GET | `/api/templates` | Шаблоны анкет |
| POST | `/api/osint/scan` | Полное сканирование |
| GET | `/api/osint/email/{email}` | Анализ email |
| GET | `/api/osint/phone/{phone}` | Анализ телефона |
| GET | `/api/osint/domain/{domain}` | Анализ домена |
| GET | `/api/osint/ip/{ip}` | Анализ IP |
| GET | `/api/osint/username/{username}` | Поиск по нику |

## 🏗️ Архитектура

```
osintham/
├── index.html              # React SPA entry
├── assets/
│   ├── index-*.js          # React bundle (837KB)
│   └── index-*.css         # Tailwind CSS (25KB)
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI entry point
│   │   ├── database.py     # SQLAlchemy models + SQLite
│   │   ├── graph_engine.py # NetworkX analysis
│   │   ├── schemas.py      # Pydantic models
│   │   ├── api/            # 7 роутеров (CRUD + OSINT)
│   │   ├── scanners/       # Модульные сканеры
│   │   └── agents/         # AI-агенты анализа
│   ├── tests/              # Pytest тесты
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Router + layout
│   │   ├── Sidebar.jsx     # Навигация
│   │   ├── store.js        # Zustand state
│   │   ├── api.js          # Axios client
│   │   ├── components/     # 10 компонентов
│   │   └── pages/          # 4 страницы
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

## 🛠️ Технологии

### Backend
- **Python 3.11** + **FastAPI** — REST API
- **SQLAlchemy 2.0** + **SQLite** — хранилище
- **NetworkX** — анализ графов
- **Pydantic 2** — валидация данных
- **HTTPX** — асинхронные HTTP-запросы

### Frontend
- **React 18** + **Vite 5** — SPA
- **Tailwind CSS 3** — стилизация
- **Cytoscape.js** — визуализация графов
- **Zustand** — управление состоянием
- **Axios** — HTTP-клиент
- **Lucide React** — иконки

### OSINT Интеграции (25+)
- **Username Search:** Sherlock, Maigret, Snoop, Holehe
- **Email/Breaches:** HIBP, LeakCheck, BreachHound
- **DNS/Network:** DNSDumpster, Shodan, Censys
- **Web:** Wayback Machine, GHDB
- **Frameworks:** SpiderFoot, Recon-ng, theHarvester
- **Regional:** VK, OK, TeleSINT
- **Face:** PimEyes

## 🔒 Безопасность Этика

- Данные хранятся локально (LocalStorage / SQLite)
- Нет автоматического сканирования — исследователь контролирует ввод
- Уровни доверия (1-5) для каждой информации
- Журнал действий отслеживает все изменения
- Экспорт с защитой по паролю

## 📜 Лицензия

MIT License — свободное использование и модификация.

## 🔗 Ссылки

- **GitHub:** [github.com/RaphailRu/osintham](https://github.com/RaphailRu/osintham)
- **Live Demo:** [raphailru.github.io/osintham](https://raphailru.github.io/osintham/)
- **API Docs:** `http://localhost:8000/docs` (при запуске backend)
