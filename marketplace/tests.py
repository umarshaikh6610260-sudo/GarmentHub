
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Business, BusinessMembership
from marketplace.models import (
    WorkRequest,
    WorkOffer,
    BusinessReview,
)


@override_settings(SECURE_SSL_REDIRECT=False)
class BusinessReviewTests(TestCase):

    def setUp(self):
        User = get_user_model()

        # Create test users
        self.owner = User.objects.create_user(
            username="test_owner",
            password="StrongTestPass123!",
        )

        self.supplier = User.objects.create_user(
            username="test_supplier",
            password="StrongTestPass123!",
        )

        self.other_user = User.objects.create_user(
            username="test_other_user",
            password="StrongTestPass123!",
        )

        # Create businesses
        self.client_business = Business.objects.create(
            owner=self.owner,
            name="Test Manufacturer",
            business_type="manufacturer",
            city="Ahmedabad",
        )

        self.supplier_business = Business.objects.create(
            owner=self.supplier,
            name="Test Stitching Factory",
            business_type="job_worker",
            city="Ahmedabad",
        )

        # Create memberships
        BusinessMembership.objects.create(
            user=self.owner,
            business=self.client_business,
            role="owner",
        )

        BusinessMembership.objects.create(
            user=self.supplier,
            business=self.supplier_business,
            role="owner",
        )

        # Create completed work
        self.work = WorkRequest.objects.create(
            business=self.client_business,
            title="Stitching 500 Shirts",
            category="stitching",
            description="Shirt stitching work",
            quantity=500,
            unit="pieces",
            budget=Decimal("25000.00"),
            city="Ahmedabad",
            deadline=timezone.localdate() + timedelta(days=7),
            status="completed",
        )

        # Create accepted offer
        self.offer = WorkOffer.objects.create(
            work_request=self.work,
            business=self.supplier_business,
            offer_type="instant",
            status="accepted",
        )

        self.url = reverse(
            "marketplace:submit_business_review",
            kwargs={"work_id": self.work.pk},
        )

    # -------------------------------------
    # Test 1: Owner can submit review
    # -------------------------------------

    def test_owner_can_review_completed_work(self):

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "rating": 5,
                "comment": "Excellent stitching quality.",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            BusinessReview.objects.count(),
            1,
        )

        review = BusinessReview.objects.first()

        self.assertEqual(review.rating, 5)
        self.assertEqual(
            review.reviewer_business,
            self.client_business,
        )
        self.assertEqual(
            review.reviewed_business,
            self.supplier_business,
        )

    # -------------------------------------
    # Test 2: Duplicate reviews blocked
    # -------------------------------------

    def test_duplicate_review_is_blocked(self):

        self.client.force_login(self.owner)

        data = {
            "rating": 5,
            "comment": "Good work.",
        }

        self.client.post(self.url, data)
        self.client.post(self.url, data)

        self.assertEqual(
            BusinessReview.objects.count(),
            1,
        )

    # -------------------------------------
    # Test 3: Supplier cannot self-review
    # -------------------------------------

    def test_supplier_cannot_review_itself(self):

        self.client.force_login(self.supplier)

        response = self.client.post(
            self.url,
            {
                "rating": 5,
                "comment": "Self review attempt.",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            BusinessReview.objects.count(),
            0,
        )

    # -------------------------------------
    # Test 4: Unrelated user cannot review
    # -------------------------------------

    def test_unrelated_user_cannot_review(self):

        self.client.force_login(self.other_user)

        response = self.client.post(
            self.url,
            {
                "rating": 5,
                "comment": "Unauthorized review.",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            BusinessReview.objects.count(),
            0,
        )

    # -------------------------------------
    # Test 5: Open work cannot be reviewed
    # -------------------------------------

    def test_open_work_cannot_be_reviewed(self):

        self.work.status = "open"
        self.work.save(update_fields=["status"])

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "rating": 5,
                "comment": "Trying to review open work.",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            BusinessReview.objects.count(),
            0,
        )

    # -------------------------------------
    # Test 6: Invalid rating is rejected
    # -------------------------------------

    def test_invalid_rating_is_rejected(self):

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "rating": 6,
                "comment": "Invalid rating.",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            BusinessReview.objects.count(),
            0,
        )

    # -------------------------------------
    # Test 7: Login required
    # -------------------------------------

    def test_login_required_for_review(self):

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            BusinessReview.objects.count(),
            0,
        )
