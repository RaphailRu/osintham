"""OsintHAM — OSINT Framework API Router
Интеграция с OSINT-Framework (github.com/lockfale/OSINT-Framework)
Предоставляет доступ к базе из 1417+ OSINT-инструментов, организованных по 33 категориям.
"""
import json
import os
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/framework", tags=["OSINT Framework"])

# Загружаем данные при старте
FRAMEWORK_DATA = {}
FRAMEWORK_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "osint_framework.json")

def load_framework():
    global FRAMEWORK_DATA
    if os.path.exists(FRAMEWORK_FILE):
        with open(FRAMEWORK_FILE, 'r', encoding='utf-8') as f:
            FRAMEWORK_DATA = json.load(f)
    else:
        FRAMEWORK_DATA = {'categories': {}, 'all_nodes': []}

load_framework()


@router.get("/")
async def framework_root():
    """Информация об OSINT Framework"""
    categories = FRAMEWORK_DATA.get('categories', {})
    nodes = FRAMEWORK_DATA.get('all_nodes', [])
    tools_with_url = sum(1 for n in nodes if n.get('url'))
    return {
        "name": "OSINT Framework",
        "source": "https://github.com/lockfale/OSINT-Framework",
        "total_nodes": len(nodes),
        "total_tools": tools_with_url,
        "total_categories": len(categories),
        "endpoints": {
            "categories": "/api/framework/categories",
            "category": "/api/framework/category/{name}",
            "search": "/api/framework/search?q={query}",
            "tools": "/api/framework/tools",
            "stats": "/api/framework/stats",
        }
    }


@router.get("/categories")
async def list_categories():
    """Список всех категорий OSINT Framework"""
    categories = FRAMEWORK_DATA.get('categories', {})
    result = []
    for name, items in sorted(categories.items()):
        with_url = sum(1 for i in items if i.get('url'))
        result.append({
            'name': name,
            'total_items': len(items),
            'tools_with_url': with_url,
        })
    return result


@router.get("/category/{category_name}")
async def get_category(category_name: str):
    """Получить инструменты по категории"""
    categories = FRAMEWORK_DATA.get('categories', {})
    # Поиск без учёта регистра
    for name, items in categories.items():
        if name.lower() == category_name.lower():
            return {
                'name': name,
                'items': items
            }
    raise HTTPException(status_code=404, detail=f"Категория '{category_name}' не найдена")


@router.get("/search")
async def search_tools(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    type: Optional[str] = Query(None, description="Фильтр по типу (url, folder)"),
    limit: int = Query(50, ge=1, le=200)
):
    """Поиск инструментов по ключевому слову"""
    nodes = FRAMEWORK_DATA.get('all_nodes', [])
    query = q.lower()
    results = []
    
    for node in nodes:
        if type and node.get('type') != type:
            continue
        name = node.get('name', '').lower()
        desc = node.get('description', '').lower()
        url = node.get('url', '').lower()
        
        if query in name or query in desc or query in url:
            results.append(node)
            if len(results) >= limit:
                break
    
    return {
        'query': q,
        'total_found': len(results),
        'results': results
    }


@router.get("/tools")
async def list_tools(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    type: Optional[str] = None,
    has_url: Optional[bool] = None
):
    """Список всех инструментов с пагинацией"""
    nodes = FRAMEWORK_DATA.get('all_nodes', [])
    
    if type:
        nodes = [n for n in nodes if n.get('type') == type]
    if has_url is not None:
        nodes = [n for n in nodes if (bool(n.get('url')) == has_url)]
    
    total = len(nodes)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'tools': nodes[start:end]
    }


@router.get("/stats")
async def framework_stats():
    """Статистика OSINT Framework"""
    nodes = FRAMEWORK_DATA.get('all_nodes', [])
    categories = FRAMEWORK_DATA.get('categories', {})
    
    # Статистика по типам
    types = {}
    for n in nodes:
        t = n.get('type') or 'unknown'
        types[t] = types.get(t, 0) + 1
    
    # Статистика по статусу
    statuses = {}
    for n in nodes:
        s = n.get('status') or 'unknown'
        statuses[s] = statuses.get(s, 0) + 1
    
    # Статистика по ценообразованию
    pricing = {}
    for n in nodes:
        p = n.get('pricing') or 'unknown'
        pricing[p] = pricing.get(p, 0) + 1
    
    return {
        'total_nodes': len(nodes),
        'total_categories': len(categories),
        'tools_with_url': sum(1 for n in nodes if n.get('url')),
        'by_type': types,
        'by_status': statuses,
        'by_pricing': pricing,
        'top_categories': sorted(
            [{'name': k, 'count': len(v)} for k, v in categories.items()],
            key=lambda x: -x['count']
        )[:10]
    }
