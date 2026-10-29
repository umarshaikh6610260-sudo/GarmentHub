
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Business

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "email",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            "name",
            "business_type",
            "phone",
            "city",
            "address",
            "description",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

from django import forms
from .models import BusinessVerification


class BusinessVerificationForm(forms.ModelForm):

    class Meta:
        model = BusinessVerification

        fields = [
            "registration_number",
            "business_email",
            "document",
        ]

        widgets = {
            "registration_number": forms.TextInput(
                attrs={
                    "placeholder": "GSTIN / Registration number (optional)",
                }
            ),

            "business_email": forms.EmailInput(
                attrs={
                    "placeholder": "Business email address",
                }
            ),
        }

    def clean_document(self):
        document = self.cleaned_data.get("document")

        if not document:
            raise forms.ValidationError(
                "Please upload a verification document."
            )

        allowed_extensions = (".pdf", ".jpg", ".jpeg", ".png")
        filename = document.name.lower()

        if not filename.endswith(allowed_extensions):
            raise forms.ValidationError(
                "Only PDF, JPG and PNG files are allowed."
            )

        if document.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Maximum file size is 5 MB."
            )

        # Check basic file signatures, not only extension.
        header = document.read(12)
        document.seek(0)

        valid_pdf = header.startswith(b"%PDF-")
        valid_jpg = header.startswith(b"\xff\xd8\xff")
        valid_png = header.startswith(b"\x89PNG\r\n\x1a\n")

        if not (valid_pdf or valid_jpg or valid_png):
            raise forms.ValidationError(
                "Invalid file format."
            )

        if filename.endswith(".pdf") and not valid_pdf:
            raise forms.ValidationError("Invalid PDF document.")

        if filename.endswith((".jpg", ".jpeg")) and not valid_jpg:
            raise forms.ValidationError("Invalid JPEG image.")

        if filename.endswith(".png") and not valid_png:
            raise forms.ValidationError("Invalid PNG image.")

        return document
