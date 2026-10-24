import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# Same escaping as Django's json_script, so text can't close the <script> tag early.
JSON_ESCAPES = {ord(">"): "\\u003E", ord("<"): "\\u003C", ord("&"): "\\u0026"}


@register.filter
def json_ld(data):
    """Render a dict as a JSON-LD structured data script tag."""
    payload = json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False).translate(JSON_ESCAPES)
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(payload))
