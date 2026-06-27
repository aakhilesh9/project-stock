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
import http.server
import socketserver

STOCKS_FILE = "stocks.json"

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

# Global state to keep the web server updated
app_data = {
    "all_data": {},
    "global_seen_titles": []
}

# ----------- STOCK STORAGE HELPERS -----------

def load_stocks():
    if not os.path.exists(STOCKS_FILE):
        print(f"{STOCKS_FILE} not found. Creating it with default stocks...")
        default_stocks = [
            {"name": "ANGELONE", "ticker": "ANGELONE.NS", "keywords": ["angel one", "angelone", "angel broking"]},
            {"name": "ASIANPAINT", "ticker": "ASIANPAINT.NS", "keywords": ["asianpain", "asian paints", "asian paint stock", "asian paints share"]},
            {"name": "BAJAJFINANCE", "ticker": "BAJFINANCE.NS", "keywords": ["bajajfinance", "bajaj finance", "bajajfinance stock"]},
            {"name": "COALINDIA", "ticker": "COALINDIA.NS", "keywords": ["coal india", "coal india stock", "coal india limited"]},
            {"name": "DIVISLAB", "ticker": "DIVISLAB.NS", "keywords": ["divi's", "divis", "divi's labs", "divis labs", "divis laboratories", "divis labs stock", "divis labs share"]},
            {"name": "DIXON", "ticker": "DIXON.NS", "keywords": ["dixon", "dixon technologies", "dixon tech"]},
            {"name": "EPIGRAL", "ticker": "EPIGRAL.NS", "keywords": ["epigral", "epigral ltd"]},
            {"name": "FCL", "ticker": "FCL.NS", "keywords": ["fineotex", "fineotex chemical", "fineotex share"]},
            {"name": "GAIL", "ticker": "GAIL.NS", "keywords": ["gail", "gail india", "gas authority of india"]},
            {"name": "HDBFS", "ticker": "HDBFS.NS", "keywords": ["hdbfs", "hdb financial", "hdfc financial"]},
            {"name": "HDFC BANK", "ticker": "HDFCBANK.NS", "keywords": ["hdfc bank", "hdfc"]},
            {"name": "ICICI BANK", "ticker": "ICICIBANK.NS", "keywords": ["icici bank", "icici"]},
            {"name": "INFOSYS", "ticker": "INFY.NS", "keywords": ["infosys", "infy"]},
            {"name": "ITC", "ticker": "ITC.NS", "keywords": ["itc", "itc stock", "itc share"]},
            {"name": "KIRLOSENG", "ticker": "KIRLOSENG.NS", "keywords": ["kirloseng", "kirloskar oil", "kirloskar oil engines"]},
            {"name": "KOTAKBANK", "ticker": "KOTAKBANK.NS", "keywords": ["kotakbank", "kotak bank", "kotak mahindra bank", "kotak"]},
            {"name": "LAURUSLABS", "ticker": "LAURUSLABS.NS", "keywords": ["laurus labs", "laurus", "lauruslabs"]},
            {"name": "MANKIND", "ticker": "MANKIND.NS", "keywords": ["mankind pharma", "mankind"]},
            {"name": "MARICO", "ticker": "MARICO.NS", "keywords": ["marico"]},
            {"name": "NTPC", "ticker": "NTPC.NS", "keywords": ["ntpc"]},
            {"name": "PETRONET", "ticker": "PETRONET.NS", "keywords": ["petronet lng", "petronet"]},
            {"name": "PFC", "ticker": "PFC.NS", "keywords": ["power finance corporation", "pfc"]},
            {"name": "PIIND", "ticker": "PIIND.NS", "keywords": ["p i industries", "pi industries", "pi ind"]},
            {"name": "POLYCAB", "ticker": "POLYCAB.NS", "keywords": ["polycab"]},
            {"name": "POONAWALLA", "ticker": "POONAWALLA.NS", "keywords": ["poonawalla fincorp", "poonawalla"]},
            {"name": "RELIANCE", "ticker": "RELIANCE.NS", "keywords": ["reliance", "ril", "mukesh ambani"]},
            {"name": "SBIN", "ticker": "SBIN.NS", "keywords": ["sbin", "state bank of india"]},
            {"name": "STYLAMIND", "ticker": "STYLAMIND.NS", "keywords": ["stylamind", "stylam industries", "stylam"]},
            {"name": "TCS", "ticker": "TCS.NS", "keywords": ["tcs", "tata consultancy services"]},
            {"name": "TMPV", "ticker": "TMPV.NS", "keywords": ["tata motors", "tmpv"]},
            {"name": "TMCV", "ticker": "TMCV.NS", "keywords": ["tata motors", "tmcv"]},
            {"name": "TRIVENI", "ticker": "TRIVENI.NS", "keywords": ["triveni engg", "triveni engineering"]},
            {"name": "VBL", "ticker": "VBL.NS", "keywords": ["varun beverages", "vbl"]},
            {"name": "ZENTEC", "ticker": "ZENTEC.NS", "keywords": ["zen technologies", "zen tech", "zentech", "zentec", "zentec.ns", "zen technologies ltd"]}
        ]
        save_stocks(default_stocks)
        return default_stocks
        
    try:
        with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {STOCKS_FILE}: {e}")
        return []

def save_stocks(stocks):
    try:
        with open(STOCKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stocks, f, indent=4)
    except Exception as e:
        print(f"Error saving {STOCKS_FILE}: {e}")

def add_stock(name, ticker):
    stocks = load_stocks()
    
    if not name or not ticker:
        raise ValueError("Company name and ticker cannot be empty.")
    
    ticker_upper = ticker.upper()
    
    # Duplicate Check
    if any(s['ticker'].upper() == ticker_upper for s in stocks):
        raise ValueError(f"Stock with ticker {ticker_upper} already exists.")
    
    new_stock = {
        "name": name,
        "ticker": ticker_upper,
        "keywords": [name.lower(), ticker_upper.lower()]
    }
    stocks.append(new_stock)
    save_stocks(stocks)
    return new_stock


# ----------- PRICE FETCH -----------
def get_stock_data(stock):
    ticker = stock.get("ticker")
    if not ticker:
        return None

    try:
        data = yf.Ticker(ticker)
        hist_1d = data.history(period="1d")
        hist_1mo = data.history(period="1mo")
        hist_3mo = data.history(period="3mo")

        if hist_1d.empty or hist_1mo.empty:
            return None

        close = hist_1d["Close"].iloc[-1]
        open_ = hist_1d["Open"].iloc[-1]
        daily_change = ((close - open_) / open_) * 100

        if len(hist_1mo) >= 5:
            week_ago = hist_1mo["Close"].iloc[-5]
            weekly_change = ((close - week_ago) / week_ago) * 100
        else:
            weekly_change = None

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
        print(f"yfinance failed for {ticker}: {e}")
        return None


# ----------- NEWS HELPERS -----------
def get_google_news_rss(stock):
    query = quote_plus(f"{stock['name']} stock")
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
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    text = text.replace(" ", "")
    return text

def is_relevant_to_stock(title, stock):
    title_norm = normalize(title)
    keywords = stock.get("keywords", [stock["name"]])

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

            title = entry.title.strip()
            
            if not is_relevant_to_stock(title, stock):
                continue

            dt = parse_date(entry)
            if not dt:
                continue

            dt = dt.astimezone(ZoneInfo("Asia/Kolkata"))

            if not is_recent(dt, now):
                continue

            if is_duplicate(title, titles):
                continue

            if is_duplicate(title, global_seen_titles):
                continue

            titles.append(title)
            global_seen_titles.append(title)

            collected.append({
                "title": title,
                "link": entry.link,
                "date": dt,
                "source": source_name
            })

    collected.sort(key=lambda x: x["date"], reverse=True)
    return collected


# ----------- HTML -----------

def generate_html(all_data):
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%d %b %Y %I:%M %p')

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

    .stock.trend-up {{ border-left-color: #22c55e; }}
    .stock.trend-down {{ border-left-color: #ef4444; }}
    .stock.trend-neutral {{ border-left-color: #94a3b8; }}

    .stock-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}

    .stock h2 {{ margin: 0; }}
    .price {{ font-weight: bold; }}

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

    .card:hover {{ transform: translateY(-3px); }}

    .card a {{
        color: var(--text);
        text-decoration: none;
        font-weight: 500;
    }}

    .card a:hover {{ color: var(--accent); }}

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

    .empty {{ color: var(--muted); font-size: 14px; }}

    /* ---- SUMMARY TABLE ---- */
    .summary-table-wrap {{ overflow-x: auto; margin-bottom: 35px; }}

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

    .summary-table thead th.sortable {{ cursor: pointer; user-select: none; }}
    .summary-table thead th.sortable:hover {{ background: rgba(255,255,255,0.15); }}
    
    .summary-table thead th .sort-icon {{
        display: inline-block; margin-left: 5px; opacity: 0.4; font-size: 11px; transition: opacity 0.15s;
    }}

    .summary-table thead th.sort-asc .sort-icon,
    .summary-table thead th.sort-desc .sort-icon {{ opacity: 1; }}

    .summary-table tbody tr {{
        border-bottom: 1px solid var(--border);
        transition: background 0.15s;
    }}
    .summary-table tbody tr:last-child {{ border-bottom: none; }}
    .summary-table tbody tr:hover {{ background: var(--border); }}
    .summary-table tbody tr:nth-child(even) {{ background: rgba(255,255,255,0.03); }}

    .summary-table td {{
        padding: 9px 14px; text-align: center; white-space: nowrap;
    }}
    .summary-table td.stock-name {{
        text-align: left; font-weight: 600; letter-spacing: 0.02em;
    }}
    .summary-table td.price-cell {{ font-weight: 600; }}

    .chg-pos {{ color: #22c55e; font-weight: 600; }}
    .chg-neg {{ color: #ef4444; font-weight: 600; }}
    .chg-na {{ color: var(--muted); }}

    .chg-badge {{
        display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 13px;
    }}

    .chg-badge.pos {{ background: rgba(34,197,94,0.12); color: #22c55e; font-weight: 700; }}
    .chg-badge.neg {{ background: rgba(239,68,68,0.12); color: #ef4444; font-weight: 700; }}
    .chg-badge.na {{ color: var(--muted); }}

    .rank-badge {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 24px; height: 24px; border-radius: 50%; background: var(--border);
        font-size: 11px; color: var(--muted); font-weight: 600;
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

        <div class="card" style="margin-bottom: 25px; padding: 20px;">
            <h3 style="margin-top: 0;">➕ Add New Stock</h3>
            <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                <input type="text" id="newStockName" placeholder="Company Name (e.g. Tesla)" style="padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text); flex: 1; min-width: 200px;">
                <input type="text" id="newStockTicker" placeholder="Ticker (e.g. TSLA)" style="padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text); flex: 1; min-width: 150px;">
                <button onclick="submitNewStock()" id="addStockBtn" style="padding: 10px 16px; background: var(--accent); color: white; border: none; font-weight: bold; border-radius: 6px;">Add Stock</button>
            </div>
            <div id="addStockMsg" style="margin-top: 10px; font-size: 14px; font-weight: bold;"></div>
        </div>
        """

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
        <th class="sortable" data-col="price" onclick="sortTable(this)">Price<span class="sort-icon">⇅</span></th>
        <th class="sortable" data-col="daily" onclick="sortTable(this)">1D Change<span class="sort-icon">⇅</span></th>
        <th class="sortable" data-col="weekly" onclick="sortTable(this)">1W Change<span class="sort-icon">⇅</span></th>
        <th class="sortable sort-desc" data-col="monthly" onclick="sortTable(this)">1M Change<span class="sort-icon">▼</span></th>
    </tr></thead><tbody>'''

    def null_val(v): return "null" if v is None else str(v)

    for rank, (stock, data) in enumerate(table_rows, 1):
        pd = data["price"]
        if pd:
            price_val, daily_val, weekly_val, monthly_val = null_val(pd["price"]), null_val(pd["daily"]), null_val(pd["weekly"]), null_val(pd["monthly"])
            price_cell   = f'<td class="price-cell">{pd["price"]}</td>'
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
        def normalize_dt(dt):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            return dt
        return max(normalize_dt(article["date"]) for article in news)

    sorted_items = sorted(all_data.items(), key=lambda x: get_latest_news_time(x[1]), reverse=True)

    for stock, data in sorted_items:
        articles = data["news"]
        price_data = data["price"]

        if price_data:
            price, daily, weekly, monthly = price_data["price"], price_data["daily"], price_data["weekly"], price_data["monthly"]
            def get_color(val): return "#94a3b8" if val is None else ("#22c55e" if val >= 0 else "#ef4444")

            price_html = f"""
            <div class="price">
                {price}
                <div style="font-size:12px;">
                    <span style="color:{get_color(daily)}">1D: {daily}%</span> |
                    <span style="color:{get_color(weekly)}">1W: {weekly if weekly is not None else 'N/A'}%</span> |
                    <span style="color:{get_color(monthly)}">1M: {monthly if monthly is not None else 'N/A'}%</span>
                </div>
            </div>
            """
            trend_class = "trend-neutral" if monthly is None else ("trend-up" if monthly >= 0 else "trend-down")
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
    async function submitNewStock() {
        const name = document.getElementById('newStockName').value.trim();
        const ticker = document.getElementById('newStockTicker').value.trim();
        const msg = document.getElementById('addStockMsg');
        const btn = document.getElementById('addStockBtn');
        
        if (!name || !ticker) {
            msg.style.color = '#ef4444';
            msg.textContent = 'Company Name and Ticker are required.';
            return;
        }
        
        btn.disabled = true;
        btn.style.opacity = '0.5';
        msg.style.color = 'var(--muted)';
        msg.textContent = 'Adding stock and fetching data (this may take a few seconds)...';
        
        try {
            const res = await fetch('/api/add_stock', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, ticker })
            });
            const data = await res.json();
            
            if (res.ok && data.success) {
                msg.style.color = '#22c55e';
                msg.textContent = data.message + ' Reloading page...';
                setTimeout(() => location.reload(), 1000);
            } else {
                msg.style.color = '#ef4444';
                msg.textContent = data.message || 'Error adding stock.';
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        } catch (e) {
            msg.style.color = '#ef4444';
            msg.textContent = 'Network error or server disconnected.';
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    }
    </script>
    <script>
    function sortTable(th) {
        const table = document.getElementById("summaryTable");
        const tbody = table.querySelector("tbody");
        const col = th.dataset.col;
        const isDesc = th.classList.contains("sort-desc");
        const newDir = isDesc ? "asc" : "desc";

        table.querySelectorAll("th.sortable").forEach(h => {
            h.classList.remove("sort-asc", "sort-desc");
            h.querySelector(".sort-icon").textContent = "⇅";
        });

        th.classList.add("sort-" + newDir);
        th.querySelector(".sort-icon").textContent = newDir === "desc" ? "▼" : "▲";

        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort((a, b) => {
            const av = a.dataset[col], bv = b.dataset[col];
            const an = av === "null" ? -Infinity : parseFloat(av);
            const bn = bv === "null" ? -Infinity : parseFloat(bv);
            return newDir === "desc" ? bn - an : an - bn;
        });

        rows.forEach((row, i) => {
            row.querySelector(".rank-badge").textContent = i + 1;
            tbody.appendChild(row);
        });
    }

    function toggleTheme() {
        document.body.classList.toggle("light");
        localStorage.setItem("theme", document.body.classList.contains("light") ? "light" : "dark");
    }

    window.onload = function() {
        if (localStorage.getItem("theme") === "light") {
            document.body.classList.add("light");
        }
    }
    </script>
    </body>
    </html>
    """
    return html

# ----------- SERVER & MAIN RUNNER -----------

def trigger_html_build():
    html = generate_html(app_data["all_data"])
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)

def update_all_data():
    stocks = load_stocks()
    if not stocks:
        print("No stocks found in database.")
        return
        
    print(f"Fetching prices for {len(stocks)} stocks concurrently...")
    prices = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_stock = {executor.submit(get_stock_data, s): s for s in stocks}
        for future in as_completed(future_to_stock):
            stock = future_to_stock[future]
            try:
                prices[stock['name']] = future.result()
            except Exception:
                prices[stock['name']] = None
                
    print("Fetching news...")
    app_data["global_seen_titles"] = []
    
    for stock in stocks:
        news = fetch_news(stock, app_data["global_seen_titles"])
        app_data["all_data"][stock['name']] = {
            "news": news,
            "price": prices.get(stock['name'])
        }
        
    trigger_html_build()

class StockAppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)
        
    def do_POST(self):
        if self.path == '/api/add_stock':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                name = data.get('name', '').strip()
                ticker = data.get('ticker', '').strip()
                
                new_stock = add_stock(name, ticker)
                print(f"User added new stock via UI: {name} ({ticker})")
                
                # Fetch price and news specifically for this stock
                price = get_stock_data(new_stock)
                news = fetch_news(new_stock, app_data["global_seen_titles"])
                
                # Update global data & regenerate immediately
                app_data["all_data"][new_stock['name']] = {
                    "news": news,
                    "price": price
                }
                trigger_html_build()
                
                response = {"success": True, "message": f"Added {name} successfully!"}
                status = 200
            except ValueError as e:
                response = {"success": False, "message": str(e)}
                status = 400
            except Exception as e:
                response = {"success": False, "message": f"Server Error: {str(e)}"}
                status = 500
                
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            super().do_POST()

def main():
    print("Initial startup data fetch...")
    # This will now successfully run, create the JSON if missing, and create the public folder
    update_all_data()
    
    print("\n=============================================")
    print("✅ Dashboard ready! Serving locally.")
    print("👉 Open your browser to: http://localhost:8000")
    print("=============================================\n")
    
    # Keeps script running to capture user UI additions dynamically.
    with socketserver.TCPServer(("", 8000), StockAppHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down local server.")
        
    print("Initial startup data fetch...")
    update_all_data()
    
    print("\n=============================================")
    print("✅ Dashboard ready! Serving locally.")
    print("👉 Open your browser to: http://localhost:8000")
    print("=============================================\n")
    
    # Keeps script running to capture user UI additions dynamically.
    with socketserver.TCPServer(("", 8000), StockAppHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down local server.")

if __name__ == "__main__":
    main()