import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import format_datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom

URL = "https://www.vectorta.com/insights"
OUTPUT_FILE = "vector-talent-insights.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
}


def parse_date(text):
    for fmt in ("%B %d, %Y", "%B %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def fetch_articles():
    response = requests.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # First pass: build a URL -> date lookup from articles that have clean dates
    # These are the main chronological list items which include "mins" as a separator
    url_to_date = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/article/" not in href:
            continue
        full_url = href if href.startswith("http") else f"https://www.vectorta.com{href}"
        texts = [
            t.strip() for t in a.stripped_strings
            if t.strip() and t.strip().lower() not in ("mins", "min", "1 min", "1 minute", "3 mins", "5 mins")
        ]
        for t in texts:
            parsed = parse_date(t)
            if parsed:
                url_to_date[full_url] = parsed
                break

    # Second pass: collect all articles with title, url, category
    articles = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/article/" not in href:
            continue

        full_url = href if href.startswith("http") else f"https://www.vectorta.com{href}"

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # Strip noise
        texts = [
            t.strip() for t in a.stripped_strings
            if t.strip() and t.strip().lower() not in ("mins", "min", "1 min", "1 minute", "3 mins", "5 mins")
        ]

        title = None
        category = None

        for t in texts:
            # Skip date strings — we'll use the lookup instead
            if parse_date(t):
                continue
            if title is None and len(t) > 8:
                title = t
            elif title is not None and category is None and len(t) < 50:
                category = t

        if not title:
            continue

        # Use the date lookup — covers featured/popular articles that lack inline dates
        pub_date = url_to_date.get(full_url)

        articles.append({
            "title": title,
            "url": full_url,
            "category": category or "",
            "pub_date": pub_date,
        })

    # Sort by date descending, undated items go to the bottom
    articles.sort(key=lambda x: x["pub_date"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    return articles


def build_rss(articles):
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Vector Talent Insights"
    ET.SubElement(channel, "link").text = "https://www.vectorta.com/insights"
    ET.SubElement(channel, "description").text = (
        "Recruitment, talent development and industry trends for CDMO & CRO "
        "organisations from Vector Talent."
    )
    ET.SubElement(channel, "language").text = "en-gb"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/vector-talent-insights.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for article in articles:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = article["title"]
        ET.SubElement(item, "link").text = article["url"]
        if article["category"]:
            ET.SubElement(item, "category").text = article["category"]
        if article["pub_date"]:
            ET.SubElement(item, "pubDate").text = format_datetime(article["pub_date"])
        ET.SubElement(item, "guid").text = article["url"]

    return rss


def prettify(element):
    raw = ET.tostring(element, encoding="unicode")
    dom = xml.dom.minidom.parseString(f'<?xml version="1.0" encoding="UTF-8"?>{raw}')
    pretty = dom.toprettyxml(indent="  ", encoding=None)
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)


def main():
    print("Fetching articles from Vector Talent Insights...")
    articles = fetch_articles()
    print(f"Found {len(articles)} articles.")

    # Print first 5 to verify dates are correct
    for a in articles[:5]:
        print(f"  {a['pub_date'].strftime('%d %b %Y') if a['pub_date'] else 'NO DATE'} | {a['title']}")

    rss = build_rss(articles)
    xml_str = prettify(rss)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"\nFeed written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
