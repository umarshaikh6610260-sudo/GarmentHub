from django import forms
from .models import WorkRequest, WorkOffer

from .models import BusinessReview


class WorkRequestForm(forms.ModelForm):
    class Meta:
        model = WorkRequest
        fields = [
            "business",
            "title",
            "category",
            "description",
            "quantity",
            "unit",
            "budget",
            "city",
            "deadline",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "quantity": forms.NumberInput(attrs={"min": 1}),
            "budget": forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
        }


class WorkOfferForm(forms.ModelForm):
    class Meta:
        model = WorkOffer
        fields = ["offer_type", "quoted_price", "message"]
        widgets = {
            "quoted_price": forms.NumberInput(
                attrs={"min": 0, "step": "0.01"}
            ),
            "message": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        offer_type = cleaned_data.get("offer_type")
        quoted_price = cleaned_data.get("quoted_price")

        if offer_type == "quote" and quoted_price is None:
            self.add_error(
                "quoted_price",
                "Quotation ke liye apni price enter karo.",
            )

        if quoted_price is not None and quoted_price < 0:
            self.add_error("quoted_price", "Price negative nahi ho sakti.")

        if offer_type == "instant":
            cleaned_data["quoted_price"] = None

        return cleaned_data

class BusinessReviewForm(forms.ModelForm):

    class Meta:
        model = BusinessReview

        fields = ["rating", "comment"]

        widgets = {
            "rating": forms.Select(
                choices=[
                    (5, "5 - Excellent"),
                    (4, "4 - Very Good"),
                    (3, "3 - Good"),
                    (2, "2 - Fair"),
                    (1, "1 - Poor"),
                ]
            ),

            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Describe your experience working with this business...",
                }
            ),
        }