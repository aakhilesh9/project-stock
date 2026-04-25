import feedparser
from datetime import datetime

STOCKS = ["Infosys", "HDFC Bank", "TCS"]

def fetch_news(stock):
    url = f"https://news.google.com/rss/search?q={stock}+stock&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    return feed.entries[:5]

def generate_html(all_news):
    html = f"<html><head><title>Stock News</title></head><body>"
    html += f"<h1>Stock News Dashboard</h1>"
    html += f"<p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"

    for stock, articles in all_news.items():
        html += f"<h2>{stock}</h2><ul>"
        for a in articles:
            html += f"<li><a href='{a.link}'>{a.title}</a></li>"
        html += "</ul>"

    html += "</body></html>"
    return html

def main():
    all_news = {}
    for stock in STOCKS:
        all_news[stock] = fetch_news(stock)

    html = generate_html(all_news)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
