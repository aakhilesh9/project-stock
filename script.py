import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
import os
import yfinance as yf

STOCKS = ["ANGELONE", "ASIANPAINT", "BAJAJFINANCE", "COALINDIA", "DIVISLAB",
          "DIXON", "EPIGRAL", "FCL", "GAIL", "HDFC BANK", "HDBFS",
          "ICICI BANK", "INFOSYS", "ITC", "KIRLOSENG", "KOTAKBANK",
          "LAURUSLABS", "MANKIND", "MARICO", "NTPC", "PETRONET",
          "PFC", "PIIND", "POLYCAB", "POONAWALLA", "RELIANCE",
          "SBIN", "STYLAMIND", "TATACAP", "TCS", "TMCV",
          "TMPV", "TRIVENI", "VBL", "ZENTEC"]


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
        "TMCV": "TMCV.NS", 
        "TMPV": "TMPV.NS",
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


# ----------- FILTER -----------
def is_relevant(title):
    title = title.lower()
    bad_keywords = [
        "ad", "sponsored", "live updates", "watch live",
        "youtube", "instagram", "tweet"
    ]
    return not any(word in title for word in bad_keywords)


# ----------- NEWS FETCH (LATEST + TRENDING) -----------
def fetch_news(stock, mode="latest", max_items=5):
    query = quote_plus(f"{stock} stock")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)

    seen = set()
    filtered = []

    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    cutoff = now - timedelta(days=30 if mode == "latest" else 90)

    for entry in feed.entries:
        title = entry.title.strip()

        if title in seen:
            continue

        if not is_relevant(title):
            continue

        published = getattr(entry, "published_parsed", None)
        if not published:
            continue

        pub_date = datetime(*published[:6], tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Kolkata"))

        if pub_date < cutoff:
            continue

        seen.add(title)
        filtered.append(entry)

        if len(filtered) == max_items:
            break

    return filtered


def format_time(entry):
    return getattr(entry, "published", "No date")


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
        :root {{
            --bg: #0f172a;
            --text: #e2e8f0;
            --card: #1e293b;
            --muted: #94a3b8;
        }}

        body.light {{
            --bg: #f5f5f5;
            --text: #1e293b;
            --card: #ffffff;
            --muted: #555;
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
            padding: 20px;
        }}

        .toggle {{
            text-align: right;
        }}

        button {{
            margin-left: 5px;
            padding: 6px 12px;
            border-radius: 8px;
            cursor: pointer;
        }}

        .updated {{
            text-align: center;
            color: var(--muted);
            margin-bottom: 20px;
        }}

        .stock-header {{
            display: flex;
            justify-content: space-between;
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
        }}

        .time {{
            font-size: 12px;
            color: var(--muted);
        }}
        </style>
    </head>

    <body>
        <div class="container">
            <h1>📈 Portfolio Stock News</h1>

            <div class="toggle">
                <button onclick="toggleTheme()">Theme</button>
                <button onclick="toggleNewsMode()">Latest / Trending</button>
            </div>

            <div class="updated">Last updated: {now}</div>
    """

    for stock, data in all_data.items():
        price_data = data["price"]

        if price_data:
            price, change = price_data
            color = "#22c55e" if change >= 0 else "#ef4444"
            price_html = f'<div class="price" style="color:{color}">₹{price} ({change}%)</div>'
        else:
            price_html = '<div class="price">N/A</div>'

        html += f"""
        <div>
            <div class="stock-header">
                <h2>{stock}</h2>
                {price_html}
            </div>
            <div class="grid">
        """

        # LATEST
        html += '<div class="news latest">'
        for a in data["latest"]:
            html += f"""
            <div class="card">
                <a href="{a.link}" target="_blank">{a.title}</a>
                <div class="time">{format_time(a)}</div>
            </div>
            """
        html += "</div>"

        # TRENDING
        html += '<div class="news trending" style="display:none;">'
        for a in data["trending"]:
            html += f"""
            <div class="card">
                <a href="{a.link}" target="_blank">{a.title}</a>
                <div class="time">{format_time(a)}</div>
            </div>
            """
        html += "</div>"

        html += "</div></div>"

    html += """
        </div>

        <script>
        function toggleTheme() {
            document.body.classList.toggle("light");
            localStorage.setItem("theme",
                document.body.classList.contains("light") ? "light" : "dark"
            );
        }

        function toggleNewsMode() {
            const latest = document.querySelectorAll(".latest");
            const trending = document.querySelectorAll(".trending");

            const isLatestVisible = latest[0].style.display !== "none";

            latest.forEach(el => el.style.display = isLatestVisible ? "none" : "block");
            trending.forEach(el => el.style.display = isLatestVisible ? "block" : "none");

            localStorage.setItem("newsMode", isLatestVisible ? "trending" : "latest");
        }

        window.onload = function() {
            if (localStorage.getItem("theme") === "light") {
                document.body.classList.add("light");
            }

            if (localStorage.getItem("newsMode") === "trending") {
                toggleNewsMode();
            }
        }
        </script>

    </body>
    </html>
    """

    return html


# ----------- MAIN -----------
def main():
    print("=== Script Started ===")

    all_data = {}

    for stock in STOCKS:
        print(f"Fetching {stock}...")

        latest_news = fetch_news(stock, mode="latest")
        trending_news = fetch_news(stock, mode="trending")
        price = get_stock_data(stock)

        all_data[stock] = {
            "latest": latest_news,
            "trending": trending_news,
            "price": price
        }

    html = generate_html(all_data)

    os.makedirs("public", exist_ok=True)

    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("public/index.html written successfully")


if __name__ == "__main__":
    main()