from django.shortcuts import render

# Create your views here.

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Business

from django.db.models import Avg, Count
from marketplace.models import BusinessReview

from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET
import os

from .forms import BusinessVerificationForm
from .models import Business, BusinessMembership, BusinessVerification

from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegisterForm, BusinessForm
from .models import Business, BusinessMembership


def is_business_owner(user, business):
    return (
        user.is_authenticated
        and business.owner_id == user.id
        and BusinessMembership.objects.filter(
            user=user,
            business=business,
            role="owner",
        ).exists()
    )


def can_manage_business(user, business):
    if not user.is_authenticated:
        return False

    return BusinessMembership.objects.filter(
        user=user,
        business=business,
        role__in=["owner", "manager"],
    ).exists()

def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("accounts:create_business")

    return render(request, "accounts/register.html", {"form": form})


@login_required
def create_business(request):
    form = BusinessForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            business = form.save(commit=False)
            business.owner = request.user
            business.save()

            BusinessMembership.objects.create(
                user=request.user,
                business=business,
                role="owner",
            )

        messages.success(request, "Your business profile was created.")
        return redirect("accounts:dashboard")

    return render(
        request,
        "accounts/business_form.html",
        {"form": form},
    )


@login_required
def dashboard(request):
    businesses = Business.objects.filter(
        memberships__user=request.user
    ).distinct()

    return render(
        request,
        "accounts/dashboard.html",
        {"businesses": businesses},
    )



@login_required
def business_detail(request, business_id):
    business = get_object_or_404(
        Business.objects.filter(
            memberships__user=request.user,
        ).distinct(),
        pk=business_id,
    )

    members = BusinessMembership.objects.filter(
        business=business,
    ).select_related("user").order_by("role", "joined_at")

    context = {
        "business": business,
        "members": members,
        "is_owner": is_business_owner(request.user, business),
        "can_manage": can_manage_business(request.user, business),
    }

    return render(
        request,
        "accounts/business_detail.html",
        context,
    )




@login_required
def edit_business(request, business_id):
    business = get_object_or_404(
        Business,
        pk=business_id,
        owner=request.user,
    )

    form = BusinessForm(
        request.POST or None,
        instance=business,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Business profile updated successfully.")

        return redirect(
            "accounts:business_detail",
            business_id=business.pk,
        )

    return render(
        request,
        "accounts/business_form.html",
        {
            "form": form,
            "is_edit": True,
            "business": business,
        },
    )


@login_required
def add_business_member(request, business_id):
    business = get_object_or_404(
        Business,
        pk=business_id,
        owner=request.user,
    )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        role = request.POST.get("role", "").strip()

        if role not in ["manager", "employee"]:
            messages.error(request, "Invalid role selected.")
            return redirect(
                "accounts:business_detail",
                business_id=business.pk,
            )

        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user is None:
            messages.error(request, "No registered user found with this username.")
            return redirect(
                "accounts:business_detail",
                business_id=business.pk,
            )

        if user.pk == business.owner_id:
            messages.error(request, "Business owner is already a member.")
            return redirect(
                "accounts:business_detail",
                business_id=business.pk,
            )

        membership, created = BusinessMembership.objects.get_or_create(
            user=user,
            business=business,
            defaults={"role": role},
        )

        if not created:
            messages.error(request, "This user is already a member.")
        else:
            messages.success(request, "Business member added successfully.")

        return redirect(
            "accounts:business_detail",
            business_id=business.pk,
        )

    return redirect(
        "accounts:business_detail",
        business_id=business.pk,
    )



@login_required
@require_POST
def change_member_role(request, business_id, membership_id):
    business = get_object_or_404(
        Business,
        pk=business_id,
        owner=request.user,
    )

    membership = get_object_or_404(
        BusinessMembership,
        pk=membership_id,
        business=business,
    )

    if membership.user_id == business.owner_id:
        messages.error(request, "Owner role cannot be changed.")
        return redirect(
            "accounts:business_detail",
            business_id=business.pk,
        )

    new_role = request.POST.get("role")

    if new_role not in ["manager", "employee"]:
        messages.error(request, "Invalid role.")
    else:
        membership.role = new_role
        membership.save(update_fields=["role"])
        messages.success(request, "Member role updated.")

    return redirect(
        "accounts:business_detail",
        business_id=business.pk,
    )



@login_required
@require_POST
def remove_business_member(request, business_id, membership_id):
    business = get_object_or_404(
        Business,
        pk=business_id,
        owner=request.user,
    )

    membership = get_object_or_404(
        BusinessMembership,
        pk=membership_id,
        business=business,
    )

    if membership.user_id == business.owner_id:
        messages.error(request, "Business owner cannot be removed.")
    else:
        membership.delete()
        messages.success(request, "Member removed successfully.")

    return redirect(
        "accounts:business_detail",
        business_id=business.pk,
    )

def supplier_directory(request):
    businesses = (
    Business.objects
    .select_related("verification")
    .all()
    .order_by("name", "pk")
)

    search = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    business_type = request.GET.get("type", "").strip()

    valid_types = dict(Business.BUSINESS_TYPES)

    if search:
        businesses = businesses.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(city__icontains=search)
        )

    if city:
        businesses = businesses.filter(city__icontains=city)

    if business_type in valid_types:
        businesses = businesses.filter(
            business_type=business_type
        )
    else:
        business_type = ""

    paginator = Paginator(businesses, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "accounts/supplier_directory.html",
        {
            "businesses": page_obj.object_list,
            "page_obj": page_obj,
            "business_types": Business.BUSINESS_TYPES,
            "search_query": search,
            "city_query": city,
            "selected_type": business_type,
            "filter_query": query_params.urlencode(),
            "total_results": paginator.count,
        },
    )


def supplier_profile(request, business_id):
    business = get_object_or_404(
    Business.objects.select_related("owner", "verification"),
    pk=business_id,
)

    posted_works = business.work_requests.filter(
        status="open",
    ).order_by("-created_at")[:6]

    reviews = (
    BusinessReview.objects
    .filter(reviewed_business=business)
    .select_related("reviewer_business")
    .order_by("-created_at")[:10]
    )

    rating_summary = BusinessReview.objects.filter(
    reviewed_business=business
    ).aggregate(
    average_rating=Avg("rating"),
    review_count=Count("id"),
    )

    return render(
        request,
        "accounts/supplier_profile.html",
        {
            "business": business,
            "posted_works": posted_works,
            "reviews": reviews,
            "rating_summary": rating_summary,
        },
    )

@login_required
def request_business_verification(request, business_id):

    business = get_object_or_404(
        Business.objects.filter(
            memberships__user=request.user,
        ).distinct(),
        pk=business_id,
    )

    # Only business owner can request verification
    is_owner = (
        business.owner_id == request.user.id
        and BusinessMembership.objects.filter(
            user=request.user,
            business=business,
            role="owner",
        ).exists()
    )

    if not is_owner:
        messages.error(
            request,
            "Only the business owner can request verification.",
        )
        return redirect(
            "accounts:business_detail",
            business_id=business.pk,
        )

    verification = BusinessVerification.objects.filter(
        business=business,
    ).first()

    if verification and verification.status in ["pending", "approved"]:
        messages.info(
            request,
            "Your verification is already pending or approved.",
        )
        return redirect(
            "accounts:verification_status",
            business_id=business.pk,
        )

    form = BusinessVerificationForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():

        with transaction.atomic():

            verification = (
                BusinessVerification.objects
                .select_for_update()
                .filter(business=business)
                .first()
            )

            if verification and verification.status != "rejected":
                messages.error(
                    request,
                    "A verification request already exists.",
                )
                return redirect(
                    "accounts:verification_status",
                    business_id=business.pk,
                )

            # Save a fresh request; rejected requests can be resubmitted
            new_request = form.save(commit=False)
            new_request.business = business
            new_request.submitted_by = request.user
            new_request.status = "pending"
            new_request.rejection_reason = ""
            new_request.reviewed_at = None
            new_request.reviewed_by = None

            if verification:
                # Replace previous rejected request
                verification.registration_number = new_request.registration_number
                verification.business_email = new_request.business_email
                verification.document = new_request.document
                verification.submitted_by = request.user
                verification.status = "pending"
                verification.rejection_reason = ""
                verification.reviewed_at = None
                verification.reviewed_by = None
                verification.submitted_at = timezone.now()
                verification.save()
            else:
                new_request.save()

        messages.success(
            request,
            "Verification request submitted successfully.",
        )

        return redirect(
            "accounts:verification_status",
            business_id=business.pk,
        )

    return render(
        request,
        "accounts/verification_request.html",
        {
            "form": form,
            "business": business,
        },
    )

@login_required
def verification_status(request, business_id):

    business = get_object_or_404(
        Business.objects.filter(
            memberships__user=request.user,
        ).distinct(),
        pk=business_id,
    )

    verification = BusinessVerification.objects.filter(
        business=business,
    ).first()

    return render(
        request,
        "accounts/verification_status.html",
        {
            "business": business,
            "verification": verification,
            "is_owner": (
                business.owner_id == request.user.id
                and BusinessMembership.objects.filter(
                    user=request.user,
                    business=business,
                    role="owner",
                ).exists()
            ),
        },
    )

@staff_member_required
@require_GET
def download_verification_document(request, verification_id):

    verification = get_object_or_404(
        BusinessVerification,
        pk=verification_id,
    )

    if not request.user.has_perm(
        "accounts.change_businessverification"
    ):
        raise Http404("Document not found.")

    if not verification.document:
        raise Http404("Document not found.")

    try:
        document = verification.document.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("Document not found.")

    return FileResponse(
        document,
        as_attachment=True,
        filename=os.path.basename(verification.document.name),
        content_type="application/octet-stream",
    )