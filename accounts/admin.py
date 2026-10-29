from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.utils import timezone

from .models import BusinessVerification


@admin.register(BusinessVerification)
class BusinessVerificationAdmin(admin.ModelAdmin):

    list_display = [
        "business",
        "status",
        "business_email",
        "submitted_at",
        "reviewed_at",
    ]

    list_filter = [
        "status",
        "submitted_at",
    ]

    search_fields = [
        "business__name",
        "business_email",
        "registration_number",
    ]

    readonly_fields = [
        "business",
        "submitted_by",
        "registration_number",
        "business_email",
        "document",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
    ]

    fields = [
        "business",
        "submitted_by",
        "registration_number",
        "business_email",
        "document",
        "submitted_at",
        "status",
        "rejection_reason",
        "reviewed_at",
        "reviewed_by",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):

        if change and "status" in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()

            if obj.status != "rejected":
                obj.rejection_reason = ""

        super().save_model(request, obj, form, change)