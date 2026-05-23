"""OsintHAM — OSINT Tools Registry & Integration Hub
Maps all external OSINT tools and provides unified access.
Each tool has: name, category, description, install command, API/config notes.
"""
import os
import json
import shutil
import subprocess
from typing import Optional
from dataclasses import dataclass, field, asdict

@dataclass
class OsintTool:
    name: str
    slug: str
    category: str
    description: str
    url: str
    github: str = ""
    install_cmd: str = ""
    pip_package: str = ""
    npm_package: str = ""
    api_endpoint: str = ""
    requires_key: bool = False
    key_env_var: str = ""
    cli_command: str = ""
    tags: list = field(default_factory=list)
    is_installed: bool = False


# ── Full Tools Registry ──

TOOLS_REGISTRY = [
    # ═══ Username / Social Media Search ═══
    OsintTool(
        name="Sherlock", slug="sherlock",
        category="username_search",
        username="sherlock-project", repo="sherlock",
        description="Hunt down social media accounts by username across 400+ sites",
        url="https://sherlock-project.github.io",
        github="sherlock-project/sherlock",
        pip_package="sherlock-project",
        cli_command="sherlock {target}",
        tags=["username", "social_media", "search"],
    ),
    OsintTool(
        name="Maigret", slug="maigret",
        category="username_search",
        username="soxoj", repo="maigret",
        description="Collect a dossier on a person by username from 1000+ sites",
        url="https://maigret.readthedocs.io",
        github="soxoj/maigret",
        pip_package="maigret",
        cli_command="maigret {target}",
        tags=["username", "social_media", "dossier"],
    ),
    OsintTool(
        name="Holehe", slug="holehe",
        category="username_search",
        username="megadose", repo="holehe",
        description="Check if email is registered on various sites",
        url="",
        github="megadose/holehe",
        pip_package="holehe",
        cli_command="holehe {target}",
        tags=["email", "account_check"],
    ),
    OsintTool(
        name="Osintgram", slug="osintgram",
        category="username_search",
        username="Datalux", repo="Osintgram",
        description="Instagram OSINT tool — collect account info, followers, tags",
        url="",
        github="Datalux/Osintgram",
        cli_command="python main.py {target}",
        tags=["instagram", "social_media"],
    ),
    OsintTool(
        name="X-osint", slug="x-osint",
        category="username_search",
        username="TermuxHackz", repo="X-osint",
        description="Twitter/X OSINT tool for profile analysis",
        url="",
        github="TermuxHackz/X-osint",
        tags=["twitter", "x", "social_media"],
    ),
    OsintTool(
        name="OSS Bot (Sherlock)", slug="oss-bot",
        category="username_search",
        description="Telegram bot for username search (Sherlock-based)",
        url="",
        github="cat228608/OpenSoucesSearcherUsername",
        tags=["telegram", "bot", "username"],
    ),

    # ═══ Email & Breach Search ═══
    OsintTool(
        name="Have I Been Pwned", slug="hibp",
        category="breach_search",
        description="Check if email/data appears in known data breaches",
        url="https://haveibeenpwned.com",
        api_endpoint="https://haveibeenpwned.com/api/v3/",
        requires_key=True,
        key_env_var="HIBP_API_KEY",
        tags=["breach", "email", "passwords"],
    ),
    OsintTool(
        name="LeakCheck Bot", slug="leakcheck",
        category="breach_search",
        description="Telegram bot for searching leaked credentials",
        url="https://wiki.leakcheck.io",
        tags=["telegram", "bot", "leaks", "credentials"],
    ),
    OsintTool(
        name="BreachHound", slug="breachhound",
        category="breach_search",
        description="Breach data analysis tool",
        url="",
        github="hashangit/breachhound",
        npm_package="breachhound",
        tags=["breach", "analysis"],
    ),

    # ═══ DNS & Network Recon ═══
    OsintTool(
        name="DNSDumpster", slug="dnsdumpster",
        category="dns_recon",
        description="Domain DNS reconnaissance — maps DNS records visually",
        url="https://dnsdumpster.com",
        tags=["dns", "visual", "recon"],
    ),
    OsintTool(
        name="Shodan", slug="shodan",
        category="dns_recon",
        description="Search engine for internet-connected devices & services",
        url="https://shodan.io",
        api_endpoint="https://api.shodan.io/",
        requires_key=True,
        key_env_var="SHODAN_API_KEY",
        pip_package="shodan",
        cli_command="shodan host {target}",
        tags=["iot", "devices", "ports", "banner"],
    ),
    OsintTool(
        name="Censys", slug="censys",
        category="dns_recon",
        description="Internet infrastructure intelligence — certs, hosts, services",
        url="https://censys.io",
        api_endpoint="https://search.censys.io/api",
        requires_key=True,
        key_env_var="CENSYS_API_ID",
        pip_package="censys",
        tags=["certificates", "hosts", "infrastructure"],
    ),
    OsintTool(
        name="ExifTool", slug="exiftool",
        category="dns_recon",
        description="Read, write, edit metadata in files (images, PDFs, etc.)",
        url="https://exiftool.org",
        cli_command="exiftool {target}",
        tags=["metadata", "images", "files"],
    ),

    # ═══ Web & URL Analysis ═══
    OsintTool(
        name="Wayback Machine", slug="wayback",
        category="web_analysis",
        description="Access archived versions of websites",
        url="https://web.archive.org",
        api_endpoint="https://archive.org/wayback/available",
        pip_package="waybackpy",
        tags=["archive", "history", "web"],
    ),
    OsintTool(
        name="Google Earth", slug="google_earth",
        category="web_analysis",
        description="Satellite imagery and geospatial analysis",
        url="https://earth.google.com",
        tags=["geospatial", "satellite", "mapping"],
    ),
    OsintTool(
        name="GHDB", slug="ghdb",
        category="web_analysis",
        description="Google Hacking Database — advanced search queries (dorks)",
        url="https://exploit-db.com/google-hacking-database",
        tags=["google", "dorks", "search_operators"],
    ),

    # ═══ OSINT Frameworks & Dashboards ═══
    OsintTool(
        name="OSINT Framework", slug="osint_framework",
        category="framework",
        description="Collection of OSINT tools organized by category",
        url="https://osintframework.com",
        github="lockfale/OSINT-Framework",
        tags=["directory", "reference", "collection"],
    ),
    OsintTool(
        name="SpiderFoot", slug="spiderfoot",
        category="framework",
        description="Automated OSINT collection — 200+ integrations",
        url="https://spiderfoot.net",
        github="smicallef/spiderfoot",
        pip_package="spiderfoot",
        cli_command="python3 sf.py -l 127.0.0.1:5001",
        tags=["automation", "framework", "scanning"],
    ),
    OsintTool(
        name="Recon-ng", slug="recon_ng",
        category="framework",
        description="Web reconnaissance framework (Metasploit-style)",
        url="https://github.com/lanmaster53/recon-ng",
        github="lanmaster53/recon-ng",
        tags=["recon", "framework", "web"],
    ),
    OsintTool(
        name="theHarvester", slug="theharvester",
        category="framework",
        description="Emails, subdomains, IPs, URLs reconnaissance",
        url="",
        github="laramies/theHarvester",
        cli_command="theHarvester -d {target} -b all",
        tags=["emails", "subdomains", "harvesting"],
    ),
    OsintTool(
        name="Maltego", slug="maltego",
        category="framework",
        description="Visual link analysis & data mining (Community edition free)",
        url="https://maltego.com",
        tags=["visual", "link_analysis", "graph"],
    ),
    OsintTool(
        name="Intel-Scan", slug="intel_scan",
        category="framework",
        description="Comprehensive OSINT scanning toolkit",
        url="",
        github="mizazhaider-ceh/Intel-Scan",
        tags=["scanning", "comprehensive"],
    ),
    OsintTool(
        name="OSINTel Dashboard", slug="osintel",
        category="framework",
        description="OSINT web dashboard with multiple tool integrations",
        url="",
        github="aenoshrajora/OSINTel-Dashboard",
        tags=["dashboard", "web", "multi_tool"],
    ),
    OsintTool(
        name="Osint-ToolKit-Web", slug="osint_toolkit_web",
        category="framework",
        description="Web-based OSINT toolkit with multiple scanners",
        url="",
        github="parthxd3/Osint-ToolKit-Web",
        tags=["web", "toolkit", "scanners"],
    ),
    OsintTool(
        name="OSINT_V2 Toolkit", slug="osint_v2",
        category="framework",
        description="Advanced OSINT toolkit v2",
        url="",
        github="DotX-47/OSINT-V2",
        tags=["toolkit", "advanced"],
    ),

    # ═══ Telegram Bots ═══
    OsintTool(
        name="TeleSINT Bot", slug="telesint",
        category="telegram_bot",
        description="Telegram bot for Telegram-specific OSINT",
        url="https://t.me/TeleSINT_Bot",
        tags=["telegram", "bot", "messenger"],
    ),
    OsintTool(
        name="PRObivon Bot", slug="probivon",
        category="telegram_bot",
        description="Telegram bot for phone/email/name search",
        url="",
        tags=["telegram", "bot", "phone", "email"],
    ),
    OsintTool(
        name="unamer_search_bot", slug="unamer",
        category="telegram_bot",
        description="Telegram username search bot",
        url="",
        tags=["telegram", "bot", "username"],
    ),
    OsintTool(
        name="UniversalSearchBot", slug="universal_search",
        category="telegram_bot",
        description="Universal Telegram search bot",
        url="",
        tags=["telegram", "bot", "search"],
    ),
    OsintTool(
        name="UsersBox", slug="usersbox",
        category="telegram_bot",
        description="Telegram bot for user/phone/email search",
        url="",
        tags=["usersbox-tg", "telegram", "bot"],
    ),
    OsintTool(
        name="Глаз Бога / Шерлок", slug="glaz_boga",
        category="telegram_bot",
        description="Telegram bot — all-in-one OSINT (RU)",
        url="",
        tags=["telegram", "bot", "russian", "phone"],
    ),

    # ═══ Search Engines & Intelligence ═══
    OsintTool(
        name="Intelligence X", slug="intelx",
        category="search_engine",
        description="Independent search engine for Tor, I2P, leaks, domains, emails",
        url="https://intelx.io",
        api_endpoint="https://2.intelx.io/",
        requires_key=True,
        key_env_var="INTELX_API_KEY",
        tags=["search", "leaks", "tor", "darknet"],
    ),
    OsintTool(
        name="Snoop Project", slug="snoop",
        category="search_engine",
        description="Username search across Russian social networks",
        url="https://myseldon.com",
        github="snooppr/snoop",
        tags=["username", "russian", "social_media"],
    ),
    OsintTool(
        name="Infoooze", slug="infoooze",
        category="search_engine",
        description="Node.js OSINT tool — IP, domain, email, phone lookup",
        url="",
        github="devxprite/infoooze",
        npm_package="infoooze",
        tags=["nodejs", "multi_purpose"],
    ),

    # ═══ Face / Image Search ═══
    OsintTool(
        name="PimEyes", slug="pimeyes",
        category="face_search",
        description="Face search engine — find photos by face across the web",
        url="https://pimeyes.com",
        tags=["face", "biometric", "image_search"],
    ),

    # ═══ Regional / Specialized ═══
    OsintTool(
        name="Odnoklassniki Checker", slug="ok_checker",
        category="regional",
        description="OSINT tool for Russian social network Odnoklassniki",
        url="",
        github="OSINT-mindset/odnoklassniki-checker",
        tags=["odnoklassniki", "russian", "social_media"],
    ),
    OsintTool(
        name="OSINTvk", slug="osintvk",
        category="regional",
        description="VKontakte OSINT tool",
        url="",
        github="AdrianGuretto/OSINTvk",
        tags=["vk", "russian", "social_media"],
    ),
    OsintTool(
        name="OSINT-SAN Framework", slug="osint_san",
        category="regional",
        description="Russian OSINT framework (osintsan.ru)",
        url="https://osintsan.ru",
        github="Bafomet666/OSINT-SAN",
        tags=["russian", "framework", "comprehensive"],
    ),
    OsintTool(
        name="OSINT-Tools-Russia", slug="osint_russia",
        category="regional",
        description="Collection of Russian-focused OSINT tools",
        url="",
        github="paulpogoda/OSINT-Tools-Russia",
        tags=["russian", "collection", "tools"],
    ),
    OsintTool(
        name="CreepyEYE Genesis", slug="creepyeye",
        category="regional",
        description="Geolocation OSINT tool — Instagram, Twitter, Facebook",
        url="",
        github="CreepyHunterX/CreepyEYE-Genesis",
        tags=["geolocation", "social_media"],
    ),

    # ═══ Packages / Libraries ═══
    OsintTool(
        name="Osintplus", slug="osintplus",
        category="library",
        description="Python OSINT library with multiple modules",
        url="",
        github="hakersgenie/osintplus",
        pip_package="osintplus",
        tags=["python", "library"],
    ),
    OsintTool(
        name="Osixr", slug="osixr",
        category="library",
        description="Python OSINT reconnaissance library",
        url="",
        github="DevZ44d/Osixr",
        pip_package="osixr",
        tags=["python", "recon"],
    ),
    OsintTool(
        name="js-recon", slug="js_recon",
        category="library",
        description="JavaScript OSINT reconnaissance framework",
        url="https://js-recon.io",
        github="shriyanss/js-recon",
        npm_package="js-recon",
        tags=["javascript", "recon"],
    ),
    OsintTool(
        name="BlackTrace", slug="blacktrace",
        category="library",
        description="OSINT tracing and tracking tool",
        url="",
        github="fawadqureshi007/BlackTrace",
        tags=["tracing", "tracking"],
    ),
    OsintTool(
        name="WEREWIKS", slug="werewiks",
        category="library",
        description="Wikipedia/Wikidata OSINT tool",
        url="",
        github="krokykode/WEREWIKS",
        tags=["wikipedia", "wikidata"],
    ),
    OsintTool(
        name="Anastasis", slug="anastasis",
        category="library",
        description="Digital forensics and OSINT toolkit",
        url="",
        github="0xazanul/Anastasis",
        npm_package="anastasis",
        tags=["forensics", "toolkit"],
    ),
    OsintTool(
        name="Awesome OSINT", slug="awesome_osint",
        category="library",
        description="Curated list of OSINT tools and resources",
        url="",
        github="jivoi/awesome-osint",
        tags=["reference", "curated", "list"],
    ),
    OsintTool(
        name="OSINT-Angel Framework", slug="osint_angel",
        category="telegram_bot",
        description="Telegram-based OSINT framework bot",
        url="",
        github="DarkAngelbot/OSINT-Telegram",
        tags=["telegram", "bot", "framework"],
    ),
]


class ToolsRegistry:
    """Manages the OSINT tools registry — search, filter, get info."""

    def __init__(self):
        self.tools = {t.slug: t for t in TOOLS_REGISTRY}
        self.categories = self._build_categories()

    def _build_categories(self) -> dict:
        cats = {}
        for t in TOOLS_REGISTRY:
            cats.setdefault(t.category, []).append(t.slug)
        return cats

    def get_all(self) -> list:
        return [asdict(t) for t in TOOLS_REGISTRY]

    def get_by_slug(self, slug: str) -> Optional[dict]:
        t = self.tools.get(slug)
        return asdict(t) if t else None

    def get_by_category(self, category: str) -> list:
        slugs = self.categories.get(category, [])
        return [asdict(self.tools[s]) for s in slugs if s in self.tools]

    def search(self, query: str) -> list:
        q = query.lower()
        results = []
        for t in TOOLS_REGISTRY:
            searchable = f"{t.name} {t.description} {' '.join(t.tags)}".lower()
            if q in searchable:
                results.append(asdict(t))
        return results

    def get_categories(self) -> dict:
        return {cat: len(slugs) for cat, slugs in self.categories.items()}

    def check_tool_installed(self, slug: str) -> bool:
        """Check if a CLI tool is installed."""
        t = self.tools.get(slug)
        if not t or not t.cli_command:
            return False
        cmd = t.cli_command.split()[0]
        return shutil.which(cmd) is not None

    def get_install_guide(self, slug: str) -> str:
        """Get installation guide for a tool."""
        t = self.tools.get(slug)
        if not t:
            return "Tool not found."

        guide = f"=== {t.name} ===\n"
        guide += f"Description: {t.description}\n"
        guide += f"URL: {t.url}\n" if t.url else ""
        guide += f"GitHub: {t.github}\n" if t.github else ""

        if t.pip_package:
            guide += f"\nInstall via pip:\n  pip install {t.pip_package}\n"
        if t.npm_package:
            guide += f"\nInstall via npm:\n  npm install -g {t.npm_package}\n"
        if t.github and not t.pip_package and not t.npm_package:
            guide += f"\nInstall from source:\n  git clone https://github.com/{t.github}.git\n  cd {t.github.split('/')[-1]}\n  pip install -r requirements.txt\n"

        if t.requires_key and t.key_env_var:
            guide += f"\n⚠️ Requires API key:\n  export {t.key_env_var}=your_key_here\n"

        if t.cli_command:
            guide += f"\nUsage:\n  {t.cli_command}\n"

        return guide


# ── Module-level singleton ──
registry = ToolsRegistry()
