"""OsintHAM — Scanners Base Module"""
import asyncio
import hashlib
import json
import re
import ssl
import time
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse, quote

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

try:
    import whois
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False


# ─── HTTP Client (shared) ───

def _client():
    """Create httpx async client with proper headers."""
    if not HAS_HTTPX:
        return None
    return httpx.AsyncClient(
        follow_redirects=True,
        timeout=15,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )


# ─── Base Scanner ───

class ScanResult:
    """Standard result format for all scanners."""
    
    def __init__(self, scan_type: str, target: str):
        self.scan_type = scan_type
        self.target = target
        self.success = True
        self.data = {}
        self.errors = []
        self.metadata = {
            "timestamp": datetime.now().isoformat(),
            "duration": None,
            "tools_used": [],
        }
    
    def add_error(self, error: str):
        self.errors.append(error)
        if self.errors:
            self.success = False
    
    def add_tool(self, tool: str):
        if tool not in self.metadata["tools_used"]:
            self.metadata["tools_used"].append(tool)
    
    def set_duration(self, duration: float):
        self.metadata["duration"] = duration
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_type": self.scan_type,
            "target": self.target,
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "metadata": self.metadata,
        }


async def _check_hibp_async(email: str) -> Dict[str, Any]:
    """Check HIBP API for email breaches."""
    if not HAS_HTTPX:
        return {"breaches": [], "error": "httpx not available"}
    
    try:
        client = _client()
        if not client:
            return {"breaches": [], "error": "httpx client failed"}
        
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        response = await client.get(url, headers={"hibp-api-key": "YOUR_API_KEY"})
        
        if response.status_code == 200:
            breaches = response.json()
            return {"breaches": breaches}
        elif response.status_code == 404:
            return {"breaches": []}
        else:
            return {"breaches": [], "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"breaches": [], "error": str(e)}
    finally:
        if client:
            await client.aclose()


# ─── Email Scanner ───

async def scan_email(email: str) -> Dict[str, Any]:
    """Full email analysis — format, MX, provider, breaches."""
    result = ScanResult("email", email)
    
    start_time = time.time()
    
    try:
        # Format validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            result.add_error("Invalid email format")
            return result.to_dict()
        
        user, domain = email.split("@", 1)
        result.data["username"] = user
        result.data["domain"] = domain
        
        # Provider detection
        disposable_domains = {
            'guerrillamail.com', 'tempmail.com', 'throwaway.email', 'mailinator.com',
            'sharklasers.com', 'grr.la', 'dispostable.com', 'yopmail.com',
            'trashmail.com', 'temp-mail.org', 'fakeinbox.com', 'mailnesia.com',
            'maildrop.cc', 'discard.email', 'tempail.com', '10minutemail.com',
        }
        free_providers = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
            'mail.com', 'yandex.ru', 'rambler.ru', 'protonmail.com', 'icloud.com',
            'zoho.com', 'gmx.com', 'fastmail.com', 'tutanota.com', 'hey.com',
            'live.com', 'msn.com', 'mail.ru', 'list.ru', 'bk.ru', 'inbox.ru',
        }
        
        result.data["is_disposable"] = domain.lower() in disposable_domains
        result.data["is_free_provider"] = domain.lower() in free_providers
        result.add_tool("provider_detection")
        
        # DNS lookups
        if HAS_DNS:
            # MX records
            try:
                mx_answers = dns.resolver.resolve(domain, 'MX')
                result.data["mx_records"] = [
                    {"exchange": str(r.exchange).rstrip('.'), "preference": r.preference}
                    for r in sorted(mx_answers, key=lambda r: r.preference)
                ]
                result.data["has_mx"] = len(result.data["mx_records"]) > 0
                result.add_tool("dns_mx")
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
                result.add_error("No MX records found")
            except Exception as e:
                result.add_error(f"MX lookup: {str(e)}")
            
            # SPF
            try:
                txt_answers = dns.resolver.resolve(domain, 'TXT')
                for r in txt_answers:
                    txt = str(r)
                    if 'v=spf1' in txt:
                        result.data["spf_record"] = txt[:500]
                        result.add_tool("dns_spf")
                        break
            except Exception:
                pass
            
            # DMARC
            try:
                dmarc_answers = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
                for r in dmarc_answers:
                    txt = str(r)
                    if 'v=DMARC1' in txt:
                        result.data["dmarc_record"] = txt[:500]
                        result.add_tool("dns_dmarc")
                        break
            except Exception:
                pass
        
        # HIBP breach check
        hibp_result = await _check_hibp_async(email)
        if "breaches" in hibp_result:
            result.data["breaches"] = hibp_result["breaches"]
            if result.data["breaches"]:
                result.add_tool("hibp_check")
        
        # Social media check (email-based)
        social_results = await _check_email_social(email, user)
        if social_results:
            result.data["social_accounts"] = social_results
            result.add_tool("social_search")
        
        result.set_duration(time.time() - start_time)
        return result.to_dict()
        
    except Exception as e:
        result.add_error(f"Email scan failed: {str(e)}")
        result.set_duration(time.time() - start_time)
        return result.to_dict()


async def _check_email_social(email: str, username: str) -> list:
    """Check social media for email-based username."""
    social_results = []
    social_platforms = {
        "gmail.com": ["Google", "Gmail"],
        "yahoo.com": ["Yahoo"],
        "hotmail.com": ["Microsoft", "Outlook", "Hotmail"],
        "vk.com": ["VK"],
        "mail.ru": ["Mail.ru"],
    }
    
    if email in social_platforms:
        social_results.append({
            "platform": social_platforms[email][0],
            "username": username,
            "found": True,
            "note": f"Likely account on {social_platforms[email][1]}"
        })
    
    return social_results