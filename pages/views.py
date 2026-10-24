import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from .forms import MemoryForm

logger = logging.getLogger(__name__)

PERSON = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "Ralph Kinney Bennett",
    "alternateName": "John Ligonier",
    "birthDate": "1941-03-03",
    "birthPlace": "Latrobe, Pennsylvania",
    "deathDate": "2024-12-18",
    "deathPlace": "Delray Beach, Florida",
    "alumniOf": "Allegheny College",
    "jobTitle": "Journalist",
}

LEGACY_PAGES = {
    "index": "pages:home",
    "about": "pages:about",
    "obituary": "pages:obituary",
    "archives": "archive:article_list",
    "appearances": "archive:appearance_list",
}


class PageView(TemplateView):
    title = ""
    description = ""
    structured_data = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.title
        context["page_description"] = self.description
        if self.structured_data:
            context["structured_data"] = {**self.structured_data, "url": settings.SITE_URL}
        return context


def share_memory(request):
    form = MemoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not form.cleaned_data["website"]:
            memory = form.save()
            memory.emailed = send_memory(memory)
            memory.save(update_fields=["emailed"])
        return redirect("pages:memory_thanks")
    return render(
        request,
        "pages/share_memory.html",
        {
            "page_title": "Share a memory",
            "page_description": "Send a memory of Ralph Kinney Bennett privately to his family.",
            "form": form,
        },
    )


def send_memory(memory):
    """Email a memory to the family inbox. Returns False if sending failed."""
    lines = [
        f"From: {memory.name} <{memory.email}>",
        f"How they knew Ralph: {memory.relationship or 'not given'}",
        "",
        memory.message,
    ]
    message = EmailMessage(
        subject=f"A memory of Ralph from {memory.name}",
        body="\n".join(lines),
        to=[settings.MEMORY_RECIPIENT],
        reply_to=[memory.email],
    )
    try:
        message.send()
    except SMTPException, OSError:
        logger.exception("Could not email memory %s", memory.pk)
        return False
    return True


def robots_txt(request):
    lines = ["User-agent: *", "Disallow: /admin/", f"Sitemap: {settings.SITE_URL}/sitemap.xml"]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def legacy_page(request, page):
    return redirect(LEGACY_PAGES[page], permanent=True)
