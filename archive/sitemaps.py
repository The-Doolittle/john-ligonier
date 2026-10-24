from django.contrib.sitemaps import Sitemap

from .models import Article


class ArticleSitemap(Sitemap):
    def items(self):
        return Article.objects.published()

    def lastmod(self, article):
        return article.updated_at
