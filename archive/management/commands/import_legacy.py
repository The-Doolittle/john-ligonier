from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from archive.legacy import DUPLICATES, parse_appearances, parse_article
from archive.models import Appearance, Article, Publication, Topic


class Command(BaseCommand):
    help = "Import articles and appearances from the old static site in legacy/."

    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path, default=settings.BASE_DIR / "legacy")
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace articles that already exist. Without this, existing articles "
            "are left alone so edits made in the admin are kept.",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Report what would happen, then roll back."
        )

    def handle(self, *args, source, overwrite, dry_run, **options):
        articles_dir = source / "articles"
        if not articles_dir.is_dir():
            raise CommandError(f"No articles folder at {articles_dir}")

        with transaction.atomic():
            self.import_articles(articles_dir, overwrite)
            appearances_page = source / "appearances.html"
            if appearances_page.exists():
                self.import_appearances(appearances_page)
            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run: nothing was saved."))

    def import_articles(self, articles_dir, overwrite):
        created = updated = skipped = 0
        report = {}
        titles = defaultdict(list)

        for path in sorted(articles_dir.glob("*.html")):
            if path.stem == "article-template" or path.stem in DUPLICATES:
                continue
            fields, notes = parse_article(path.read_text(encoding="utf-8"), path.stem)
            titles[fields["title"].lower()].append(fields["slug"])

            existing = Article.objects.filter(slug=fields["slug"]).first()
            if existing and not overwrite:
                skipped += 1
                continue

            article = existing or Article(slug=fields["slug"])
            article.title = fields["title"]
            article.body = fields["body"]
            article.excerpt = fields["excerpt"]
            article.published_on = fields["published_on"]
            article.publication = get_named(Publication, fields["publication"])
            article.status = Article.Status.PUBLISHED if fields["body"] else Article.Status.DRAFT
            article.save()
            article.topics.set([get_named(Topic, name) for name in fields["topics"]])

            if existing:
                updated += 1
            else:
                created += 1
            if notes:
                report[fields["slug"]] = notes

        self.stdout.write(
            self.style.SUCCESS(
                f"Articles: {created} created, {updated} updated, {skipped} already present."
            )
        )
        for slug, notes in report.items():
            self.stdout.write(f"  {slug}")
            for note in dict.fromkeys(notes):
                self.stdout.write(f"    - {note}")
        for slugs in titles.values():
            if len(slugs) > 1:
                self.stdout.write(
                    self.style.WARNING(f"  Same title, possible duplicates: {', '.join(slugs)}")
                )

    def import_appearances(self, page):
        created = 0
        for fields in parse_appearances(page.read_text(encoding="utf-8")):
            _, was_created = Appearance.objects.get_or_create(
                title=fields.pop("title"),
                appeared_on=fields.pop("appeared_on"),
                defaults=fields,
            )
            created += was_created
        self.stdout.write(self.style.SUCCESS(f"Appearances: {created} created."))


def get_named(model, name):
    if not name:
        return None
    obj, _ = model.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
    return obj
