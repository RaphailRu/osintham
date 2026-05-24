"""OsintHAM — SpiderFoot Integration API Router
Интеграция с SpiderFoot (github.com/smicallef/spiderfoot)
233 модуля OSINT-сканирования, классифицированных по 8 категориям.
"""
import json
import os
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/spiderfoot", tags=["SpiderFoot"])

# Загружаем данные при старте
SF_DATA = {}
SF_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "spiderfoot_modules.json")

def load_spiderfoot():
    global SF_DATA
    if os.path.exists(SF_FILE):
        with open(SF_FILE, 'r', encoding='utf-8') as f:
            SF_DATA = json.load(f)
    else:
        SF_DATA = {'total': 0, 'categories': {}, 'all_modules': []}

load_spiderfoot()


@router.get("/")
async def spiderfoot_root():
    """Информация о SpiderFoot интеграции"""
    cats = SF_DATA.get('categories', {})
    return {
        "name": "SpiderFoot",
        "source": "https://github.com/smicallef/spiderfoot",
        "description": "Автоматизированный OSINT-фреймворк с 233 модулями сканирования",
        "total_modules": SF_DATA.get('total', 0),
        "total_categories": len(cats),
        "endpoints": {
            "info": "/api/spiderfoot",
            "categories": "/api/spiderfoot/categories",
            "category": "/api/spiderfoot/category/{name}",
            "modules": "/api/spiderfoot/modules",
            "search": "/api/spiderfoot/search?q={query}",
            "stats": "/api/spiderfoot/stats",
        }
    }


@router.get("/categories")
async def list_categories():
    """Список всех категорий SpiderFoot"""
    cats = SF_DATA.get('categories', {})
    result = []
    for name, mods in sorted(cats.items()):
        result.append({'name': name, 'module_count': len(mods)})
    return result


@router.get("/category/{category_name}")
async def get_category(category_name: str):
    """Получить модули по категории"""
    cats = SF_DATA.get('categories', {})
    # Поиск без учёта регистра
    for name, mods in cats.items():
        if name.lower() == category_name.lower():
            return {'name': name, 'modules': mods}
    raise HTTPException(status_code=404, detail=f"Категория '{category_name}' не найдена")


@router.get("/modules")
async def list_modules(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    category: Optional[str] = None
):
    """Список всех модулей с пагинацией"""
    all_mods = SF_DATA.get('all_modules', [])
    
    if category:
        cats = SF_DATA.get('categories', {})
        for name, mods in cats.items():
            if name.lower() == category.lower():
                all_mods = mods
                break
    
    total = len(all_mods)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'modules': all_mods[start:end]
    }


@router.get("/search")
async def search_modules(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    limit: int = Query(50, ge=1, le=200)
):
    """Поиск модулей по ключевому слову"""
    all_mods = SF_DATA.get('all_modules', [])
    query = q.lower()
    results = [m for m in all_mods if query in m.lower()][:limit]
    return {'query': q, 'total_found': len(results), 'results': results}


@router.get("/stats")
async def spiderfoot_stats():
    """Статистика SpiderFoot"""
    cats = SF_DATA.get('categories', {})
    return {
        'total_modules': SF_DATA.get('total', 0),
        'total_categories': len(cats),
        'categories': [{'name': k, 'count': len(v)} for k, v in sorted(cats.items(), key=lambda x: -x[1])]
    }
