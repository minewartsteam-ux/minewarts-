from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.cache import cache
from . import services

# آدرس سرور ماینکرفت
SERVER_IP = "sv6.tgmc.ir"
SERVER_PORT = 31001
CACHE_TIMEOUT = 15  # ثانیه

@require_GET
def server_status_json(request):
    """
    دریافت وضعیت سرور به صورت JSON برای AJAX
    """
    cache_key = f'server_status_{SERVER_IP}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse(cached_data)
    
    # دریافت داده از سرور
    raw_data = services.get_minecraft_server_status(SERVER_IP, SERVER_PORT)
    
    if raw_data.get("error"):
        response_data = {
            "status": "OFF",
            "online_players": 0,
            "max_players": 0,
            "latency": 0,
            "occupancy_percent": 0,
            "status_class": "offline",
            "error": raw_data["error"],
            "server_ip": SERVER_IP
        }
    else:
        online = raw_data.get("online_players", 0)
        max_players = raw_data.get("max_players", 1)
        occupancy = int((online / max_players) * 100) if max_players > 0 else 0
        
        response_data = {
            "status": "ON",
            "online_players": online,
            "max_players": max_players,
            "latency": raw_data.get("latency", 0),
            "occupancy_percent": occupancy,
            "status_class": "online",
            "error": None,
            "server_ip": SERVER_IP
        }
    
    # ذخیره در کش
    cache.set(cache_key, response_data, CACHE_TIMEOUT)
    
    return JsonResponse(response_data)

@require_GET
def online_players_json(request):
    """
    دریافت فقط تعداد پلیرهای آنلاین به صورت JSON
    """
    cache_key = f'server_status_{SERVER_IP}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse({
            "online": cached_data.get("online_players", 0),
            "max": cached_data.get("max_players", 0),
            "percent": cached_data.get("occupancy_percent", 0),
            "status": cached_data.get("status", "OFF")
        })
    
    # دریافت داده جدید
    raw_data = services.get_minecraft_server_status(SERVER_IP, SERVER_PORT)
    
    if raw_data.get("error"):
        return JsonResponse({
            "online": 0,
            "max": 0,
            "percent": 0,
            "status": "OFF",
            "error": raw_data.get("error")
        })
    
    online = raw_data.get("online_players", 0)
    max_players = raw_data.get("max_players", 1)
    occupancy = int((online / max_players) * 100) if max_players > 0 else 0
    
    return JsonResponse({
        "online": online,
        "max": max_players,
        "percent": occupancy,
        "status": "ON"
    })

def server_status(request):
    """
    نمایش صفحه وضعیت سرور
    """
    return render(request, "server/server_status.html")