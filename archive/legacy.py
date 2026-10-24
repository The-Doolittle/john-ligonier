"""Parsing helpers for the HTML pages of the old static site."""

import re
from datetime import datetime
from html import unescape
from html.parser import HTMLParser

from .formatting import make_excerpt, markdown_to_text

PUBLICATION_NAMES = {
    "Readers Digest": "Reader's Digest",
    # AEI published these in its magazine, The American.
    "American Enterprise Institute": "The American",
    # Found among Ralph's own files; never published.
    "Unreleased": "Unpublished",
}

# 2014 reprints of earlier articles, mapped to the original that replaces them.
DUPLICATES = {
    "this-astounding-enterprise-2": "this-astounding-enterprise",
    "what-a-father-taught-me-2": "what-a-father-taught-me",
}

BYLINE = re.compile(r"^(?:\\?#)*\s*(?:by\s+)?ralph kinney bennett\b", re.IGNORECASE)
IMAGE_EMBED = re.compile(r"!\[\[([^\]]+)\]\]")
EMPHASIS_MARK = re.compile(r"(?<![\w\\])_|_(?!\w)")


class MarkdownWriter(HTMLParser):
    """Convert the small set of tags used in legacy article bodies to Markdown."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.parts = []
        self.prefix = ""
        self.quote_depth = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "div"}:
            self.flush()
        elif tag == "li":
            self.flush()
            self.prefix = "- "
        elif tag == "blockquote":
            self.flush()
            self.quote_depth += 1
        elif tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "a":
            self.links.append((dict(attrs).get("href", ""), len(self.parts)))
            self.parts.append("[")
        elif tag == "br":
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"p", "div", "li", "ul", "ol"}:
            self.flush()
        elif tag == "blockquote":
            self.flush()
            self.quote_depth = max(0, self.quote_depth - 1)
        elif tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "a" and self.links:
            href, index = self.links.pop()
            if href:
                href = href.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
                self.parts.append(f"]({href})")
            else:
                self.parts[index] = ""

    def handle_data(self, data):
        text = data.replace("\\", "\\\\").replace("*", "\\*")
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        self.parts.append(text)

    def flush(self):
        text = re.sub(r"\s+", " ", "".join(self.parts)).strip()
        if text:
            text = escape_block_start(text)
            if self.quote_depth:
                text = "> " + text
            self.blocks.append(self.prefix + text)
        self.parts = []
        self.prefix = ""

    def close(self):
        super().close()
        self.flush()


def escape_block_start(text):
    """Escape characters that Markdown would read as a list or heading at the start of a block."""
    text = re.sub(r"^(\d+)\. ", r"\1\\. ", text)
    return re.sub(r"^([-+#])", r"\\\1", text)


def fix_emphasis(block):
    """Repair underscore italics left over from an earlier Markdown conversion."""
    quote, text = split_quote(block)
    text = re.sub(r"\s+__", "_ _", text)
    if len(EMPHASIS_MARK.findall(text)) % 2:
        if text.startswith("_"):
            text += "_"
        elif text.endswith("_"):
            text = "_" + text
    return quote + text


def split_quote(block):
    """Split a block into its "> " quotation prefix (if any) and its text."""
    if block.startswith("> "):
        return "> ", block[2:]
    return "", block


def plain_link_text(block):
    """Replace Markdown links with their text, for matching bylines."""
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", block)


def parse_byline_date(text):
    for pattern, fmt in [
        (r"\b(\d{1,2} [A-Z][a-z]{2} \d{4})\b", "%d %b %Y"),
        (r"\b([A-Z][a-z]+ \d{1,2}, \d{4})\b", "%B %d, %Y"),
    ]:
        match = re.search(pattern, text)
        if match:
            try:
                return datetime.strptime(match.group(1), fmt).date()
            except ValueError:
                continue
    return None


def simplify(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def parse_article(html, slug):
    """Return a dict of article fields and a list of notes about anything that needed fixing."""
    notes = []
    title_match = re.search(r"<title>(.*?)</title>", html, re.S)
    title = unescape(title_match.group(1)).replace(" | John Ligonier Archive", "").strip()

    start = list(re.finditer(r'<article class="article-body"[^>]*>', html))[-1].end()
    content = html[start : html.rfind("</article>")]

    tags = re.findall(r'<span class="archive-tag tag-(publication|topic)">(.*?)</span>', content)
    publication = next((unescape(value) for kind, value in tags if kind == "publication"), "")
    publication = PUBLICATION_NAMES.get(publication, publication)
    topics = [unescape(value) for kind, value in tags if kind == "topic"]

    content = re.sub(r"<h2[^>]*>.*?</h2>", "", content, count=1, flags=re.S)
    content = re.sub(r'<div class="archive-tags">.*?</div>', "", content, count=1, flags=re.S)

    writer = MarkdownWriter()
    writer.feed(content)
    writer.close()

    published_on = None
    blocks = []
    for index, block in enumerate(writer.blocks):
        if index == 0 and BYLINE.match(plain_link_text(block)):
            published_on = parse_byline_date(block)
            continue
        if index <= 1 and simplify(block) == simplify(title):
            continue
        if block.startswith("©") or block == "Article content is unavailable.":
            continue
        if split_quote(block)[1] == "&gt;":
            continue
        for image in IMAGE_EMBED.findall(block):
            notes.append(f"missing image: {image}")
        block = IMAGE_EMBED.sub("", block).strip()
        block = re.sub(r"^\\?#+\s*", "", block)
        if not block:
            continue
        fixed = fix_emphasis(block)
        if fixed != block:
            notes.append("repaired italics in one paragraph")
        blocks.append(fixed)

    body = "\n\n".join(blocks)
    if not body:
        notes.append("no article text; imported as a draft")
    if published_on is None:
        notes.append("no date found")

    return {
        "slug": slug,
        "title": title,
        "publication": publication,
        "topics": topics,
        "published_on": published_on,
        "body": body,
        "excerpt": listing_excerpt(blocks),
    }, notes


def listing_excerpt(blocks):
    """First real paragraph, skipping editor's notes, quotations and italic epigraphs."""
    for block in blocks:
        text = markdown_to_text(block).lstrip("(").lower()
        if block.startswith((">", "_", "*")) or text.startswith(("editor’s note", "editor's note")):
            continue
        if len(text.split()) >= 12:
            return make_excerpt(block)
    return ""


def parse_appearances(html):
    """Yield appearance fields from the old appearances page."""
    for card in re.findall(r'<article class="video-card[^"]*">(.*?)</article>', html, re.S):
        meta = re.search(r'<p class="video-meta">(.*?)</p>', card, re.S).group(1)
        outlet, _, when = unescape(meta).partition(" / ")
        iframe = re.search(r'<iframe[^>]*src="([^"]+)"', card)
        embed_url = iframe.group(1) if iframe and "youtube" not in iframe.group(1) else ""
        yield {
            "title": unescape(re.search(r"<h3>(.*?)</h3>", card, re.S).group(1)).strip(),
            "outlet": outlet.strip(),
            "appeared_on": datetime.strptime(when.strip(), "%B %d, %Y").date(),
            "description": unescape(re.search(r"</h3>\s*<p>(.*?)</p>", card, re.S).group(1)),
            "watch_url": re.search(r'class="video-link-button" href="([^"]+)"', card).group(1),
            "embed_url": embed_url,
        }
