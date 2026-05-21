import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
import os
import yfinance as yf
from rapidfuzz.fuzz import ratio
from dateutil import parser as dateparser

STOCKS = ["ANGELONE", "ASIANPAINT", "BAJAJFINANCE", "COALINDIA", "DIVISLAB",
          "DIXON", "EPIGRAL", "FCL", "GAIL", "HDBFS", "HDFC BANK",
          "ICICI BANK", "INFOSYS", "ITC", "KIRLOSENG", "KOTAKBANK",
          "LAURUSLABS", "MANKIND", "MARICO", "NTPC", "PETRONET",
          "PFC", "PIIND", "POLYCAB", "POONAWALLA", "RELIANCE",
          "SBIN", "STYLAMIND", "TCS", "TMPV", "TMCV", "TRIVENI", "VBL", "ZENTEC"]

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
    
    "DIVISLAB": ["divi's", "divis", "divi's labs", "divis labs", "divis laboratories", "divis labs stock", "divis labs share", "divi"],
    
    "DIXON": ["dixon","dixon technologies", "dixon tech"],
    
    "EPIGRAL": ["epigral", "epigral ltd"],
    
    "FCL": ["fineotex", "fineotex chemical", "fcl stock", "fineotex share"],
    
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
    
    "SBIN": ["sbi", "state bank of india"],
    
    "STYLAMIND": ["stylamind","stylam industries", "stylam"],
    
    "TCS": ["tcs", "tata consultancy services"],
    
    "TMPV":["Tata motors", "TPMV"],

    "TMCV": ["Tata motors", "TMCV"],

    "TRIVENI": ["triveni engg", "triveni engineering"],
    
    "VBL": ["varun beverages", "vbl"],
    
    "ZENTEC": ["zen technologies", "zen tech", "zentech", "zentec", "zentec.ns"]
}

# ----------- PRICE FETCH -----------
def get_stock_data(stock):
    mapping = {
        "ANGELONE": "ANGELONE.NS",
        "ASIANPAINT": "ASIANPAINT.NS",
        "BAJAJFINANCE": "BAJFINANCE.NS",
        "COALINDIA": "COALINDIA.NS",
        "DIVISLAB": "DIVISLAB.NS",
        "DIXON": "DIXON.NS",
        "EPIGRAL": "EPIGRAL.NS",
        "FCL": "FCL.NS",
        "GAIL": "GAIL.NS",
        "HDBFS": "HDBFS.NS",
        "HDFC BANK": "HDFCBANK.NS",
        "ICICI BANK": "ICICIBANK.NS",
        "INFOSYS": "INFY.NS",
        "ITC": "ITC.NS",
        "KIRLOSENG": "KIRLOSENG.NS",
        "KOTAKBANK": "KOTAKBANK.NS",
        "LAURUSLABS": "LAURUSLABS.NS",
        "MANKIND": "MANKIND.NS",
        "MARICO": "MARICO.NS",
        "NTPC": "NTPC.NS",
        "PETRONET": "PETRONET.NS",
        "PFC": "PFC.NS",
        "PIIND": "PIIND.NS",
        "POLYCAB": "POLYCAB.NS",
        "POONAWALLA": "POONAWALLA.NS",
        "RELIANCE": "RELIANCE.NS",
        "SBIN": "SBIN.NS",
        "STYLAMIND": "STYLAMIND.NS",
        "TCS": "TCS.NS",
        "TMCV": "TMCV.NS",
        "TMPV": "TMPV.NS",
        "TRIVENI": "TRIVENI.NS",
        "VBL": "VBL.NS",
        "ZENTEC": "ZENTEC.NS",
    }

    ticker = mapping.get(stock)
    if not ticker:
        return None

    try:
        data = yf.Ticker(ticker)

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

    keywords = STOCK_KEYWORDS.get(stock, [stock])

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


    // --- FAKE NOTIFICATION SYSTEM ---
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

    window.addEventListener("load", () => {
        const current = getCurrentTitles();
        const previous = JSON.parse(localStorage.getItem("seenTitles") || "[]");

        const prevSet = new Set(previous);

        const newItems = current.filter(t => !prevSet.has(t));

        if (previous.length > 0 && newItems.length > 0) {
            showNotification(newItems.length);
            highlightNew(prevSet);
        }

        localStorage.setItem("seenTitles", JSON.stringify(current));
    });
    </script>

    </body>
    </html>
    """

    return html


# ----------- MAIN -----------

def main():
    all_data = {}

    global_seen_titles = []

    for stock in STOCKS:
        print(f"Fetching {stock}...")
        news = fetch_news(stock, global_seen_titles)
        price = get_stock_data(stock)

        all_data[stock] = {
            "news": news,
            "price": price
        }

    html = generate_html(all_data)

    os.makedirs("public", exist_ok=True)

    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Done → public/index.html")


if __name__ == "__main__":
    main()