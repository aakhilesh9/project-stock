import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
import os
import yfinance as yf
from rapidfuzz.fuzz import ratio
from dateutil import parser as dateparser

STOCKS = ["ANGELONE", "ASIANPAINT", "BAJAJFINANCE", "COALINDIA", "DIVISLAB",
          "DIXON", "EPIGRAL", "FCL", "GAIL", "HDFC BANK",
          "ICICI BANK", "INFOSYS", "ITC", "KIRLOSENG", "KOTAKBANK",
          "LAURUSLABS", "MANKIND", "MARICO", "NTPC", "PETRONET",
          "PFC", "PIIND", "POLYCAB", "POONAWALLA", "RELIANCE",
          "SBIN", "STYLAMIND", "TCS", "TRIVENI", "VBL", "ZENTEC"]

# ----------- RSS SOURCES (PRIORITY ORDER) -----------
RSS_SOURCES = [
    ("Google News", "GOOGLE_NEWS"),
    ("BusinessLine", "https://www.thehindubusinessline.com/feeder/default.rss"),
    ("Financial Express", "https://www.financialexpress.com/feed/"),
    ("FE Markets", "https://www.financialexpress.com/markets/feed/"),
    ("BL Markets", "https://www.thehindubusinessline.com/markets/feeder/default.rss"),
    ("Business Standard", "https://www.business-standard.com/rss/markets-106.rss"),
    ("BS Top", "https://www.business-standard.com/rss/home_page_top_stories.rss"),
    ("Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
    ("ET Markets", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Mint Companies", "https://www.livemint.com/rss/companies"),
    ("Mint Markets", "https://www.livemint.com/rss/markets"),
]

SIMILARITY_THRESHOLD = 70
MAX_NEWS = 7
DAYS_LIMIT = 7


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


# ----------- NEWS FETCH -----------

def fetch_news(stock):
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

            dt = parse_date(entry)
            if not dt:
                continue

            dt = dt.astimezone(ZoneInfo("Asia/Kolkata"))

            if not is_recent(dt, now):
                continue

            if is_duplicate(title, titles):
                continue

            titles.append(title)

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
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S IST')

    html = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Stock News</title>

    <style>
    body {{
        font-family: sans-serif;
        background: #0f172a;
        color: #e2e8f0;
    }}

    .container {{
        max-width: 1100px;
        margin: auto;
        padding: 20px;
    }}

    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 15px;
    }}

    .card {{
        background: #1e293b;
        padding: 15px;
        border-radius: 12px;
    }}

    .time {{
        font-size: 12px;
        color: #94a3b8;
    }}

    .source {{
        font-size: 11px;
        background: #334155;
        padding: 2px 6px;
        border-radius: 6px;
        margin-left: 6px;
    }}
    </style>
    </head>

    <body>
    <div class="container">
    <h1>📈 Portfolio Stock News</h1>
    <div>Last updated: {now}</div>
    """

    for stock, data in all_data.items():
        html += f"<h2>{stock}</h2><div class='grid'>"

        for a in data["news"]:
            time_str = a["date"].strftime('%d %b %Y %I:%M %p')

            html += f"""
            <div class="card">
                <a href="{a['link']}" target="_blank">{a['title']}</a>
                <div class="time">
                    {time_str}
                    <span class="source">{a['source']}</span>
                </div>
            </div>
            """

        html += "</div>"

    html += "</div></body></html>"
    return html


# ----------- MAIN -----------

def main():
    all_data = {}

    for stock in STOCKS:
        print(f"Fetching {stock}...")
        news = fetch_news(stock)
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