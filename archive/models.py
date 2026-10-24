from urllib.parse import parse_qs, urlparse

from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from .formatting import make_excerpt, markdown_to_text, render_markdown


class Publication(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Topic(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Article.Status.PUBLISHED)


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="Used in the web address: /articles/<slug>/. Avoid changing it once published.",
    )
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="articles",
        null=True,
        blank=True,
    )
    published_on = models.DateField(
        "date published",
        null=True,
        blank=True,
        help_text="Leave blank if the date is unknown.",
    )
    topics = models.ManyToManyField(Topic, related_name="articles", blank=True)
    excerpt = models.TextField(
        blank=True,
        help_text="One or two sentences for the archive listing. "
        "Filled in from the first paragraph if left blank.",
    )
    body = models.TextField(
        blank=True,
        help_text="Leave a blank line between paragraphs. *italics*, **bold**, "
        "[link text](https://example.com), and start a line with > for a quotation.",
    )
    body_text = models.TextField(editable=False, default="")
    source_url = models.URLField(
        "original source",
        max_length=500,
        blank=True,
        help_text="Where the article first ran online, if known.",
    )
    status = models.CharField(max_length=10, choices=Status, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = [models.F("published_on").desc(nulls_last=True), "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.body_text = markdown_to_text(self.body)
        if not self.excerpt:
            self.excerpt = make_excerpt(self.body)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("archive:article_detail", args=[self.slug])

    @cached_property
    def body_html(self):
        return render_markdown(self.body)

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED


class Appearance(models.Model):
    title = models.CharField(max_length=200)
    outlet = models.CharField(max_length=120, help_text="e.g. C-SPAN, New Life Christian Church")
    appeared_on = models.DateField("date")
    description = models.TextField(blank=True)
    watch_url = models.URLField(
        "video page",
        max_length=500,
        help_text="Link to the page where the video can be watched.",
    )
    embed_url = models.URLField(
        "player address",
        max_length=500,
        blank=True,
        help_text="Optional. Address of an embeddable player. "
        "YouTube links work without this; leave blank to show a link only.",
    )

    class Meta:
        ordering = ["-appeared_on"]

    def __str__(self):
        return f"{self.title} ({self.appeared_on:%Y})"

    @property
    def player_url(self):
        if self.embed_url:
            return self.embed_url
        video_id = youtube_id(self.watch_url)
        if video_id:
            return f"https://www.youtube-nocookie.com/embed/{video_id}?rel=0"
        return ""

    @property
    def watch_label(self):
        host = urlparse(self.watch_url).netloc
        if "youtube" in host or "youtu.be" in host:
            return "Watch on YouTube"
        if "c-span" in host:
            return "Watch on C-SPAN"
        return "Watch the video"


def youtube_id(url):
    """Video ID from a YouTube watch or share link, or an empty string."""
    parsed = urlparse(url or "")
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.lstrip("/")
    if "youtube" in parsed.netloc:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [""])[0]
        if parsed.path.startswith("/embed/"):
            return parsed.path.removeprefix("/embed/")
    return ""
