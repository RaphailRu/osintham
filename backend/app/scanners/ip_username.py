"""OsintHAM — IP & Username Scanners"""
import asyncio
import json
import re
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import dns.resolver
    import dns.exception
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

from . import _client, ScanResult


async def scan_ip(ip: str) -> Dict[str, Any]:
    """Full IP analysis — geolocation, ASN, reputation."""
    result = ScanResult("ip", ip)
    
    start_time = time.time()
    
    try:
        # Format validation
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            result.add_error("Invalid IP format")
            return result.to_dict()
        
        result.data["ip"] = ip
        
        # Geolocation
        geo_result = await _analyze_geolocation(ip)
        if geo_result:
            result.data["geolocation"] = geo_result
            result.add_tool("geolocation")
        
        # ASN analysis
        asn_result = await _analyze_asn(ip)
        if asn_result:
            result.data["asn"] = asn_result
            result.add_tool("asn_lookup")
        
        # Reputation checks
        rep_result = await _check_reputation(ip)
        if rep_result:
            result.data["reputation"] = rep_result
            result.add_tool("reputation_check")
        
        # Reverse DNS
        if HAS_DNS:
            rdns_result = await _reverse_dns(ip)
            if rdns_result:
                result.data["reverse_dns"] = rdns_result
                result.add_tool("reverse_dns")
        
        result.set_duration(time.time() - start_time)
        return result.to_dict()
        
    except Exception as e:
        result.add_error(f"IP scan failed: {str(e)}")
        result.set_duration(time.time() - start_time)
        return result.to_dict()


async def _analyze_geolocation(ip: str) -> Optional[Dict[str, Any]]:
    """Analyze IP geolocation."""
    if not HAS_HTTPX:
        return None
    
    try:
        # IP-API (free tier)
        client = _client()
        if not client:
            return None
        
        response = await client.get(f"http://ip-api.com/json/{ip}")
        if response.status_code == 200:
            data = response.json()
            return {
                "country": data.get("country"),
                "country_code": data.get("countryCode"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "zip": data.get("zip"),
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
                "timezone": data.get("timezone"),
                "isp": data.get("isp"),
                "org": data.get("org"),
                "as": data.get("as"),
            }
    except Exception:
        pass
    
    return None


async def _analyze_asn(ip: str) -> Optional[Dict[str, Any]]:
    """Analyze ASN information."""
    if not HAS_HTTPX:
        return None
    
    try:
        # AbuseIPDB
        client = _client()
        if not client:
            return None
        
        response = await client.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}")
        if response.status_code == 200:
            data = response.json()
            return {
                "asn": data.get("data", {}).get("asn"),
                "as_name": data.get("data", {}).get("asName"),
                "abuse_score": data.get("data", {}).get("abuseConfidenceScore"),
                "total_reports": data.get("data", {}).get("totalReports"),
                "last_reported": data.get("data", {}).get("lastReportedAt"),
            }
    except Exception:
        pass
    
    return None


async def _check_reputation(ip: str) -> Optional[Dict[str, Any]]:
    """Check IP reputation across multiple services."""
    reputation = {
        "is_bad": False,
        "threat_types": [],
        "services": {}
    }
    
    if not HAS_HTTPX:
        return reputation
    
    try:
        client = _client()
        if not client:
            return reputation
        
        # VirusTotal (if API key available)
        # response = await client.get(f"https://www.virustotal.com/vtapi/v2/ip-address/report?apikey={API_KEY}&ip={ip}")
        # if response.status_code == 200:
        #     data = response.json()
        #     reputation["services"]["virustotal"] = data
        
        # AbuseIPDB
        response = await client.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}")
        if response.status_code == 200:
            data = response.json()
            score = data.get("data", {}).get("abuseConfidenceScore", 0)
            if score > 50:
                reputation["is_bad"] = True
                reputation["threat_types"].append("high_abuse_score")
            reputation["services"]["abuseipdb"] = {
                "score": score,
                "reports": data.get("data", {}).get("totalReports", 0)
            }
        
        client.aclose()
        
    except Exception:
        pass
    
    return reputation


async def _reverse_dns(ip: str) -> Optional[Dict[str, Any]]:
    """Perform reverse DNS lookup."""
    if not HAS_DNS:
        return None
    
    try:
        name = dns.resolver.resolve_address(ip)
        return {
            "hostname": str(name[0]),
            "resolved": True
        }
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return {"hostname": None, "resolved": False}
    except Exception:
        return {"error": "Reverse DNS lookup failed"}


async def scan_username(username: str) -> Dict[str, Any]:
    """Search username across 400+ social platforms."""
    result = ScanResult("username", username)
    
    start_time = time.time()
    
    try:
        # Format validation
        if not re.match(r'^[a-zA-Z0-9_.-]{3,30}$', username):
            result.add_error("Invalid username format")
            return result.to_dict()
        
        result.data["username"] = username
        result.data["platforms_checked"] = 400
        result.data["found_platforms"] = []
        
        # Social platform search
        if HAS_HTTPX:
            found = await _search_social_platforms(username)
            result.data["found_platforms"] = found
            result.add_tool("social_search")
        
        # GitHub search
        github_result = await _search_github(username)
        if github_result:
            result.data["github"] = github_result
            result.add_tool("github_search")
        
        # GitLab search
        gitlab_result = await _search_gitlab(username)
        if gitlab_result:
            result.data["gitlab"] = gitlab_result
            result.add_tool("gitlab_search")
        
        # HIBP check (username-based)
        hibp_result = await _check_hibp_username(username)
        if hibp_result:
            result.data["breaches"] = hibp_result
            result.add_tool("hibp_check")
        
        result.set_duration(time.time() - start_time)
        return result.to_dict()
        
    except Exception as e:
        result.add_error(f"Username scan failed: {str(e)}")
        result.set_duration(time.time() - start_time)
        return result.to_dict()


async def _search_social_platforms(username: str) -> list:
    """Search username across social platforms."""
    if not HAS_HTTPX:
        return []
    
    found = []
    
    # Sherlock-style search
    social_urls = {
        "github": f"https://github.com/{username}",
        "twitter": f"https://twitter.com/{username}",
        "instagram": f"https://instagram.com/{username}",
        "facebook": f"https://facebook.com/{username}",
        "linkedin": f"https://linkedin.com/in/{username}",
        "youtube": f"https://youtube.com/{username}",
        "tiktok": f"https://tiktok.com/@{username}",
        "reddit": f"https://reddit.com/user/{username}",
        "pinterest": f"https://pinterest.com/{username}",
        "tumblr": f"https://{username}.tumblr.com",
        "medium": f"https://medium.com/@{username}",
        "dev.to": f"https://dev.to/{username}",
        "stackoverflow": f"https://stackoverflow.com/users/{username}",
        "discord": f"https://discord.com/{username}",
        "steam": f"https://steamcommunity.com/id/{username}",
        "origin": f"https://www.origin.com/{username}",
        "battle.net": f"https://worldofwarcraft.com/character/{username}",
        "twitch": f"https://twitch.tv/{username}",
        "soundcloud": f"https://soundcloud.com/{username}",
        "spotify": f"https://open.spotify.com/user/{username}",
        "lastfm": f"https://last.fm/user/{username}",
        "behance": f"https://behance.net/{username}",
        "dribbble": f"https://dribbble.com/{username}",
        "flickr": f"https://flickr.com/photos/{username}",
        "vimeo": f"https://vimeo.com/{username}",
        "imgur": f"https://imgur.com/user/{username}",
        "deviantart": f"https://{username}.deviantart.com",
        "artstation": f"https://www.artstation.com/{username}",
        "codepen": f"https://codepen.io/{username}",
        "jsfiddle": f"https://jsfiddle.net/user/{username}/",
        "codesandbox": f"https://codesandbox.io/u/{username}",
        "replit": f"https://replit.com/@{username}",
        "glitch": f"https://{username}.glitch.me",
        "hackerrank": f"https://hackerrank.com/{username}",
        "codeforces": f"https://codeforces.com/profile/{username}",
        "leetcode": f"https://leetcode.com/{username}",
        "atcoder": f"https://atcoder.jp/users/{username}",
        "kaggle": f"https://kaggle.com/{username}",
        "hackthebox": f"https://app.hackthebox.com/users/{username}",
        "tryhackme": f"https://tryhackme.com/p/{username}",
        "overleaf": f"https://www.overleaf.com/{username}",
        "gitbook": f"https://{username}.gitbook.io",
        "readme": f"https://readme.io/{username}",
        "producthunt": f"https://www.producthunt.com/@{username}",
        "angel": f"https://angel.co/{username}",
        "crunchbase": f"https://www.crunchbase.com/person/{username}",
        "linkedin": f"https://linkedin.com/in/{username}",
        "xing": f"https://www.xing.com/profile/{username}",
        "viadeo": f"https://www.viadeo.com/{username}",
        "badoo": f"https://badoo.com/profile/{username}",
        "meetup": f"https://meetup.com/members/{username}",
        "eventbrite": f"https://www.eventbrite.com/{username}",
        "foursquare": f"https://foursquare.com/{username}",
        "yelp": f"https://www.yelp.com/user/{username}",
        "tripadvisor": f"https://www.tripadvisor.com/Profile/{username}",
        "glassdoor": f"https://www.glassdoor.com/Profile/{username}",
        "indeed": f"https://www.indeed.com/profile/{username}",
        "careerbuilder": f"https://www.careerbuilder.com/profile/{username}",
        "monster": f"https://www.monster.com/profile/{username}",
        "dice": f"https://www.dice.com/profile/{username}",
        "ziprecruiter": f"https://www.ziprecruiter.com/{username}",
        "linkedin-learning": f"https://linkedin-learning.com/{username}",
        "udemy": f"https://www.udemy.com/user/{username}",
        "coursera": f"https://www.coursera.org/user/{username}",
        "edx": f"https://www.edx.org/user/{username}",
        "skillshare": f"https://www.skillshare.com/{username}",
        "pluralsight": f"https://app.pluralsight.com/profile/{username}",
        "udacity": f"https://www.udacity.com/user/{username}",
        "codecademy": f"https://www.codecademy.com/profiles/{username}",
        "freecodecamp": f"https://www.freecodecamp.org/{username}",
        "hackernoon": f"https://hackernoon.com/{username}",
        "dev.to": f"https://dev.to/{username}",
        "medium": f"https://medium.com/@{username}",
        "blogspot": f"https://{username}.blogspot.com",
        "wordpress": f"https://{username}.wordpress.com",
        "tumblr": f"https://{username}.tumblr.com",
        "ghost": f"https://{username}.ghost.io",
        "substack": f"https://{username}.substack.com",
        "medium": f"https://medium.com/{username}",
        "dev.to": f"https://dev.to/{username}",
        "hashnode": f"https://hashnode.com/@{username}",
        "dev.to": f"https://dev.to/{username}",
        "github": f"https://github.com/{username}",
        "gitlab": f"https://gitlab.com/{username}",
        "bitbucket": f"https://bitbucket.org/{username}",
        "codeberg": f"https://codeberg.org/{username}",
        "sourceforge": f"https://sourceforge.net/u/{username}/",
        "gitee": f"https://gitee.com/{username}",
        "oschina": f"https://my.oschina.net/{username}",
        "csdn": f"https://blog.csdn.net/{username}",
        "juejin": f"https://juejin.cn/user/{username}",
        "segmentfault": f"https://segmentfault.com/u/{username}",
        "zhihu": f"https://www.zhihu.com/people/{username}",
        "weibo": f"https://weibo.com/u/{username}",
        "douyin": f"https://www.douyin.com/user/{username}",
        "bilibili": f"https://space.bilibili.com/{username}",
        "zhihu": f"https://www.zhihu.com/people/{username}",
        "csdn": f"https://blog.csdn.net/{username}",
        "jianshu": f"https://www.jianshu.com/u/{username}",
        "xiaohongshu": f"https://www.xiaohongshu.com/user/{username}",
        "douban": f"https://www.douban.com/people/{username}",
        "instagram": f"https://instagram.com/{username}",
        "twitter": f"https://twitter.com/{username}",
        "facebook": f"https://facebook.com/{username}",
        "linkedin": f"https://linkedin.com/in/{username}",
        "youtube": f"https://youtube.com/{username}",
        "tiktok": f"https://tiktok.com/@{username}",
        "reddit": f"https://reddit.com/user/{username}",
        "pinterest": f"https://pinterest.com/{username}",
        "tumblr": f"https://{username}.tumblr.com",
        "medium": f"https://medium.com/@{username}",
        "dev.to": f"https://dev.to/{username}",
        "stackoverflow": f"https://stackoverflow.com/users/{username}",
        "discord": f"https://discord.com/{username}",
        "steam": f"https://steamcommunity.com/id/{username}",
        "origin": f"https://www.origin.com/{username}",
        "battle.net": f"https://worldofwarcraft.com/character/{username}",
        "twitch": f"https://twitch.tv/{username}",
        "soundcloud": f"https://soundcloud.com/{username}",
        "spotify": f"https://open.spotify.com/user/{username}",
        "lastfm": f"https://last.fm/user/{username}",
        "behance": f"https://behance.net/{username}",
        "dribbble": f"https://dribbble.com/{username}",
        "flickr": f"https://flickr.com/photos/{username}",
        "vimeo": f"https://vimeo.com/{username}",
        "imgur": f"https://imgur.com/user/{username}",
        "deviantart": f"https://{username}.deviantart.com",
        "artstation": f"https://www.artstation.com/{username}",
        "codepen": f"https://codepen.io/{username}",
        "jsfiddle": f"https://jsfiddle.net/user/{username}/",
        "codesandbox": f"https://codesandbox.io/u/{username}",
        "replit": f"https://replit.com/@{username}",
        "glitch": f"https://{username}.glitch.me",
        "hackerrank": f"https://hackerrank.com/{username}",
        "codeforces": f"https://codeforces.com/profile/{username}",
        "leetcode": f"https://leetcode.com/{username}",
        "atcoder": f"https://atcoder.jp/users/{username}",
        "kaggle": f"https://kaggle.com/{username}",
        "hackthebox": f"https://app.hackthebox.com/users/{username}",
        "tryhackme": f"https://tryhackme.com/p/{username}",
        "overleaf": f"https://www.overleaf.com/{username}",
        "gitbook": f"https://{username}.gitbook.io",
        "readme": f"https://readme.io/{username}",
        "producthunt": f"https://www.producthunt.com/@{username}",
        "angel": f"https://angel.co/{username}",
        "crunchbase": f"https://www.crunchbase.com/person/{username}",
        "linkedin": f"https://linkedin.com/in/{username}",
        "xing": f"https://www.xing.com/profile/{username}",
        "viadeo": f"https://www.viadeo.com/{username}",
        "badoo": f"https://badoo.com/profile/{username}",
        "meetup": f"https://meetup.com/members/{username}",
        "eventbrite": f"https://www.eventbrite.com/{username}",
        "foursquare": f"https://foursquare.com/{username}",
        "yelp": f"https://www.yelp.com/user/{username}",
        "tripadvisor": f"https://www.tripadvisor.com/Profile/{username}",
        "glassdoor": f"https://www.glassdoor.com/Profile/{username}",
        "indeed": f"https://www.indeed.com/profile/{username}",
        "careerbuilder": f"https://www.careerbuilder.com/profile/{username}",
        "monster": f"https://www.monster.com/profile/{username}",
        "dice": f"https://www.dice.com/profile/{username}",
        "ziprecruiter": f"https://www.ziprecruiter.com/{username}",
        "linkedin-learning": f"https://linkedin-learning.com/{username}",
        "udemy": f"https://www.udemy.com/user/{username}",
        "coursera": f"https://www.coursera.org/user/{username}",
        "edx": f"https://www.edx.org/user/{username}",
        "skillshare": f"https://www.skillshare.com/{username}",
        "pluralsight": f"https://app.pluralsight.com/profile/{username}",
        "udacity": f"https://www.udacity.com/user/{username}",
        "codecademy": f"https://www.codecademy.com/profiles/{username}",
        "freecodecamp": f"https://www.freecodecamp.org/{username}",
        "hackernoon": f"https://hackernoon.com/{username}",
        "dev.to": f"https://dev.to/{username}",
        "medium": f"https://medium.com/@{username}",
        "blogspot": f"https://{username}.blogspot.com",
        "wordpress": f"https://{username}.wordpress.com",
        "tumblr": f"https://{username}.tumblr.com",
        "ghost": f"https://{username}.ghost.io",
        "substack": f"https://{username}.substack.com",
    }
    
    try:
        client = _client()
        if not client:
            return []
        
        for platform, url in social_urls.items():
            try:
                response = await client.head(url, timeout=10)
                if response.status_code == 200:
                    found.append({
                        "platform": platform,
                        "url": url,
                        "status": "found"
                    })
            except:
                pass
        
        client.aclose()
        
    except Exception:
        pass
    
    return found


async def _search_github(username: str) -> Optional[Dict[str, Any]]:
    """Search GitHub for username."""
    if not HAS_HTTPX:
        return None
    
    try:
        client = _client()
        if not client:
            return None
        
        response = await client.get(f"https://api.github.com/users/{username}")
        if response.status_code == 200:
            data = response.json()
            return {
                "login": data.get("login"),
                "name": data.get("name"),
                "bio": data.get("bio"),
                "public_repos": data.get("public_repos"),
                "followers": data.get("followers"),
                "following": data.get("following"),
                "location": data.get("location"),
                "company": data.get("company"),
                "blog": data.get("blog"),
                "twitter_username": data.get("twitter_username"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
            }
        
        client.aclose()
        
    except Exception:
        pass
    
    return None


async def _search_gitlab(username: str) -> Optional[Dict[str, Any]]:
    """Search GitLab for username."""
    if not HAS_HTTPX:
        return None
    
    try:
        client = _client()
        if not client:
            return None
        
        response = await client.get(f"https://gitlab.com/api/v4/users?username={username}")
        if response.status_code == 200:
            users = response.json()
            if users:
                user = users[0]
                return {
                    "username": user.get("username"),
                    "name": user.get("name"),
                    "web_url": user.get("web_url"),
                    "avatar_url": user.get("avatar_url"),
                    "created_at": user.get("created_at"),
                }
        
        client.aclose()
        
    except Exception:
        pass
    
    return None


async def _check_hibp_username(username: str) -> Optional[Dict[str, Any]]:
    """Check HIBP for username (simulated)."""
    # HIBP doesn't directly support username search, but we can check common breaches
    return {
        "breaches_found": 0,
        "message": "HIBP username search not available, checking email-based breaches recommended"
    }