from django.contrib import admin
from django.db.models import Count

from .models import Appearance, Article, Publication, Topic


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "publication", "published_on", "status", "updated_at"]
    list_filter = ["status", "publication", "topics"]
    search_fields = ["title", "body"]
    date_hierarchy = "published_on"
    prepopulated_fields = {"slug": ["title"]}
    filter_horizontal = ["topics"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["publish", "unpublish"]
    fieldsets = [
        (None, {"fields": ["title", "slug", "status"]}),
        ("Details", {"fields": ["publication", "published_on", "topics", "source_url"]}),
        ("Text", {"fields": ["excerpt", "body"]}),
        ("History", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    @admin.action(description="Publish selected articles")
    def publish(self, request, queryset):
        queryset.update(status=Article.Status.PUBLISHED)

    @admin.action(description="Move selected articles back to draft")
    def unpublish(self, request, queryset):
        queryset.update(status=Article.Status.DRAFT)


class ArticleCountAdmin(admin.ModelAdmin):
    list_display = ["name", "article_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(article_count=Count("articles"))

    @admin.display(description="Articles", ordering="article_count")
    def article_count(self, obj):
        return obj.article_count


admin.site.register(Publication, ArticleCountAdmin)
admin.site.register(Topic, ArticleCountAdmin)


@admin.register(Appearance)
class AppearanceAdmin(admin.ModelAdmin):
    list_display = ["title", "outlet", "appeared_on"]
    list_filter = ["outlet"]
    search_fields = ["title", "description"]
    date_hierarchy = "appeared_on"
