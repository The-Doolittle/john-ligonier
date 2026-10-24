from html import unescape

import markdown
import nh3
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

ALLOWED_TAGS = {"p", "a", "em", "strong", "blockquote", "ul", "ol", "li", "br", "hr", "h2", "h3"}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}


def render_markdown(text):
    """Convert Markdown to HTML, keeping only the tags articles are allowed to use."""
    html = markdown.markdown(text or "", extensions=["sane_lists"])
    return mark_safe(nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES))


def markdown_to_text(text):
    """Plain text of a Markdown document, for search and excerpts."""
    return unescape(strip_tags(render_markdown(text))).strip()


def make_excerpt(text, words=40):
    """First paragraph of a Markdown document, shortened to a listing-sized excerpt."""
    for block in (text or "").split("\n\n"):
        plain = markdown_to_text(block)
        if plain:
            return Truncator(plain).words(words, truncate="…")
    return ""
