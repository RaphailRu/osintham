"""OsintHAM — Advanced OSINT Integrations
Integrates external OSINT tools: Sherlock, Maigret, Holehe, theHarvester,
SpiderFoot, Shodan, Censys, HIBP, DNSDumpster, Wayback Machine, IntelX, etc.
Each integration provides a unified async interface returning graph-ready data.
"""
import asyncio
import json
import re
import hashlib
import socket
import ssl
import subprocess
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, quote

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

try:
    import whois
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False


# ═══════════════════════════════════════════════════════════════
# 1. SHERLOCK — Username search across 400+ platforms
#    github.com/sherlock-project/sherlock
# ═══════════════════════════════════════════════════════════════

async def run_sherlock(username: str, timeout: int = 120) -> dict:
    """Run Sherlock to find username across platforms."""
    result = {
        "tool": "Sherlock",
        "username": username,
        "found": [],
        "not_found": [],
        "errors": [],
        "raw_output": "",
    }
    # Check if sherlock is installed
    sherlock_path = _find_tool("sherlock")
    if not sherlock_path:
        # Fallback: use our built-in platform checker
        result["note"] = "Sherlock not installed. Using built-in checker."
        return await _builtin_username_search(username)

    try:
        cmd = [sherlock_path, username, "--timeout", "10", "--print-found", "--json"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")
        result["raw_output"] = output

        # Parse JSON output if available
        try:
            for line in output.strip().split("\n"):
                line = line.strip()
                if line.startswith("{"):
                    data = json.loads(line)
                    if data.get("found"):
                        result["found"].append(data)
                    else:
                        result["not_found"].append(data)
        except json.JSONDecodeError:
            # Parse text output
            for line in output.split("\n"):
                if "[+]" in line or "Found" in line:
                    result["found"].append({"raw": line.strip()})
                elif "[-]" in line or "Not Found" in line:
                    result["not_found"].append({"raw": line.strip()})

    except asyncio.TimeoutError:
        result["errors"].append("Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 2. MAIGRET — Advanced username search (700+ sites)
#    github.com/soxoj/maigret
# ═══════════════════════════════════════════════════════════════

async def run_maigret(username: str, timeout: int = 180) -> dict:
    """Run Maigret for deep username search."""
    result = {
        "tool": "Maigret",
        "username": username,
        "found": [],
        "tags": [],
        "errors": [],
    }
    maigret_path = _find_tool("maigret")
    if not maigret_path:
        result["note"] = "Maigret not installed. Using built-in checker."
        return await _builtin_username_search(username)

    try:
        cmd = [maigret_path, username, "--timeout", "10", "--no-progress-bar",
               "--json", "--folderprefix", "/tmp/maigret_"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")

        # Maigret outputs JSON per site
        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                site = data.get("site_name", data.get("url", "unknown"))
                if data.get("status") == "found" or data.get("exists"):
                    entry = {
                        "site": site,
                        "url": data.get("url", ""),
                        "status": "found",
                    }
                    if data.get("tags"):
                        entry["tags"] = data["tags"]
                        result["tags"].extend(data["tags"])
                    result["found"].append(entry)
            except json.JSONDecodeError:
                pass

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 3. HOLEHE — Email to accounts checker
#    github.com/megadose/holehe
# ═══════════════════════════════════════════════════════════════

async def run_holehe(email: str, timeout: int = 120) -> dict:
    """Run Holehe to find accounts linked to email."""
    result = {
        "tool": "Holehe",
        "email": email,
        "accounts": [],
        "errors": [],
    }
    holehe_path = _find_tool("holehe")
    if not holehe_path:
        result["note"] = "Holehe not installed. Using built-in email checker."
        return await _builtin_email_breach_check(email)

    try:
        cmd = [holehe_path, email, "--no-clear"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")

        for line in output.split("\n"):
            line = line.strip()
            if "[+]" in line:
                service = line.replace("[+]", "").strip()
                if service:
                    result["accounts"].append({
                        "service": service,
                        "email": email,
                        "exists": True,
                    })

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 4. THEHARVESTER — Domain reconnaissance
#    github.com/laramies/theHarvester
# ═══════════════════════════════════════════════════════════════

async def run_theharvester(domain: str, timeout: int = 120) -> dict:
    """Run theHarvester for domain reconnaissance."""
    result = {
        "tool": "theHarvester",
        "domain": domain,
        "emails": [],
        "hosts": [],
        "ips": [],
        "urls": [],
        "asns": [],
        "errors": [],
    }
    harvester_path = _find_tool("theHarvester")
    if not harvester_path:
        harvester_path = _find_tool("theharvester")

    if not harvester_path:
        result["note"] = "theHarvester not installed. Using built-in DNS scanner."
        return await _builtin_domain_scan(domain)

    try:
        cmd = [harvester_path, "-d", domain, "-b", "all", "-f", "/tmp/harvester_"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")

        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("[") or line.startswith("[").startswith("*"):
                continue
            # Parse emails
            if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', line):
                result["emails"].append(line)
            # Parse IPs
            elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', line):
                result["ips"].append(line)
            # Parse hosts/URLs
            elif "." in line and not line.startswith(" "):
                if line.startswith("http"):
                    result["urls"].append(line)
                else:
                    result["hosts"].append(line)

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 5. HAVE I BEEN PWNED — Data breach checker
#    haveibeenpwned.com
# ═══════════════════════════════════════════════════════════════

async def check_hibp(email: str, api_key: str = "") -> dict:
    """Check email against Have I Been Pwned database."""
    result = {
        "tool": "Have I Been Pwned",
        "email": email,
        "breaches": [],
        "pastes": [],
        "checked": False,
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    headers = {
        "User-Agent": "OsintHAM-OSINT-Tool",
        "hibp-api-key": api_key or os.getenv("HIBP_API_KEY", ""),
    }

    try:
        # Check breaches
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            resp = await client.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote(email)}",
                params={"truncateResponse": "false"},
            )
            if resp.status_code == 200:
                breaches = resp.json()
                result["breaches"] = [
                    {
                        "name": b.get("Name"),
                        "title": b.get("Title"),
                        "domain": b.get("Domain"),
                        "date": b.get("BreachDate"),
                        "added_date": b.get("AddedDate"),
                        "pwn_count": b.get("PwnCount"),
                        "data_classes": b.get("DataClasses", []),
                        "description": b.get("Description", "")[:300],
                        "is_verified": b.get("IsVerified", False),
                        "is_sensitive": b.get("IsSensitive", False),
                    }
                    for b in breaches
                ]
                result["checked"] = True
                result["total_breaches"] = len(breaches)
            elif resp.status_code == 404:
                result["checked"] = True
                result["total_breaches"] = 0
            elif resp.status_code == 429:
                result["error"] = "Rate limited. Try again in 30s."
            else:
                result["error"] = f"HTTP {resp.status_code}"

            # Check pastes
            if result["checked"]:
                resp2 = await client.get(
                    f"https://haveibeenpwned.com/api/v3/pasteaccount/{quote(email)}",
                )
                if resp2.status_code == 200:
                    pastes = resp2.json()
                    result["pastes"] = [
                        {
                            "source": p.get("Source"),
                            "title": p.get("Title"),
                            "date": p.get("Date"),
                            "email_count": p.get("EmailCount"),
                        }
                        for p in pastes
                    ]

    except httpx.TimeoutException:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)

    return result


# ═══════════════════════════════════════════════════════════════
# 6. SHODAN — Internet-connected device search
#    shodan.io
# ═══════════════════════════════════════════════════════════════

async def check_shodan(ip: str = "", domain: str = "", api_key: str = "") -> dict:
    """Query Shodan for IP/domain information."""
    result = {
        "tool": "Shodan",
        "ip": ip,
        "domain": domain,
        "data": None,
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    key = api_key or os.getenv("SHODAN_API_KEY", "")
    if not key:
        result["error"] = "Shodan API key not configured. Set SHODAN_API_KEY env var."
        return result

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if ip:
                resp = await client.get(
                    f"https://api.shodan.io/shodan/host/{ip}",
                    params={"key": key},
                )
            elif domain:
                resp = await client.get(
                    f"https://api.shodan.io/dns/resolve",
                    params={"hostnames": domain, "key": key},
                )
                if resp.status_code == 200:
                    ips = resp.json()
                    if ips:
                        ip = list(ips.values())[0]
                        resp = await client.get(
                            f"https://api.shodan.io/shodan/host/{ip}",
                            params={"key": key},
                        )
                    else:
                        result["error"] = f"Could not resolve {domain}"
                        return result
            else:
                result["error"] = "Provide IP or domain"
                return result

            if resp.status_code == 200:
                data = resp.json()
                result["data"] = {
                    "ip": data.get("ip_str"),
                    "hostnames": data.get("hostnames", []),
                    "org": data.get("org"),
                    "isp": data.get("isp"),
                    "asn": data.get("asn"),
                    "country": data.get("country_name"),
                    "city": data.get("city"),
                    "os": data.get("os"),
                    "ports": data.get("ports", []),
                    "vulns": data.get("vulns", []),
                    "tags": data.get("tags", []),
                    "last_update": data.get("last_update"),
                    "data_count": len(data.get("data", [])),
                }
            elif resp.status_code == 401:
                result["error"] = "Invalid API key"
            else:
                result["error"] = f"HTTP {resp.status_code}"

    except Exception as e:
        result["error"] = str(e)

    return result


# ═══════════════════════════════════════════════════════════════
# 7. CENSYS — Internet infrastructure search
#    censys.io
# ═══════════════════════════════════════════════════════════════

async def check_censys(ip: str = "", domain: str = "", api_id: str = "", api_secret: str = "") -> dict:
    """Query Censys for host/certificate information."""
    result = {
        "tool": "Censys",
        "ip": ip,
        "domain": domain,
        "data": None,
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    cid = api_id or os.getenv("CENSYS_API_ID", "")
    csec = api_secret or os.getenv("CENSYS_API_SECRET", "")
    if not cid or not csec:
        result["error"] = "Censys API credentials not configured."
        return result

    try:
        async with httpx.AsyncClient(timeout=15, auth=(cid, csec)) as client:
            if ip:
                resp = await client.get(
                    f"https://search.censys.io/api/v2/hosts/{ip}",
                )
                if resp.status_code == 200:
                    data = resp.json().get("result", {})
                    result["data"] = {
                        "ip": ip,
                        "services": [
                            {
                                "port": s.get("port"),
                                "service_name": s.get("service_name"),
                                "transport": s.get("transport_protocol"),
                            }
                            for s in data.get("services", [])
                        ],
                        "autonomous_system": data.get("autonomous_system", {}),
                        "location": data.get("location", {}),
                        "last_updated": data.get("last_updated_at"),
                    }
            elif domain:
                resp = await client.post(
                    "https://search.censys.io/api/v2/certificates/search",
                    json={"q": f"names: {domain}", "per_page": 5},
                )
                if resp.status_code == 200:
                    hits = resp.json().get("result", {}).get("hits", [])
                    result["data"] = {
                        "certificates": [
                            {
                                "fingerprint": h.get("fingerprint_sha256"),
                                "names": h.get("names", []),
                                "issuer": h.get("issuer", {}),
                                "not_before": h.get("not_before"),
                                "not_after": h.get("not_after"),
                            }
                            for h in hits
                        ]
                    }
    except Exception as e:
        result["error"] = str(e)

    return result


# ═══════════════════════════════════════════════════════════════
# 8. DNSDUMPSTER — DNS reconnaissance
#    dnsdumpster.com
# ═══════════════════════════════════════════════════════════════

async def check_dnsdumpster(domain: str) -> dict:
    """Query DNSDumpster for DNS records."""
    result = {
        "tool": "DNSDumpster",
        "domain": domain,
        "dns_records": [],
        "mx_records": [],
        "txt_records": [],
        "host_records": [],
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # Get CSRF token
            resp = await client.get("https://dnsdumpster.com/")
            csrf_token = ""
            for cookie in resp.cookies.jar:
                if cookie.name == "csrftoken":
                    csrf_token = cookie.value
                    break

            # Submit search
            resp2 = await client.post(
                "https://dnsdumpster.com/",
                data={"csrfmiddlewaretoken": csrf_token, "targetip": domain, "user": "free"},
                headers={"Referer": "https://dnsdumpster.com/"},
            )

            if resp2.status_code == 200:
                html = resp2.text
                # Parse DNS records from HTML (simplified)
                import re as re2
                # Extract tables
                tables = re2.findall(r'<table[^>]*>(.*?)</table>', html, re2.DOTALL)
                for table in tables:
                    rows = re2.findall(r'<tr[^>]*>(.*?)</tr>', table, re2.DOTALL)
                    for row in rows:
                        cells = re2.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re2.DOTALL)
                        cells = [re2.sub(r'<[^>]+>', '', c).strip() for c in cells]
                        if len(cells) >= 2:
                            record = {"cells": cells}
                            if "mx" in cells[0].lower():
                                result["mx_records"].append(record)
                            elif "txt" in cells[0].lower():
                                result["txt_records"].append(record)
                            else:
                                result["host_records"].append(record)

                result["raw_html_length"] = len(html)
            else:
                result["error"] = f"HTTP {resp2.status_code}"

    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 9. WAYBACK MACHINE — Historical web snapshots
#    web.archive.org
# ═══════════════════════════════════════════════════════════════

async def check_wayback(url: str = "", domain: str = "", limit: int = 20) -> dict:
    """Query Wayback Machine for historical snapshots."""
    result = {
        "tool": "Wayback Machine",
        "url": url or domain,
        "snapshots": [],
        "total_snapshots": 0,
        "first_seen": None,
        "last_seen": None,
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    target = url or domain
    if not target:
        result["error"] = "Provide URL or domain"
        return result

    try:
        # CDX API
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://web.archive.org/cdx/search/cdx",
                params={
                    "url": target,
                    "output": "json",
                    "limit": limit,
                    "fl": "timestamp,statuscode,original,mimetype,digest",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1:
                    headers = data[0]
                    for row in data[1:]:
                        record = dict(zip(headers, row))
                        snapshot = {
                            "timestamp": record.get("timestamp"),
                            "url": record.get("original"),
                            "status": record.get("statuscode"),
                            "mime_type": record.get("mimetype"),
                            "archive_url": f"https://web.archive.org/web/{record.get('timestamp')}/{record.get('original')}",
                        }
                        result["snapshots"].append(snapshot)

                    result["total_snapshots"] = len(result["snapshots"])
                    if result["snapshots"]:
                        result["first_seen"] = result["snapshots"][0]["timestamp"]
                        result["last_seen"] = result["snapshots"][-1]["timestamp"]

                # Also get availability
                resp2 = await client.get(
                    f"https://archive.org/wayback/available?url={quote(target)}",
                )
                if resp2.status_code == 200:
                    avail = resp2.json()
                    if avail.get("archived_snapshots", {}).get("closest"):
                        result["latest_snapshot"] = avail["archived_snapshots"]["closest"]

            else:
                result["error"] = f"HTTP {resp.status_code}"

    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 10. INTELX (Intelligence X) — Data search engine
#     intelx.io
# ═══════════════════════════════════════════════════════════════

async def check_intelx(query: str, api_key: str = "") -> dict:
    """Query Intelligence X for data."""
    result = {
        "tool": "Intelligence X",
        "query": query,
        "results": [],
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    key = api_key or os.getenv("INTELX_API_KEY", "")
    if not key:
        result["error"] = "IntelX API key not configured."
        return result

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Search
            resp = await client.post(
                "https://2.intelx.io/intel/search",
                json={"term": query, "maxresults": 10, "media": 0},
                headers={"X-Key": key},
            )
            if resp.status_code == 200:
                data = resp.json()
                result["results"] = [
                    {
                        "name": r.get("name"),
                        "type": r.get("type"),
                        "date": r.get("date"),
                        "media": r.get("media"),
                        "size": r.get("size"),
                    }
                    for r in data.get("records", [])
                ]
                result["total"] = len(result["results"])
            else:
                result["error"] = f"HTTP {resp.status_code}"

    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 11. SPIDERFOOT — Automated OSINT collection
#     github.com/smicallef/spiderfoot
# ═══════════════════════════════════════════════════════════════

async def run_spiderfoot(target: str, timeout: int = 300) -> dict:
    """Run SpiderFoot scan on target."""
    result = {
        "tool": "SpiderFoot",
        "target": target,
        "data": [],
        "errors": [],
    }
    sf_path = _find_tool("sf.py")
    if not sf_path:
        sf_path = _find_tool("spiderfoot")

    if not sf_path:
        result["note"] = "SpiderFoot not installed. Using built-in scanners."
        return await _builtin_domain_scan(target)

    try:
        cmd = [sf_path, "-m", "ALL", "-s", target, "-o", "json",
               "-f", "/tmp/spiderfoot_output.json"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")

        # Try to read JSON output
        try:
            with open("/tmp/spiderfoot_output.json", "r") as f:
                result["data"] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Parse text output
            for line in output.split("\n"):
                if line.strip():
                    result["data"].append({"raw": line.strip()})

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 12. EXIFTOOL — Metadata extraction
#     exiftool.org
# ═══════════════════════════════════════════════════════════════

async def run_exiftool(file_path: str) -> dict:
    """Extract metadata from file using ExifTool."""
    result = {
        "tool": "ExifTool",
        "file": file_path,
        "metadata": {},
        "errors": [],
    }
    exiftool_path = _find_tool("exiftool")
    if not exiftool_path:
        result["error"] = "ExifTool not installed"
        return result

    try:
        cmd = [exiftool_path, "-json", "-a", "-u", "-g", file_path]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="replace")

        try:
            data = json.loads(output)
            if isinstance(data, list) and len(data) > 0:
                result["metadata"] = data[0]
        except json.JSONDecodeError:
            # Parse text output
            for line in output.split("\n"):
                if ":" in line:
                    key, _, value = line.partition(":")
                    result["metadata"][key.strip()] = value.strip()

    except asyncio.TimeoutError:
        result["errors"].append("Timeout")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 13. RECON-NG — Web reconnaissance framework
#     github.com/lanmaster53/recon-ng
# ═══════════════════════════════════════════════════════════════

async def run_recon_ng(domain: str, timeout: int = 120) -> dict:
    """Run recon-ng modules for domain reconnaissance."""
    result = {
        "tool": "Recon-ng",
        "domain": domain,
        "hosts": [],
        "contacts": [],
        "credentials": [],
        "errors": [],
    }
    recon_path = _find_tool("recon-ng")
    if not recon_path:
        result["note"] = "Recon-ng not installed"
        return result

    try:
        # Create a resource script
        script = f"""
workspaces add osintham_{domain}
options set SOURCE {domain}
use recon/domains-hosts/hackertarget
run
use recon/domains-contacts/whois_pocs
run
show hosts
show contacts
exit
"""
        proc = await asyncio.create_subprocess_exec(
            recon_path, "-r", "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=script.encode()), timeout=timeout
        )
        output = stdout.decode("utf-8", errors="replace")

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            if re.match(r'^[\w\.-]+\.\w{2,}$', line):
                result["hosts"].append(line)
            elif "@" in line:
                result["contacts"].append(line)

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 14. SNOOP — Advanced username search (Russian platforms)
#     github.com/snooppr/snoop
# ═══════════════════════════════════════════════════════════════

async def run_snoop(username: str, timeout: int = 120) -> dict:
    """Run Snoop for Russian platform username search."""
    result = {
        "tool": "Snoop",
        "username": username,
        "found": [],
        "errors": [],
    }
    snoop_path = _find_tool("snoop")
    if not snoop_path:
        result["note"] = "Snoop not installed"
        return result

    try:
        cmd = [snoop_path, username]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")

        for line in output.split("\n"):
            if "+" in line or "найден" in line.lower() or "found" in line.lower():
                result["found"].append(line.strip())

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 15. OSINTGRAM — Instagram OSINT
#     github.com/Datalux/Osintgram
# ═══════════════════════════════════════════════════════════════

async def run_osintgram(username: str, timeout: int = 60) -> dict:
    """Run Osintgram for Instagram reconnaissance."""
    result = {
        "tool": "Osintgram",
        "username": username,
        "data": {},
        "errors": [],
    }
    osintgram_path = _find_tool("osintgram")
    if not osintgram_path:
        result["note"] = "Osintgram not installed"
        return result

    try:
        cmd = [osintgram_path, username]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")
        result["raw_output"] = output

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 16. X-OSINT — Multi-platform OSINT
#     github.com/TermuxHackz/X-osint
# ═══════════════════════════════════════════════════════════════

async def run_x_osint(target: str, timeout: int = 60) -> dict:
    """Run X-osint for multi-platform search."""
    result = {
        "tool": "X-OSINT",
        "target": target,
        "data": {},
        "errors": [],
    }
    xosint_path = _find_tool("x-osint")
    if not xosint_path:
        result["note"] = "X-OSINT not installed"
        return result

    try:
        cmd = [xosint_path]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=target.encode()), timeout=timeout
        )
        output = stdout.decode("utf-8", errors="replace")
        result["raw_output"] = output

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 17. INFOOOZE — OSINT API toolkit
#     github.com/devxprite/infoooze
# ═══════════════════════════════════════════════════════════════

async def check_infoooze(query: str, query_type: str = "ip") -> dict:
    """Query Infoooze API for OSINT data."""
    result = {
        "tool": "Infoooze",
        "query": query,
        "type": query_type,
        "data": None,
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            endpoints = {
                "ip": f"https://infoooze.com/api/v1/ip/{query}",
                "whois": f"https://infoooze.com/api/v1/whois/{query}",
                "dns": f"https://infoooze.com/api/v1/dns/{query}",
                "reverse_dns": f"https://infoooze.com/api/v1/reverse-dns/{query}",
            }
            endpoint = endpoints.get(query_type, endpoints["ip"])
            resp = await client.get(endpoint)
            if resp.status_code == 200:
                result["data"] = resp.json()
            else:
                result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 18. LEAKCHECK — Data leak checker
#     leakcheck.io
# ═══════════════════════════════════════════════════════════════

async def check_leakcheck(query: str, api_key: str = "", query_type: str = "email") -> dict:
    """Query LeakCheck API for data leaks."""
    result = {
        "tool": "LeakCheck",
        "query": query,
        "type": query_type,
        "data": None,
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    key = api_key or os.getenv("LEAKCHECK_API_KEY", "")
    if not key:
        result["error"] = "LeakCheck API key not configured."
        return result

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://leakcheck.io/api/v2/query",
                json={"type": query_type, "query": query},
                headers={"X-API-Key": key},
            )
            if resp.status_code == 200:
                result["data"] = resp.json()
            else:
                result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 19. BREACHHOUND — Breach data search
#     github.com/hashangit/breachhound
# ═══════════════════════════════════════════════════════════════

async def run_breachhound(email: str, timeout: int = 60) -> dict:
    """Run BreachHound for breach data search."""
    result = {
        "tool": "BreachHound",
        "email": email,
        "breaches": [],
        "errors": [],
    }
    bh_path = _find_tool("breachhound")
    if not bh_path:
        result["note"] = "BreachHound not installed. Using HIBP instead."
        return await check_hibp(email)

    try:
        cmd = [bh_path, "-e", email]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")

        for line in output.split("\n"):
            if line.strip():
                result["breaches"].append({"raw": line.strip()})

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 20. GOOGLE HACKING DATABASE (GHDB)
#     exploit-db.com/google-hacking-database
# ═══════════════════════════════════════════════════════════════

GHDB_QUERIES = {
    "emails": 'intext:"@{}" filetype:xls OR filetype:csv OR filetype:txt',
    "passwords": 'intext:"password" site:{} filetype:log OR filetype:txt',
    "config_files": 'site:{} filetype:env OR filetype:ini OR filetype:conf OR filetype:yaml',
    "admin_panels": 'site:{} inurl:admin OR inurl:login OR inurl:dashboard',
    "exposed_docs": 'site:{} filetype:pdf OR filetype:doc OR filetype:xls',
    "git_exposed": 'site:{} filetype:git OR inurl:.git',
    "backup_files": 'site:{} filetype:bak OR filetype:old OR filetype:backup',
    "database_dumps": 'site:{} filetype:sql OR filetype:db OR filetype:sqlite',
    "vulnerable_sites": 'site:{} inurl:id= OR inurl=redirect OR inurl=url=',
    "sensitive_dirs": 'site:{} intitle:"index of" OR intitle:"directory listing"',
}

def get_ghdb_queries(domain: str) -> dict:
    """Generate Google Hacking Database queries for a domain."""
    result = {
        "tool": "GHDB (Google Hacking Database)",
        "domain": domain,
        "queries": {},
    }
    for category, template in GHDB_QUERIES.items():
        result["queries"][category] = {
            "query": template.replace("{}", domain),
            "url": f"https://www.google.com/search?q={quote(template.replace('{}', domain))}",
        }
    return result


# ═══════════════════════════════════════════════════════════════
# 21. PIMEYES — Face search engine
#     pimeyes.com
# ═══════════════════════════════════════════════════════════════

async def check_pimeyes(image_url: str = "", api_key: str = "") -> dict:
    """Check Pimeyes for face search (requires API key)."""
    result = {
        "tool": "PimEyes",
        "image_url": image_url,
        "matches": [],
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    key = api_key or os.getenv("PIMEYES_API_KEY", "")
    if not key:
        result["error"] = "PimEyes API key not configured."
        return result

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.pimeyes.com/search",
                json={"image_url": image_url},
                headers={"Authorization": f"Bearer {key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                result["matches"] = data.get("results", [])
            else:
                result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 22. ODNOCLASSNIKI CHECKER — Russian social network
#     github.com/OSINT-mindset/odnoklassniki-checker
# ═══════════════════════════════════════════════════════════════

async def check_odnoklassniki(user_id: str = "", name: str = "") -> dict:
    """Check Odnoklassniki for user information."""
    result = {
        "tool": "Odnoklassniki Checker",
        "user_id": user_id,
        "name": name,
        "data": None,
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if user_id:
                resp = await client.get(
                    f"https://ok.ru/profile/{user_id}",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    result["data"] = {
                        "url": f"https://ok.ru/profile/{user_id}",
                        "status": "found",
                        "html_length": len(resp.text),
                    }
                else:
                    result["data"] = {"status": "not_found", "http_status": resp.status_code}
            elif name:
                resp = await client.get(
                    f"https://ok.ru/search?st.query={quote(name)}&st.mode=Users",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                result["data"] = {
                    "search_url": f"https://ok.ru/search?st.query={name}&st.mode=Users",
                    "status": resp.status_code,
                }
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 23. OSINT-VK — VKontakte OSINT
#     github.com/AdrianGuretto/OSINTvk
# ═══════════════════════════════════════════════════════════════

async def check_vk(user_id: str = "", name: str = "") -> dict:
    """Check VKontakte for user information."""
    result = {
        "tool": "OSINT-VK",
        "user_id": user_id,
        "name": name,
        "data": None,
        "errors": [],
    }
    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if user_id:
                resp = await client.get(
                    f"https://vk.com/{user_id}",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    result["data"] = {
                        "url": f"https://vk.com/{user_id}",
                        "status": "found",
                        "html_length": len(resp.text),
                    }
                else:
                    result["data"] = {"status": "not_found", "http_status": resp.status_code}
            elif name:
                resp = await client.get(
                    f"https://vk.com/search?c%5Bq%5D={quote(name)}&c%5Bsection%5D=people",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                result["data"] = {
                    "search_url": f"https://vk.com/search?q={name}&section=people",
                    "status": resp.status_code,
                }
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# 24. GOOGLE EARTH — Geolocation
#     earth.google.com
# ═══════════════════════════════════════════════════════════════

def get_google_earth_link(lat: float, lon: float, zoom: int = 15) -> dict:
    """Generate Google Earth link for coordinates."""
    return {
        "tool": "Google Earth",
        "lat": lat,
        "lon": lon,
        "links": {
            "google_earth_web": f"https://earth.google.com/search/{lat},{lon}",
            "google_maps": f"https://www.google.com/maps?q={lat},{lon}&z={zoom}",
            "google_streetview": f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}",
            "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map={zoom}/{lat}/{lon}",
            "bing_maps": f"https://www.bing.com/maps?cp={lat}~{lon}&lvl={zoom}",
        },
    }


# ═══════════════════════════════════════════════════════════════
# 25. UNIVERSAL SEARCH — Multi-engine search
# ═══════════════════════════════════════════════════════════════

async def universal_search(query: str) -> dict:
    """Search across multiple engines and aggregate results."""
    result = {
        "tool": "Universal Search",
        "query": query,
        "search_urls": {},
        "whois": None,
        "dns": None,
        "wayback": None,
        "ghdb": None,
    }

    encoded = quote(query)

    # Search engine URLs
    result["search_urls"] = {
        "google": f"https://www.google.com/search?q={encoded}",
        "bing": f"https://www.bing.com/search?q={encoded}",
        "duckduckgo": f"https://duckduckgo.com/?q={encoded}",
        "yandex": f"https://yandex.com/search/?text={encoded}",
        "yahoo": f"https://search.yahoo.com/search?p={encoded}",
        "baidu": f"https://www.baidu.com/s?wd={encoded}",
        "startpage": f"https://www.startpage.com/do/dsearch?query={encoded}",
    }

    # Specialized searches
    if re.match(r'^[\w\.-]+\.\w{2,}$', query):
        # Domain-specific
        result["whois"] = f"https://who.is/whois/{query}"
        result["dns_dumpster"] = f"https://dnsdumpster.com/"
        result["shodan"] = f"https://www.shodan.io/search?query={encoded}"
        result["censys"] = f"https://search.censys.io/search?resource=hosts&q={encoded}"
        result["wayback"] = f"https://web.archive.org/web/*/{query}"
        result["virustotal"] = f"https://www.virustotal.com/gui/domain/{query}"
        result["urlscan"] = f"https://urlscan.io/search/#{encoded}"
        result["ghdb"] = get_ghdb_queries(query)
    elif re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', query):
        # Email-specific
        result["hibp"] = f"https://haveibeenpwned.com/account/{encoded}"
        result["hunter_io"] = f"https://hunter.io/email-verifier/{query}"
        result["emailrep"] = f"https://emailrep.io/{query}"
    elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
        # IP-specific
        result["shodan"] = f"https://www.shodan.io/host/{query}"
        result["censys"] = f"https://search.censys.io/hosts/{query}"
        result["virustotal"] = f"https://www.virustotal.com/gui/ip-address/{query}"
        result["abuseipdb"] = f"https://www.abuseipdb.com/check/{query}"
        result["ipinfo"] = f"https://ipinfo.io/{query}"
    else:
        # Username/person
        result["namechk"] = f"https://namechk.com/{encoded}"
        result["whatsmyname"] = f"https://whatsmyname.app/"
        result["sherlock"] = f"https://github.com/sherlock-project/sherlock"

    return result


# ═══════════════════════════════════════════════════════════════
# MASTER ORCHESTRATOR — Run all applicable tools
# ═══════════════════════════════════════════════════════════════

async def run_full_osint(target: str, target_type: str = "auto",
                         enabled_tools: list = None) -> dict:
    """
    Run full OSINT scan using all applicable tools.
    
    Args:
        target: The target to investigate (email, domain, IP, username, phone, URL)
        target_type: auto, email, domain, ip, username, phone, url
        enabled_tools: List of tool names to run (None = all applicable)
    
    Returns:
        Comprehensive OSINT report with graph-ready data
    """
    result = {
        "target": target,
        "target_type": target_type,
        "detected_type": target_type,
        "scanned_at": datetime.utcnow().isoformat(),
        "tools_results": {},
        "suggested_nodes": [],
        "suggested_edges": [],
        "errors": [],
    }

    # Auto-detect type
    if target_type == "auto":
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', target):
            target_type = "email"
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
            target_type = "ip"
        elif re.match(r'^[\w\.-]+\.\w{2,}$', target):
            target_type = "domain"
        elif re.match(r'^[\w\.-]+$', target) and 3 <= len(target) <= 30:
            target_type = "username"
        elif target.startswith("http"):
            target_type = "url"
        else:
            target_type = "username"

    result["detected_type"] = target_type

    # Determine which tools to run
    all_tools = {
        "email": ["hibp", "holehe", "universal_search"],
        "domain": ["theharvester", "dnsdumpster", "wayback", "shodan", "censys", "ghdb", "universal_search"],
        "ip": ["shodan", "censys", "universal_search"],
        "username": ["sherlock", "maigret", "snoop", "universal_search"],
        "url": ["wayback", "universal_search"],
        "phone": ["universal_search"],
    }

    tools_to_run = enabled_tools or all_tools.get(target_type, ["universal_search"])

    # Run tools concurrently
    tasks = {}
    if "sherlock" in tools_to_run:
        tasks["sherlock"] = run_sherlock(target)
    if "maigret" in tools_to_run:
        tasks["maigret"] = run_maigret(target)
    if "holehe" in tools_to_run:
        tasks["holehe"] = run_holehe(target)
    if "theharvester" in tools_to_run:
        tasks["theharvester"] = run_theharvester(target)
    if "hibp" in tools_to_run:
        tasks["hibp"] = check_hibp(target)
    if "shodan" in tools_to_run:
        tasks["shodan"] = check_shodan(ip=target if target_type == "ip" else "", domain=target if target_type == "domain" else "")
    if "censys" in tools_to_run:
        tasks["censys"] = check_censys(ip=target if target_type == "ip" else "", domain=target if target_type == "domain" else "")
    if "dnsdumpster" in tools_to_run:
        tasks["dnsdumpster"] = check_dnsdumpster(target)
    if "wayback" in tools_to_run:
        tasks["wayback"] = check_wayback(domain=target)
    if "snoop" in tools_to_run:
        tasks["snoop"] = run_snoop(target)
    if "spiderfoot" in tools_to_run:
        tasks["spiderfoot"] = run_spiderfoot(target)
    if "recon_ng" in tools_to_run:
        tasks["recon_ng"] = run_recon_ng(target)
    if "breachhound" in tools_to_run:
        tasks["breachhound"] = run_breachhound(target)
    if "leakcheck" in tools_to_run:
        tasks["leakcheck"] = check_leakcheck(target, query_type=target_type)
    if "intelx" in tools_to_run:
        tasks["intelx"] = check_intelx(target)
    if "infoooze" in tools_to_run:
        tasks["infoooze"] = check_infoooze(target, query_type=target_type)
    if "osintgram" in tools_to_run:
        tasks["osintgram"] = run_osintgram(target)
    if "x_osint" in tools_to_run:
        tasks["x_osint"] = run_x_osint(target)
    if "odnoklassniki" in tools_to_run:
        tasks["odnoklassniki"] = check_odnoklassniki(user_id=target if target_type == "username" else "")
    if "vk" in tools_to_run:
        tasks["vk"] = check_vk(user_id=target if target_type == "username" else "")
    if "pimeyes" in tools_to_run:
        tasks["pimeyes"] = check_pimeyes(image_url=target if target.startswith("http") else "")
    if "universal_search" in tools_to_run:
        tasks["universal_search"] = universal_search(target)
    if "ghdb" in tools_to_run:
        result["tools_results"]["ghdb"] = get_ghdb_queries(target)

    # Execute all tasks concurrently
    if tasks:
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for tool_name, tool_result in zip(tasks.keys(), results):
            if isinstance(tool_result, Exception):
                result["tools_results"][tool_name] = {"error": str(tool_result)}
            else:
                result["tools_results"][tool_name] = tool_result

    # Generate suggested nodes from results
    result["suggested_nodes"] = _generate_suggested_nodes(result)
    result["suggested_edges"] = _generate_suggested_edges(result)

    return result


def _generate_suggested_nodes(scan_result: dict) -> list:
    """Generate graph nodes from scan results."""
    nodes = []
    target = scan_result["target"]
    target_type = scan_result["detected_type"]

    # Main target node
    nodes.append({
        "type": target_type,
        "label": target,
        "trust_level": 5,
        "source": "User input",
        "data": {},
    })

    # Process each tool's results
    for tool_name, tool_data in scan_result.get("tools_results", {}).items():
        if isinstance(tool_data, dict):
            # Sherlock/Maigret found accounts
            if tool_name in ("sherlock", "maigret", "snoop"):
                for found in tool_data.get("found", []):
                    site = found.get("site", found.get("platform", tool_name))
                    url = found.get("url", "")
                    nodes.append({
                        "type": "social_account",
                        "label": f"{site}: {target}",
                        "trust_level": 3,
                        "source": f"Found by {tool_name}",
                        "data": {"platform": site, "url": url},
                    })

            # HIBP breaches
            elif tool_name == "hibp":
                for breach in tool_data.get("breaches", []):
                    nodes.append({
                        "type": "document",
                        "label": f"Breach: {breach.get('name', 'Unknown')}",
                        "trust_level": 4,
                        "source": "Have I Been Pwned",
                        "data": {
                            "domain": breach.get("domain"),
                            "date": breach.get("date"),
                            "data_classes": breach.get("data_classes", []),
                            "pwn_count": breach.get("pwn_count"),
                        },
                    })

            # theHarvester results
            elif tool_name == "theharvester":
                for email in tool_data.get("emails", []):
                    nodes.append({
                        "type": "email",
                        "label": email,
                        "trust_level": 3,
                        "source": f"theHarvester ({target})",
                        "data": {},
                    })
                for host in tool_data.get("hosts", []):
                    nodes.append({
                        "type": "domain",
                        "label": host,
                        "trust_level": 3,
                        "source": f"theHarvester ({target})",
                        "data": {},
                    })
                for ip in tool_data.get("ips", []):
                    nodes.append({
                        "type": "ip",
                        "label": ip,
                        "trust_level": 3,
                        "source": f"theHarvester ({target})",
                        "data": {},
                    })

            # Shodan results
            elif tool_name == "shodan" and tool_data.get("data"):
                shodan_data = tool_data["data"]
                nodes.append({
                    "type": "ip",
                    "label": shodan_data.get("ip", target),
                    "trust_level": 4,
                    "source": "Shodan",
                    "data": {
                        "org": shodan_data.get("org"),
                        "isp": shodan_data.get("isp"),
                        "country": shodan_data.get("country"),
                        "city": shodan_data.get("city"),
                        "ports": shodan_data.get("ports", []),
                        "vulns": shodan_data.get("vulns", []),
                    },
                })

            # Wayback Machine
            elif tool_name == "wayback" and tool_data.get("snapshots"):
                nodes.append({
                    "type": "document",
                    "label": f"Wayback: {target}",
                    "trust_level": 3,
                    "source": "Wayback Machine",
                    "data": {
                        "total_snapshots": tool_data.get("total_snapshots"),
                        "first_seen": tool_data.get("first_seen"),
                        "last_seen": tool_data.get("last_seen"),
                    },
                })

            # Holehe accounts
            elif tool_name == "holehe":
                for account in tool_data.get("accounts", []):
                    nodes.append({
                        "type": "social_account",
                        "label": f"{account.get('service', 'Unknown')}: {target}",
                        "trust_level": 3,
                        "source": "Holehe",
                        "data": {"service": account.get("service"), "email": target},
                    })

    return nodes


def _generate_suggested_edges(scan_result: dict) -> list:
    """Generate graph edges from scan results."""
    edges = []
    target = scan_result["target"]
    target_type = scan_result["detected_type"]

    # This is a simplified edge generator
    # In production, you'd map actual node IDs
    for tool_name, tool_data in scan_result.get("tools_results", {}).items():
        if isinstance(tool_data, dict):
            if tool_name in ("sherlock", "maigret", "snoop"):
                for found in tool_data.get("found", []):
                    site = found.get("site", found.get("platform", tool_name))
                    edges.append({
                        "from": "target_node",
                        "to": f"social_{site}_node",
                        "label": f"found on {site}",
                        "trust_level": 3,
                    })
            elif tool_name == "hibp":
                for breach in tool_data.get("breaches", []):
                    edges.append({
                        "from": "target_node",
                        "to": f"breach_{breach.get('name', 'unknown')}_node",
                        "label": "appears in breach",
                        "trust_level": 4,
                    })
            elif tool_name == "theharvester":
                for email in tool_data.get("emails", []):
                    edges.append({
                        "from": "target_node",
                        "to": f"email_{email}_node",
                        "label": "related email",
                        "trust_level": 3,
                    })

    return edges


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _find_tool(name: str) -> Optional[str]:
    """Find if a command-line tool is available."""
    try:
        result = subprocess.run(
            ["which", name],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


async def _builtin_username_search(username: str) -> dict:
    """Fallback username search when Sherlock/Maigret not installed."""
    platforms = {
        'GitHub': f'https://github.com/{username}',
        'Twitter': f'https://twitter.com/{username}',
        'Instagram': f'https://instagram.com/{username}',
        'Reddit': f'https://reddit.com/user/{username}',
        'YouTube': f'https://youtube.com/@{username}',
        'TikTok': f'https://tiktok.com/@{username}',
        'Telegram': f'https://t.me/{username}',
        'VK': f'https://vk.com/{username}',
        'LinkedIn': f'https://linkedin.com/in/{username}',
        'Medium': f'https://medium.com/@{username}',
        'GitLab': f'https://gitlab.com/{username}',
        'Patreon': f'https://patreon.com/{username}',
        'Dribbble': f'https://dribbble.com/{username}',
        'Behance': f'https://behance.net/{username}',
        'SoundCloud': f'https://soundcloud.com/{username}',
        'Spotify': f'https://open.spotify.com/user/{username}',
        'Steam': f'https://steamcommunity.com/id/{username}',
        'Keybase': f'https://keybase.io/{username}',
        'HackerNews': f'https://news.ycombinator.com/user?id={username}',
        'Pinterest': f'https://pinterest.com/{username}',
        'Tumblr': f'https://{username}.tumblr.com',
        'Flickr': f'https://flickr.com/people/{username}',
        'Vimeo': f'https://vimeo.com/{username}',
        'Fandom': f'https://fandom.com/u/{username}',
        'Wikipedia': f'https://wikipedia.org/wiki/User:{username}',
        'Etsy': f'https://etsy.com/people/{username}',
        'Goodreads': f'https://goodreads.com/{username}',
        'Last.fm': f'https://last.fm/user/{username}',
        'DeviantArt': f'https://deviantart.com/{username}',
        'Bitbucket': f'https://bitbucket.org/{username}',
    }

    result = {
        "tool": "Built-in Username Search",
        "username": username,
        "platforms_checked": len(platforms),
        "found": [],
        "not_found": [],
        "errors": [],
    }

    if HAS_HTTPX:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        ) as client:
            for platform, url in platforms.items():
                try:
                    resp = await client.get(url)
                    is_found = resp.status_code == 200
                    not_found_indicators = [
                        'page not found', '404', 'not found', "doesn't exist",
                        'no such user', 'could not be found', 'unavailable',
                    ]
                    if any(ind in resp.text.lower() for ind in not_found_indicators):
                        is_found = False
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
    else:
        for platform, url in platforms.items():
            result["found"].append({
                "platform": platform,
                "url": url,
                "status_code": "manual_check",
            })

    return result


async def _builtin_email_breach_check(email: str) -> dict:
    """Fallback email breach check."""
    return await check_hibp(email)


async def _builtin_domain_scan(domain: str) -> dict:
    """Fallback domain scan."""
    result = {
        "tool": "Built-in Domain Scanner",
        "domain": domain,
        "dns": {},
        "whois": None,
        "subdomains": [],
        "errors": [],
    }

    if HAS_DNS:
        for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                result["dns"][record_type] = [str(r) for r in answers]
            except Exception:
                pass

    if HAS_WHOIS:
        try:
            w = whois.whois(domain)
            result["whois"] = {
                "registrar": str(w.registrar) if w.registrar else None,
                "creation_date": str(w.creation_date) if w.creation_date else None,
                "expiration_date": str(w.expiration_date) if w.expiration_date else None,
                "name_servers": [str(ns) for ns in w.name_servers] if w.name_servers else [],
                "org": str(w.org) if w.org else None,
                "country": str(w.country) if w.country else None,
            }
        except Exception as e:
            result["errors"].append(f"WHOIS: {str(e)}")

    # Subdomain enumeration
    common_subs = [
        'www', 'mail', 'ftp', 'admin', 'api', 'blog', 'shop', 'dev',
        'staging', 'test', 'portal', 'vpn', 'cdn', 'ns1', 'ns2', 'mx',
        'smtp', 'pop', 'imap', 'webmail', 'docs', 'support', 'status',
        'git', 'gitlab', 'jenkins', 'cpanel', 'whm', 'autodiscover',
        'owa', 'exchange', 'remote', 'cloud', 'storage', 'media',
    ]
    for sub in common_subs:
        try:
            full = f"{sub}.{domain}"
            dns.resolver.resolve(full, 'A')
            result["subdomains"].append(full)
        except Exception:
            pass

    return result
