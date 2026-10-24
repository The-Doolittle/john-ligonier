from django.db import models


class Memory(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    relationship = models.CharField("how they knew Ralph", max_length=200, blank=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    emailed = models.BooleanField(
        "sent to inbox",
        default=False,
        help_text="Whether the email to the family inbox went through.",
    )

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name_plural = "memories"

    def __str__(self):
        return f"{self.name}, {self.submitted_at:%B %-d, %Y}"
