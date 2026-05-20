import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
import os
import yfinance as yf
from rapidfuzz.fuzz import ratio
from dateutil import parser as dateparser
import re

# ---------------- STOCKS ----------------
STOCKS = ["ANGELONE","ASIANPAINT","BAJAJFINANCE","COALINDIA","DIVISLAB",
"DIXON","EPIGRAL","FCL","GAIL","HDBFS","HDFC BANK","ICICI BANK",
"INFOSYS","ITC","KIRLOSENG","KOTAKBANK","LAURUSLABS","MANKIND",
"MARICO","NTPC","PETRONET","PFC","PIIND","POLYCAB","POONAWALLA",
"RELIANCE","SBIN","STYLAMIND","TCS","TMPV","TMCV","TRIVENI","VBL","ZENTEC"]

# ---------------- RSS ----------------
RSS_SOURCES = [
    ("Google News", "GOOGLE_NEWS"),
    ("Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
]

SIMILARITY_THRESHOLD = 70
MAX_NEWS = 7
DAYS_LIMIT = 7

# ---------------- PRICE ----------------
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
    "TMPV": "TMPV.NS",
    "TMCV": "TMCV.NS",
    "TRIVENI": "TRIVENI.NS",
    "VBL": "VBL.NS",
    "ZENTEC": "ZENTEC.NS",
}

    ticker = mapping.get(stock)
    if not ticker:
        return None

    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="3mo")

        if hist.empty:
            return None

        close = hist["Close"].iloc[-1]
        open_ = hist["Open"].iloc[-1]

        daily = ((close - open_) / open_) * 100
        weekly = ((close - hist["Close"].iloc[-5]) / hist["Close"].iloc[-5]) * 100 if len(hist)>=5 else None
        monthly = ((close - hist["Close"].iloc[-21]) / hist["Close"].iloc[-21]) * 100 if len(hist)>=21 else None

        return {
            "price": round(close,2),
            "daily": round(daily,2),
            "weekly": round(weekly,2) if weekly else None,
            "monthly": round(monthly,2) if monthly else None
        }

    except:
        return None

# ---------------- HELPERS ----------------
def get_google_news_rss(stock):
    return f"https://news.google.com/rss/search?q={quote_plus(stock)}&hl=en-IN&gl=IN&ceid=IN:en"

def parse_date(entry):
    try:
        dt = dateparser.parse(entry.published)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        return dt
    except:
        return None

def is_recent(dt):
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    return dt and dt >= (now - timedelta(days=7))

def is_duplicate(title, titles):
    return any(ratio(title.lower(), t.lower())>=SIMILARITY_THRESHOLD for t in titles)

# ---------------- NEWS ----------------
def fetch_news(stock):
    collected = []
    titles = []

    for name,url in RSS_SOURCES:
        if len(collected)>=MAX_NEWS: break
        url = get_google_news_rss(stock) if url=="GOOGLE_NEWS" else url

        feed = feedparser.parse(url)

        for e in feed.entries:
            if len(collected)>=MAX_NEWS: break

            title = e.title.strip()
            dt = parse_date(e)
            if not dt or not is_recent(dt): continue
            if is_duplicate(title,titles): continue

            titles.append(title)

            collected.append({
                "title": title,
                "link": e.link,
                "date": dt,
                "source": name
            })

    return sorted(collected,key=lambda x:x["date"],reverse=True)

# ---------------- HTML ----------------
def generate_html(all_data):
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%d %b %Y %I:%M %p')

    def get_latest(stock):
        if not stock["news"]:
            return datetime(1970,1,1,tzinfo=ZoneInfo("Asia/Kolkata"))
        return max(n["date"] for n in stock["news"])

    sorted_items = sorted(all_data.items(), key=lambda x:get_latest(x[1]), reverse=True)

    html = f"<html><body><h1>Portfolio News</h1><p>{now}</p>"

    for stock,data in sorted_items:
        html += f"<h2>{stock}</h2>"

        for n in data["news"]:
            html += f"<p><a href='{n['link']}'>{n['title']}</a></p>"

    # -------- TABLE --------
    html += "<h2>Stock Summary</h2><table border='1'><tr><th>Stock</th><th>Price</th><th>1D</th><th>1W</th><th>1M</th></tr>"

    for s,d in all_data.items():
        p = d["price"]
        if p:
            html += f"<tr><td>{s}</td><td>{p['price']}</td><td>{p['daily']}</td><td>{p['weekly']}</td><td>{p['monthly']}</td></tr>"
        else:
            html += f"<tr><td>{s}</td><td colspan='4'>N/A</td></tr>"

    html += "</table></body></html>"

    return html

# ---------------- MAIN ----------------
def main():
    all_data = {}

    for stock in STOCKS:
        news = fetch_news(stock)
        price = get_stock_data(stock)

        all_data[stock] = {
            "news": news,
            "price": price
        }

    html = generate_html(all_data)

    os.makedirs("public",exist_ok=True)
    with open("public/index.html","w",encoding="utf-8") as f:
        f.write(html)

    print("Done")

if __name__=="__main__":
    main()