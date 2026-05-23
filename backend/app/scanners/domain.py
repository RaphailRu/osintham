"""OsintHAM — Domain Scanners"""
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

try:
    import whois
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False

from . import _client, ScanResult


async def scan_domain(domain: str) -> Dict[str, Any]:
    """Full domain analysis — DNS, WHOIS, SSL, subdomains."""
    result = ScanResult("domain", domain)
    
    start_time = time.time()
    
    try:
        # Format validation
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
            result.add_error("Invalid domain format")
            return result.to_dict()
        
        # Basic info
        result.data["domain"] = domain
        result.data["is_ip"] = False
        
        # DNS analysis
        if HAS_DNS:
            dns_results = await _analyze_dns(domain)
            result.data.update(dns_results)
            result.add_tool("dns_analysis")
        
        # WHOIS lookup
        if HAS_WHOIS:
            whois_result = await _analyze_whois(domain)
            if whois_result:
                result.data["whois"] = whois_result
                result.add_tool("whois_lookup")
        
        # SSL certificate
        ssl_result = await _analyze_ssl(domain)
        if ssl_result:
            result.data["ssl"] = ssl_result
            result.add_tool("ssl_analysis")
        
        # Web technologies
        tech_result = await _analyze_web_tech(domain)
        if tech_result:
            result.data["technologies"] = tech_result
            result.add_tool("web_detection")
        
        # Subdomain enumeration
        subdomains_result = await _enumerate_subdomains(domain)
        if subdomains_result:
            result.data["subdomains"] = subdomains_result
            result.add_tool("subdomain_enum")
        
        result.set_duration(time.time() - start_time)
        return result.to_dict()
        
    except Exception as e:
        result.add_error(f"Domain scan failed: {str(e)}")
        result.set_duration(time.time() - start_time)
        return result.to_dict()


async def _analyze_dns(domain: str) -> Dict[str, Any]:
    """Analyze DNS records."""
    dns_info = {
        "a_records": [],
        "aaaa_records": [],
        "mx_records": [],
        "txt_records": [],
        "ns_records": [],
        "soa": None,
        "has_dns": False,
    }
    
    try:
        # A records
        try:
            a_answers = dns.resolver.resolve(domain, 'A')
            dns_info["a_records"] = [str(r) for r in a_answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except Exception as e:
            dns_info["errors"] = dns_info.get("errors", []) + [f"A record: {str(e)}"]
        
        # AAAA records
        try:
            aaaa_answers = dns.resolver.resolve(domain, 'AAAA')
            dns_info["aaaa_records"] = [str(r) for r in aaaa_answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except Exception as e:
            dns_info["errors"] = dns_info.get("errors", []) + [f"AAAA record: {str(e)}"]
        
        # MX records
        try:
            mx_answers = dns.resolver.resolve(domain, 'MX')
            dns_info["mx_records"] = [
                {"exchange": str(r.exchange).rstrip('.'), "preference": r.preference}
                for r in sorted(mx_answers, key=lambda r: r.preference)
            ]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except Exception as e:
            dns_info["errors"] = dns_info.get("errors", []) + [f"MX record: {str(e)}"]
        
        # TXT records
        try:
            txt_answers = dns.resolver.resolve(domain, 'TXT')
            dns_info["txt_records"] = [str(r) for r in txt_answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except Exception as e:
            dns_info["errors"] = dns_info.get("errors", []) + [f"TXT record: {str(e)}"]
        
        # NS records
        try:
            ns_answers = dns.resolver.resolve(domain, 'NS')
            dns_info["ns_records"] = [str(r) for r in ns_answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except Exception as e:
            dns_info["errors"] = dns_info.get("errors", []) + [f"NS record: {str(e)}"]
        
        # SOA record
        try:
            soa_answers = dns.resolver.resolve(domain, 'SOA')
            soa = soa_answers[0]
            dns_info["soa"] = {
                "mname": str(soa.mname),
                "rname": str(soa.rname),
                "serial": soa.serial,
                "refresh": soa.refresh,
                "retry": soa.retry,
                "expire": soa.expire,
                "minimum": soa.minimum,
            }
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except Exception as e:
            dns_info["errors"] = dns_info.get("errors", []) + [f"SOA record: {str(e)}"]
        
        dns_info["has_dns"] = any([
            dns_info["a_records"],
            dns_info["aaaa_records"],
            dns_info["mx_records"],
            dns_info["txt_records"],
            dns_info["ns_records"],
            dns_info["soa"]
        ])
        
    except Exception as e:
        dns_info["errors"] = dns_info.get("errors", []) + [f"DNS analysis: {str(e)}"]
    
    return dns_info


async def _analyze_whois(domain: str) -> Optional[Dict[str, Any]]:
    """Analyze WHOIS information."""
    try:
        w = whois.whois(domain)
        return {
            "registrar": w.registrar,
            "creation_date": str(w.creation_date) if w.creation_date else None,
            "expiration_date": str(w.expiration_date) if w.expiration_date else None,
            "name_servers": w.name_servers if w.name_servers else [],
            "status": w.status if w.status else [],
            "emails": w.emails if w.emails else [],
            "updated_date": str(w.updated_date) if w.updated_date else None,
        }
    except Exception as e:
        return {"error": str(e)}


async def _analyze_ssl(domain: str) -> Optional[Dict[str, Any]]:
    """Analyze SSL certificate."""
    try:
        context = ssl.create_default_context()
        with context.connect_to_host(domain, timeout=10):
            cert = context.getpeercert()
            return {
                "issuer": cert.get("issuer", []),
                "subject": cert.get("subject", []),
                "version": cert.get("version", None),
                "not_before": cert.get("notBefore", None),
                "not_after": cert.get("notAfter", None),
                "serial_number": cert.get("serialNumber", None),
                "dns_names": cert.get("DNS", []),
            }
    except Exception:
        return None


async def _analyze_web_tech(domain: str) -> Optional[Dict[str, Any]]:
    """Analyze web technologies."""
    if not HAS_HTTPX:
        return None
    
    try:
        client = _client()
        if not client:
            return None
        
        # Check common tech stack
        headers = await client.head(f"https://{domain}", follow_redirects=False)
        technologies = []
        
        # Server headers
        server = headers.headers.get("server", "").lower()
        if "nginx" in server:
            technologies.append("Nginx")
        if "apache" in server:
            technologies.append("Apache")
        if "cloudflare" in server:
            technologies.append("Cloudflare")
        
        # Common headers
        if "x-powered-by" in headers.headers:
            tech = headers.headers["x-powered-by"].lower()
            if "php" in tech:
                technologies.append("PHP")
            if "express" in tech:
                technologies.append("Express.js")
        
        # Check for frameworks
        response = await client.get(f"https://{domain}", timeout=10)
        content = response.text.lower()
        
        if "wp-content" in content or "wp-includes" in content:
            technologies.append("WordPress")
        if "django" in content or "csrfmiddlewaretoken" in content:
            technologies.append("Django")
        if "react" in content or "react-dom" in content:
            technologies.append("React")
        if "vue" in content:
            technologies.append("Vue.js")
        
        client.aclose()
        
        if technologies:
            return {"technologies": technologies, "server": server}
        return None
        
    except Exception:
        return None


async def _enumerate_subdomains(domain: str) -> Optional[Dict[str, Any]]:
    """Enumerate common subdomains."""
    common_subdomains = [
        "www", "mail", "ftp", "api", "blog", "shop", "store", "dev", "staging",
        "test", "admin", "dashboard", "panel", "app", "web", "docs", "support",
        "help", "cdn", "cache", "static", "images", "assets", "media", "files",
        "upload", "download", "search", "login", "register", "user", "profile",
        "settings", "config", "api", "v1", "v2", "v3", "mobile", "m", "wap"
    ]
    
    found_subdomains = []
    
    if not HAS_DNS:
        return None
    
    try:
        for sub in common_subdomains:
            subdomain = f"{sub}.{domain}"
            try:
                dns.resolver.resolve(subdomain, 'A')
                found_subdomains.append(subdomain)
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                pass
    except Exception:
        pass
    
    if found_subdomains:
        return {"subdomains": found_subdomains, "count": len(found_subdomains)}
    return None