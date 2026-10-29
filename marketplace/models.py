from django.conf import settings
from django.db import models

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, F


class WorkRequest(models.Model):
    CATEGORIES = [
        ("cutting", "Cutting"),
        ("stitching", "Stitching"),
        ("printing", "Printing"),
        ("embroidery", "Embroidery"),
        ("washing", "Washing"),
        ("ironing", "Pressing / Ironing"),
        ("packing", "Packing"),
        ("fabric", "Fabric Supply"),
        ("other", "Other Work"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("assigned", "Assigned"),
        ("completion_pending", "Completion Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="work_requests",
    )
    title = models.CharField(max_length=180)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=40, default="pieces")
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    city = models.CharField(max_length=100)
    deadline = models.DateField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class WorkOffer(models.Model):
    OFFER_TYPES = [
        ("instant", "Accept at Listed Budget"),
        ("quote", "Submit a Quotation"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    work_request = models.ForeignKey(
        WorkRequest,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="work_offers",
    )
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)
    quoted_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["work_request", "business"],
                name="unique_offer_per_business_request",
            )
        ]

    def __str__(self):
        return f"{self.business.name} - {self.work_request.title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("new_offer", "New Offer"),
        ("offer_accepted", "Offer Accepted"),
        ("offer_rejected", "Offer Rejected"),
        ("work_completed", "Work Completed"),
        ("work_cancelled", "Work Cancelled"),
        ("completion_requested", "Completion Requested"),
        ("completion_rejected", "Completion Rejected"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="garmenthub_notifications",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
    )
    title = models.CharField(max_length=180)
    message = models.CharField(max_length=300)
    work_request = models.ForeignKey(
        "marketplace.WorkRequest",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient} - {self.title}"

class BusinessReview(models.Model):

    work_request = models.ForeignKey(
        "marketplace.WorkRequest",
        on_delete=models.CASCADE,
        related_name="business_reviews",
    )

    reviewer_business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="reviews_given",
    )

    reviewed_business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="reviews_received",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="submitted_business_reviews",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    comment = models.TextField(
        max_length=1500,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["work_request", "reviewer_business"],
                name="unique_review_per_work_business",
            ),

            models.CheckConstraint(
                condition=~Q(
                    reviewer_business_id=F("reviewed_business_id")
                ),
                name="prevent_business_self_review",
            ),
        ]

    def __str__(self):
        return (
            f"{self.reviewer_business.name} rated "
            f"{self.reviewed_business.name}: {self.rating}/5"
        )