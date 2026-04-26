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
    ("BusinessLine", "https://www.thehindubusinessline.com/feeder/default.rss"),
    ("BusinessLine markets", "https://www.thehindubusinessline.com/markets/feeder/default.rss"),
    ("FE companies", "https://www.financialexpress.com/industry/companies/feed/"),
    ("Financial Express", "https://www.financialexpress.com/feed/"),
    ("FE Markets", "https://www.financialexpress.com/markets/feed/"),
    ("BL Markets", "https://www.thehindubusinessline.com/markets/feeder/default.rss"),
    ("BS companies", "https://www.business-standard.com/rss/companies-101.rss"),
    ("Business Standard", "https://www.business-standard.com/rss/markets-106.rss"),
    ("BS Top", "https://www.business-standard.com/rss/home_page_top_stories.rss"),
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
    
    "ASIANPAINT": ["asian paints", "Asian paint stock", "asian paints share"],
    
    "BAJAJFINANCE": ["bajaj finance", "BAJAJFINANCE stock", "Bajaj"],
    
    "COALINDIA": ["coal india", "Coal India stock", "coal india limited"],
    
    "DIVISLAB": ["divi's", "divis", "divi's labs", "divis labs", "divis laboratories", "divis labs stock", "divis labs share"],
    
    "DIXON": ["dixon technologies", "dixon tech"],
    
    "EPIGRAL": ["epigral", "epigral ltd"],
    
    "FCL": ["fineotex", "fineotex chemical", "fcl stock", "fineotex share"],
    
    "GAIL": ["gail", "gail india"],
    
    "HDBFS":["HDB Financial", "hdfc financial", "hdb financial services"],

    "HDFC BANK": ["hdfc bank", "hdfc"],
    
    "ICICI BANK": ["icici bank", "icici"],
    
    "INFOSYS": ["infosys", "infy"],
    
    "ITC": ["itc"],
    
    "KIRLOSENG": ["kirloskar oil", "kirloskar oil engines"],
    
    "KOTAKBANK": ["kotak bank", "kotak mahindra bank", "kotak"],
    
    "LAURUSLABS": ["laurus labs", "laurus"],
    
    "MANKIND": ["mankind pharma", "mankind"],
    
    "MARICO": ["marico"],
    
    "NTPC": ["ntpc"],
    
    "PETRONET": ["petronet lng", "petronet"],
    
    "PFC": ["power finance corporation", "pfc"],
    
    "PIIND": ["pi industries", "pi ind"],
    
    "POLYCAB": ["polycab"],
    
    "POONAWALLA": ["poonawalla fincorp", "poonawalla"],
    
    "RELIANCE": ["reliance", "ril", "mukesh ambani"],
    
    "SBIN": ["sbi", "state bank of india"],
    
    "STYLAMIND": ["stylam industries", "stylam"],
    
    "TCS": ["tcs", "tata consultancy services"],
    
    "TMPV":["Tata motors", "TPMV"],

    "TMCV": ["Tata motors", "TMCV"],

    "TRIVENI": ["triveni turbine", "triveni"],
    
    "VBL": ["varun beverages", "vbl"],
    
    "ZENTEC": ["zen technologies", "zen tech", "zentech"]
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
        hist = data.history(period="1d")

        if hist.empty:
            return None

        close = hist["Close"].iloc[-1]
        open_ = hist["Open"].iloc[-1]
        change = ((close - open_) / open_) * 100

        return round(close, 2), round(change, 2)

    except:
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
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%d %b %Y %H:%M')

    html = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <title>Portfolio Monitor</title>

    <style>
    body {{
        margin: 0;
        background: #000;
        color: #E5E5E5;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
    }}

    .container {{
        max-width: 1200px;
        margin: auto;
        padding: 15px;
    }}

    .header {{
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid #222;
        padding-bottom: 8px;
        margin-bottom: 15px;
    }}

    h1 {{
        font-size: 16px;
        margin: 0;
        color: #FFD700;
        letter-spacing: 1px;
    }}

    .time {{
        color: #A0A0A0;
        font-size: 12px;
    }}

    .stock {{
        margin-bottom: 18px;
        border-bottom: 1px solid #111;
        padding-bottom: 10px;
    }}

    .stock-header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 6px;
    }}

    .stock-name {{
        font-weight: bold;
        letter-spacing: 0.5px;
    }}

    .price {{
        font-weight: bold;
    }}

    .news-list {{
        list-style: none;
        padding: 0;
        margin: 0;
    }}

    .news-item {{
    display: flex;
    justify-content: space-between;
    gap: 10px;
}}

.news-item a {{
    flex: 1;
    min-width: 0;  /* IMPORTANT for ellipsis */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.meta {{
    white-space: nowrap;
}}

/* MOBILE FIX */
@media (max-width: 600px) {{
    .news-item {{
        flex-direction: column;
        align-items: flex-start;
    }}

    .news-item a {{
        white-space: normal;   /* allow wrapping */
    }}

    .meta {{
        margin-top: 2px;
    }}
}}

    .source {{
        color: #FFD700;
    }}

    .empty {{
        color: #666;
        font-size: 12px;
    }}
    </style>
    </head>

    <body>
    <div class="container">

        <div class="header">
            <h1>PORTFOLIO MONITOR</h1>
            <div class="time">{now}</div>
        </div>
    """

    for stock, data in all_data.items():
        articles = data["news"]
        price_data = data["price"]

        if price_data:
            price, change = price_data
            color = "#00FF90" if change >= 0 else "#FF4D4D"
            price_html = f'<span class="price" style="color:{color}">₹{price} ({change}%)</span>'
        else:
            price_html = '<span class="price">N/A</span>'

        html += f"""
        <div class="stock">
            <div class="stock-header">
                <div class="stock-name">{stock}</div>
                {price_html}
            </div>
        """

        if not articles:
            html += '<div class="empty">No recent news</div>'
        else:
            html += '<ul class="news-list">'
            for a in articles:
                time_str = a["date"].strftime('%H:%M')
                html += f"""
                <li class="news-item">
                    <a href="{a['link']}" target="_blank">{a['title']}</a>
                    <span class="meta">
                        <span class="source">{a['source']}</span> {time_str}
                    </span>
                </li>
                """
            html += '</ul>'

        html += "</div>"

    html += """
    </div>
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