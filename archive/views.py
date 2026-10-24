import re

from django.conf import settings
from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.core.paginator import Paginator
from django.db.models import Count, Exists, F, OuterRef, Q, Value
from django.db.models.functions import ExtractYear
from django.shortcuts import get_object_or_404, render
from django.utils.cache import patch_vary_headers

from .models import Appearance, Article, Publication, Topic

PAGE_SIZE = 20
SORTS = {
    "relevance": "Best match",
    "newest": "Newest first",
    "oldest": "Oldest first",
    "title": "Title A–Z",
}
ORDERINGS = {
    "newest": [F("published_on").desc(nulls_last=True), "title"],
    "oldest": [F("published_on").asc(nulls_last=True), "title"],
    "title": ["title"],
}
# Brackets that never appear in article text; swapped for <mark> after escaping.
HIGHLIGHT_START = "⟦"
HIGHLIGHT_STOP = "⟧"


def prefix_query(text):
    """Postgres query matching every word in `text` as a prefix, so "pont" finds "Pontiac"."""
    words = re.findall(r"[^\W_]+", text)
    if not words:
        return None
    return SearchQuery(
        " & ".join(f"{word}:*" for word in words), search_type="raw", config="english"
    )


def search(articles, text):
    """Filter to articles matching `text` in the title, body, publication or a topic name."""
    vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("body_text", weight="B", config="english")
        + SearchVector("publication__name", weight="C", config="english")
    )
    topic_match = Topic.articles.through.objects.filter(
        article=OuterRef("pk"), topic__name__iexact=text
    )
    articles = articles.annotate(topic_match=Exists(topic_match))
    matches = Q(title__icontains=text) | Q(topic_match=True)

    query = prefix_query(text)
    if query is None:
        return articles.filter(matches).annotate(rank=Value(0.0))

    return (
        articles.annotate(search=vector, rank=SearchRank(vector, query))
        .filter(matches | Q(search=query))
        .annotate(
            headline=SearchHeadline(
                "body_text",
                query,
                config="english",
                start_sel=HIGHLIGHT_START,
                stop_sel=HIGHLIGHT_STOP,
                max_words=30,
                min_words=15,
            )
        )
    )


def year_value(raw):
    if raw == "undated" or (raw.isdigit() and len(raw) == 4):
        return raw
    return ""


def article_list(request):
    q = request.GET.get("q", "").strip()[:200]
    publication = Publication.objects.filter(slug=request.GET.get("publication", "")).first()
    topic = Topic.objects.filter(slug=request.GET.get("topic", "")).first()
    year = year_value(request.GET.get("year", ""))

    articles = Article.objects.published().select_related("publication").prefetch_related("topics")
    if q:
        articles = search(articles, q)

    filters = {}
    if publication:
        filters["publication"] = Q(publication=publication)
    if topic:
        filters["topic"] = Q(topics=topic)
    if year == "undated":
        filters["year"] = Q(published_on__isnull=True)
    elif year:
        filters["year"] = Q(published_on__year=int(year))

    def filtered(exclude=None):
        result = articles
        for name, condition in filters.items():
            if name != exclude:
                result = result.filter(condition)
        return result

    sort = request.GET.get("sort", "")
    if sort not in SORTS or (sort == "relevance" and not q):
        sort = "relevance" if q else "newest"
    results = filtered()
    if sort == "relevance":
        results = results.order_by("-rank", *ORDERINGS["newest"])
    else:
        results = results.order_by(*ORDERINGS[sort])

    page = Paginator(results, PAGE_SIZE).get_page(request.GET.get("page"))

    context = {
        "page_title": "Archives",
        "page_description": "Search and browse articles by Ralph Kinney Bennett, from TCS Daily, "
        "The American, National Review and more.",
        "q": q,
        "sort": sort,
        "sorts": {key: label for key, label in SORTS.items() if q or key != "relevance"},
        "active_publication": publication,
        "active_topic": topic,
        "active_year": year,
        "has_filters": bool(filters),
        "page": page,
        "publication_facets": publication_facets(filtered("publication")),
        "topic_facets": topic_facets(filtered("topic")),
        "year_facets": year_facets(filtered("year")),
    }

    is_htmx = request.headers.get("HX-Request") and not request.headers.get(
        "HX-History-Restore-Request"
    )
    template = "archive/_results_update.html" if is_htmx else "archive/article_list.html"
    response = render(request, template, context)
    patch_vary_headers(response, ["HX-Request"])
    return response


def publication_facets(articles):
    ids = articles.values("pk")
    return (
        Publication.objects.annotate(count=Count("articles", filter=Q(articles__in=ids)))
        .filter(count__gt=0)
        .order_by("name")
    )


def topic_facets(articles):
    ids = articles.values("pk")
    return (
        Topic.objects.annotate(count=Count("articles", filter=Q(articles__in=ids)))
        .filter(count__gt=0)
        .order_by("name")
    )


def year_facets(articles):
    dated = (
        Article.objects.filter(pk__in=articles.values("pk"), published_on__isnull=False)
        .annotate(year=ExtractYear("published_on"))
        .values("year")
        .annotate(count=Count("pk"))
        .order_by("-year")
    )
    facets = [{"value": str(row["year"]), "count": row["count"]} for row in dated]
    undated = Article.objects.filter(pk__in=articles.values("pk"), published_on__isnull=True)
    if undated_count := undated.count():
        facets.append({"value": "undated", "count": undated_count})
    return facets


def article_detail(request, slug):
    articles = Article.objects.all() if request.user.is_staff else Article.objects.published()
    article = get_object_or_404(articles.select_related("publication"), slug=slug)
    topics = list(article.topics.all())

    related = (
        Article.objects.published()
        .filter(topics__in=topics)
        .exclude(pk=article.pk)
        .annotate(shared=Count("topics"))
        .select_related("publication")
        .order_by("-shared", F("published_on").desc(nulls_last=True))[:3]
    )

    structured_data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "url": settings.SITE_URL + article.get_absolute_url(),
        "author": {"@type": "Person", "name": "Ralph Kinney Bennett"},
    }
    if article.published_on:
        structured_data["datePublished"] = article.published_on.isoformat()
    if article.publication:
        structured_data["publisher"] = {
            "@type": "Organization",
            "name": article.publication.name,
        }

    return render(
        request,
        "archive/article_detail.html",
        {
            "page_title": article.title,
            "page_description": article.excerpt,
            "og_type": "article",
            "article": article,
            "topics": topics,
            "related": related,
            "structured_data": structured_data,
        },
    )


def appearance_list(request):
    return render(
        request,
        "archive/appearance_list.html",
        {
            "page_title": "Appearances",
            "page_description": "Television interviews and public appearances by Ralph Kinney "
            "Bennett, including C-SPAN call-in programs from the 1980s and 1990s.",
            "appearances": Appearance.objects.all(),
        },
    )
