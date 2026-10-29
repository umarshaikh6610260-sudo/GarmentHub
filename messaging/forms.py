from django import forms

from .models import BusinessMessage


class StartInquiryForm(forms.Form):

    sender_business = forms.ChoiceField(
        label="Send as business",
    )

    subject = forms.CharField(
        max_length=180,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Example: Fabric supply inquiry",
            }
        ),
    )

    message = forms.CharField(
        max_length=3000,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": "Write your inquiry...",
            }
        ),
    )

    def __init__(self, *args, businesses=None, **kwargs):
        super().__init__(*args, **kwargs)

        businesses = businesses or []

        self.fields["sender_business"].choices = [
            (str(business.pk), business.name)
            for business in businesses
        ]


class BusinessMessageForm(forms.ModelForm):

    class Meta:
        model = BusinessMessage

        fields = ["body"]

        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Write your message...",
                }
            ),
        }

        labels = {
            "body": "Your Message",
        }