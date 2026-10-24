from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from archive.sitemaps import ArticleSitemap
from pages.sitemaps import PageSitemap

admin.site.site_header = "Ralph Kinney Bennett Archive"
admin.site.site_title = "Archive admin"
admin.site.index_title = "Manage the archive"

sitemaps = {"pages": PageSitemap, "articles": ArticleSitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("", include("archive.urls")),
    path("", include("pages.urls")),
]
