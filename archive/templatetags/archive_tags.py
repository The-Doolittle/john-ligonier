from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from archive.views import HIGHLIGHT_START, HIGHLIGHT_STOP

register = template.Library()


@register.filter
def highlight(text):
    """Escape a search headline, then turn its match markers into <mark> tags."""
    escaped = escape(text)
    return mark_safe(escaped.replace(HIGHLIGHT_START, "<mark>").replace(HIGHLIGHT_STOP, "</mark>"))
