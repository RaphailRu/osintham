# OsintHAM — Дорожная карта и план оптимизации

## 📊 Текущее состояние проекта

### Статистика
- **46 файлов**, 344 KB
- **16 Python** файлов (backend)
- **12 JSX** компонентов (frontend)
- **~40+ API endpoints**
- **25+ OSINT-интеграций**

### Архитектура
```
osintham/
├── index.html (43 KB) ← GitHub Pages demo (standalone)
├── backend/
│   ├── app/
│   │   ├── main.py ← FastAPI entry
│   │   ├── database.py ← SQLAlchemy models
│   │   ├── graph_engine.py ← NetworkX analysis
│   │   ├── schemas.py ← Pydantic models
│   │   ├── osint_engine.py (65 KB) ← Built-in OSINT scanners
│   │   ├── osint_integrations.py (72 KB) ← External tool wrappers
│   │   ├── osint_registry.py (18 KB) ← Tools catalog
│   │   └── api/ ← 7 routers (CRUD + OSINT)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx ← Router
│   │   ├── store.js ← Zustand state
│   │   ├── api.js ← Axios client
│   │   ├── components/ ← 6 UI components
│   │   └── pages/ ← 4 pages
│   └── package.json
└── docker-compose.yml
```

---

## 🔍 Найденные проблемы

### Критические
1. **TerminalPage.jsx** — нет OSINT-команд (только базовые: help, status, nodes, edges)
2. **Investigation.jsx** — OsintScanner импортирован, но не используется в UI (нет вкладки/кнопки)
3. **osint_engine.py + osint_integrations.py** — дублирование функций (validate_email, check_hibp и др.)

### Средние
4. **index.html** — 43 KB, содержит ВСЁ (graph, terminal, OSINT commands) — нужно разделить
5. **osint_engine.py** — 65 KB, много stubs (pass, return {}, [Simulated])
6. **osint_integrations.py** — 72 KB, много fallback-заглушек
7. **Нет тестов** — ни одного test_*.py или __tests__/
8. **Нет конфигурации** — нет .env.example, config.yaml, docker-compose не настроен для production
9. **Нет CI/CD** — нет .github/workflows/
10. **Нет документации API** — нет docs/ с описанием endpoints

### Низкие
11. **Dockerfile** — базовый, без multi-stage build
12. **nginx.conf** — минимальный, без gzip, cache, security headers
13. **Нет обработки ошибок** — нет error boundaries в React
14. **Нет линтеров** — нет .eslintrc, pyproject.toml с настройками
15. **Нет лицензии в файлах** — нет header comments

---

## 🗺️ Дорожная карта (Roadmap)

### Фаза 1: Стабилизация (1-2 недели)
**Цель:** Исправить критические проблемы, привести код в порядок

| # | Задача | Приоритет | Время |
|---|--------|-----------|-------|
| 1.1 | Разделить osint_engine.py на модули | 🔴 High | 2ч |
| 1.2 | Добавить OSINT-команды в TerminalPage.jsx | 🔴 High | 3ч |
| 1.3 | Добавить вкладку OSINT в Investigation.jsx | 🔴 High | 2ч |
| 1.4 | Убрать дублирование функций | 🔴 High | 2ч |
| 1.5 | Добавить error handling (React error boundaries) | 🟡 Medium | 2ч |
| 1.6 | Добавить loading states для OSINT-сканера | 🟡 Medium | 1ч |
| 1.7 | Исправить NodeEditor.jsx (несбалансированные скобки) | 🟡 Medium | 0.5ч |
| 1.8 | Добавить .env.example | 🟡 Medium | 0.5ч |

### Фаза 2: Ядро OSINT (2-3 недели)
**Цель:** Реализовать реальную работу OSINT-инструментов

| # | Задача | Приоритет | Время |
|---|--------|-----------|-------|
| 2.1 | Реализовать validate_email (MX check, SMTP verify) | 🔴 High | 3ч |
| 2.2 | Реализовать analyze_domain (DNS, WHOIS, SSL) | 🔴 High | 4ч |
| 2.3 | Реализовать analyze_ip (geolocation, ASN) | 🔴 High | 3ч |
| 2.4 | Реализовать username search (30+ platforms) | 🔴 High | 4ч |
| 2.5 | Реализовать URL analyzer (tech detection) | 🟡 Medium | 3ч |
| 2.6 | Реализовать phone validator | 🟡 Medium | 2ч |
| 2.7 | Добавить HIBP API integration | 🟡 Medium | 2ч |
| 2.8 | Добавить Shodan API integration | 🟡 Medium | 2ч |
| 2.9 | Добавить Wayback Machine integration | 🟢 Low | 2ч |
| 2.10 | Добавить GHDB query generator | 🟢 Low | 1ч |

### Фаза 3: Интеграция внешних инструментов (2-3 недели)
**Цель:** Подключить CLI-инструменты (Sherlock, Maigret, etc.)

| # | Задача | Приоритет | Время |
|---|--------|-----------|-------|
| 3.1 | Sherlock integration (subprocess) | 🔴 High | 3ч |
| 3.2 | Maigret integration (subprocess) | 🔴 High | 3ч |
| 3.3 | Holehe integration | 🟡 Medium | 2ч |
| 3.4 | theHarvester integration | 🟡 Medium | 2ч |
| 3.5 | Snoop integration (RU platforms) | 🟡 Medium | 2ч |
| 3.6 | Recon-ng integration | 🟢 Low | 3ч |
| 3.7 | SpiderFoot integration | 🟢 Low | 3ч |
| 3.8 | ExifTool integration | 🟢 Low | 2ч |

### Фаза 4: UI/UX (1-2 недели)
**Цель:** Улучшить интерфейс, добавить визуализации

| # | Задача | Приоритет | Время |
|---|--------|-----------|-------|
| 4.1 | Добавить вкладку "OSINT Scanner" в Investigation | 🔴 High | 3ч |
| 4.2 | Добавить вкладку "Tools Catalog" | 🟡 Medium | 2ч |
| 4.3 | Добавить вкладку "Scan History" | 🟡 Medium | 2ч |
| 4.4 | Улучшить визуализацию результатов OSINT | 🟡 Medium | 3ч |
| 4.5 | Добавить экспорт в PDF | 🟢 Low | 3ч |
| 4.6 | Добавить тёмную/светлую тему | 🟢 Low | 2ч |
| 4.7 | Добавить поиск по графу | 🟢 Low | 2ч |

### Фаза 5: Тестирование и качество (1 неделя)
**Цель:** Покрыть код тестами, настроить CI/CD

| # | Задача | Приоритет | Время |
|---|--------|-----------|-------|
| 5.1 | Написать unit-тесты для API | 🔴 High | 4ч |
| 5.2 | Написать unit-тесты для OSINT engine | 🔴 High | 4ч |
| 5.3 | Написать integration-тесты | 🟡 Medium | 3ч |
| 5.4 | Написать frontend-тесты (Jest) | 🟡 Medium | 3ч |
| 5.5 | Настроить GitHub Actions (CI/CD) | 🟡 Medium | 2ч |
| 5.6 | Добавить ESLint + Prettier | 🟢 Low | 1ч |
| 5.7 | Добавить mypy для Python | 🟢 Low | 1ч |

### Фаза 6: Деплой и документация (1 неделя)
**Цель:** Подготовить к production

| # | Задача | Приоритет | Время |
|---|--------|-----------|-------|
| 6.1 | Оптимизировать Dockerfile (multi-stage) | 🟡 Medium | 2ч |
| 6.2 | Настроить nginx (gzip, cache, security) | 🟡 Medium | 2ч |
| 6.3 | Написать API документацию | 🔴 High | 3ч |
| 6.4 | Написать руководство пользователя | 🟡 Medium | 2ч |
| 6.5 | Написать руководство по установке | 🟡 Medium | 1ч |
| 6.6 | Подготовить Docker Compose для production | 🟡 Medium | 2ч |

---

## 📋 Оптимизированный план реализации

### Неделя 1: Стабилизация
```
День 1: Разделить osint_engine.py на модули
        - osint_engine.py → scanners/email.py, scanners/domain.py, scanners/ip.py, etc.
        - Убрать дублирование
        - Исправить NodeEditor.jsx

День 2: Добавить OSINT-команды в TerminalPage.jsx
        - 25+ OSINT команд
        - Интеграция с store.js

День 3: Добавить вкладку OSINT в Investigation.jsx
        - OsintScanner компонент
        - Результаты сканирования
        - Кнопка "Add to Graph"

День 4: Error handling + Loading states
        - React error boundaries
        - Loading spinners
        - Toast notifications

День 5: Конфигурация + .env
        - .env.example
        - config.py
        - docker-compose.prod.yml
```

### Неделя 2: Ядро OSINT
```
День 1-2: Email + Domain scanners (реальная реализация)
День 3-4: IP + Username scanners
День 5: URL analyzer + Phone validator
```

### Неделя 3: Внешние инструменты
```
День 1-2: Sherlock + Maigret
День 3: Holehe + theHarvester
День 4: Snoop + RU platforms
День 5: Recon-ng + SpiderFoot
```

### Неделя 4: UI/UX
```
День 1-2: OSINT Scanner tab + Tools Catalog
День 3-4: Визуализация результатов
День 5: PDF export + темы
```

### Неделя 5: Тестирование
```
День 1-2: Backend tests
День 3-4: Frontend tests
День 5: CI/CD + линтеры
```

### Неделя 6: Деплой
```
День 1-2: Docker + nginx optimization
День 3-4: Документация
День 5: Production deployment
```

---

## 🎯 Ключевые метрики успеха

| Метрика | Текущее | Цель (6 недель) |
|---------|---------|-----------------|
| OSINT tools working | 5 (stubs) | 20+ (real) |
| API endpoints | 40+ | 50+ |
| Test coverage | 0% | 70%+ |
| Page load time | ~2s | <500ms |
| Docker image size | ~500MB | <200MB |
| Documentation | Basic README | Full docs |

---

## 💡 Рекомендации

### Архитектура
1. **Разделить монолитные файлы** — osint_engine.py (65KB) и osint_integrations.py (72KB) нужно разбить на модули
2. **Единый интерфейс сканера** — все OSINT-сканеры должны возвращать единый формат `ScanResult`
3. **Кэширование** — добавить Redis/Memory cache для результатов сканирования
4. **Очереди задач** — для долгих сканирований использовать Celery/RQ

### Безопасность
1. **Rate limiting** — ограничить количество запросов к API
2. **API keys** — вынести все ключи в env, не хранить в коде
3. **CORS** — настроить для production
4. **Input validation** — валидировать все входные данные

### Производительность
1. **Lazy loading** — загружать компоненты по требованию
2. **Pagination** — добавить пагинацию для списков
3. **Debounce** — для поиска и сканирования
4. **Compression** — gzip для API responses
