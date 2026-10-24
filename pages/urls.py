from django.urls import path, re_path

from . import views
from .views import PERSON, PageView

app_name = "pages"

urlpatterns = [
    path(
        "",
        PageView.as_view(
            template_name="pages/home.html",
            description="Writings, appearances and memorial archive of Ralph Kinney Bennett "
            "(1941–2024), Reader's Digest writer and editor and Ligonier historian.",
            structured_data=PERSON,
        ),
        name="home",
    ),
    path(
        "about/",
        PageView.as_view(
            template_name="pages/about.html",
            title="About",
            description="The life of Ralph Kinney Bennett: Ligonier native, Reader's Digest "
            "writer and editor for more than 30 years, and author of Ligonier 250.",
            structured_data=PERSON,
        ),
        name="about",
    ),
    path(
        "obituary/",
        PageView.as_view(
            template_name="pages/obituary.html",
            title="Obituary",
            description="Obituary of Ralph Kinney Bennett, March 3, 1941 – December 18, 2024.",
        ),
        name="obituary",
    ),
    path("share-a-memory/", views.share_memory, name="share_memory"),
    path(
        "share-a-memory/thanks/",
        PageView.as_view(template_name="pages/memory_thanks.html", title="Thank you"),
        name="memory_thanks",
    ),
    path("robots.txt", views.robots_txt, name="robots"),
    re_path(r"^(?P<page>index|about|obituary|archives|appearances)\.html$", views.legacy_page),
]
