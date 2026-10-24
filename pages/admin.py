from django.contrib import admin

from .models import Memory


@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ["name", "relationship", "submitted_at", "emailed"]
    list_filter = ["emailed"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["name", "email", "relationship", "message", "submitted_at", "emailed"]

    def has_add_permission(self, request):
        return False
