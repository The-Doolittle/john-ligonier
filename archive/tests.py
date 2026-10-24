from datetime import date

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .legacy import fix_emphasis, parse_article, parse_byline_date
from .models import Appearance, Article, Publication, Topic, youtube_id

LEGACY_PAGE = """<html><head><title>Armor All | John Ligonier Archive</title></head><body>
<article class="article-body">
<h2>Armor All</h2>
<div class="archive-tags"><span class="archive-tag tag-publication">TCS Daily</span>
<span class="archive-tag tag-year">Undated</span>
<span class="archive-tag tag-topic">War</span></div>
<p>###### By Ralph Kinney Bennett : <strong><a href="http://example.com/bio">BIO</a></strong>
| 17 Jan 2006</p>
<p>![[armor.jpg]]</p>
<p>Pfc. Steven Tschiderer fell <a href="http://example.com/video">thunderously</a>.</p>
<blockquote><p>A quoted line.</p></blockquote>
</article></body></html>"""


class LegacyParsingTests(SimpleTestCase):
    def test_parses_fields_and_cleans_body(self):
        fields, notes = parse_article(LEGACY_PAGE, "armor-all")
        self.assertEqual(fields["title"], "Armor All")
        self.assertEqual(fields["publication"], "TCS Daily")
        self.assertEqual(fields["topics"], ["War"])
        self.assertEqual(fields["published_on"], date(2006, 1, 17))
        self.assertEqual(
            fields["body"],
            "Pfc. Steven Tschiderer fell [thunderously](http://example.com/video).\n\n"
            "> A quoted line.",
        )
        self.assertIn("missing image: armor.jpg", notes)

    def test_byline_date_formats(self):
        self.assertEqual(parse_byline_date("By Ralph | June 06, 2014"), date(2014, 6, 6))
        self.assertEqual(parse_byline_date("By Ralph | 02 Nov 2005"), date(2005, 11, 2))
        self.assertIsNone(parse_byline_date("RALPH KINNEY BENNETT"))

    def test_fix_emphasis(self):
        self.assertEqual(fix_emphasis("_He fell. __-- The Iliad_"), "_He fell._ _-- The Iliad_")
        self.assertEqual(fix_emphasis("_We used no mattress,"), "_We used no mattress,_")


class YoutubeIdTests(SimpleTestCase):
    def test_formats(self):
        self.assertEqual(youtube_id("https://www.youtube.com/watch?v=abc123"), "abc123")
        self.assertEqual(youtube_id("https://youtu.be/abc123"), "abc123")
        self.assertEqual(youtube_id("https://www.c-span.org/video/1"), "")


class ArchiveViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        tcs = Publication.objects.create(name="TCS Daily", slug="tcs-daily")
        cars = Topic.objects.create(name="Automotive", slug="automotive")
        cls.pontiac = Article.objects.create(
            title="The Passing of Pontiac",
            slug="the-passing-of-pontiac",
            publication=tcs,
            published_on=date(2009, 5, 1),
            body="Sometimes irony is shrouded in the mists of forgotten history.",
            status=Article.Status.PUBLISHED,
        )
        cls.pontiac.topics.add(cars)
        Article.objects.create(
            title="Glovology",
            slug="glovology",
            body="We used no mattress on our hands.",
            status=Article.Status.PUBLISHED,
        )
        Article.objects.create(title="Unfinished", slug="unfinished", body="Draft text.")

    def test_list_shows_published_only(self):
        response = self.client.get(reverse("archive:article_list"))
        self.assertContains(response, "The Passing of Pontiac")
        self.assertContains(response, "Glovology")
        self.assertNotContains(response, "Unfinished")

    def test_prefix_search_matches_body_text(self):
        response = self.client.get(reverse("archive:article_list"), {"q": "irony shroud"})
        self.assertContains(response, "The Passing of Pontiac")
        self.assertNotContains(response, "Glovology")

    def test_topic_filter(self):
        response = self.client.get(reverse("archive:article_list"), {"topic": "automotive"})
        self.assertContains(response, "The Passing of Pontiac")
        self.assertNotContains(response, ">Glovology<")

    def test_htmx_request_returns_fragment(self):
        response = self.client.get(reverse("archive:article_list"), headers={"HX-Request": "true"})
        self.assertNotContains(response, "<html")
        self.assertContains(response, 'id="results"')

    def test_draft_hidden_from_public(self):
        response = self.client.get(reverse("archive:article_detail", args=["unfinished"]))
        self.assertEqual(response.status_code, 404)

    def test_legacy_address_redirects(self):
        response = self.client.get("/articles/glovology.html")
        self.assertRedirects(response, "/articles/glovology/", status_code=301)
        response = self.client.get("/articles/glovology/index.html")
        self.assertRedirects(response, "/articles/glovology/", status_code=301)

    def test_removed_duplicate_redirects_to_original(self):
        response = self.client.get("/articles/what-a-father-taught-me-2/")
        self.assertRedirects(
            response,
            "/articles/what-a-father-taught-me/",
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_excerpt_filled_on_save(self):
        self.assertEqual(
            self.pontiac.excerpt, "Sometimes irony is shrouded in the mists of forgotten history."
        )


class AppearanceTests(TestCase):
    def test_youtube_player_derived_from_link(self):
        appearance = Appearance(
            title="Why Celebrate Independence Day",
            outlet="New Life Christian Church",
            appeared_on=date(2020, 7, 4),
            watch_url="https://www.youtube.com/watch?v=dBXZju2hh94",
        )
        self.assertEqual(
            appearance.player_url, "https://www.youtube-nocookie.com/embed/dBXZju2hh94?rel=0"
        )
        self.assertEqual(appearance.watch_label, "Watch on YouTube")
