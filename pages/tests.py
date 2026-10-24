from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Memory

VALID_MEMORY = {
    "name": "Jane Reader",
    "email": "jane@example.com",
    "relationship": "Longtime reader",
    "message": "His column on the Jeep stayed with me.",
    "website": "",
}


@override_settings(MEMORY_RECIPIENT="family@johnligonier.com")
class ShareMemoryTests(TestCase):
    def test_memory_is_saved_and_emailed(self):
        response = self.client.post(reverse("pages:share_memory"), VALID_MEMORY)
        self.assertRedirects(response, reverse("pages:memory_thanks"))

        memory = Memory.objects.get()
        self.assertTrue(memory.emailed)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["family@johnligonier.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["jane@example.com"])

    def test_honeypot_discards_submission(self):
        response = self.client.post(
            reverse("pages:share_memory"), {**VALID_MEMORY, "website": "spam.example"}
        )
        self.assertRedirects(response, reverse("pages:memory_thanks"))
        self.assertFalse(Memory.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_fields_show_errors(self):
        response = self.client.post(reverse("pages:share_memory"), {"name": "Jane"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")


class PageTests(TestCase):
    def test_pages_render_with_one_h1(self):
        for name in ["pages:home", "pages:about", "pages:obituary"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(b"<h1"), 1, name)

    def test_robots_lists_sitemap(self):
        response = self.client.get("/robots.txt")
        self.assertContains(response, "Sitemap: ")

    def test_legacy_page_redirects(self):
        response = self.client.get("/about.html")
        self.assertRedirects(response, "/about/", status_code=301)
