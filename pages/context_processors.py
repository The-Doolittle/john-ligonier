from django.conf import settings
from django.utils import timezone

NAV_SECTIONS = {
    "pages:home": "home",
    "pages:about": "about",
    "pages:obituary": "obituary",
    "archive:article_list": "archives",
    "archive:article_detail": "archives",
    "archive:appearance_list": "appearances",
}


def site(request):
    view_name = request.resolver_match.view_name if request.resolver_match else ""
    return {
        "site_url": settings.SITE_URL,
        "canonical_url": settings.SITE_URL + request.path,
        "current_year": timezone.now().year,
        "nav_section": NAV_SECTIONS.get(view_name, ""),
        "nav_current": "true" if view_name == "archive:article_detail" else "page",
    }
