import feedparser
from datetime import datetime
import random
import os

STOCKS = ["Infosys", "HDFC+Bank", "TCS", "ANGELONE", "ASIANPAINT", "BAJAJFINANCE", "COALINDIA", "DIVISLAB", "DIXON", "EPIGRAL","FCL", "GAIL", "HDBFS", "ICICI+BANK", "ITC", "KIRLOSENG", "KOTAKBANK", "LAURUSLABS", "MANKIND", "MARICO", "NTPC", "PETRONET", "PFC", "PIIND", "POLYCAB", "POONAWALLA", "RELIANCE", "SBIN", "STYLAMIND", "TATACAP", "TCS", "TMCV", "TMPV", "TRIVENI", "VBL", "ZENTEC"]

def fetch_news(stock):
    url = f"https://news.google.com/rss/search?q={stock}+stock&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    entries = feed.entries

    if not entries:
        print(f"[WARN] No news found for {stock}")
        return []

    return entries[:5]

def format_time(entry):
    try:
        return entry.published
    except AttributeError:
        return "No date"

def generate_html(all_news):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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

            .stock h2 {{
                margin-bottom: 15px;
                color: #38bdf8;
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

            .card a:hover {{
                color: #38bdf8;
            }}

            .time {{
                font-size: 12px;
                color: #94a3b8;
            }}

            .empty {{
                color: #94a3b8;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <h1>📈 Stock News Dashboard</h1>
            <div class="updated">Last updated: {now}</div>
    """

    for stock, articles in all_news.items():
        html += f"""
        <div class="stock">
            <h2>{stock}</h2>
            <div class="grid">
        """

        if not articles:
            html += '<div class="empty">No news found</div>'
        else:
            for a in articles:
                title = a.title
                link = a.link
                published = format_time(a)

                html += f"""
                <div class="card">
                    <a href="{link}" target="_blank">{title}</a>
                    <div class="time">{published}</div>
                </div>
                """

        html += "</div></div>"

    html += """
        </div>
    </body>
    </html>
    """

    return html


def main():
    print("=== Script Started ===")

    all_news = {}

    for stock in STOCKS:
        print(f"Fetching news for {stock}...")
        news = fetch_news(stock)
        print(f"{stock}: {len(news)} articles fetched")
        all_news[stock] = news

    print("Generating HTML...")
    html = generate_html(all_news)

    # NEW: Create a dedicated public folder for the website
    os.makedirs("public", exist_ok=True)

    # NEW: Write the HTML file into the public folder
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("public/index.html written successfully")

if __name__ == "__main__":
    main()
