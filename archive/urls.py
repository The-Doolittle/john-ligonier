from django.urls import path, re_path
from django.views.generic import RedirectView

from . import views
from .legacy import DUPLICATES

app_name = "archive"

urlpatterns = [
    path("archives/", views.article_list, name="article_list"),
    *[
        path(
            f"articles/{duplicate}/",
            RedirectView.as_view(url=f"/articles/{original}/", permanent=True),
        )
        for duplicate, original in DUPLICATES.items()
    ],
    path("articles/<slug:slug>/", views.article_detail, name="article_detail"),
    path("appearances/", views.appearance_list, name="appearance_list"),
    # Addresses used by the old static site.
    re_path(
        r"^articles/(?P<slug>[\w-]+)(?:\.html|/index\.html)$",
        RedirectView.as_view(pattern_name="archive:article_detail", permanent=True),
    ),
]
