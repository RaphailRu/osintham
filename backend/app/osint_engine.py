"""OsintHAM — OSINT Engine
Core module for automated data collection and enrichment.
Each scanner returns structured data that can be added to the graph.
"""
import re
import hashlib
import json
import asyncio
import socket
import ssl
import dns.resolver
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import whois
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False


# ── Utility Functions ──

def validate_email(email: str) -> dict:
    """Validate email format and extract components."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(pattern, email))
    result = {
        "email": email,
        "is_valid_format": is_valid,
        "checks": {},
    }
    if is_valid:
        user, domain = email.split('@', 1)
        result["username"] = user
        result["domain"] = domain
        result["is_disposable"] = _check_disposable_email(domain)
        result["is_free_provider"] = domain.lower() in FREE_EMAIL_PROVIDERS
        # MX record check
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            result["mx_records"] = [str(r.exchange).rstrip('.') for r in mx_records]
            result["has_mx"] = len(result["mx_records"]) > 0
        except Exception:
            result["mx_records"] = []
            result["has_mx"] = False
    return result


def validate_phone(phone: str) -> dict:
    """Validate and analyze phone number."""
    cleaned = re.sub(r'[^\d+]', '', phone)
    result = {
        "original": phone,
        "cleaned": cleaned,
        "is_valid": False,
        "country": None,
        "carrier": None,
        "type": None,
    }
    # Basic validation
    digits = re.sub(r'\D', '', phone)
    if len(digits) >= 7 and len(digits) <= 15:
        result["is_valid"] = True
    # Country detection by prefix
    country_prefixes = {
        '1': 'US/Canada', '7': 'Russia/Kazakhstan', '33': 'France',
        '44': 'UK', '49': 'Germany', '39': 'Italy', '34': 'Spain',
        '86': 'China', '81': 'Japan', '82': 'South Korea', '91': 'India',
        '55': 'Brazil', '52': 'Mexico', '61': 'Australia', '31': 'Netherlands',
        '48': 'Poland', '380': 'Ukraine', '375': 'Belarus', '371': 'Latvia',
        '372': 'Estonia', '370': 'Lithuania', '358': 'Finland', '46': 'Sweden',
        '47': 'Norway', '45': 'Denmark', '41': 'Switzerland', '43': 'Austria',
    }
    for prefix, country in sorted(country_prefixes.items(), key=lambda x: -len(x[0])):
        if cleaned.startswith(prefix) or cleaned.startswith('+' + prefix):
            result["country"] = country
            break
    return result


def analyze_domain(domain: str) -> dict:
    """Analyze domain — WHOIS, DNS, SSL."""
    result = {
        "domain": domain,
        "whois": None,
        "dns": {},
        "ssl": None,
        "subdomains": [],
        "technologies": [],
    }
    # DNS records
    for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            result["dns"][record_type] = [str(r) for r in answers]
        except Exception:
            pass
    # WHOIS
    if HAS_WHOIS:
        try:
            w = whois.whois(domain)
            result["whois"] = {
                "registrar": str(w.registrar) if w.registrar else None,
                "creation_date": str(w.creation_date) if w.creation_date else None,
                "expiration_date": str(w.expiration_date) if w.expiration_date else None,
                "name_servers": [str(ns) for ns in w.name_servers] if w.name_servers else [],
                "status": str(w.status) if w.status else None,
                "org": str(w.org) if w.org else None,
                "country": str(w.country) if w.country else None,
            }
        except Exception as e:
            result["whois"] = {"error": str(e)}
    # SSL certificate
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
            result["ssl"] = {
                "subject": dict(x[0] for x in cert.get('subject', [])),
                "issuer": dict(x[0] for x in cert.get('issuer', [])),
                "not_before": cert.get('notBefore'),
                "not_after": cert.get('notAfter'),
                "serial_number": cert.get('serialNumber'),
                "version": cert.get('version'),
            }
    except Exception as e:
        result["ssl"] = {"error": str(e)}
    # Common subdomains enumeration
    common_subs = ['www', 'mail', 'ftp', 'admin', 'api', 'blog', 'shop',
                   'dev', 'staging', 'test', 'portal', 'vpn', 'cdn',
                   'ns1', 'ns2', 'mx', 'smtp', 'pop', 'imap', 'webmail',
                   'docs', 'support', 'status', 'git', 'gitlab', 'jenkins']
    for sub in common_subs:
        try:
            full = f"{sub}.{domain}"
            dns.resolver.resolve(full, 'A')
            result["subdomains"].append(full)
        except Exception:
            pass
    return result


def analyze_ip(ip: str) -> dict:
    """Analyze IP address — geolocation, ASN, reverse DNS."""
    result = {
        "ip": ip,
        "is_valid": False,
        "version": None,
        "reverse_dns": None,
        "geolocation": None,
        "blacklists": [],
    }
    # Validate IP
    try:
        import ipaddress
        addr = ipaddress.ip_address(ip)
        result["is_valid"] = True
        result["version"] = f"IPv{addr.version}"
        result["is_private"] = addr.is_private
        result["is_loopback"] = addr.is_loopback
    except ValueError:
        return result
    # Reverse DNS
    try:
        result["reverse_dns"] = socket.gethostbyaddr(ip)[0]
    except Exception:
        pass
    # Geolocation via free API
    if HAS_HTTPX:
        try:
            resp = httpx.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,zip,lat,lon,isp,org,as,asname,reverse,query", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    result["geolocation"] = {
                        "country": data.get('country'),
                        "region": data.get('regionName'),
                        "city": data.get('city'),
                        "zip": data.get('zip'),
                        "lat": data.get('lat'),
                        "lon": data.get('lon'),
                        "isp": data.get('isp'),
                        "org": data.get('org'),
                        "asn": data.get('as'),
                        "asn_name": data.get('asname'),
                    }
        except Exception:
            pass
    return result


def search_username(username: str) -> dict:
    """Search for username across platforms (Sherlock-style)."""
    platforms = {
        'GitHub': f'https://github.com/{username}',
        'Twitter': f'https://twitter.com/{username}',
        'Instagram': f'https://instagram.com/{username}',
        'Reddit': f'https://reddit.com/user/{username}',
        'YouTube': f'https://youtube.com/@{username}',
        'TikTok': f'https://tiktok.com/@{username}',
        'Pinterest': f'https://pinterest.com/{username}',
        'Spotify': f'https://open.spotify.com/user/{username}',
        'Steam': f'https://steamcommunity.com/id/{username}',
        'Telegram': f'https://t.me/{username}',
        'VK': f'https://vk.com/{username}',
        'LinkedIn': f'https://linkedin.com/in/{username}',
        'Medium': f'https://medium.com/@{username}',
        'DeviantArt': f'https://deviantart.com/{username}',
        'Flickr': f'https://flickr.com/people/{username}',
        'SoundCloud': f'https://soundcloud.com/{username}',
        'HackerNews': f'https://news.ycombinator.com/user?id={username}',
        'Keybase': f'https://keybase.io/{username}',
        'GitLab': f'https://gitlab.com/{username}',
        'Bitbucket': f'https://bitbucket.org/{username}',
        'Patreon': f'https://patreon.com/{username}',
        'Etsy': f'https://etsy.com/people/{username}',
        'Tumblr': f'https://{username}.tumblr.com',
        'Dribbble': f'https://dribbble.com/{username}',
        'Behance': f'https://behance.net/{username}',
        'Goodreads': f'https://goodreads.com/{username}',
        'Last.fm': f'https://last.fm/user/{username}',
        'Vimeo': f'https://vimeo.com/{username}',
        'Fandom': f'https://fandom.com/u/{username}',
        'Wikipedia': f'https://wikipedia.org/wiki/User:{username}',
    }

    result = {
        "username": username,
        "platforms_checked": len(platforms),
        "found": [],
        "not_found": [],
        "errors": [],
    }

    if HAS_HTTPX:
        client = httpx.Client(follow_redirects=True, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        for platform, url in platforms.items():
            try:
                resp = client.get(url)
                # Heuristic: if status is 200 and no "not found" indicators
                is_found = resp.status_code == 200
                not_found_indicators = [
                    'page not found', '404', 'not found', 'doesn\'t exist',
                    'no such user', 'could not be found', 'unavailable',
                ]
                content_lower = resp.text.lower()
                if any(ind in content_lower for ind in not_found_indicators):
                    is_found = False
                # Some platforms return 404 properly
                if resp.status_code == 404:
                    is_found = False

                if is_found:
                    result["found"].append({
                        "platform": platform,
                        "url": url,
                        "status_code": resp.status_code,
                    })
                else:
                    result["not_found"].append(platform)
            except httpx.TimeoutException:
                result["errors"].append(f"{platform}: timeout")
            except Exception as e:
                result["errors"].append(f"{platform}: {str(e)[:50]}")
        client.close()
    else:
        # Without httpx, just return URLs for manual checking
        for platform, url in platforms.items():
            result["found"].append({
                "platform": platform,
                "url": url,
                "status_code": "manual_check",
                "note": "Install httpx for automatic checking"
            })

    return result


def analyze_url(url: str) -> dict:
    """Analyze URL — extract technologies, headers, security."""
    result = {
        "url": url,
        "parsed": {},
        "headers": {},
        "technologies": [],
        "security": {},
        "status_code": None,
    }
    # Parse URL
    parsed = urlparse(url if '://' in url else f'https://{url}')
    result["parsed"] = {
        "scheme": parsed.scheme or 'https',
        "domain": parsed.hostname,
        "path": parsed.path,
        "query": parsed.query,
        "fragment": parsed.fragment,
    }
    if HAS_HTTPX:
        try:
            client = httpx.Client(follow_redirects=True, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            resp = client.get(url)
            result["status_code"] = resp.status_code
            result["final_url"] = str(resp.url)
            result["headers"] = dict(resp.headers)
            # Technology detection
            headers = resp.headers
            body = resp.text.lower()
            tech = []
            # Server
            if 'server' in headers:
                tech.append(f"Server: {headers['server']}")
            # Frameworks
            if 'x-powered-by' in headers:
                tech.append(f"Powered by: {headers['x-powered-by']}")
                if 'django' in body or 'csrfmiddlewaretoken' in body:
                    tech.append('Django')
                if 'wp-content' in body or 'wp-includes' in body:
                    tech.append('WordPress')
                if 'react' in body or 'reactroot' in body or '__next' in body:
                    tech.append('React')
                if 'vue' in body or 'vuejs' in body:
                    tech.append('Vue.js')
                if 'angular' in body or 'ng-version' in body:
                    tech.append('Angular')
                if 'jquery' in body:
                    tech.append('jQuery')
                if 'bootstrap' in body:
                    tech.append('Bootstrap')
                if 'laravel' in body or 'laravel_session' in headers.get('set-cookie', ''):
                    tech.append('Laravel')
                if 'express' in headers.get('x-powered-by', '').lower():
                    tech.append('Express.js')
                if 'cloudflare' in headers.get('server', '').lower() or 'cf-ray' in headers:
                    tech.append('Cloudflare')
                if 'nginx' in headers.get('server', '').lower():
                    tech.append('Nginx')
                if 'apache' in headers.get('server', '').lower():
                    tech.append('Apache')
            result["technologies"] = tech
            # Security headers check
            sec_headers = {
                'Strict-Transport-Security': 'HSTS',
                'Content-Security-Policy': 'CSP',
                'X-Frame-Options': 'Clickjacking Protection',
                'X-Content-Type-Options': 'MIME Sniffing Protection',
                'X-XSS-Protection': 'XSS Filter',
                'Referrer-Policy': 'Referrer Policy',
                'Permissions-Policy': 'Permissions Policy',
            }
            for header, name in sec_headers.items():
                if header.lower() in {k.lower() for k in headers}:
                    result["security"][name] = "✅ Present"
                else:
                    result["security"][name] = "❌ Missing"
            client.close()
        except Exception as e:
            result["error"] = str(e)
    return result


def generate_hashes(text: str) -> dict:
    """Generate multiple hashes for a string."""
    encoded = text.encode('utf-8')
    return {
        "text": text,
        "md5": hashlib.md5(encoded).hexdigest(),
        "sha1": hashlib.sha1(encoded).hexdigest(),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "sha512": hashlib.sha512(encoded).hexdigest(),
    }


def check_breaches(email: str) -> dict:
    """Check if email appears in known data breaches (via HIBP API)."""
    result = {"email": email, "breaches": [], "checked": False}
    if not HAS_HTTPX:
        return result
    try:
        # Have I Been Pwned API v3 (requires API key for full access)
        # Using the free tier with rate limiting
        headers = {
            'User-Agent': 'OsintHAM-OSINT-Tool',
            'hibp-api-key': '',  # Add your HIBP API key here
        }
        resp = httpx.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers=headers, timeout=15
        )
        if resp.status_code == 200:
            breaches = resp.json()
            result["breaches"] = [
                {"name": b.get("Name"), "domain": b.get("Domain"),
                 "date": b.get("BreachDate"), "description": b.get("Description", "")[:200]}
                for b in breaches
            ]
            result["checked"] = True
            result["total_breaches"] = len(breaches)
        elif resp.status_code == 404:
            result["checked"] = True
            result["total_breaches"] = 0
        elif resp.status_code == 429:
            result["error"] = "Rate limited. Try again later."
        else:
            result["error"] = f"API returned status {resp.status_code}"
    except Exception as e:
        result["error"] = str(e)
    return result


# ── Master Scanner ──

async def scan_target(target: str, target_type: str = "auto") -> dict:
    """Auto-detect target type and run all relevant scanners."""
    result = {
        "target": target,
        "target_type": target_type,
        "scanned_at": datetime.utcnow().isoformat(),
        "results": {},
        "suggested_nodes": [],
        "suggested_edges": [],
    }

    # Auto-detect type
    if target_type == "auto":
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', target):
            target_type = "email"
        elif re.match(r'^\d{7,15}$', re.sub(r'[^\d]', '', target)):
            target_type = "phone"
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
            target_type = "ip"
        elif re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$', target):
            target_type = "domain"
        else:
            target_type = "username"

    result["detected_type"] = target_type

    # Run appropriate scanners
    if target_type == "email":
        result["results"]["email_analysis"] = validate_email(target)
        result["results"]["breaches"] = check_breaches(target)
        # Also scan the domain
        domain = target.split('@')[1]
        result["results"]["domain_analysis"] = analyze_domain(domain)
        # Suggest nodes
        result["suggested_nodes"].append({
            "type": "email", "label": target,
            "trust_level": 5, "source": "User input",
            "data": result["results"]["email_analysis"]
        })
        result["suggested_nodes"].append({
            "type": "domain", "label": domain,
            "trust_level": 3, "source": "Extracted from email",
            "data": {"whois": result["results"]["domain_analysis"].get("whois")}
        })
        result["suggested_edges"].append({
            "from": "email_node", "to": "domain_node", "label": "uses domain"
        })

    elif target_type == "domain":
        result["results"]["domain_analysis"] = analyze_domain(target)
        # Extract IPs from DNS
        dns_a = result["results"]["domain_analysis"].get("dns", {}).get("A", [])
        for ip in dns_a:
            result["results"][f"ip_{ip}"] = analyze_ip(ip)
        # Suggest nodes
        result["suggested_nodes"].append({
            "type": "domain", "label": target,
            "trust_level": 4, "source": "OSINT scan",
            "data": result["results"]["domain_analysis"]
        })
        for ip in dns_a:
            result["suggested_nodes"].append({
                "type": "ip", "label": ip,
                "trust_level": 3, "source": f"DNS A record for {target}",
                "data": result["results"].get(f"ip_{ip}", {})
            })
            result["suggested_edges"].append({
                "from": "domain_node", "to": f"ip_{ip}_node", "label": "resolves to"
            })

    elif target_type == "ip":
        result["results"]["ip_analysis"] = analyze_ip(target)
        result["suggested_nodes"].append({
            "type": "ip", "label": target,
            "trust_level": 4, "source": "OSINT scan",
            "data": result["results"]["ip_analysis"]
        })

    elif target_type == "phone":
        result["results"]["phone_analysis"] = validate_phone(target)
        result["suggested_nodes"].append({
            "type": "phone", "label": target,
            "trust_level": 4, "source": "OSINT scan",
            "data": result["results"]["phone_analysis"]
        })

    elif target_type == "username":
        result["results"]["username_search"] = search_username(target)
        result["suggested_nodes"].append({
            "type": "person", "label": target,
            "trust_level": 2, "source": "Username search",
            "data": {"platforms_found": len(result["results"]["username_search"].get("found", []))}
        })
        for found in result["results"]["username_search"].get("found", []):
            result["suggested_nodes"].append({
                "type": "social_account",
                "label": f"{found['platform']}: {target}",
                "trust_level": 3, "source": f"Found on {found['platform']}",
                "data": {"platform": found["platform"], "url": found["url"]}
            })
            result["suggested_edges"].append({
                "from": "person_node", "to": f"social_{found['platform']}_node",
                "label": "has account on"
            })

    return result


# ── Constants ──

FREE_EMAIL_PROVIDERS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
    'mail.com', 'yandex.ru', 'rambler.ru', 'protonmail.com', 'icloud.com',
    'zoho.com', 'gmx.com', 'fastmail.com', 'tutanota.com', 'hey.com',
    'live.com', 'msn.com', 'comcast.net', 'verizon.net', 'att.net',
}

DISPOSABLE_EMAIL_PROVIDERS = {
    'guerrillamail.com', 'tempmail.com', 'throwaway.email', 'mailinator.com',
    'sharklasers.com', 'guerrillamailblock.com', 'grr.la', 'dispostable.com',
    'yopmail.com', 'trashmail.com', 'temp-mail.org', 'fakeinbox.com',
    'mailnesia.com', 'maildrop.cc', 'discard.email', 'tempail.com',
}


def _check_disposable_email(domain: str) -> bool:
    """Check if email domain is a disposable email provider."""
    return domain.lower() in DISPOSABLE_EMAIL_PROVIDERS
