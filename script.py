import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
import os

STOCKS = [
    "ANGELONE", "ASIANPAINT", "BAJAJFINANCE", "COALINDIA", "DIVISLAB",
    "DIXON", "EPIGRAL", "FCL", "GAIL", "HDFC BANK", "HDBFS",
    "ICICI BANK", "INFOSYS", "ITC", "KIRLOSENG", "KOTAKBANK",
    "LAURUSLABS", "MANKIND", "MARICO", "NTPC", "PETRONET",
    "PFC", "PIIND", "POLYCAB", "POONAWALLA", "RELIANCE",
    "SBIN", "STYLAMIND", "TATACAP", "TCS", "TMCV",
    "TMPV", "TRIVENI", "VBL", "ZENTEC"
]

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
def generate_html(all_news):
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S IST')

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock News Dashboard</title>

        <style>
        :root {{
            --bg: #0f172a;
            --text: #e2e8f0;
            --card: #1e293b;
            --muted: #94a3b8;
            --accent: #38bdf8;
        }}

        body.light {{
            --bg: #f5f5f5;
            --text: #1e293b;
            --card: #ffffff;
            --muted: #555;
            --accent: #2563eb;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            background: var(--bg);
            color: var(--text);
            transition: 0.3s ease;
        }}

        .container {{
            max-width: 1100px;
            margin: auto;
            padding: 20px;
        }}

        h1 {{
            text-align: center;
        }}

        .toggle {{
            text-align: right;
            margin-bottom: 10px;
        }}

        button {{
            background: var(--card);
            color: var(--text);
            border: 1px solid var(--muted);
            padding: 6px 12px;
            border-radius: 8px;
            cursor: pointer;
        }}

        .updated {{
            text-align: center;
            color: var(--muted);
            font-size: 14px;
            margin-bottom: 25px;
        }}

        .stock {{
            margin-bottom: 40px;
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
            transition: 0.2s ease;
        }}

        .card:hover {{
            transform: translateY(-4px);
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
        </style>
    </head>

    <body>
        <div class="container">
            <h1>📈 Stock News Dashboard</h1>

            <div class="toggle">
                <button onclick="toggleTheme()">Toggle Theme</button>
            </div>

            <div class="updated">Last updated: {now}</div>
    """

    for stock, articles in all_news.items():
        html += f"""
        <div class="stock">
            <h2>{stock}</h2>
            <div class="grid">
        """

        if not articles:
            html += "<div>No news found</div>"
        else:
            for a in articles:
                html += f"""
                <div class="card">
                    <a href="{a.link}" target="_blank">{a.title}</a>
                    <div class="time">{format_time(a)}</div>
                </div>
                """

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

        window.onload = function() {
            const saved = localStorage.getItem("theme");
            if (saved === "light") {
                document.body.classList.add("light");
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

    all_news = {}

    for stock in STOCKS:
        print(f"Fetching {stock}...")
        news = fetch_news(stock)
        all_news[stock] = news

    html = generate_html(all_news)

    os.makedirs("public", exist_ok=True)

    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("public/index.html written successfully")


if __name__ == "__main__":
    main()
