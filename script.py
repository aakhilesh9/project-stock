import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo
import random
import os
from urllib.parse import quote_plus
import yfinance as yf

STOCKS = ["ANGELONE", "ASIANPAINT", "BAJAJFINANCE", "COALINDIA", "DIVISLAB", "DIXON", "EPIGRAL","FCL", "GAIL", "HDFC BANK", "HDBFS", "ICICI BANK", "INFOSYS","ITC", "KIRLOSENG", "KOTAKBANK", "LAURUSLABS", "MANKIND", "MARICO", "NTPC", "PETRONET", "PFC", "PIIND", "POLYCAB", "POONAWALLA", "RELIANCE", "SBIN", "STYLAMIND", "TATACAP", "TCS", "TMCV", "TMPV", "TRIVENI", "VBL", "ZENTEC"]

# ----------- PRICE FETCH -----------
def get_stock_data(stock):
    mapping = {
        "INFOSYS": "INFY.NS",
        "TCS": "TCS.NS",
        "HDFC BANK": "HDFCBANK.NS",
        "ICICI BANK": "ICICIBANK.NS",
        "RELIANCE": "RELIANCE.NS",
        "SBIN": "SBIN.NS",
        "ITC": "ITC.NS",
        "KOTAKBANK": "KOTAKBANK.NS",
        "BAJAJFINANCE": "BAJFINANCE.NS",
        "ASIANPAINT": "ASIANPAINT.NS",
        "NTPC": "NTPC.NS",
        "COALINDIA": "COALINDIA.NS",
        "DIVISLAB": "DIVISLAB.NS",
        "MARICO": "MARICO.NS",
        "PFC": "PFC.NS",
        "PIIND": "PIIND.NS",
        "POLYCAB": "POLYCAB.NS",
        "VBL": "VBL.NS"
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

    except Exception as e:
        print(f"[ERROR] {stock}: {e}")
        return None


# ----------- NEWS FETCH -----------
def fetch_news(stock):
    query = quote_plus(f"{stock} stock")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)
    entries = feed.entries

    if not entries:
        return []

    return entries[:5]


def format_time(entry):
    try:
        return entry.published
    except AttributeError:
        return "No date"


# ----------- HTML -----------
def generate_html(all_data):
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S IST')

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock News Dashboard</title>

        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                background: #0f172a;
                color: #e2e8f0;
            }}

            .container {{
                max-width: 1100px;
                margin: auto;
                padding: 20px;
            }}

            h1 {{
                text-align: center;
                margin-bottom: 5px;
            }}

            .updated {{
                text-align: center;
                color: #94a3b8;
                font-size: 14px;
                margin-bottom: 30px;
            }}

            .stock {{
                margin-bottom: 40px;
            }}

            .stock-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}

            .price {{
                font-weight: bold;
                font-size: 16px;
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
                transition: 0.2s ease;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}

            .card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.5);
            }}

            .card a {{
                color: #e2e8f0;
                text-decoration: none;
                font-weight: 500;
                display: block;
                margin-bottom: 8px;
            }}

            .time {{
                font-size: 12px;
                color: #94a3b8;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <h1>📈 Stock News Dashboard</h1>
            <div class="updated">Last updated: {now}</div>
    """

    for stock, data in all_data.items():
        articles = data["news"]
        price_data = data["price"]

        if price_data:
            price, change = price_data
            color = "#22c55e" if change >= 0 else "#ef4444"
            price_html = f'<div class="price" style="color:{color}">₹{price} ({change}%)</div>'
        else:
            price_html = '<div class="price">N/A</div>'

        html += f"""
        <div class="stock">
            <div class="stock-header">
                <h2>{stock}</h2>
                {price_html}
            </div>
            <div class="grid">
        """

        if not articles:
            html += '<div>No news found</div>'
        else:
            for a in articles:
                html += f"""
                <div class="card">
                    <a href="{a.link}" target="_blank">{a.title}</a>
                    <div class="time">{format_time(a)}</div>
                </div>
                """

        html += "</div></div>"

    html += "</div></body></html>"
    return html


# ----------- MAIN -----------
def main():
    print("=== Script Started ===")

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

    print("public/index.html written successfully")


if __name__ == "__main__":
    main()
