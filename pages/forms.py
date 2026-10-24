from django import forms

from .models import Memory


class MemoryForm(forms.ModelForm):
    # Spam trap: hidden from people, filled in by bots.
    website = forms.CharField(required=False, label="Leave this field empty")

    class Meta:
        model = Memory
        fields = ["name", "email", "relationship", "message"]
        labels = {
            "name": "Your name",
            "email": "Your email",
            "relationship": "How you knew Ralph",
            "message": "Your memory",
        }
        help_texts = {
            "email": "Only the family will see this, so they can reply.",
            "relationship": "Optional. For example: neighbor, colleague, reader.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 8}),
        }
