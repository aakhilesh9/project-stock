import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
from rapidfuzz.fuzz import ratio
from dateutil import parser as dateparser

STOCKS_FILE = "stocks.json"

# Default stocks loaded if stocks.json does not exist yet
DEFAULT_STOCKS = {
    "ANGELONE":   {"name": "Angel One",              "ticker": "ANGELONE.NS"},
    "ASIANPAINT": {"name": "Asian Paints",            "ticker": "ASIANPAINT.NS"},
    "BAJAJFINANCE":{"name": "Bajaj Finance",          "ticker": "BAJFINANCE.NS"},
    "COALINDIA":  {"name": "Coal India",              "ticker": "COALINDIA.NS"},
    "DIVISLAB":   {"name": "Divi's Laboratories",     "ticker": "DIVISLAB.NS"},
    "DIXON":      {"name": "Dixon Technologies",      "ticker": "DIXON.NS"},
    "EPIGRAL":    {"name": "Epigral",                 "ticker": "EPIGRAL.NS"},
    "FCL":        {"name": "Fineotex Chemical",       "ticker": "FCL.NS"},
    "GAIL":       {"name": "GAIL India",              "ticker": "GAIL.NS"},
    "HDBFS":      {"name": "HDB Financial Services",  "ticker": "HDBFS.NS"},
    "HDFC BANK":  {"name": "HDFC Bank",               "ticker": "HDFCBANK.NS"},
    "ICICI BANK": {"name": "ICICI Bank",              "ticker": "ICICIBANK.NS"},
    "INFOSYS":    {"name": "Infosys",                 "ticker": "INFY.NS"},
    "ITC":        {"name": "ITC",                     "ticker": "ITC.NS"},
    "KIRLOSENG":  {"name": "Kirloskar Oil Engines",   "ticker": "KIRLOSENG.NS"},
    "KOTAKBANK":  {"name": "Kotak Mahindra Bank",     "ticker": "KOTAKBANK.NS"},
    "LAURUSLABS": {"name": "Laurus Labs",             "ticker": "LAURUSLABS.NS"},
    "MANKIND":    {"name": "Mankind Pharma",          "ticker": "MANKIND.NS"},
    "MARICO":     {"name": "Marico",                  "ticker": "MARICO.NS"},
    "NTPC":       {"name": "NTPC",                    "ticker": "NTPC.NS"},
    "PETRONET":   {"name": "Petronet LNG",            "ticker": "PETRONET.NS"},
    "PFC":        {"name": "Power Finance Corporation","ticker": "PFC.NS"},
    "PIIND":      {"name": "PI Industries",           "ticker": "PIIND.NS"},
    "POLYCAB":    {"name": "Polycab India",           "ticker": "POLYCAB.NS"},
    "POONAWALLA": {"name": "Poonawalla Fincorp",      "ticker": "POONAWALLA.NS"},
    "RELIANCE":   {"name": "Reliance Industries",     "ticker": "RELIANCE.NS"},
    "SBIN":       {"name": "State Bank of India",     "ticker": "SBIN.NS"},
    "STYLAMIND":  {"name": "Stylam Industries",       "ticker": "STYLAMIND.NS"},
    "TCS":        {"name": "Tata Consultancy Services","ticker": "TCS.NS"},
    "TMPV":       {"name": "Tata Motors PV",          "ticker": "TMPV.NS"},
    "TMCV":       {"name": "Tata Motors CV",          "ticker": "TMCV.NS"},
    "TRIVENI":    {"name": "Triveni Engineering",     "ticker": "TRIVENI.NS"},
    "VBL":        {"name": "Varun Beverages",         "ticker": "VBL.NS"},
    "ZENTEC":     {"name": "Zen Technologies",        "ticker": "ZENTEC.NS"},
}


# ----------- PERSISTENT STOCK STORAGE -----------

def load_stocks():
    """Load stock list from stocks.json; create it with defaults if missing."""
    if not os.path.exists(STOCKS_FILE):
        save_stocks(DEFAULT_STOCKS)
        return dict(DEFAULT_STOCKS)
    try:
        with open(STOCKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("stocks.json must be a JSON object")
        return data
    except Exception as e:
        print(f"  Warning: Could not read {STOCKS_FILE} ({e}). Using defaults.")
        return dict(DEFAULT_STOCKS)


def save_stocks(stocks_dict):
    """Persist the stock dict to stocks.json."""
    try:
        with open(STOCKS_FILE, "w", encoding="utf-8") as f:
            json.dump(stocks_dict, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  Warning: Could not write {STOCKS_FILE}: {e}")


def add_stock(name, ticker, stocks_dict):
    """
    Validate and add a new stock entry.

    Returns (True, key) on success or (False, error_message) on failure.
    The yfinance ticker symbol is derived from the user-supplied ticker by
    appending '.NS' if no exchange suffix is present.
    """
    name = name.strip()
    ticker = ticker.strip().upper()

    # --- Input validation ---
    if not name:
        return False, "Company name cannot be empty."
    if not ticker:
        return False, "Ticker symbol cannot be empty."

    # Normalise: add .NS suffix for NSE stocks if not already qualified
    yf_ticker = ticker if "." in ticker else f"{ticker}.NS"

    # Duplicate check (case-insensitive key comparison)
    existing_keys = {k.upper() for k in stocks_dict}
    if ticker in existing_keys:
        return False, f"Ticker '{ticker}' already exists in the stock list."

    # Verify the ticker resolves to real data via yfinance
    try:
        t = yf.Ticker(yf_ticker)
        hist = t.history(period="1d")
        if hist.empty:
            return False, f"Ticker '{yf_ticker}' returned no price data. Please verify the symbol."
    except Exception as e:
        return False, f"Could not validate ticker '{yf_ticker}': {e}"

    # Add to dict and persist
    stocks_dict[ticker] = {"name": name, "ticker": yf_ticker}
    save_stocks(stocks_dict)
    return True, ticker


# Load the working stock list at module level so the rest of the script can use it
STOCKS_DATA = load_stocks()

# Flat list of stock keys (used wherever the original STOCKS list was used)
STOCKS = list(STOCKS_DATA.keys())

# ----------- RSS SOURCES (PRIORITY ORDER) -----------
RSS_SOURCES = [
    ("Google News", "GOOGLE_NEWS"),
    ("BusinessLine companies", "https://www.thehindubusinessline.com/companies/feeder/default.rss"),
    ("BusinessLine Home", "https://www.thehindubusinessline.com/feeder/default.rss"),
    ("BusinessLine News", "https://www.thehindubusinessline.com/news/feeder/default.rss"),
    ("BusinessLine Stocks", "https://www.thehindubusinessline.com/markets/stock-markets/feeder/default.rss"),
    ("BusinessLine markets", "https://www.thehindubusinessline.com/markets/feeder/default.rss"),
    ("BusinessLine Fundamentals", "https://www.thehindubusinessline.com/portfolio/stock-fundamental-analysis-india/feeder/default.rss"),
    ("BusinessLine Technicals", "https://www.thehindubusinessline.com/portfolio/technical-analysis/feeder/default.rss"),
    ("FE companies", "https://www.financialexpress.com/industry/companies/feed/"),
    ("Financial Express", "https://www.financialexpress.com/feed/"),
    ("FE Indian markets", "https://www.financialexpress.com/markets/indian-markets/feed/"),
    ("FE Markets", "https://www.financialexpress.com/markets/feed/"),
    ("BL Markets", "https://www.thehindubusinessline.com/markets/feeder/default.rss"),
    ("BS companies", "https://www.business-standard.com/rss/companies-101.rss"),
    ("BS Results", "https://www.business-standard.com/rss/companies/quarterly-results-10103.rss"),
    ("BS markets", "https://www.business-standard.com/rss/markets-106.rss"),
    ("BS Top", "https://www.business-standard.com/rss/home_page_top_stories.rss"),
    ("BS Finance", "https://www.business-standard.com/rss/finance/news-10301.rss"),
    ("Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
    ("ET companies", "https://economictimes.indiatimes.com/news/company/rssfeeds/2143429.cms"),
    ("ET Markets", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Mint Companies", "https://www.livemint.com/rss/companies"),
    ("Mint Markets", "https://www.livemint.com/rss/markets"),
    ("Mint News","https://www.livemint.com/rss/news")
]

SIMILARITY_THRESHOLD = 70
MAX_NEWS = 7
DAYS_LIMIT = 7

STOCK_KEYWORDS = {
    "ANGELONE": ["angel one", "angelone", "angel broking"],
    
    "ASIANPAINT": ["asianpain","asian paints", "Asian paint stock", "asian paints share"],
    
    "BAJAJFINANCE": ["bajajfinance","bajaj finance", "BAJAJFINANCE stock"],
    
    "COALINDIA": ["coal india", "Coal India stock", "coal india limited"],
    
    "DIVISLAB": ["divi's", "divis", "divi's labs", "divis labs", "divis laboratories", "divis labs stock", "divis labs share"],
    
    "DIXON": ["dixon","dixon technologies", "dixon tech"],
    
    "EPIGRAL": ["epigral", "epigral ltd"],
    
    "FCL": ["fineotex", "fineotex chemical", "fineotex share"],
    
    "GAIL": ["gail", "gail india", "Gas authority of India"],
    
    "HDBFS":["hdbfs","HDB Financial", "hdfc financial"],

    "HDFC BANK": ["hdfc bank", "hdfc"],
    
    "ICICI BANK": ["icici bank", "icici"],
    
    "INFOSYS": ["infosys", "infy"],
    
    "ITC": ["itc", "itc stock","itc share"],
    
    "KIRLOSENG": ["kirloseng","kirloskar oil", "kirloskar oil engines"],
    
    "KOTAKBANK": ["kotakbank","kotak bank", "kotak mahindra bank", "kotak"],
    
    "LAURUSLABS": ["laurus labs", "laurus", "lauruslabs"],
    
    "MANKIND": ["mankind pharma", "mankind"],
    
    "MARICO": ["marico"],
    
    "NTPC": ["ntpc"],
    
    "PETRONET": ["petronet lng", "petronet"],
    
    "PFC": ["power finance corporation", "pfc"],
    
    "PIIND": ["P I industries","pi industries", "pi ind"],
    
    "POLYCAB": ["polycab"],
    
    "POONAWALLA": ["poonawalla fincorp", "poonawalla"],
    
    "RELIANCE": ["reliance", "ril", "mukesh ambani"],
    
    "SBIN": ["sbin", "state bank of india"],
    
    "STYLAMIND": ["stylamind","stylam industries", "stylam"],
    
    "TCS": ["tcs", "tata consultancy services"],
    
    "TMPV":["Tata motors", "TPMV"],

    "TMCV": ["Tata motors", "TMCV"],

    "TRIVENI": ["triveni engg", "triveni engineering"],
    
    "VBL": ["varun beverages", "vbl"],
    
    "ZENTEC": ["zen technologies", "zen tech", "zentech", "zentec", "zentec.ns", "ZEN Technologies Ltd"]
}

# ----------- PRICE FETCH -----------
def get_stock_data(stock):
    # Look up the yfinance ticker from the loaded stock data; fall back gracefully
    entry = STOCKS_DATA.get(stock)
    if not entry:
        return None
    yf_ticker = entry.get("ticker")
    if not yf_ticker:
        return None

    try:
        data = yf.Ticker(yf_ticker)

        # Fetch multiple periods
        hist_1d = data.history(period="1d")
        hist_1mo = data.history(period="1mo")
        hist_3mo = data.history(period="3mo")

        if hist_1d.empty or hist_1mo.empty:
            return None

        # --- Current price ---
        close = hist_1d["Close"].iloc[-1]
        open_ = hist_1d["Open"].iloc[-1]

        daily_change = ((close - open_) / open_) * 100

        # --- Weekly change (last 5 trading days) ---
        if len(hist_1mo) >= 5:
            week_ago = hist_1mo["Close"].iloc[-5]
            weekly_change = ((close - week_ago) / week_ago) * 100
        else:
            weekly_change = None

        # --- Monthly change (last ~21 trading days) ---
        if len(hist_3mo) >= 21:
            month_ago = hist_3mo["Close"].iloc[-21]
            monthly_change = ((close - month_ago) / month_ago) * 100
        else:
            monthly_change = None

        return {
            "price": round(close, 2),
            "daily": round(daily_change, 2),
            "weekly": round(weekly_change, 2) if weekly_change else None,
            "monthly": round(monthly_change, 2) if monthly_change else None
        }

    except Exception as e:
        return None


# ----------- NEWS HELPERS -----------

def get_google_news_rss(stock):
    query = quote_plus(f"{stock} stock")
    return f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


def parse_date(entry):
    try:
        if hasattr(entry, "published"):
            return dateparser.parse(entry.published)
        elif hasattr(entry, "updated"):
            return dateparser.parse(entry.updated)
    except:
        return None
    return None


def is_recent(dt, now):
    return dt and dt >= (now - timedelta(days=DAYS_LIMIT))


def is_duplicate(title, existing_titles):
    for t in existing_titles:
        if ratio(title.lower(), t.lower()) >= SIMILARITY_THRESHOLD:
            return True
    return False

# ----------- RELEVANCE FILTER -----------

import re

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)   # remove punctuation
    text = text.replace(" ", "")              # remove spaces
    return text


def is_relevant_to_stock(title, stock):
    title_norm = normalize(title)

    # Use manually curated keywords when available; otherwise derive from stored name/ticker
    if stock in STOCK_KEYWORDS:
        keywords = STOCK_KEYWORDS[stock]
    else:
        entry = STOCKS_DATA.get(stock, {})
        keywords = [entry.get("name", stock), stock]

    for kw in keywords:
        if normalize(kw) in title_norm:
            return True

    return False

# ----------- NEWS FETCH -----------

def fetch_news(stock, global_seen_titles):
    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    collected = []
    titles = []

    for source_name, source_url in RSS_SOURCES:
        if len(collected) >= MAX_NEWS:
            break

        url = get_google_news_rss(stock) if source_url == "GOOGLE_NEWS" else source_url

        try:
            feed = feedparser.parse(url)
        except:
            continue

        for entry in feed.entries:
            if len(collected) >= MAX_NEWS:
                break

            raw_title = entry.title.strip()
            title = raw_title.encode("utf-8", errors="replace").decode("utf-8")
            # ---- RELEVANCE FILTER ----
            if not is_relevant_to_stock(title, stock):
                continue

            dt = parse_date(entry)
            if not dt:
                continue

            dt = dt.astimezone(ZoneInfo("Asia/Kolkata"))

            if not is_recent(dt, now):
                continue

            # Local duplicate
            if is_duplicate(title, titles):
                continue

            # Global duplicate (across stocks)
            if is_duplicate(title, global_seen_titles):
                continue

            titles.append(title)
            global_seen_titles.append(title)

            collected.append({
                "title": title,
                "link": entry.link.encode("utf-8", errors="replace").decode("utf-8"),
                "date": dt,
                "source": source_name
            })

    collected.sort(key=lambda x: x["date"], reverse=True)
    return collected


# ----------- HTML -----------

def generate_html(all_data, stocks_data):
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%d %b %Y %I:%M %p')

    # Read repo identity from environment (set by GitHub Actions)
    gh_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    gh_repo_full = os.environ.get("GITHUB_REPOSITORY", "/")   # "owner/repo"
    gh_repo = gh_repo_full.split("/", 1)[-1] if "/" in gh_repo_full else gh_repo_full

    # Embed current stocks as JSON so the browser JS can diff and update
    stocks_json_embedded = json.dumps(stocks_data, ensure_ascii=False)

    html = f"""
    <html>
    <head>

    <link rel="manifest" href="manifest.json">

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Stock News</title>

    <style>
    :root {{
        --bg: #0f172a;
        --text: #e2e8f0;
        --card: #1e293b;
        --muted: #94a3b8;
        --accent: #38bdf8;
        --border: #334155;
    }}

    <script>
    let deferredPrompt;

    window.addEventListener('beforeinstallprompt', (e) => {{
        e.preventDefault();
        deferredPrompt = e;
        document.getElementById("installBtn").style.display = "block";
    }});

    document.getElementById("installBtn").onclick = async () => {{
        if (deferredPrompt) {{
            deferredPrompt.prompt();
            deferredPrompt = null;
        }}
    }};
    </script>

    .price div {{
    margin-top: 4px;
    font-weight: normal;
    }}

    body.light {{
        --bg: #f5f5f5;
        --text: #1e293b;
        --card: #ffffff;
        --muted: #555;
        --accent: #2563eb;
        --border: #ddd;
    }}

    body {{
        font-family: sans-serif;
        margin: 0;
        background: var(--bg);
        color: var(--text);
    }}

    .container {{
        max-width: 1100px;
        margin: auto;
        padding: 10px;
    }}

    .header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    button {{
        background: var(--card);
        color: var(--text);
        border: 1px solid var(--border);
        padding: 6px 12px;
        border-radius: 8px;
        cursor: pointer;
    }}

    .updated {{
        text-align: center;
        color: var(--muted);
        margin: 10px 0 25px;
    }}

    .stock {{
        margin-bottom: 35px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 20px;
        border-left: 4px solid transparent;
        padding-left: 14px;
        border-radius: 4px;
        transition: border-color 0.2s;
    }}

    .stock.trend-up {{
        border-left-color: #22c55e;
    }}

    .stock.trend-down {{
        border-left-color: #ef4444;
    }}

    .stock.trend-neutral {{
        border-left-color: #94a3b8;
    }}

    .stock-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}

    .stock h2 {{
        margin: 0;
    }}

    .price {{
        font-weight: bold;
    }}

    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 15px;
    }}

    .card {{
        background: var(--card);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid var(--border);
        transition: 0.2s;
    }}

    .card:hover {{
        transform: translateY(-3px);
    }}

    .card a {{
        color: var(--text);
        text-decoration: none;
        font-weight: 500;
    }}

    .card a:hover {{
        color: var(--accent);
    }}

    .time {{
        font-size: 12px;
        color: var(--muted);
        margin-top: 6px;
    }}

    .source {{
        font-size: 11px;
        background: var(--accent);
        color: white;
        padding: 2px 6px;
        border-radius: 6px;
        margin-left: 6px;
    }}

    .empty {{
        color: var(--muted);
        font-size: 14px;
    }}

    /* ---- SUMMARY TABLE ---- */
    .summary-table-wrap {{
        overflow-x: auto;
        margin-bottom: 35px;
    }}

    .summary-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    }}

    .summary-table thead tr {{
        background: var(--accent);
        color: #fff;
        text-align: center;
        letter-spacing: 0.04em;
        font-size: 13px;
        text-transform: uppercase;
    }}

    .summary-table thead th {{
        padding: 10px 14px;
        white-space: nowrap;
        cursor: default;
    }}

    .summary-table thead th.sortable {{
        cursor: pointer;
        user-select: none;
    }}

    .summary-table thead th.sortable:hover {{
        background: rgba(255,255,255,0.15);
    }}

    .summary-table thead th .sort-icon {{
        display: inline-block;
        margin-left: 5px;
        opacity: 0.4;
        font-size: 11px;
        transition: opacity 0.15s;
    }}

    .summary-table thead th.sort-asc .sort-icon,
    .summary-table thead th.sort-desc .sort-icon {{
        opacity: 1;
    }}

    .summary-table tbody tr {{
        border-bottom: 1px solid var(--border);
        transition: background 0.15s;
    }}

    .summary-table tbody tr:last-child {{
        border-bottom: none;
    }}

    .summary-table tbody tr:hover {{
        background: var(--border);
    }}

    .summary-table tbody tr:nth-child(even) {{
        background: rgba(255,255,255,0.03);
    }}

    .summary-table td {{
        padding: 9px 14px;
        text-align: center;
        white-space: nowrap;
    }}

    .summary-table td.stock-name {{
        text-align: left;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}

    .summary-table td.price-cell {{
        font-weight: 600;
    }}

    .chg-pos {{
        color: #22c55e;
        font-weight: 600;
    }}

    .chg-neg {{
        color: #ef4444;
        font-weight: 600;
    }}

    .chg-na {{
        color: var(--muted);
    }}

    .chg-badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 13px;
    }}

    .chg-badge.pos {{
        background: rgba(34,197,94,0.12);
        color: #22c55e;
        font-weight: 700;
    }}

    .chg-badge.neg {{
        background: rgba(239,68,68,0.12);
        color: #ef4444;
        font-weight: 700;
    }}

    .chg-badge.na {{
        color: var(--muted);
    }}

    .rank-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: var(--border);
        font-size: 11px;
        color: var(--muted);
        font-weight: 600;
    }}

    @media (max-width: 480px) and (orientation: portrait) {{
        .summary-table-wrap {{
            overflow-x: visible;
        }}

        .summary-table {{
            font-size: 11px;
            table-layout: fixed;
            width: 100%;
        }}

        /* col widths: # | Stock | Price | 1D | 1W | 1M */
        .summary-table colgroup col:nth-child(1) {{ width: 28px; }}
        .summary-table colgroup col:nth-child(2) {{ width: 22%; }}
        .summary-table colgroup col:nth-child(3) {{ width: 16%; }}
        .summary-table colgroup col:nth-child(4) {{ width: 18%; }}
        .summary-table colgroup col:nth-child(5) {{ width: 18%; }}
        .summary-table colgroup col:nth-child(6) {{ width: 18%; }}

        .summary-table thead tr {{
            font-size: 9px;
            letter-spacing: 0;
        }}

        .summary-table thead th {{
            padding: 7px 3px;
        }}

        .summary-table td {{
            padding: 6px 3px;
            white-space: normal;
            word-break: break-word;
        }}

        .summary-table td.stock-name {{
            font-size: 10px;
            letter-spacing: 0;
        }}

        .chg-badge {{
            padding: 1px 4px;
            font-size: 10px;
            border-radius: 4px;
        }}

        .rank-badge {{
            width: 18px;
            height: 18px;
            font-size: 9px;
        }}

        .summary-table thead th .sort-icon {{
            display: none;
        }}
    }}

    /* ---- ADD STOCK PANEL ---- */
    .add-stock-panel {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 30px;
    }}

    .add-stock-form {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        align-items: center;
    }}

    .add-input {{
        background: var(--bg);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 7px 12px;
        font-size: 14px;
        flex: 1 1 160px;
        min-width: 140px;
    }}

    .add-input:focus {{
        outline: 2px solid var(--accent);
    }}

    .add-msg {{
        margin-top: 10px;
        font-size: 13px;
        padding: 8px 12px;
        border-radius: 8px;
    }}

    .add-msg.success {{
        background: rgba(34,197,94,0.15);
        color: #22c55e;
        border: 1px solid rgba(34,197,94,0.3);
    }}

    .add-msg.error {{
        background: rgba(239,68,68,0.15);
        color: #ef4444;
        border: 1px solid rgba(239,68,68,0.3);
    }}

    .add-msg.info {{
        background: rgba(56,189,248,0.12);
        color: var(--accent);
        border: 1px solid rgba(56,189,248,0.3);
    }}
    </style>
    </head>

    <body>
    <div class="container">

        <div class="header">
            <button id="installBtn" style="display:none;">Install App</button>
            <h1>📈 Portfolio Stock News</h1>
            <button onclick="toggleTheme()">Toggle Theme</button>
        </div>

        <div class="updated">Last updated: {now}</div>

    <!-- ===== ADD STOCK PANEL ===== -->
    <div class="add-stock-panel" id="addStockPanel">
        <h3 style="margin:0 0 10px">➕ Add New Stock</h3>
        <div class="add-stock-form">
            <input id="newStockName"   type="text"      placeholder="Company Name (e.g. Tata Steel)"  class="add-input" />
            <input id="newStockTicker" type="text"      placeholder="NSE Ticker (e.g. TATASTEEL)"      class="add-input" />
            <input id="ghToken"        type="password"  placeholder="GitHub PAT (repo scope)"          class="add-input" style="flex:1 1 200px" />
            <button id="addStockBtn" onclick="submitAddStock()">Add Stock</button>
        </div>
        <div style="font-size:11px;color:var(--muted);margin-top:6px;">
            Token is used once to commit stocks.json to your repo. It is never stored or sent anywhere else.<br>
            Create one at <a href="https://github.com/settings/tokens" target="_blank" style="color:var(--accent)">github.com/settings/tokens</a> with <strong>repo</strong> scope.
        </div>
        <div id="addStockMsg" class="add-msg" style="display:none"></div>
    </div>
    """

    # ---- SUMMARY TABLE (sorted by monthly change, highest → lowest) ----
    def chg_sort_key(item):
        pd = item[1]["price"]
        if pd and pd["monthly"] is not None:
            return pd["monthly"]
        return float('-inf')

    def fmt_badge(val, suffix="%"):
        if val is None:
            return '<span class="chg-badge na">N/A</span>'
        cls = "pos" if val >= 0 else "neg"
        arrow = "▲" if val >= 0 else "▼"
        return f'<span class="chg-badge {cls}">{arrow} {val:+.2f}{suffix}</span>'

    table_rows = sorted(all_data.items(), key=chg_sort_key, reverse=True)

    table_html = '''<div class="summary-table-wrap"><table class="summary-table" id="summaryTable">
    <colgroup><col><col><col><col><col><col></colgroup>
    <thead><tr>
        <th>#</th>
        <th>Stock</th>
        <th class="sortable" data-col="price" onclick="sortTable(this)">Price (₹)<span class="sort-icon">⇅</span></th>
        <th class="sortable" data-col="daily" onclick="sortTable(this)">1D Change<span class="sort-icon">⇅</span></th>
        <th class="sortable" data-col="weekly" onclick="sortTable(this)">1W Change<span class="sort-icon">⇅</span></th>
        <th class="sortable sort-desc" data-col="monthly" onclick="sortTable(this)">1M Change<span class="sort-icon">▼</span></th>
    </tr></thead><tbody>'''

    def null_val(v):
        return "null" if v is None else str(v)

    for rank, (stock, data) in enumerate(table_rows, 1):
        pd = data["price"]
        if pd:
            price_val  = null_val(pd["price"])
            daily_val  = null_val(pd["daily"])
            weekly_val = null_val(pd["weekly"])
            monthly_val= null_val(pd["monthly"])
            price_cell   = f'<td class="price-cell">₹{pd["price"]}</td>'
            daily_cell   = f'<td>{fmt_badge(pd["daily"])}</td>'
            weekly_cell  = f'<td>{fmt_badge(pd["weekly"])}</td>'
            monthly_cell = f'<td>{fmt_badge(pd["monthly"])}</td>'
        else:
            price_val = daily_val = weekly_val = monthly_val = "null"
            price_cell   = '<td class="chg-na">N/A</td>'
            daily_cell = weekly_cell = monthly_cell = '<td class="chg-na">—</td>'

        table_html += f'''<tr data-price="{price_val}" data-daily="{daily_val}" data-weekly="{weekly_val}" data-monthly="{monthly_val}">
            <td><span class="rank-badge">{rank}</span></td>
            <td class="stock-name">{stock}</td>
            {price_cell}{daily_cell}{weekly_cell}{monthly_cell}
        </tr>'''

    table_html += '</tbody></table></div>'
    html += table_html

    def get_latest_news_time(stock_data):
        news = stock_data["news"]
        if not news:
            return datetime(1970, 1, 1, tzinfo=ZoneInfo("Asia/Kolkata"))

        def normalize(dt):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            return dt

        return max(normalize(article["date"]) for article in news)


    # SORT STOCKS HERE
    sorted_items = sorted(
        all_data.items(),
        key=lambda x: get_latest_news_time(x[1]),
        reverse=True
    )

    for stock, data in sorted_items:
        articles = data["news"]
        price_data = data["price"]

        if price_data:
            price = price_data["price"]
            daily = price_data["daily"]
            weekly = price_data["weekly"]
            monthly = price_data["monthly"]

            def get_color(val):
                if val is None:
                    return "#94a3b8"  # muted
                return "#22c55e" if val >= 0 else "#ef4444"

            price_html = f"""
            <div class="price">
                ₹{price}
                <div style="font-size:12px;">
                    <span style="color:{get_color(daily)}">1D: {daily}%</span> |
                    <span style="color:{get_color(weekly)}">1W: {weekly if weekly is not None else 'N/A'}%</span> |
                    <span style="color:{get_color(monthly)}">1M: {monthly if monthly is not None else 'N/A'}%</span>
                </div>
            </div>
            """
            if monthly is None:
                trend_class = "trend-neutral"
            elif monthly >= 0:
                trend_class = "trend-up"
            else:
                trend_class = "trend-down"
        else:
            price_html = '<div class="price">N/A</div>'
            trend_class = "trend-neutral"

        html += f"""
        <div class="stock {trend_class}">
            <div class="stock-header">
                <h2>{stock}</h2>
                {price_html}
            </div>
            <div class="grid">
        """

        if not articles:
            html += '<div class="empty">No recent news found</div>'
        else:
            for a in articles:
                time_str = a["date"].strftime('%d %b %I:%M %p')

                html += f"""
                <div class="card">
                    <a href="{a['link']}" target="_blank">{a['title']}</a>
                    <div class="time">
                        {time_str}
                        <span class="source">{a['source']}</span>
                    </div>
                </div>
                """

        html += "</div></div>"

    html += """
    </div>

    <script>
    function sortTable(th) {
        const table = document.getElementById("summaryTable");
        const tbody = table.querySelector("tbody");
        const col = th.dataset.col;
        const isDesc = th.classList.contains("sort-desc");
        const newDir = isDesc ? "asc" : "desc";

        // Reset all headers
        table.querySelectorAll("th.sortable").forEach(h => {
            h.classList.remove("sort-asc", "sort-desc");
            h.querySelector(".sort-icon").textContent = "⇅";
        });

        th.classList.add("sort-" + newDir);
        th.querySelector(".sort-icon").textContent = newDir === "desc" ? "▼" : "▲";

        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort((a, b) => {
            const av = a.dataset[col];
            const bv = b.dataset[col];
            const an = av === "null" ? -Infinity : parseFloat(av);
            const bn = bv === "null" ? -Infinity : parseFloat(bv);
            return newDir === "desc" ? bn - an : an - bn;
        });

        // Re-insert sorted rows and update rank badges
        rows.forEach((row, i) => {
            row.querySelector(".rank-badge").textContent = i + 1;
            tbody.appendChild(row);
        });
    }
    </script>

    <script>
    function toggleTheme() {
        document.body.classList.toggle("light");
        localStorage.setItem("theme",
            document.body.classList.contains("light") ? "light" : "dark"
        );
    }

    window.onload = function() {
        const saved = localStorage.getItem("theme");
        if (saved === "light") {
            document.body.classList.add("light");
        }
    }
    </script>

    <script>
    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("sw.js");
    }
    </script>

    <script>
    // --- AUTO REFRESH EVERY 2 HOURS ---
    setTimeout(() => {
        location.reload();
    }, 2 * 60 * 60 * 1000);


    // --- REAL BROWSER NOTIFICATION SYSTEM ---

    function getCurrentTitles() {
        return Array.from(document.querySelectorAll(".card a"))
            .map(a => a.innerText.trim());
    }

    function highlightNew(seenSet) {
        document.querySelectorAll(".card").forEach(card => {
            const title = card.querySelector("a").innerText.trim();
            if (!seenSet.has(title)) {
                card.style.border = "1px solid #22c55e";
                card.style.boxShadow = "0 0 10px rgba(34,197,94,0.5)";
            }
        });
    }

    function fireNotification(newItems) {
        if (!("Notification" in window)) return;

        const send = () => {{
            // One grouped notification summarising all new articles
            const n = new Notification("📈 Portfolio News Update", {{
                body: newItems.length === 1
                    ? newItems[0]
                    : `${{newItems.length}} new articles — ${{newItems[0]}} …`,
                icon: "https://cdn-icons-png.flaticon.com/512/2103/2103633.png",
                tag: "portfolio-news",   // replaces previous notification instead of stacking
                renotify: true
            }});
            // Clicking the notification focuses this tab
            n.onclick = () => {{ window.focus(); n.close(); }};
        }};

        if (Notification.permission === "granted") {{
            send();
        }} else if (Notification.permission === "default") {{
            Notification.requestPermission().then(perm => {{
                if (perm === "granted") send();
            }});
        }}
        // If permission === "denied" — silently skip, nothing we can do
    }}

    // Request permission early (on first load) so it's ready before the next refresh
    function requestPermissionEarly() {{
        if ("Notification" in window && Notification.permission === "default") {{
            Notification.requestPermission();
        }}
    }}

    window.addEventListener("load", () => {{
        requestPermissionEarly();

        const current = getCurrentTitles();
        const previous = JSON.parse(localStorage.getItem("seenTitles") || "[]");
        const prevSet = new Set(previous);
        const newItems = current.filter(t => !prevSet.has(t));

        if (previous.length > 0 && newItems.length > 0) {{
            fireNotification(newItems);
            highlightNew(prevSet);
        }}

        localStorage.setItem("seenTitles", JSON.stringify(current));
    }});
    </script>

    <script>
    // ---- ADD STOCK via GitHub Contents API ----
    // Writes stocks.json directly to the repo so the next build picks it up.
    // The user provides a short-lived GitHub PAT (repo scope) each time they add a stock.
    // The token is used for one API call and is never stored anywhere.

    const REPO_OWNER = "{gh_owner}";
    const REPO_NAME  = "{gh_repo}";
    const STOCKS_PATH = "stocks.json";

    // Current stocks.json content is embedded at build time so we can update it
    const CURRENT_STOCKS = {stocks_json_embedded};

    function showMsg(text, type) {{
        const el = document.getElementById("addStockMsg");
        el.textContent = text;
        el.className = "add-msg " + type;
        el.style.display = "block";
        if (type !== "success") return;
        setTimeout(() => {{ el.style.display = "none"; }}, 8000);
    }}

    async function submitAddStock() {{
        const name   = document.getElementById("newStockName").value.trim();
        const ticker = document.getElementById("newStockTicker").value.trim().toUpperCase();
        const token  = document.getElementById("ghToken").value.trim();

        if (!name)   {{ showMsg("Company name cannot be empty.", "error");   return; }}
        if (!ticker) {{ showMsg("Ticker symbol cannot be empty.", "error");  return; }}
        if (!token)  {{ showMsg("GitHub PAT is required to save the stock.", "error"); return; }}

        // Duplicate check
        if (CURRENT_STOCKS[ticker]) {{
            showMsg('"' + ticker + '" is already in your stock list.', "error");
            return;
        }}

        const btn = document.getElementById("addStockBtn");
        btn.disabled = true;
        btn.textContent = "Saving...";
        showMsg("Committing stocks.json to repo...", "info");

        try {{
            // 1. Get the current file SHA (required for the update API)
            const metaRes = await fetch(
                "https://api.github.com/repos/" + REPO_OWNER + "/" + REPO_NAME + "/contents/" + STOCKS_PATH,
                {{ headers: {{ Authorization: "token " + token, Accept: "application/vnd.github+json" }} }}
            );
            if (!metaRes.ok) {{
                const err = await metaRes.json();
                throw new Error("Could not fetch stocks.json from GitHub: " + (err.message || metaRes.status));
            }}
            const meta = await metaRes.json();
            const fileSha = meta.sha;

            // 2. Build the updated stocks object
            const updated = Object.assign({{}}, CURRENT_STOCKS);
            const yfTicker = ticker.includes(".") ? ticker : ticker + ".NS";
            updated[ticker] = {{ name: name, ticker: yfTicker }};

            // 3. Commit the updated file
            const content = btoa(unescape(encodeURIComponent(JSON.stringify(updated, null, 2))));
            const putRes = await fetch(
                "https://api.github.com/repos/" + REPO_OWNER + "/" + REPO_NAME + "/contents/" + STOCKS_PATH,
                {{
                    method: "PUT",
                    headers: {{ Authorization: "token " + token, Accept: "application/vnd.github+json", "Content-Type": "application/json" }},
                    body: JSON.stringify({{
                        message: "Add stock: " + ticker + " (" + name + ")",
                        content: content,
                        sha: fileSha
                    }})
                }}
            );
            if (!putRes.ok) {{
                const err = await putRes.json();
                throw new Error("GitHub commit failed: " + (err.message || putRes.status));
            }}

            // Clear inputs (do NOT store the token anywhere)
            document.getElementById("newStockName").value   = "";
            document.getElementById("newStockTicker").value = "";
            document.getElementById("ghToken").value        = "";

            showMsg(
                ticker + " (" + name + ") saved to stocks.json. " +
                "Trigger the workflow on GitHub Actions to see it with live data.",
                "success"
            );

        }} catch(e) {{
            showMsg("Error: " + e.message, "error");
        }} finally {{
            btn.disabled = false;
            btn.textContent = "Add Stock";
        }}
    }}
    </script>

    </body>
    </html>
    """

    # Substitute repo config and current stocks into the JS placeholders
    html = html.replace("{gh_owner}", gh_owner)
    html = html.replace("{gh_repo}", gh_repo)
    html = html.replace("{stocks_json_embedded}", stocks_json_embedded)

    return html


# ----------- MAIN -----------

def main():
    all_data = {}
    global_seen_titles = []

    # Reload the stock list fresh (picks up any stocks committed to stocks.json via the UI)
    stocks_data = load_stocks()
    stock_keys  = list(stocks_data.keys())

    # Update module-level STOCKS_DATA so helpers (get_stock_data, is_relevant_to_stock) see new entries
    STOCKS_DATA.clear()
    STOCKS_DATA.update(stocks_data)

    # --- PHASE 1: Fetch all prices concurrently ---
    print(f"Fetching prices for {len(stock_keys)} stocks concurrently...")
    prices = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_stock = {executor.submit(get_stock_data, stock): stock for stock in stock_keys}
        for future in as_completed(future_to_stock):
            stock = future_to_stock[future]
            try:
                prices[stock] = future.result()
            except Exception as e:
                print(f"  Price fetch failed for {stock}: {e}")
                prices[stock] = None
    print("  Prices fetched.")

    # --- PHASE 2: Fetch news sequentially (Google News RSS is rate-sensitive) ---
    for stock in stock_keys:
        print(f"Fetching news: {stock}...")
        try:
            news = fetch_news(stock, global_seen_titles)
        except Exception as e:
            print(f"  News fetch failed for {stock}: {e}")
            news = []
        all_data[stock] = {
            "news": news,
            "price": prices.get(stock)
        }

    html = generate_html(all_data, stocks_data)

    # Strip surrogate characters that can sneak in from malformed RSS feed content
    html = html.encode("utf-8", errors="replace").decode("utf-8")

    os.makedirs("public", exist_ok=True)

    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Done → public/index.html")


if __name__ == "__main__":
    main()