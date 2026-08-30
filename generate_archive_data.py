#!/usr/bin/env python3
import json
import re
from html import escape, unescape
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = SITE_ROOT / "generated"
ARTICLES_DIR = SITE_ROOT / "articles"
MANUAL_TAGS_FILE = SITE_ROOT / "manual-archive-tags.json"
DEFAULT_TOPIC_OPTIONS = [
    "Automotive",
    "Business",
    "Communication",
    "Culture",
    "Faith",
    "Family",
    "General Interest",
    "History",
    "Ideas",
    "Middle East",
    "Military",
    "Politics",
    "Science",
    "Security",
    "Sports",
    "Technology",
    "Transportation",
    "War",
]

MANUAL_TOPICS = {
    "you-have-a-telegram": ["Communication", "Culture"],
    "100-years-of-fill-er-up": ["Automotive", "History"],
    "americans-in-the-age-of-parody": ["Culture", "Politics"],
    "an-american-thanksgiving": ["Faith", "Family"],
    "an-ugly-little-reality": ["War", "Politics"],
    "armor-all": ["Military", "Technology"],
    "automobility-the-secrets-of-their-success": ["Automotive", "Business"],
    "confronting-he-who-confronts": ["War", "Politics"],
    "courage-in-profiles": ["Security", "Politics"],
    "death-duty-d-day": ["History", "Military"],
    "dieselmania": ["Automotive", "Technology"],
    "dreaming-of-a-remote-christmas": ["Family", "Culture"],
    "duty-and-sacrifice": ["History", "Military"],
    "electrobooks-at-last": ["Technology", "Culture"],
    "evoking-a-splendid-legend": ["Automotive", "History"],
    "fallen-heroes-never-forgotten": ["History", "Faith"],
    "faster-faster": ["Automotive", "History"],
    "funny-thing-about-christmas": ["Faith", "Culture"],
    "gangland-slaying": ["War", "Politics"],
    "glovology": ["Sports", "History"],
    "go-and-find-a-soldiers-grave": ["Military", "History"],
    "goodbye-jelly-bean": ["Automotive", "Business"],
    "happy-gathering": ["Family", "Culture"],
    "happy-gremlin-day": ["Automotive", "Culture"],
    "highway-to-heaven": ["Transportation", "History"],
    "how-honest-are-we": ["Politics", "Culture"],
    "is-the-electric-emperor-naked": ["Technology", "Automotive"],
    "long-shot": ["Sports", "History"],
    "man-without-honor": ["Military", "History"],
    "marines-notice-things": ["Military", "Security"],
    "maybe-now-well-get-it": ["Middle East", "Politics"],
    "merry-christmas": ["Faith", "Culture"],
    "more-than-hezbollah-can-chew": ["Middle East", "Military"],
    "razor-wars-and-the-cutting-edge-of-technology": ["Technology", "Culture"],
    "remembering-with-pain-anger-and-vigilance": ["History", "Politics"],
    "roadside-bombs-the-hydra-effect": ["Military", "Technology"],
    "routine-evil": ["War", "Politics"],
    "small-car-big-shadow": ["Automotive", "History"],
    "technology-on-top-appreciating-the-luxury-learning-curve": ["Technology", "Automotive"],
    "telling-the-difference-between-hamas-and-shinola": ["Middle East", "Politics"],
    "tennis-with-milton": ["Sports", "Ideas"],
    "the-2500-car": ["Automotive", "Business"],
    "the-automobiles-forgotten-secret": ["Automotive", "Culture"],
    "the-elegant-jeep": ["Automotive", "History"],
    "the-gas-pedal-sticks-the-market-works-the-hyperventilation-increases": ["Automotive", "Business"],
    "the-guardians": ["Military", "Faith"],
    "the-passing-of-pontiac": ["Automotive", "Business"],
    "the-pseudo-scientists-of-earthism": ["Science", "Politics"],
    "the-u-9-and-the-realm-of-the-unexpected": ["History", "Military"],
    "this-astounding-enterprise": ["History", "Faith"],
    "truckin": ["Automotive", "Culture"],
    "what-a-father-taught-me": ["Family", "Faith"],
    "what-did-mr-murtha-mean": ["Politics", "Culture"],
}


def decode_html_entities(value: str) -> str:
    decoded = value or ""
    for _ in range(8):
        next_value = unescape(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return decoded


def clean_html_text(value: str) -> str:
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = decode_html_entities(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_content_block(html: str) -> str:
    # Some article files have gotten mangled by repeat runs into having multiple
    # opening <article class="article-body"> tags but only one real closing tag
    # (an entire duplicate page nested inside the article body). Anchoring on the
    # LAST opening tag and the LAST closing tag - rather than a naive lazy regex
    # match, which grabs everything between the FIRST opening tag and the only
    # closing tag, swallowing the nested duplicate - reliably isolates the
    # innermost, real content in both the malformed and well-formed cases.
    opens = list(re.finditer(r'<article class="article-body"[^>]*>', html, flags=re.I))
    if opens:
        start = opens[-1].end()
        end = html.rfind("</article>")
        if end != -1 and end > start:
            return html[start:end]
        return html[start:]

    for pattern in [
        r'<main[^>]*>(.*?)</main>',
        r'<body[^>]*>(.*?)</body>'
    ]:
        match = re.search(pattern, html, flags=re.I | re.S)
        if match:
            content = match.group(1)
            inner = re.search(r'<article[^>]*>(.*?)</article>', content, flags=re.I | re.S)
            if inner:
                return inner.group(1)
            return content
    return html


def extract_title(html: str, fallback: str) -> str:
    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    if title_match:
        title = decode_html_entities(title_match.group(1).strip())
        if " | John Ligonier Archive" in title:
            title = title.replace(" | John Ligonier Archive", "")
        return title

    content = extract_content_block(html)
    h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", content, flags=re.I | re.S)
    if h2_match:
        cleaned = clean_html_text(h2_match.group(1))
        if cleaned:
            return cleaned

    return fallback


def extract_meta(html: str):
    content = extract_content_block(html)
    meta_match = re.search(r'<p class="archive-meta">(.*?)</p>', content, flags=re.I | re.S)
    if not meta_match:
        return "General", ""

    meta = clean_html_text(meta_match.group(1))
    if "·" in meta:
        category, year = [part.strip() for part in meta.split("·", 1)]
        return category, year

    if "-" in meta:
        category, year = [part.strip() for part in meta.split("-", 1)]
        return category, year

    return "General", meta


def normalize_tag(value: str) -> str:
    if value is None:
        return ""

    tag = str(value).strip()
    if not tag:
        return ""

    tag = tag.replace("&amp;", " and ").replace("&", " and ")
    tag = tag.replace("·", " ")
    tag = re.sub(r"[^A-Za-z0-9\s&/.-]", "", tag)
    tag = re.sub(r"\s+", " ", tag).strip()
    return tag or "General"


def infer_topics(title: str, category: str, slug: str = "") -> list[str]:
    title_text = title.lower()
    category_text = category.lower()
    if slug and slug in MANUAL_TOPICS:
        return MANUAL_TOPICS[slug][:2]

    topic_patterns = {
        "History": ["history", "heritage", "legacy", "century", "anniversary", "memoir", "remembering", "veterans", "day"],
        "Faith": ["faith", "church", "religion", "spiritual", "sermon", "prayer", "thanksgiving", "christmas"],
        "Education": ["education", "school", "teacher", "learning", "students", "academy"],
        "Books": ["book", "books", "literature", "author", "reading", "publication", "digest"],
        "Community": ["community", "people", "civic", "society", "neighbors", "family"],
        "Leadership": ["leadership", "leader", "service", "public", "vision", "courage"],
        "Travel": ["travel", "journey", "trip", "road", "tour", "highway", "interstate"],
        "Humor": ["humor", "funny", "wit", "story", "laughter", "parody"],
        "Business": ["business", "market", "industry", "enterprise", "commerce", "automaker", "car"],
        "Politics": ["politics", "government", "state", "campaign", "public service", "election", "policy"],
        "Military": ["military", "war", "soldier", "veteran", "battle", "army", "navy", "marine"],
        "Technology": ["technology", "digital", "electric", "device", "engineering", "innovation"],
        "Automotive": ["automobile", "car", "truck", "vehicle", "automotive", "ford", "toyota", "jeep"],
        "Culture": ["culture", "american", "society", "holiday", "christmas", "media", "parody"],
        "Sports": ["baseball", "football", "tennis", "sport", "golf", "racing"],
        "Science": ["science", "climate", "research", "study", "theory"],
        "Middle East": ["israel", "lebanon", "hezbollah", "hamas", "iraq", "middle east"],
    }

    matches = []
    for topic, patterns in topic_patterns.items():
        lowered_topic = topic.lower()
        if lowered_topic in {"general interest", "general"}:
            continue
        if any(pattern in title_text or pattern in category_text for pattern in patterns):
            matches.append(topic)

    seen = set()
    filtered = []
    for item in matches:
        key = item.lower()
        if key in seen:
            continue
        if key == normalize_tag(category).lower():
            continue
        seen.add(key)
        filtered.append(item)

    if not filtered:
        filtered = ["General Interest"]

    return filtered[:2]


def extract_excerpt(html: str) -> str:
    content = extract_content_block(html)
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", content, flags=re.I | re.S)
    for paragraph in paragraphs:
        text = clean_html_text(paragraph)
        if not text:
            continue
        if text.startswith("By ") or text.startswith("######"):
            continue
        if text.startswith("©"):
            continue
        return text[:200] + ("..." if len(text) > 200 else "")
    return ""


def strip_leading_meta_blocks(body: str) -> str:
    cleaned = (body or "").strip()
    for _ in range(12):
        updated = re.sub(r"^\s*(?:<p class=\"archive-meta\">.*?</p>\s*)+", "", cleaned, flags=re.S | re.I)
        updated = re.sub(r"^\s*(?:<div class=\"archive-tags\">.*?</div>\s*)+", "", updated, flags=re.S | re.I)
        updated = re.sub(r"^\s*<h2[^>]*>.*?</h2>\s*", "", updated, count=1, flags=re.S | re.I)
        if updated == cleaned:
            break
        cleaned = updated
    return cleaned.strip()


def build_manual_tag_template() -> dict:
    template = {
        "topic_options": DEFAULT_TOPIC_OPTIONS,
        "articles": {},
    }

    for html_path in sorted(ARTICLES_DIR.glob("*.html")):
        if html_path.name.startswith(".") or html_path.name == "article-template.html":
            continue

        html = html_path.read_text(encoding="utf-8", errors="replace")
        title = extract_title(html, html_path.stem.replace("-", " ").title())
        template["articles"][html_path.stem] = {
            "title": title,
            "publication": "",
            "year": "",
            "topics": [],
        }

    return template


def load_manual_tag_data() -> dict:
    if not MANUAL_TAGS_FILE.exists():
        MANUAL_TAGS_FILE.write_text(json.dumps(build_manual_tag_template(), indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        with MANUAL_TAGS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        data = {"topic_options": DEFAULT_TOPIC_OPTIONS, "articles": {}}

    if not isinstance(data, dict):
        data = {"topic_options": DEFAULT_TOPIC_OPTIONS, "articles": {}}
    if "topic_options" not in data or not isinstance(data["topic_options"], list):
        data["topic_options"] = DEFAULT_TOPIC_OPTIONS
    if "articles" not in data or not isinstance(data["articles"], dict):
        data["articles"] = {}

    return data


def article_page_html(article: dict) -> str:
    title = escape(article["title"])
    body = strip_leading_meta_blocks(article.get("body_html", ""))
    if not body:
        body = "<p>Article content is unavailable.</p>"

    tags = []
    publication = escape(article.get("publication") or article.get("category") or "General")
    year_value = escape(article.get("year") or "Undated")
    tags.append(f'<span class="archive-tag tag-publication">{publication}</span>')
    tags.append(f'<span class="archive-tag tag-year">{year_value}</span>')
    for topic in article.get("topics", [])[:3]:
        tags.append(f'<span class="archive-tag tag-topic">{escape(str(topic))}</span>')

    tag_html = f'<div class="archive-tags">{"".join(tags)}</div>'

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{title} | John Ligonier Archive</title>
  <link rel=\"stylesheet\" href=\"../../style.css\" />
</head>
<body>
  <header>
    <h1>Ralph Kinney Bennett</h1>
    <div class=\"pseudonym\">March 3, 1941 – December 18, 2024</div>
    <nav>
      <a href=\"../../\">Home</a>
      <a href=\"../../about\">About</a>
      <a href=\"../../obituary\">Obituary</a>
      <a href=\"../../archives\" class=\"active\">Archives</a>
      <a href=\"../../appearances\">Appearances</a>
    </nav>
  </header>
  <main class=\"article-page\">
    <div class=\"article-shell\">
      <div class=\"article-card\">
        <div class=\"article-card-header\">
          <a href=\"../../archives\" class=\"archive-back-link\">← Back to Archives</a>
        </div>
        <article class=\"article-body\">
          <h2>{title}</h2>

          {tag_html}
          {body}
        </article>
      </div>
    </div>
  </main>
  <footer>
    <p>© 2026 The Memorial Archive of Ralph Bennett. Maintained with love by his family.</p>
  </footer>
  <script src=\"../script.js\"></script>
</body>
</html>
"""


def main():
    if not ARTICLES_DIR.exists():
        raise FileNotFoundError(f"Articles directory not found: {ARTICLES_DIR}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    manual_tag_data = load_manual_tag_data()

    articles = []
    for html_path in sorted(ARTICLES_DIR.glob("*.html")):
        if html_path.name.startswith("."):
            continue
        if html_path.name == "article-template.html":
            continue

        html = html_path.read_text(encoding="utf-8", errors="replace")
        title = extract_title(html, html_path.stem.replace("-", " ").title())
        category, year = extract_meta(html)
        manual_entry = (manual_tag_data.get("articles") or {}).get(html_path.stem, {})

        publication_manual = str(manual_entry.get("publication", "")).strip()
        year_manual = str(manual_entry.get("year", "")).strip()
        topics_manual = [
            str(item).strip()
            for item in (manual_entry.get("topics", []) or [])
            if str(item).strip()
        ]

        publication = normalize_tag(publication_manual) or normalize_tag(category) or "General"
        year_value = year_manual or (year.strip() if year.strip() else "Undated")
        topics = [normalize_tag(item) for item in topics_manual if normalize_tag(item)]
        if not topics:
            topics = infer_topics(title, publication, html_path.stem)

        excerpt = extract_excerpt(html)

        content_block = extract_content_block(html)
        cleaned_body = content_block.strip() if content_block.strip() else html.strip()
        cleaned_body = re.sub(r"^\s*<!DOCTYPE html>.*?<body[^>]*>", "", cleaned_body, count=1, flags=re.S | re.I)
        cleaned_body = re.sub(r"</body>.*$", "", cleaned_body, count=1, flags=re.S | re.I)
        cleaned_body = re.sub(r"^\s*<main[^>]*>", "", cleaned_body, count=1, flags=re.S | re.I)
        cleaned_body = re.sub(r"</main>\s*$", "", cleaned_body, count=1, flags=re.S | re.I)
        cleaned_body = re.sub(r"^\s*<div class=\"article-shell\">\s*<div class=\"article-card\">\s*<div class=\"article-card-header\">.*?</div>\s*", "", cleaned_body, count=1, flags=re.S | re.I)
        cleaned_body = re.sub(r"\s*</div>\s*</div>\s*</div>\s*$", "", cleaned_body, count=1, flags=re.S | re.I)
        cleaned_body = strip_leading_meta_blocks(cleaned_body)
        cleaned_body = cleaned_body.strip()

        article_data = {
            "title": title,
            "year": year_value,
            "category": publication,
            "publication": publication,
            "topics": topics,
            "tags": [publication, year_value, *topics],
            "excerpt": excerpt,
            "slug": html_path.stem,
            "source": html_path.name,
            "link": f"articles/{html_path.stem}",
            "body_html": cleaned_body,
        }
        articles.append(article_data)

        article_dir = ARTICLES_DIR / html_path.stem
        article_dir.mkdir(exist_ok=True)
        (article_dir / "index.html").write_text(article_page_html(article_data), encoding="utf-8")

    articles.sort(key=lambda item: item["title"].lower())

    payload = {"articles": articles}
    OUTPUT_DIR.joinpath("archive-data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(articles)} archive entries at {OUTPUT_DIR / 'archive-data.json'}")


if __name__ == "__main__":
    main()
