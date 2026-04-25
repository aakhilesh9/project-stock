import feedparser
from datetime import datetime
import random
import os

STOCKS = ["Infosys", "HDFC Bank", "TCS"]

def fetch_news(stock):
    url = f"https://news.google.com/rss/search?q={stock}+stock&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    entries = feed.entries

    if not entries:
        print(f"[WARN] No news found for {stock}")
        return []

    random.shuffle(entries)  # ensures visible change
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
        <title>Stock News Dashboard</title>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f5f5f5;
            }}
            h1 {{
                color: #333;
            }}
            h2 {{
                color: #444;
                margin-top: 30px;
            }}
            ul {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            li {{
                margin-bottom: 10px;
            }}
            a {{
                text-decoration: none;
                color: #1a0dab;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .time {{
                color: gray;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <h1>Stock News Dashboard</h1>
        <p><b>Last updated:</b> {now}</p>
    """

    for stock, articles in all_news.items():
        html += f"<h2>{stock}</h2><ul>"

        if not articles:
            html += "<li>No news found</li>"
        else:
            for a in articles:
                title = a.title
                link = a.link
                published = format_time(a)

                html += f"""
                <li>
                    <a href="{link}" target="_blank">{title}</a><br>
                    <span class="time">{published}</span>
                </li>
                """

        html += "</ul>"

    html += "</body></html>"

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

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("index.html written")
    print("Current directory:", os.getcwd())
    print("Files in directory:", os.listdir())

if __name__ == "__main__":
    main()
