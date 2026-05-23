"""OsintHAM — Full OSINT Engine v2
Real scanning implementations. No simulations.
All scanners return live data via httpx/dns/whois APIs.
"""
import re
import hashlib
import json
import asyncio
import socket
import ssl
import time
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
    import dns.exception
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

try:
    import whois
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False


# ── HTTP Client (shared) ──

def _client():
    """Create httpx async client with proper headers."""
    return httpx.AsyncClient(
        follow_redirects=True,
        timeout=15,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )


# ═══════════════════════════════════════════════════════════════
# EMAIL SCANNER (real)
# ═══════════════════════════════════════════════════════════════

async def scan_email(email: str) -> dict:
    """Full email analysis — format, MX, provider, breaches."""
    result = {
        "email": email,
        "is_valid_format": False,
        "username": None,
        "domain": None,
        "is_disposable": False,
        "is_free_provider": False,
        "mx_records": [],
        "has_mx": False,
        "spf_record": None,
        "dmarc_record": None,
        "breaches": [],
        "social_accounts": [],
        "errors": [],
    }

    # Format validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        result["errors"].append("Invalid email format")
        return result
    result["is_valid_format"] = True

    user, domain = email.split("@", 1)
    result["username"] = user
    result["domain"] = domain

    # Disposable check
    disposable_domains = {
        'guerrillamail.com', 'tempmail.com', 'throwaway.email', 'mailinator.com',
        'sharklasers.com', 'grr.la', 'dispostable.com', 'yopmail.com',
        'trashmail.com', 'temp-mail.org', 'fakeinbox.com', 'mailnesia.com',
        'maildrop.cc', 'discard.email', 'tempail.com', '10minutemail.com',
        'guerrillamailblock.com', 'guerrillamail.info', 'guerrillamail.net',
    }
    result["is_disposable"] = domain.lower() in disposable_domains

    # Free provider check
    free_providers = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
        'mail.com', 'yandex.ru', 'rambler.ru', 'protonmail.com', 'icloud.com',
        'zoho.com', 'gmx.com', 'fastmail.com', 'tutanota.com', 'hey.com',
        'live.com', 'msn.com', 'mail.ru', 'list.ru', 'bk.ru', 'inbox.ru',
    }
    result["is_free_provider"] = domain.lower() in free_providers

    # DNS lookups
    if HAS_DNS:
        # MX records
        try:
            mx_answers = dns.resolver.resolve(domain, 'MX')
            result["mx_records"] = [
                {"exchange": str(r.exchange).rstrip('.'), "preference": r.preference}
                for r in sorted(mx_answers, key=lambda r: r.preference)
            ]
            result["has_mx"] = len(result["mx_records"]) > 0
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
            result["errors"].append("No MX records found")
        except Exception as e:
            result["errors"].append(f"MX lookup: {str(e)}")

        # SPF
        try:
            txt_answers = dns.resolver.resolve(domain, 'TXT')
            for r in txt_answers:
                txt = str(r)
                if 'v=spf1' in txt:
                    result["spf_record"] = txt[:500]
                    break
        except Exception:
            pass

        # DMARC
        try:
            dmarc_answers = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
            for r in dmarc_answers:
                txt = str(r)
                if 'v=DMARC1' in txt:
                    result["dmarc_record"] = txt[:500]
                    break
        except Exception:
            pass

    # HIBP breach check
    if HAS_HTTPX:
        try:
            hibp_result = await _check_hibp_async(email)
            result["breaches"] = hibp_result.get("breaches", [])
        except Exception as e:
            result["errors"].append(f"HIBP: {str(e)}")

    # Social media check (email-based)
    if HAS_HTTPUX:
        social_checks = await _check_email_social(email, user)
        result["social_accounts"] = social_checks

    return result


async def _check_hibp_async(email: str) -> dict:
    """Async HIBP check."""
    result = {"breaches": [], "checked": False}
    if not HAS_HTTPX:
        return result

    try:
        async with _client() as client:
            resp = await client.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote(email)}",
                headers={
                    "User-Agent": "OsintHAM-OSINT-Tool-v2",
                    "hibp-api-key": "",
                },
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
                        "pwn_count": b.get("PwnCount"),
                        "data_classes": b.get("DataClasses", []),
                    }
                    for b in breaches
                ]
                result["checked"] = True
            elif resp.status_code == 404:
                result["checked"] = True
    except Exception:
        pass
    return result


async def _check_email_social(email: str, username: str) -> list:
    """Check if email/username has social accounts."""
    found = []

    # Gravatar check
    try:
        email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
        async with _client() as client:
            resp = await client.get(f"https://www.gravatar.com/avatar/{email_hash}?d=404")
            if resp.status_code == 200:
                found.append({
                    "platform": "Gravatar",
                    "url": f"https://gravatar.com/{email_hash}",
                    "profile_image": f"https://www.gravatar.com/avatar/{email_hash}?s=200",
                })
    except Exception:
        pass

    return found


# ═══════════════════════════════════════════════════════════════
# PHONE SCANNER (real)
# ═══════════════════════════════════════════════════════════════

async def scan_phone(phone: str) -> dict:
    """Analyze phone number — validation, country, carrier."""
    result = {
        "original": phone,
        "cleaned": "",
        "is_valid": False,
        "country": None,
        "country_code": None,
        "national_number": None,
        "carrier": None,
        "phone_type": None,
        "time_zones": [],
        "formats": {},
    }

    # Clean
    cleaned = re.sub(r'[^\d+]', '', phone)
    result["cleaned"] = cleaned

    # Extract digits only
    digits = re.sub(r'\D', '', phone)
    if len(digits) < 7 or len(digits) > 15:
        return result

    result["is_valid"] = True

    # Country detection by ITU-T E.164
    country_data = [
        ("1", "US/Canada", "+1"),
        ("7", "Russia/Kazakhstan", "+7"),
        ("20", "Egypt", "+20"),
        ("27", "South Africa", "+27"),
        ("30", "Greece", "+30"),
        ("31", "Netherlands", "+31"),
        ("32", "Belgium", "+32"),
        ("33", "France", "+33"),
        ("34", "Spain", "+34"),
        ("36", "Hungary", "+36"),
        ("39", "Italy", "+39"),
        ("40", "Romania", "+40"),
        ("41", "Switzerland", "+41"),
        ("43", "Austria", "+43"),
        ("44", "United Kingdom", "+44"),
        ("45", "Denmark", "+45"),
        ("46", "Sweden", "+46"),
        ("47", "Norway", "+47"),
        ("48", "Poland", "+48"),
        ("49", "Germany", "+49"),
        ("51", "Peru", "+51"),
        ("52", "Mexico", "+52"),
        ("53", "Cuba", "+53"),
        ("54", "Argentina", "+54"),
        ("55", "Brazil", "+55"),
        ("56", "Chile", "+56"),
        ("57", "Colombia", "+57"),
        ("58", "Venezuela", "+58"),
        ("60", "Malaysia", "+60"),
        ("61", "Australia", "+61"),
        ("62", "Indonesia", "+62"),
        ("63", "Philippines", "+63"),
        ("64", "New Zealand", "+64"),
        ("65", "Singapore", "+65"),
        ("66", "Thailand", "+66"),
        ("81", "Japan", "+81"),
        ("82", "South Korea", "+82"),
        ("84", "Vietnam", "+84"),
        ("86", "China", "+86"),
        ("90", "Turkey", "+90"),
        ("91", "India", "+91"),
        ("92", "Pakistan", "+92"),
        ("93", "Afghanistan", "+93"),
        ("94", "Sri Lanka", "+94"),
        ("95", "Myanmar", "+95"),
        ("98", "Iran", "+98"),
        ("212", "Morocco", "+212"),
        ("213", "Algeria", "+213"),
        ("216", "Tunisia", "+216"),
        ("220", "Gambia", "+220"),
        ("221", "Senegal", "+221"),
        ("225", "Côte d'Ivoire", "+225"),
        ("234", "Nigeria", "+234"),
        ("233", "Ghana", "+233"),
        ("254", "Kenya", "+254"),
        ("256", "Uganda", "+256"),
        ("260", "Zambia", "+260"),
        ("351", "Portugal", "+351"),
        ("352", "Luxembourg", "+352"),
        ("353", "Ireland", "+353"),
        ("354", "Iceland", "+354"),
        ("355", "Albania", "+355"),
        ("356", "Malta", "+356"),
        ("357", "Cyprus", "+357"),
        ("358", "Finland", "+358"),
        ("359", "Bulgaria", "+359"),
        ("370", "Lithuania", "+370"),
        ("371", "Latvia", "+371"),
        ("372", "Estonia", "+372"),
        ("373", "Moldova", "+373"),
        ("374", "Armenia", "+374"),
        ("375", "Belarus", "+375"),
        ("376", "Andorra", "+376"),
        ("377", "Monaco", "+377"),
        ("378", "San Marino", "+378"),
        ("380", "Ukraine", "+380"),
        ("381", "Serbia", "+381"),
        ("382", "Montenegro", "+382"),
        ("385", "Croatia", "+385"),
        ("386", "Slovenia", "+386"),
        ("387", "Bosnia", "+387"),
        ("389", "North Macedonia", "+389"),
        ("420", "Czech Republic", "+420"),
        ("421", "Slovakia", "+421"),
        ("423", "Liechtenstein", "+423"),
        ("501", "Belize", "+501"),
        ("502", "Guatemala", "+502"),
        ("503", "El Salvador", "+503"),
        ("504", "Honduras", "+504"),
        ("505", "Nicaragua", "+505"),
        ("506", "Costa Rica", "+506"),
        ("507", "Panama", "+507"),
        ("509", "Haiti", "+509"),
        ("591", "Bolivia", "+591"),
        ("593", "Ecuador", "+593"),
        ("595", "Paraguay", "+595"),
        ("598", "Uruguay", "+598"),
        ("673", "Brunei", "+673"),
        ("675", "Papua New Guinea", "+675"),
        ("676", "Tonga", "+676"),
        ("680", "Palau", "+680"),
        ("850", "North Korea", "+850"),
        ("852", "Hong Kong", "+852"),
        ("853", "Macau", "+853"),
        ("855", "Cambodia", "+855"),
        ("856", "Laos", "+856"),
        ("880", "Bangladesh", "+880"),
        ("886", "Taiwan", "+886"),
        ("960", "Maldives", "+960"),
        ("961", "Lebanon", "+961"),
        ("962", "Jordan", "+962"),
        ("963", "Syria", "+963"),
        ("964", "Iraq", "+964"),
        ("965", "Kuwait", "+965"),
        ("966", "Saudi Arabia", "+966"),
        ("967", "Yemen", "+967"),
        ("968", "Oman", "+968"),
        ("970", "Palestine", "+970"),
        ("971", "UAE", "+971"),
        ("972", "Israel", "+972"),
        ("973", "Bahrain", "+973"),
        ("974", "Qatar", "+974"),
        ("975", "Bhutan", "+975"),
        ("976", "Mongolia", "+976"),
        ("977", "Nepal", "+977"),
        ("992", "Tajikistan", "+992"),
        ("993", "Turkmenistan", "+993"),
        ("994", "Azerbaijan", "+994"),
        ("995", "Georgia", "+995"),
        ("996", "Kyrgyzstan", "+996"),
        ("998", "Uzbekistan", "+998"),
    ]

    for prefix, country, code in country_data:
        if digits.startswith(prefix) or cleaned.startswith(code):
            result["country"] = country
            result["country_code"] = code
            result["national_number"] = digits[len(prefix):] if digits.startswith(prefix) else digits
            break

    # Phone type estimation
    if result["country_code"] == "+1":
        result["phone_type"] = "Mobile/Landline"
        result["time_zones"] = ["EST", "CST", "MST", "PST"]
    elif result["country_code"] == "+7":
        if digits.startswith("79"):
            result["phone_type"] = "Mobile"
        else:
            result["phone_type"] = "Landline"
        result["time_zones"] = ["MSK"]
    elif result["country_code"] in ("+44", "+49", "+33", "+39", "+34"):
        result["phone_type"] = "Mobile/Landline"
        result["time_zones"] = ["CET"]
    elif result["country_code"] == "+86":
        result["phone_type"] = "Mobile/Landline"
        result["time_zones"] = ["CST"]
    elif result["country_code"] == "+81":
        result["phone_type"] = "Mobile/Landline"
        result["time_zones"] = ["JST"]
    elif result["country_code"] == "+91":
        result["phone_type"] = "Mobile/Landline"
        result["time_zones"] = ["IST"]
    else:
        result["phone_type"] = "Unknown"

    # Formats
    if result["national_number"]:
        nat = result["national_number"]
        result["formats"] = {
            "e164": f"{result['country_code']}{nat}",
            "international": f"{result['country_code']} {nat}",
            "national": nat,
        }

    return result


# ═══════════════════════════════════════════════════════════════
# DOMAIN SCANNER (real)
# ═══════════════════════════════════════════════════════════════

async def scan_domain(domain: str) -> dict:
    """Full domain analysis — WHOIS, DNS, SSL, subdomains."""
    result = {
        "domain": domain,
        "whois": None,
        "dns": {},
        "ssl": None,
        "subdomains": [],
        "http_info": None,
        "security_headers": {},
        "technologies": [],
        "reverse_dns": [],
        "errors": [],
    }

    # WHOIS
    if HAS_WHOIS:
        try:
            w = whois.whois(domain)
            result["whois"] = {
                "registrar": str(w.registrar) if w.registrar else None,
                "creation_date": str(w.creation_date) if w.creation_date else None,
                "expiration_date": str(w.expiration_date) if w.expiration_date else None,
                "updated_date": str(w.updated_date) if w.updated_date else None,
                "name_servers": [str(ns).lower() for ns in w.name_servers] if isinstance(w.name_servers, list) else [str(w.name_servers).lower()] if w.name_servers else [],
                "status": str(w.status) if w.status else None,
                "org": str(w.org) if w.org else None,
                "country": str(w.country) if w.country else None,
                "emails": [str(e) for e in w.emails] if isinstance(w.emails, list) else [str(w.emails)] if w.emails else [],
                "raw": str(w.text)[:2000] if hasattr(w, 'text') and w.text else None,
            }
        except Exception as e:
            result["errors"].append(f"WHOIS: {str(e)}")

    # DNS records
    if HAS_DNS:
        for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME', 'SRV', 'CAA']:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records = []
                for r in answers:
                    val = str(r)
                    if record_type == 'MX':
                        val = {"exchange": str(r.exchange).rstrip('.'), "preference": r.preference}
                    elif record_type == 'SOA':
                        val = {"mname": str(r.mname), "rname": str(r.rname), "serial": r.serial}
                    records.append(val)
                result["dns"][record_type] = records
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                pass
            except dns.exception.Timeout:
                result["errors"].append(f"DNS {record_type}: timeout")
            except Exception as e:
                result["errors"].append(f"DNS {record_type}: {str(e)[:50]}")

    # SSL certificate
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(8)
            s.connect((domain, 443))
            cert = s.getpeercert()
            cipher = s.cipher()
            version = s.version()
            result["ssl"] = {
                "subject": dict(x[0] for x in cert.get('subject', [])),
                "issuer": dict(x[0] for x in cert.get('issuer', [])),
                "not_before": cert.get('notBefore'),
                "not_after": cert.get('notAfter'),
                "serial_number": cert.get('serialNumber'),
                "version": cert.get('version'),
                "san": [v for _, v in cert.get('subjectAltName', [])] if cert.get('subjectAltName') else [],
                "cipher": cipher[0] if cipher else None,
                "tls_version": version,
                "is_expired": False,
            }
            # Check expiry
            try:
                from datetime import datetime as dt
                not_after = dt.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                result["ssl"]["is_expired"] = not_after < dt.utcnow()
                result["ssl"]["days_until_expiry"] = (not_after - dt.utcnow()).days
            except Exception:
                pass
    except socket.timeout:
        result["errors"].append("SSL: connection timeout")
    except ConnectionRefusedError:
        result["errors"].append("SSL: connection refused (port 443)")
    except ssl.SSLCertVerificationError as e:
        result["errors"].append(f"SSL: cert verification failed — {str(e)[:100]}")
    except Exception as e:
        result["errors"].append(f"SSL: {str(e)[:100]}")

    # Subdomain enumeration (common)
    if HAS_DNS:
        common_subs = [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'ns2',
            'dns', 'dns1', 'dns2', 'mx', 'mx1', 'mx2', 'cloud', 'api', 'dev', 'staging',
            'test', 'beta', 'alpha', 'demo', 'app', 'apps', 'portal', 'admin', 'dashboard',
            'cpanel', 'whm', 'webdisk', 'autodiscover', 'owa', 'exchange', 'remote',
            'vpn', 'proxy', 'cdn', 'static', 'assets', 'media', 'images', 'img', 'files',
            'storage', 'backup', 'git', 'gitlab', 'jenkins', 'jira', 'confluence', 'wiki',
            'docs', 'help', 'support', 'status', 'monitor', 'grafana', 'kibana',
            'blog', 'news', 'shop', 'store', 'forum', 'community', 'chat',
            'docs', 'download', 'downloads', 'smtp', 'imap', 'pop3', 'mx',
        ]
        for sub in common_subs:
            try:
                full = f"{sub}.{domain}"
                dns.resolver.resolve(full, 'A')
                result["subdomains"].append(full)
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                pass
            except dns.exception.Timeout:
                pass
            except Exception:
                pass

    # HTTP analysis
    if HAS_HTTPX:
        try:
            url = f"https://{domain}"
            async with _client() as client:
                resp = await client.get(url)
                result["http_info"] = {
                    "status_code": resp.status_code,
                    "final_url": str(resp.url),
                    "server": resp.headers.get("server", ""),
                    "content_type": resp.headers.get("content-type", ""),
                    "content_length": len(resp.text),
                    "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
                }
                # Security headers
                sec_headers = {
                    "Strict-Transport-Security": "HSTS",
                    "Content-Security-Policy": "CSP",
                    "X-Frame-Options": "Clickjacking Protection",
                    "X-Content-Type-Options": "MIME Sniffing Protection",
                    "X-XSS-Protection": "XSS Filter",
                    "Referrer-Policy": "Referrer Policy",
                    "Permissions-Policy": "Permissions Policy",
                    "X-Powered-By": "Technology Disclosure",
                }
                for header, name in sec_headers.items():
                    val = resp.headers.get(header)
                    result["security_headers"][name] = val if val else "Missing"

                # Technology detection
                tech = []
                body_lower = resp.text.lower()
                headers_lower = {k.lower(): v.lower() for k, v in resp.headers.items()}

                if "x-powered-by" in headers_lower:
                    tech.append(f"Powered by: {resp.headers['x-powered-by']}")
                if "server" in headers_lower:
                    server = resp.headers["server"].lower()
                    if "nginx" in server:
                        tech.append("Nginx")
                    elif "apache" in server:
                        tech.append("Apache")
                    elif "cloudflare" in server:
                        tech.append("Cloudflare")
                    elif "iis" in server:
                        tech.append("IIS")
                    elif "litespeed" in server:
                        tech.append("LiteSpeed")

                if "cf-ray" in headers_lower:
                    tech.append("Cloudflare CDN")
                if "x-aspnet-version" in headers_lower:
                    tech.append("ASP.NET")
                if "x-drupal-cache" in headers_lower:
                    tech.append("Drupal")
                if "wp-content" in body_lower or "wp-includes" in body_lower:
                    tech.append("WordPress")
                if "react" in body_lower or "reactroot" in body_lower or "__next" in body_lower:
                    tech.append("React")
                if "vue" in body_lower or "vuejs" in body_lower or "nuxt" in body_lower:
                    tech.append("Vue.js/Nuxt")
                if "angular" in body_lower:
                    tech.append("Angular")
                if "jquery" in body_lower:
                    tech.append("jQuery")
                if "bootstrap" in body_lower:
                    tech.append("Bootstrap")
                if "django" in body_lower or "csrfmiddlewaretoken" in body_lower:
                    tech.append("Django")
                if "laravel" in headers_lower.get("set-cookie", "") or "laravel_session" in body_lower:
                    tech.append("Laravel")
                if "ruby" in body_lower or "rails" in body_lower:
                    tech.append("Ruby on Rails")
                if "express" in headers_lower.get("x-powered-by", ""):
                    tech.append("Express.js")
                if "graphql" in body_lower:
                    tech.append("GraphQL")
                if "socket.io" in body_lower:
                    tech.append("Socket.io")
                if "recaptcha" in body_lower:
                    tech.append("reCAPTCHA")
                if "google-analytics" in body_lower or "gtag" in body_lower:
                    tech.append("Google Analytics")
                if "facebook" in body_lower or "fbq" in body_lower:
                    tech.append("Facebook Pixel")

                result["technologies"] = tech

        except httpx.TimeoutException:
            result["errors"].append("HTTP: timeout")
        except httpx.ConnectError:
            result["errors"].append("HTTP: connection failed")
        except Exception as e:
            result["errors"].append(f"HTTP: {str(e)[:100]}")

    return result


# ═══════════════════════════════════════════════════════════════
# IP SCANNER (real)
# ═══════════════════════════════════════════════════════════════

async def scan_ip(ip: str) -> dict:
    """Full IP analysis — geolocation, ASN, reverse DNS, ports."""
    result = {
        "ip": ip,
        "is_valid": False,
        "version": None,
        "is_private": False,
        "reverse_dns": None,
        "geolocation": None,
        "open_ports": [],
        "errors": [],
    }

    # Validate
    try:
        import ipaddress
        addr = ipaddress.ip_address(ip)
        result["is_valid"] = True
        result["version"] = f"IPv{addr.version}"
        result["is_private"] = addr.is_private
        result["is_loopback"] = addr.is_loopback
        result["is_multicast"] = addr.is_multicast
    except ValueError:
        result["errors"].append("Invalid IP address")
        return result

    if result["is_private"]:
        result["geolocation"] = {"note": "Private IP — no public geolocation"}
        return result

    # Reverse DNS
    try:
        result["reverse_dns"] = socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror):
        pass

    # Geolocation via ip-api.com (free, no key)
    if HAS_HTTPX:
        try:
            async with _client() as client:
                resp = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={"fields": "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,query"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success":
                        result["geolocation"] = {
                            "country": data.get("country"),
                            "country_code": data.get("countryCode"),
                            "region": data.get("regionName"),
                            "city": data.get("city"),
                            "zip": data.get("zip"),
                            "lat": data.get("lat"),
                            "lon": data.get("lon"),
                            "timezone": data.get("timezone"),
                            "isp": data.get("isp"),
                            "org": data.get("org"),
                            "asn": data.get("as"),
                            "asn_name": data.get("asname"),
                        }
                    else:
                        result["errors"].append(f"Geo: {data.get('message', 'unknown error')}")
        except Exception as e:
            result["errors"].append(f"Geolocation: {str(e)[:50]}")

    # Quick port scan (common ports)
    common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 3389, 5432, 5900, 8080, 8443, 27017]
    open_ports = []

    async def check_port(port):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=3
            )
            writer.close()
            await writer.wait_closed()
            return port
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return None

    # Scan ports concurrently (max 10 at a time)
    semaphore = asyncio.Semaphore(10)

    async def bounded_check(port):
        async with semaphore:
            return await check_port(port)

    port_tasks = [bounded_check(p) for p in common_ports]
    port_results = await asyncio.gather(*port_tasks)

    result["open_ports"] = [p for p in port_results if p is not None]
    result["ports_scanned"] = len(common_ports)

    return result


# ═══════════════════════════════════════════════════════════════
# USERNAME SCANNER (real — checks actual sites)
# ═══════════════════════════════════════════════════════════════

# Full platform list with existence detection logic
USERNAME_PLATFORMS = [
    ("GitHub", "https://api.github.com/users/{}", None, lambda r: r.get("id") is not None),
    ("Twitter", "https://twitter.com/{}", None, lambda r: True),
    ("Instagram", "https://www.instagram.com/{}/", None, lambda r: r.status_code == 200),
    ("Reddit", "https://www.reddit.com/user/{}/about.json", None, lambda r: r.get("data", {}).get("name") is not None),
    ("YouTube", "https://www.youtube.com/@{}", None, lambda r: r.status_code == 200),
    ("TikTok", "https://www.tiktok.com/@{}", None, lambda r: r.status_code == 200),
    ("Telegram", "https://t.me/{}", "href", lambda r: "tgme_page_title" in r),
    ("VK", "https://vk.com/{}", None, lambda r: r.status_code == 200 and "404" not in r),
    ("Pinterest", "https://www.pinterest.com/{}/", None, lambda r: r.status_code == 200),
    ("Medium", "https://medium.com/@{}", None, lambda r: r.status_code == 200),
    ("GitLab", "https://gitlab.com/{}", None, lambda r: r.status_code == 200),
    ("Spotify", "https://open.spotify.com/user/{}", None, lambda r: r.status_code == 200),
    ("SoundCloud", "https://soundcloud.com/{}", None, lambda r: r.status_code == 200),
    ("Steam", "https://steamcommunity.com/id/{}", None, lambda r: r.status_code == 200),
    ("Keybase", "https://keybase.io/{}", None, lambda r: r.status_code == 200),
    ("HackerNews", "https://hacker-news.firebaseio.com/v0/user/{}.json", None, lambda r: r.get("id") is not None),
    ("Dribbble", "https://dribbble.com/{}", None, lambda r: r.status_code == 200),
    ("Behance", "https://www.behance.net/{}", None, lambda r: r.status_code == 200),
    ("Flickr", "https://www.flickr.com/people/{}", None, lambda r: r.status_code == 200),
    ("Vimeo", "https://vimeo.com/{}", None, lambda r: r.status_code == 200),
    ("DeviantArt", "https://www.deviantart.com/{}", None, lambda r: r.status_code == 200),
    ("Goodreads", "https://www.goodreads.com/{}", None, lambda r: r.status_code == 200),
    ("Tumblr", "https://{}.tumblr.com/", None, lambda r: r.status_code == 200),
    ("Etsy", "https://www.etsy.com/people/{}", None, lambda r: r.status_code == 200),
    ("Patreon", "https://www.patreon.com/{}", None, lambda r: r.status_code == 200),
    ("Bitbucket", "https://bitbucket.org/{}/", None, lambda r: r.status_code == 200),
    ("Fandom", "https://www.fandom.com/u/{}", None, lambda r: r.status_code == 200),
    ("Wikipedia", "https://en.wikipedia.org/wiki/User:{}", None, lambda r: r.status_code == 200 and "does not have a user page" not in r),
    ("Twitch", "https://www.twitch.tv/{}", None, lambda r: r.status_code == 200),
    ("Snapchat", "https://www.snapchat.com/add/{}", None, lambda r: r.status_code == 200),
    ("Quora", "https://www.quora.com/profile/{}", None, lambda r: r.status_code == 200),
]


async def scan_username(username: str, max_concurrent: int = 10) -> dict:
    """Search username across 30+ platforms with real HTTP checks."""
    result = {
        "username": username,
        "platforms_checked": 0,
        "found": [],
        "not_found": [],
        "errors": [],
        "scan_time_seconds": 0,
    }

    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    start_time = time.time()
    semaphore = asyncio.Semaphore(max_concurrent)

    async def check_platform(name, url_template, response=None, exists_check=None):
        url = url_template.format(username)
        try:
            async with semaphore:
                async with _client() as client:
                    resp = await client.get(url)

                    # Platform-specific checks
                    if name == "GitHub":
                        data = resp.json() if resp.status_code == 200 else {}
                        if data.get("id"):
                            return {
                                "platform": name,
                                "url": f"https://github.com/{username}",
                                "profile_url": data.get("html_url"),
                                "name": data.get("name"),
                                "bio": data.get("bio"),
                                "public_repos": data.get("public_repos"),
                                "followers": data.get("followers"),
                                "following": data.get("following"),
                                "created_at": data.get("created_at"),
                                "company": data.get("company"),
                                "location": data.get("location"),
                                "blog": data.get("blog"),
                                "twitter": data.get("twitter_username"),
                            }
                        return None

                    elif name == "Reddit":
                        data = resp.json() if resp.status_code == 200 else {}
                        if data.get("data", {}).get("name"):
                            rd = data["data"]
                            return {
                                "platform": name,
                                "url": f"https://reddit.com/user/{username}",
                                "name": rd.get("name"),
                                "comment_karma": rd.get("comment_karma"),
                                "link_karma": rd.get("link_karma"),
                                "created_utc": rd.get("created_utc"),
                            }
                        return None

                    elif name == "HackerNews":
                        data = resp.json() if resp.status_code == 200 else {}
                        if data.get("id"):
                            return {
                                "platform": name,
                                "url": f"https://news.ycombinator.com/user?id={username}",
                                "karma": data.get("karma"),
                                "created": data.get("created"),
                            }
                        return None

                    elif name == "Telegram":
                        if "tgme_page_title" in resp.text or "tgme_page_extra" in resp.text:
                            return {
                                "platform": name,
                                "url": url,
                                "status": "found",
                            }
                        return None

                    # Generic check
                    elif resp.status_code == 200:
                        not_found_indicators = [
                            'page not found', '404', 'not found', "doesn't exist",
                            'no such user', 'could not be found', 'unavailable',
                            'this page is not available', 'account suspended',
                            'user not found', 'profile not found',
                        ]
                        body_lower = resp.text.lower()
                        if any(ind in body_lower for ind in not_found_indicators):
                            return None

                        return {
                            "platform": name,
                            "url": url,
                            "status_code": resp.status_code,
                        }

                    return None

        except httpx.TimeoutException:
            return {"platform": name, "error": "timeout"}
        except Exception as e:
            return {"platform": name, "error": str(e)[:50]}

    # Run all checks concurrently
    tasks = [check_platform(name, url) for name, url, _, _ in USERNAME_PLATFORMS]
    raw_results = await asyncio.gather(*tasks)

    for check_result in raw_results:
        if check_result is None:
            continue
        if isinstance(check_result, dict):
            if "error" in check_result:
                result["errors"].append(f"{check_result['platform']}: {check_result['error']}")
            else:
                result["found"].append(check_result)

    result["platforms_checked"] = len(USERNAME_PLATFORMS)
    result["not_found_count"] = len(USERNAME_PLATFORMS) - len(result["found"]) - len(result["errors"])
    result["scan_time_seconds"] = round(time.time() - start_time, 2)

    return result


# ═══════════════════════════════════════════════════════════════
# WAYBACK MACHINE (real)
# ═══════════════════════════════════════════════════════════════

async def scan_wayback(domain_or_url: str, limit: int = 20) -> dict:
    """Query Wayback Machine CDX API."""
    result = {
        "target": domain_or_url,
        "snapshots": [],
        "total_estimated": 0,
        "first_seen": None,
        "last_seen": None,
        "errors": [],
    }

    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    target = domain_or_url
    if not target.startswith("http"):
        target = f"https://{target}"

    try:
        async with _client() as c:
            resp = await c.get(
                "https://web.archive.org/cdx/search/cdx",
                params={
                    "url": target,
                    "output": "json",
                    "limit": limit,
                    "fl": "timestamp,statuscode,original,mimetype,digest,length",
                    "filter": "statuscode:200",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1:
                    headers = data[0]
                    for row in data[1:]:
                        record = dict(zip(headers, row))
                        ts = record.get("timestamp", "")
                        snapshot = {
                            "timestamp": ts,
                            "date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[8:10]}:{ts[10:12]}:{ts[12:14]}" if len(ts) >= 14 else ts,
                            "url": record.get("original", ""),
                            "status": record.get("statuscode"),
                            "mime_type": record.get("mimetype"),
                            "archive_url": f"https://web.archive.org/web/{ts}/{record.get('original', '')}",
                            "size": record.get("length"),
                        }
                        result["snapshots"].append(snapshot)

                    if result["snapshots"]:
                        result["first_seen"] = result["snapshots"][0]["date"]
                        result["last_seen"] = result["snapshots"][-1]["date"]

                # Get total count
                resp2 = await c.get(
                    "https://web.archive.org/cdx/search/cdx",
                    params={
                        "url": target,
                        "output": "json",
                        "limit": 1,
                        "showNumPages": "true",
                    },
                )
                if resp2.status_code == 200:
                    try:
                        total_data = resp2.json()
                        if total_data and len(total_data) > 1:
                            result["total_estimated"] = int(total_data[-1][0]) if total_data[-1] else len(result["snapshots"])
                    except Exception:
                        result["total_estimated"] = len(result["snapshots"])

                # Latest snapshot
                resp3 = await c.get(
                    "https://archive.org/wayback/available",
                    params={"url": target},
                )
                if resp3.status_code == 200:
                    avail = resp3.json()
                    if avail.get("archived_snapshots", {}).get("closest"):
                        result["latest_snapshot"] = avail["archived_snapshots"]["closest"]

            else:
                result["errors"].append(f"HTTP {resp.status_code}")

    except httpx.TimeoutException:
        result["errors"].append("Timeout")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# SHODAN (real API)
# ═══════════════════════════════════════════════════════════════

async def scan_shodan(ip: str = "", domain: str = "") -> dict:
    """Query Shodan API."""
    import os
    result = {"tool": "Shodan", "target": ip or domain, "data": None, "errors": []}

    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    key = os.getenv("SHODAN_API_KEY", "")
    if not key:
        result["error"] = "Set SHODAN_API_KEY env var"
        result["web_url"] = f"https://www.shodan.io/search?query={ip or domain}"
        return result

    try:
        async with _client() as c:
            if ip:
                resp = await c.get(
                    f"https://api.shodan.io/shodan/host/{ip}",
                    params={"key": key, "minify": "false"},
                )
            elif domain:
                resp = await c.get(
                    "https://api.shodan.io/dns/resolve",
                    params={"hostnames": domain, "key": key},
                )
                if resp.status_code == 200:
                    ips = resp.json()
                    if ips:
                        ip = list(ips.values())[0]
                        resp = await c.get(
                            f"https://api.shodan.io/shodan/host/{ip}",
                            params={"key": key},
                        )
                    else:
                        result["error"] = f"Could not resolve {domain}"
                        return result

            if resp.status_code == 200:
                data = resp.json()
                result["data"] = {
                    "ip": data.get("ip_str"),
                    "hostnames": data.get("hostnames", []),
                    "domains": data.get("domains", []),
                    "org": data.get("org"),
                    "isp": data.get("isp"),
                    "asn": data.get("asn"),
                    "country": data.get("country_name"),
                    "city": data.get("city"),
                    "os": data.get("os"),
                    "ports": data.get("ports", []),
                    "vulns": list(data.get("vulns", {}).keys()) if isinstance(data.get("vulns"), dict) else data.get("vulns", []),
                    "tags": data.get("tags", []),
                    "last_update": data.get("last_update"),
                    "services": [
                        {
                            "port": s.get("port"),
                            "transport": s.get("transport"),
                            "product": s.get("product"),
                            "version": s.get("version"),
                            "title": s.get("title", "")[:100] if s.get("title") else None,
                            "data": s.get("data", "")[:200] if s.get("data") else None,
                        }
                        for s in data.get("data", [])
                    ],
                }
            elif resp.status_code == 401:
                result["error"] = "Invalid API key"
            elif resp.status_code == 429:
                result["error"] = "Rate limited"
            else:
                result["error"] = f"HTTP {resp.status_code}"

    except Exception as e:
        result["errors"].append(str(e))

    return result


# ═══════════════════════════════════════════════════════════════
# GHDB — Google Hacking Database
# ═══════════════════════════════════════════════════════════════

def generate_ghdb_queries(domain_or_ip: str, query_type: str = "domain") -> dict:
    """Generate Google Dork queries from GHDB."""
    result = {
        "target": domain_or_ip,
        "type": query_type,
        "categories": {},
    }

    if query_type == "domain":
        d = domain_or_ip
        result["categories"] = {
            "Emails": {
                "queries": [
                    f"site:{d} intext:@ filetype:xls",
                    f"site:{d} intext:@ filetype:csv",
                    f"site:{d} intext:@ filetype:txt",
                    f"site:{d} intext:@ filetype:doc",
                    f"site:linkedin.com intext:\"{d}\"",
                ],
                "description": "Find email addresses associated with domain",
            },
            "Sensitive Files": {
                "queries": [
                    f"site:{d} filetype:pdf",
                    f"site:{d} filetype:doc OR filetype:docx",
                    f"site:{d} filetype:xls OR filetype:xlsx",
                    f"site:{d} filetype:ppt OR filetype:pptx",
                ],
                "description": "Find publicly accessible documents",
            },
            "Config & Backup": {
                "queries": [
                    f"site:{d} filetype:env",
                    f"site:{d} filetype:ini OR filetype:conf OR filetype:cfg",
                    f"site:{d} filetype:bak OR filetype:old OR filetype:backup",
                    f"site:{d} filetype:sql OR filetype:db OR filetype:sqlite",
                    f"site:{d} filetype:log",
                    f"site:{d} filetype:xml OR filetype:json OR filetype:yaml OR filetype:yml",
                ],
                "description": "Find configuration files and backups",
            },
            "Admin & Login": {
                "queries": [
                    f"site:{d} inurl:admin OR inurl:administrator",
                    f"site:{d} inurl:login OR inurl:signin",
                    f"site:{d} inurl:dashboard",
                    f"site:{d} inurl:wp-admin",
                    f"site:{d} inurl:phpmyadmin",
                    f"site:{d} intitle:\"admin\" OR intitle:\"login\"",
                ],
                "description": "Find admin panels and login pages",
            },
            "Database Dumps": {
                "queries": [
                    f"site:{d} filetype:sql",
                    f"site:{d} intext:\"SQL dump\" OR intext:\"Database dump\"",
                    f"site:{d} intext:\"CREATE TABLE\" OR intext:\"INSERT INTO\"",
                ],
                "description": "Find database dumps",
            },
            "Git & Source Code": {
                "queries": [
                    f"site:{d} inurl:.git",
                    f"site:{d} inurl:.svn",
                    f"site:{d} filetype:git OR filetype:svn",
                    f"site:github.com intext:\"{d}\"",
                    f"site:gitlab.com intext:\"{d}\"",
                ],
                "description": "Find exposed source code",
            },
            "Directory Listings": {
                "queries": [
                    f"site:{d} intitle:\"index of\"",
                    f"site:{d} intitle:\"directory listing\"",
                    f"site:{d} \"Parent Directory\"",
                ],
                "description": "Find open directory listings",
            },
            "Vulnerable Pages": {
                "queries": [
                    f"site:{d} inurl:id= OR inurl:pid=",
                    f"site:{d} inurl:redirect OR inurl:return OR inurl:url=",
                    f"site:{d} inurl:cat OR inurl:category",
                    f"site:{d} inurl:search OR inurl:query",
                ],
                "description": "Find potentially vulnerable pages",
            },
            "Error Messages": {
                "queries": [
                    f"site:{d} \"error\" OR \"warning\" OR \"fatal\"",
                    f"site:{d} intext:\"stack trace\"",
                    f"site:{d} intext:\"mysql error\" OR intext:\"sql error\"",
                ],
                "description": "Find error messages revealing info",
            },
        }
    elif query_type == "ip":
        ip = domain_or_ip
        result["categories"] = {
            "Direct": {
                "queries": [
                    f"ip:{ip}",
                    f"\"{ip}\"",
                ],
            },
            "Related": {
                "queries": [
                    f"ip:{ip} filetype:log",
                    f"ip:{ip} filetype:conf",
                    f"\"{ip}\" filetype:env",
                ],
            },
        }

    # Generate Google search URLs
    for category, data in result["categories"].items():
        for i, query in enumerate(data["queries"]):
            data["queries"][i] = {
                "query": query,
                "url": f"https://www.google.com/search?q={quote(query)}",
            }

    return result


# ═══════════════════════════════════════════════════════════════
# GOOGLE EARTH / GEOLOCATION
# ═══════════════════════════════════════════════════════════════

async def scan_geolocation(query: str) -> dict:
    """Get geolocation data and map links."""
    result = {
        "query": query,
        "coordinates": None,
        "map_links": None,
        "geolocation": None,
        "errors": [],
    }

    # Check if query is already coordinates
    coord_match = re.match(r'^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$', query.strip())
    if coord_match:
        lat, lon = float(coord_match.group(1)), float(coord_match.group(2))
        result["coordinates"] = {"lat": lat, "lon": lon}
        if HAS_HTTPX:
            try:
                async with _client() as c:
                    resp = await c.get(
                        f"http://ip-api.com/json/",
                        params={"fields": "status,message,city,regionName,country,zip,lat,lon,timezone,isp,org,as,query"},
                    )
                    if resp.status_code == 200:
                        result["geolocation"] = resp.json()
            except Exception:
                pass
    elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
        # It's an IP
        ip_result = await scan_ip(query)
        result["geolocation"] = ip_result.get("geolocation")

    # Generate map links
    coords = result["coordinates"]
    if coords:
        lat, lon = coords["lat"], coords["lon"]
    elif result.get("geolocation"):
        lat = result["geolocation"].get("lat")
        lon = result["geolocation"].get("lon")
    else:
        lat = lon = None

    if lat and lon:
        result["map_links"] = {
            "google_maps": f"https://www.google.com/maps?q={lat},{lon}",
            "google_maps_streetview": f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}",
            "google_earth": f"https://earth.google.com/web/@{lat},{lon},1000a,35y,0h,0t,0r",
            "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15",
            "bing_maps": f"https://www.bing.com/maps?cp={lat}~{lon}&lvl=15",
            "yandex_maps": f"https://yandex.ru/maps/?ll={lon},{lat}&z=15&l=map",
            "yandex_streetview": f"https://yandex.ru/maps/?ll={lon},{lat}&z=17&l=stv%2Csta",
            "here_maps": f"https://wego.here.com/directions/mix/{lat},{lon}",
            "mapquest": f"https://www.mapquest.com/search/results?query={lat},{lon}",
            "karto_flickr": f"https://www.flickr.com/map/?&fLat={lat}&fLon={lon}&zl=10",
            "geohack": f"https://geohack.toolforge.org/geohack.php?params={lat}_N_{lon}_E",
        }

    return result


# ═══════════════════════════════════════════════════════════════
# UNIVERSAL SEARCH
# ═══════════════════════════════════════════════════════════════

def generate_universal_search(query: str) -> dict:
    """Generate search URLs for multiple engines."""
    encoded = quote(query)
    return {
        "query": query,
        "search_engines": {
            "Google": f"https://www.google.com/search?q={encoded}",
            "Bing": f"https://www.bing.com/search?q={encoded}",
            "DuckDuckGo": f"https://duckduckgo.com/?q={encoded}",
            "Yandex": f"https://yandex.com/search/?text={encoded}",
            "Yahoo": f"https://search.yahoo.com/search?p={encoded}",
            "Startpage": f"https://www.startpage.com/do/dsearch?query={encoded}",
            "Baidu": f"https://www.baidu.com/s?wd={encoded}",
            "Ask": f"https://www.ask.com/web?q={encoded}",
            "AOL": f"https://search.aol.com/aol/search?q={encoded}",
            "Ecosia": f"https://www.ecosia.org/search?q={encoded}",
        },
        "osint_engines": {
            "Shodan": f"https://www.shodan.io/search?query={encoded}",
            "Censys": f"https://search.censys.io/search?q={encoded}",
            "Hunter.io": f"https://hunter.io/search/{encoded}",
            "Wayback Machine": f"https://web.archive.org/web/*/{encoded}",
            "VirusTotal": f"https://www.virustotal.com/gui/search/{encoded}",
            "URLScan": f"https://urlscan.io/search/#\"{encoded}\"",
            "ThreatCrowd": f"https://www.threatcrowd.org/searchApi/v2/ip/report/?ip={encoded}://" + encoded if re.match(r'^\d', query) else "",
            "Intelligence X": f"https://intelx.io/?s={encoded}",
        },
        "social_media": {
            "Google Social": f"https://www.google.com/search?q={encoded}+site:twitter.com+OR+site:facebook.com+OR+site:instagram.com",
            "LinkedIn": f"https://www.google.com/search?q={encoded}+site:linkedin.com",
            "Facebook": f"https://www.facebook.com/search/people/?q={encoded}",
            "Twitter": f"https://twitter.com/search?q={encoded}&f=users",
        },
    }


# ═══════════════════════════════════════════════════════════════
# HASH GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_hashes(text: str) -> dict:
    """Generate multiple hash types."""
    encoded = text.encode('utf-8')
    return {
        "text": text,
        "md5": hashlib.md5(encoded).hexdigest(),
        "sha1": hashlib.sha1(encoded).hexdigest(),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "sha512": hashlib.sha512(encoded).hexdigest(),
        "sha3_256": hashlib.sha3_256(encoded).hexdigest(),
        "blake2b": hashlib.blake2b(encoded).hexdigest(),
        "ntlm": hashlib.new('md4', text.encode('utf-16le')).hexdigest(),
    }


# ═══════════════════════════════════════════════════════════════
# URL ANALYZER
# ═══════════════════════════════════════════════════════════════

async def scan_url(url: str) -> dict:
    """Full URL analysis — headers, tech, security."""
    result = {
        "url": url,
        "parsed": {},
        "status_code": None,
        "final_url": None,
        "headers": {},
        "security_headers": {},
        "technologies": [],
        "cookies": [],
        "meta_tags": {},
        "links": {"internal": [], "external": []},
        "response_time_ms": None,
        "content_length": None,
        "errors": [],
    }

    if not HAS_HTTPX:
        result["error"] = "httpx not installed"
        return result

    # Ensure scheme
    if not url.startswith("http"):
        url = f"https://{url}"

    # Parse
    parsed = urlparse(url)
    result["parsed"] = {
        "scheme": parsed.scheme,
        "domain": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path,
        "query": parsed.query,
        "fragment": parsed.fragment,
        "base_url": f"{parsed.scheme}://{parsed.netloc}",
    }

    try:
        start = time.time()
        async with _client() as client:
            resp = await client.get(url)

        result["response_time_ms"] = int((time.time() - start) * 1000)
        result["status_code"] = resp.status_code
        result["final_url"] = str(resp.url)
        result["content_length"] = len(resp.text)

        # Headers
        for key, val in resp.headers.items():
            result["headers"][key] = val

        # Security headers
        sec_map = {
            "Strict-Transport-Security": "HSTS",
            "Content-Security-Policy": "CSP",
            "X-Frame-Options": "Clickjacking Protection",
            "X-Content-Type-Options": "MIME Sniffing Protection",
            "X-XSS-Protection": "XSS Filter",
            "Referrer-Policy": "Referrer Policy",
            "Permissions-Policy": "Permissions Policy",
        }
        for header, name in sec_map.items():
            val = resp.headers.get(header)
            result["security_headers"][name] = {"present": val is not None, "value": val}

        # Cookies
        for cookie in resp.cookies.jar:
            result["cookies"].append({
                "name": cookie.name,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "http_only": cookie.has_nonstandard_attr("HttpOnly"),
            })

        # Technologies (same detection as domain scanner)
        tech = []
        body = resp.text.lower()
        headers_lower = {k.lower(): v.lower() for k, v in resp.headers.items()}

        if "x-powered-by" in headers_lower:
            tech.append(f"Powered by: {resp.headers['x-powered-by']}")
        server = resp.headers.get("server", "").lower()
        if "nginx" in server: tech.append("Nginx")
        elif "apache" in server: tech.append("Apache")
        elif "cloudflare" in server: tech.append("Cloudflare")
        if "cf-ray" in headers_lower: tech.append("Cloudflare CDN")
        if "wp-content" in body or "wp-includes" in body: tech.append("WordPress")
        if "react" in body or "__next" in body: tech.append("React/Next.js")
        if "vue" in body or "nuxt" in body: tech.append("Vue.js/Nuxt")
        if "angular" in body: tech.append("Angular")
        if "jquery" in body: tech.append("jQuery")
        if "bootstrap" in body: tech.append("Bootstrap")
        if "django" in body: tech.append("Django")
        if "recaptcha" in body: tech.append("reCAPTCHA")
        if "google-analytics" in body or "gtag" in body: tech.append("Google Analytics")
        if "facebook" in body or "fbq" in body: tech.append("Facebook Pixel")
        if "socket.io" in body: tech.append("Socket.io")

        result["technologies"] = tech

        # Extract links
        import re as re2
        links = re2.findall(r'href=["\']([^"\']+)["\']', resp.text)
        base_domain = parsed.hostname
        for link in links[:50]:
            if link.startswith("http"):
                if base_domain in link:
                    result["links"]["internal"].append(link)
                else:
                    result["links"]["external"].append(link)
            elif link.startswith("/"):
                result["links"]["internal"].append(f"{result['parsed']['base_url']}{link}")

    except httpx.TimeoutException:
        result["errors"].append("Timeout")
    except httpx.ConnectError:
        result["errors"].append("Connection failed")
    except Exception as e:
        result["errors"].append(str(e)[:100])

    return result


# ═══════════════════════════════════════════════════════════════
# MASTER SCANNER — Auto-detect + run all applicable
# ═══════════════════════════════════════════════════════════════

async def master_scan(target: str, target_type: str = "auto") -> dict:
    """Auto-detect target type and run all applicable scanners."""
    result = {
        "target": target,
        "target_type": target_type,
        "detected_type": target_type,
        "scanned_at": datetime.utcnow().isoformat(),
        "results": {},
        "errors": [],
    }

    # Auto-detect
    if target_type == "auto":
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', target):
            target_type = "email"
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
            target_type = "ip"
        elif re.match(r'^[\w\.-]+\.\w{2,}$', target):
            target_type = "domain"
        elif target.startswith("http"):
            target_type = "url"
        elif re.match(r'^[\w.-]{3,30}$', target):
            target_type = "username"
        else:
            target_type = "universal"

    result["detected_type"] = target_type

    # Run scanners based on type
    scanners = {
        "email": [("email_analysis", scan_email)],
        "phone": [("phone_analysis", scan_phone)],
        "domain": [
            ("domain_analysis", scan_domain),
            ("username_search", scan_username),
            ("wayback_history", scan_wayback),
            ("ghdb_queries", lambda d: asyncio.coroutine(generate_ghdb_queries)(d)),
        ],
        "ip": [("ip_analysis", scan_ip)],
        "username": [
            ("username_search", scan_username),
            ("wayback_history", lambda u: scan_wayback(u)),
        ],
        "url": [("url_analysis", scan_url)],
        "universal": [("universal_search", lambda q: asyncio.coroutine(generate_universal_search)(q))],
    }

    # Simpler approach — run directly
    try:
        if target_type == "email":
            result["results"]["email_analysis"] = await scan_email(target)
        elif target_type == "phone":
            result["results"]["phone_analysis"] = await scan_phone(target)
        elif target_type == "domain":
            result["results"]["domain_analysis"] = await scan_domain(target)
            result["results"]["wayback_history"] = await scan_wayback(target)
            result["results"]["ghdb_queries"] = generate_ghdb_queries(target)
        elif target_type == "ip":
            result["results"]["ip_analysis"] = await scan_ip(target)
        elif target_type == "username":
            result["results"]["username_search"] = await scan_username(target)
            result["results"]["wayback_history"] = await scan_wayback(target)
        elif target_type == "url":
            result["results"]["url_analysis"] = await scan_url(target)
        else:
            result["results"]["universal_search"] = generate_universal_search(target)
    except Exception as e:
        result["errors"].append(str(e))

    return result
