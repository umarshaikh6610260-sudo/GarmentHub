from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models

from .storage import PrivateVerificationStorage


class Business(models.Model):
    BUSINESS_TYPES = [
        ("brand", "Garment Brand"),
        ("manufacturer", "Manufacturer / Factory"),
        ("trader", "Garment Trader"),
        ("fabric_supplier", "Fabric Supplier"),
        ("job_worker", "Job Worker"),
        ("service_provider", "Service Provider"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_businesses",
    )
    name = models.CharField(max_length=150)
    business_type = models.CharField(
        max_length=30,
        choices=BUSINESS_TYPES,
    )
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BusinessMembership(models.Model):
    ROLES = [
        ("owner", "Owner"),
        ("manager", "Manager"),
        ("employee", "Employee"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_memberships",
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default="employee",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "business"],
                name="unique_business_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.business} ({self.role})"


class BusinessVerification(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    business = models.OneToOneField(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="verification",
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_verifications",
    )

    registration_number = models.CharField(
        max_length=100,
        blank=True,
    )

    business_email = models.EmailField()

    document = models.FileField(
        upload_to="business_verifications/",
        storage=PrivateVerificationStorage(),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_verifications",
    )

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.business.name} - {self.get_status_display()}"
