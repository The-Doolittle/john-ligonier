from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class PageSitemap(Sitemap):
    def items(self):
        return [
            "pages:home",
            "pages:about",
            "pages:obituary",
            "archive:article_list",
            "archive:appearance_list",
        ]

    def location(self, item):
        return reverse(item)
