from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render


from django.views.decorators.http import require_http_methods

from accounts.models import BusinessMembership
from .models import WorkRequest, WorkOffer, BusinessReview
from .forms import BusinessReviewForm


from decimal import Decimal, InvalidOperation

from accounts.models import Business, BusinessMembership
from .forms import WorkRequestForm, WorkOfferForm
from .models import WorkRequest, WorkOffer, Notification

def get_user_businesses(user):
    return Business.objects.filter(
        memberships__user=user
    ).distinct()


def is_business_member(user, business):
    return BusinessMembership.objects.filter(
        user=user, business=business
    ).exists()

def can_manage_business_work(user, business):
    if not user.is_authenticated:
        return False

    return BusinessMembership.objects.filter(
        user=user,
        business=business,
        role__in=["owner", "manager"],
    ).exists()



def can_manage_business_work(user, business):
    if not user.is_authenticated:
        return False

    return BusinessMembership.objects.filter(
        user=user,
        business=business,
        role__in=["owner", "manager"],
    ).exists()




def marketplace_home(request):

    # Show only open work with valid deadlines
    works = (
        WorkRequest.objects
        .filter(
            status="open",
            deadline__gte=timezone.localdate(),
        )
        .select_related("business")
    )

    # Read search and filter values
    category = request.GET.get("category", "").strip()
    city = request.GET.get("city", "").strip()
    search = request.GET.get("q", "").strip()
    min_budget = request.GET.get("min_budget", "").strip()
    max_budget = request.GET.get("max_budget", "").strip()
    sort = request.GET.get("sort", "newest").strip()

    # Category filter
    valid_categories = dict(WorkRequest.CATEGORIES)

    if category in valid_categories:
        works = works.filter(category=category)
    else:
        category = ""

    # City filter
    if city:
        works = works.filter(
            city__icontains=city
        )

    # Search work title, description, business and city
    if search:
        works = works.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(business__name__icontains=search)
            | Q(city__icontains=search)
        )

    # Budget validation helper
    def parse_budget(value):
        if not value:
            return None

        try:
            amount = Decimal(value)

            if not amount.is_finite() or amount < 0:
                return None

            # Match WorkRequest.budget DecimalField(max_digits=12,
            # decimal_places=2)
            if amount > Decimal("9999999999.99"):
                return None

            return amount

        except (InvalidOperation, ValueError, TypeError):
            return None

    minimum = parse_budget(min_budget)
    maximum = parse_budget(max_budget)

    # Apply minimum budget
    if minimum is not None:
        works = works.filter(
            budget__gte=minimum
        )

    # Apply maximum budget
    if maximum is not None:
        works = works.filter(
            budget__lte=maximum
        )

    # Sorting options
    sorting_options = {
        "newest": "-created_at",
        "oldest": "created_at",
        "budget_low": "budget",
        "budget_high": "-budget",
        "deadline": "deadline",
    }

    if sort not in sorting_options:
        sort = "newest"

    works = works.order_by(
        sorting_options[sort],
        "-pk",
    )

    # Pagination: 12 works per page
    paginator = Paginator(
        works,
        12,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    # Preserve filters while changing pages
    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "works": page_obj.object_list,
        "page_obj": page_obj,

        "categories": WorkRequest.CATEGORIES,
        "selected_category": category,

        "city_query": city,
        "search_query": search,

        "min_budget": min_budget,
        "max_budget": max_budget,

        "selected_sort": sort,

        "filter_query": query_params.urlencode(),
        "total_results": paginator.count,
    }

    return render(
        request,
        "marketplace/home.html",
        context,
    )


@login_required
def create_work(request):

    # Only businesses where user is Owner or Manager
    businesses = Business.objects.filter(
        memberships__user=request.user,
        memberships__role__in=["owner", "manager"],
    ).distinct()

    # Check whether user has any business membership
    if not businesses.exists():

        if get_user_businesses(request.user).exists():
            messages.error(
                request,
                "Only business owners and managers can post work.",
            )
            return redirect("accounts:dashboard")

        messages.error(
            request,
            "Pehle apna business create karo.",
        )
        return redirect("accounts:create_business")

    # Create form and restrict business selection
    form = WorkRequestForm(request.POST or None)
    form.fields["business"].queryset = businesses

    if request.method == "POST" and form.is_valid():

        work = form.save(commit=False)

        # Server-side permission verification
        if not can_manage_business_work(
            request.user,
            work.business,
        ):
            messages.error(
                request,
                "You do not have permission to post work for this business.",
            )
            return redirect("marketplace:create_work")

        # Validate deadline
        if work.deadline < timezone.localdate():
            form.add_error(
                "deadline",
                "Past date select nahi kar sakte.",
            )
        else:
            work.save()

            messages.success(
                request,
                "Work successfully post ho gaya.",
            )

            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

    return render(
        request,
        "marketplace/work_form.html",
        {
            "form": form,
        },
    )


@login_required
def work_detail(request, work_id):

    work = get_object_or_404(
        WorkRequest.objects.select_related("business"),
        pk=work_id,
    )

    # Check whether user belongs to work owner business
    is_owner = BusinessMembership.objects.filter(
        user=request.user,
        business=work.business,
    ).exists()

    # Owner / Manager permission
    can_manage_owner_work = can_manage_business_work(
        request.user,
        work.business,
    )

    # Accepted offer must be fetched for every user
    accepted_offer = (
        WorkOffer.objects
        .filter(
            work_request=work,
            status="accepted",
        )
        .select_related("business")
        .first()
    )

    # Always initialize variables
    is_assigned_supplier = False
    can_submit_completion = False
    my_offer = None

    # Work owner can see all offers
    if is_owner:

        offers = (
            WorkOffer.objects
            .filter(work_request=work)
            .select_related("business")
            .order_by("-created_at")
        )

    else:

        offers = WorkOffer.objects.none()

        my_businesses = get_user_businesses(request.user)

        my_offer = (
            WorkOffer.objects
            .filter(
                work_request=work,
                business__in=my_businesses,
            )
            .select_related("business")
            .first()
        )

    # Check assigned supplier membership
    if accepted_offer is not None:

        is_assigned_supplier = is_business_member(
            request.user,
            accepted_offer.business,
        )

        can_submit_completion = can_manage_business_work(
            request.user,
            accepted_offer.business,
        )

    context = {
        "work": work,
        "is_owner": is_owner,
        "offers": offers,
        "my_offer": my_offer,
        "accepted_offer": accepted_offer,
        "is_assigned_supplier": is_assigned_supplier,
        "can_manage_owner_work": can_manage_owner_work,
        "can_submit_completion": can_submit_completion,
    }

    return render(
        request,
        "marketplace/work_detail.html",
        context,
    )

@login_required
def submit_offer(request, work_id):
    work = get_object_or_404(
        WorkRequest.objects.select_related("business"),
        pk=work_id,
    )

    # Only Owner/Manager businesses can submit offers
    businesses = Business.objects.filter(
        memberships__user=request.user,
        memberships__role__in=["owner", "manager"],
    ).distinct()

    if not businesses.exists():
        if get_user_businesses(request.user).exists():
            messages.error(
                request,
                "Only business owners and managers can submit offers.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        messages.error(
            request,
            "Offer bhejne se pehle business create karo.",
        )
        return redirect("accounts:create_business")

    # Work must be open and deadline valid
    if work.status != "open" or work.deadline < timezone.localdate():
        messages.error(
            request,
            "Is work par ab offers accept nahi ho rahe.",
        )
        return redirect(
            "marketplace:work_detail",
            work_id=work.pk,
        )

    # Remove own business from eligible businesses
    businesses = businesses.exclude(pk=work.business_id)

    if not businesses.exists():
        messages.error(
            request,
            "Apne hi business ke work par offer nahi de sakte.",
        )
        return redirect(
            "marketplace:work_detail",
            work_id=work.pk,
        )

    form = WorkOfferForm(request.POST or None)
    form.fields["business"] = forms_business_field(businesses)

    if request.method == "POST" and form.is_valid():
        business = form.cleaned_data["business"]

        # Check permission on selected supplier business
        if not can_manage_business_work(request.user, business):
            messages.error(
                request,
                "You cannot submit offers for this business.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Prevent submitting an offer on a work
        # posted by any business the user belongs to
        if is_business_member(request.user, work.business):
            messages.error(
                request,
                "You cannot submit offers on your own business's work.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        if WorkOffer.objects.filter(
            work_request=work,
            business=business,
        ).exists():
            messages.error(
                request,
                "Is business se offer pehle hi bheja ja chuka hai.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        try:
            with transaction.atomic():
                # Lock work and recheck status before saving
                locked_work = get_object_or_404(
                    WorkRequest.objects.select_for_update(),
                    pk=work.pk,
                )

                if (
                    locked_work.status != "open"
                    or locked_work.deadline < timezone.localdate()
                ):
                    messages.error(
                        request,
                        "This work is no longer accepting offers.",
                    )
                    return redirect(
                        "marketplace:work_detail",
                        work_id=work.pk,
                    )

                offer_data = form.cleaned_data.copy()
                offer_data.pop("business", None)

                WorkOffer.objects.create(
                    work_request=locked_work,
                    business=business,
                    **offer_data,
                )

                notify_business_members(
                    business=locked_work.business,
                    notification_type="new_offer",
                    title="New offer received",
                    message=(
                        f"{business.name} ne "
                        f"'{locked_work.title}' par offer bheja hai."
                    ),
                    work=locked_work,
                )

        except IntegrityError:
            messages.error(
                request,
                "Offer pehle hi submit ho chuka hai.",
            )
        else:
            messages.success(
                request,
                "Aapka offer successfully submit ho gaya.",
            )

        return redirect(
            "marketplace:work_detail",
            work_id=work.pk,
        )

    return render(
        request,
        "marketplace/offer_form.html",
        {
            "form": form,
            "work": work,
        },
    )



def forms_business_field(businesses):
    from django import forms

    return forms.ModelChoiceField(
        queryset=businesses,
        label="Offer kis business ki taraf se hai?",
    )





@login_required
@require_POST
def accept_offer(request, offer_id):
    with transaction.atomic():

        # Get offer reference
        offer_ref = get_object_or_404(
            WorkOffer,
            pk=offer_id,
        )

        # Lock work to prevent simultaneous acceptance
        work = get_object_or_404(
            WorkRequest.objects.select_for_update(),
            pk=offer_ref.work_request_id,
        )

        # Only Owner / Manager can accept offers
        if not can_manage_business_work(request.user, work.business):
            messages.error(
                request,
                "You do not have permission to accept this offer.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Get and lock selected offer
        offer = get_object_or_404(
            WorkOffer.objects
            .select_for_update()
            .select_related("business"),
            pk=offer_id,
            work_request=work,
        )

        # Check work and offer status + deadline
        if (
            work.status != "open"
            or offer.status != "pending"
            or work.deadline < timezone.localdate()
        ):
            messages.error(
                request,
                "This offer cannot be accepted. Work may be closed or expired.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Prevent own business offer acceptance
        if offer.business_id == work.business_id:
            messages.error(
                request,
                "A business cannot accept its own offer.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Fetch all other pending offers
        other_offers = list(
            WorkOffer.objects.select_for_update()
            .filter(
                work_request=work,
                status="pending",
            )
            .exclude(pk=offer.pk)
            .select_related("business")
        )

        # Accept selected offer
        offer.status = "accepted"
        offer.save(update_fields=["status"])

        # Reject all other pending offers
        for other_offer in other_offers:
            other_offer.status = "rejected"
            other_offer.save(update_fields=["status"])

        # Update work status
        work.status = "assigned"
        work.save(update_fields=["status"])

        # Notify accepted supplier
        notify_business_members(
            business=offer.business,
            notification_type="offer_accepted",
            title="Your offer has been accepted",
            message=f"Your offer for '{work.title}' has been accepted.",
            work=work,
        )

        # Notify rejected suppliers
        for other_offer in other_offers:
            notify_business_members(
                business=other_offer.business,
                notification_type="offer_rejected",
                title="Your offer was not selected",
                message=f"Another offer was selected for '{work.title}'.",
                work=work,
            )

    messages.success(
        request,
        "Offer accepted successfully!",
    )

    return redirect(
        "marketplace:work_detail",
        work_id=work.pk,
    )



@login_required
def workspace(request):
    businesses = get_user_businesses(request.user)

    posted_works = WorkRequest.objects.filter(
        business__in=businesses
    ).select_related("business").prefetch_related("offers")

    received_offers = WorkOffer.objects.filter(
        work_request__business__in=businesses
    ).select_related(
        "business", "work_request"
    )

    sent_offers = WorkOffer.objects.filter(
        business__in=businesses
    ).select_related(
        "business", "work_request"
    )

    pending_sent_offers = sent_offers.filter(status="pending")
    accepted_sent_offers = sent_offers.filter(status="accepted")
    rejected_sent_offers = sent_offers.filter(status="rejected")

    assigned_work = WorkRequest.objects.filter(
        offers__business__in=businesses,
        offers__status="accepted",
        status="assigned",
    ).select_related("business").distinct()

    completed_work = WorkRequest.objects.filter(
        offers__business__in=businesses,
        offers__status="accepted",
        status="completed",
    ).select_related("business").distinct()

    context = {
        "businesses": businesses,
        "posted_works": posted_works,
        "received_offers": received_offers,
        "sent_offers": sent_offers,
        "open_count": posted_works.filter(status="open").count(),
        "assigned_count": posted_works.filter(status="assigned").count(),
        "received_count": received_offers.count(),
        "sent_count": sent_offers.count(),
        "pending_sent_offers": pending_sent_offers,
        "accepted_sent_offers": accepted_sent_offers,
        "rejected_sent_offers": rejected_sent_offers,
        "assigned_work": assigned_work,
        "completed_work": completed_work,
        "pending_sent_count": pending_sent_offers.count(),
        "accepted_sent_count": accepted_sent_offers.count(),
        "rejected_sent_count": rejected_sent_offers.count(),
        "assigned_work_count": assigned_work.count(),
        "completed_work_count": completed_work.count(),
    }

    return render(request, "marketplace/workspace.html", context)




@login_required
@require_POST
def update_work_status(request, work_id):

    with transaction.atomic():

        # Get and lock work request
        work = get_object_or_404(
            WorkRequest.objects.select_for_update(),
            pk=work_id,
        )

        # Only Owner / Manager can cancel work
        if not can_manage_business_work(
            request.user,
            work.business,
        ):
            messages.error(
                request,
                "You do not have permission to manage this work.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Only open work can be cancelled
        if (
            work.status != "open"
            or request.POST.get("status") != "cancelled"
        ):
            messages.error(
                request,
                "This status change is not allowed.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Cancel work request
        work.status = "cancelled"
        work.save(update_fields=["status"])

        # Get all pending offers
        pending_offers = list(
            WorkOffer.objects.filter(
                work_request=work,
                status="pending",
            ).select_related("business")
        )

        # Notify suppliers about cancellation
        for offer in pending_offers:
            notify_business_members(
                business=offer.business,
                notification_type="work_cancelled",
                title="Work request cancelled",
                message=f"'{work.title}' has been cancelled.",
                work=work,
            )

    messages.success(
        request,
        "Work request cancelled successfully.",
    )

    return redirect(
        "marketplace:work_detail",
        work_id=work.pk,
    )


def notify_business_members(business, notification_type, title, message, work):
    members = BusinessMembership.objects.filter(
        business=business
    ).values_list("user_id", flat=True).distinct()

    notifications = [
        Notification(
            recipient_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            work_request=work,
        )
        for user_id in members
    ]

    Notification.objects.bulk_create(notifications)

@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related("work_request")

    unread_count = notifications.filter(is_read=False).count()

    return render(
        request,
        "marketplace/notifications.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        },
    )


@login_required
def mark_notification_read(request, notification_id):
    if request.method != "POST":
        return redirect("marketplace:notifications")

    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        recipient=request.user,
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    if notification.work_request_id:
        return redirect(
            "marketplace:work_detail",
            work_id=notification.work_request_id,
        )

    return redirect("marketplace:notifications")


@login_required
def mark_all_notifications_read(request):
    if request.method == "POST":
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)

        messages.success(request, "All notifications marked as read.")

    return redirect("marketplace:notifications")

def how_it_works(request):
    return render(request, "marketplace/how_it_works.html")



@login_required
@require_POST
def reject_offer(request, offer_id):

    with transaction.atomic():

        # Get offer reference
        offer_ref = get_object_or_404(
            WorkOffer,
            pk=offer_id,
        )

        # Lock work request first
        work = get_object_or_404(
            WorkRequest.objects.select_for_update(),
            pk=offer_ref.work_request_id,
        )

        # Only Owner / Manager can reject offers
        if not can_manage_business_work(
            request.user,
            work.business,
        ):
            messages.error(
                request,
                "You do not have permission to reject this offer.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Get and lock selected offer
        offer = get_object_or_404(
            WorkOffer.objects
            .select_for_update()
            .select_related("business"),
            pk=offer_id,
            work_request=work,
        )

        # Check whether offer can still be rejected
        if (
            work.status != "open"
            or offer.status != "pending"
        ):
            messages.error(
                request,
                "This offer cannot be rejected now.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Reject offer
        offer.status = "rejected"
        offer.save(update_fields=["status"])

        # Notify supplier business members
        notify_business_members(
            business=offer.business,
            notification_type="offer_rejected",
            title="Your offer was rejected",
            message=f"Your offer for '{work.title}' was not selected.",
            work=work,
        )

    messages.success(
        request,
        "Offer rejected successfully.",
    )

    return redirect(
        "marketplace:work_detail",
        work_id=work.pk,
    )




@login_required
@require_POST
def submit_work_completion(request, work_id):

    with transaction.atomic():

        # Get and lock work request
        work = get_object_or_404(
            WorkRequest.objects.select_for_update(),
            pk=work_id,
        )

        # Work must be assigned
        if work.status != "assigned":
            messages.error(
                request,
                "This work cannot be submitted for completion.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Find the accepted supplier
        accepted_offer = (
            WorkOffer.objects
            .select_related("business")
            .filter(
                work_request=work,
                status="accepted",
            )
            .first()
        )

        if not accepted_offer:
            messages.error(
                request,
                "No accepted supplier found.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Only accepted supplier's Owner / Manager
        # can submit completion
        if not can_manage_business_work(
            request.user,
            accepted_offer.business,
        ):
            messages.error(
                request,
                "Only the assigned supplier's owner or manager "
                "can submit this work for completion.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Update work status
        work.status = "completion_pending"
        work.save(update_fields=["status"])

        # Notify the work-posting business
        notify_business_members(
            business=work.business,
            notification_type="completion_requested",
            title="Work completion submitted",
            message=(
                f"{accepted_offer.business.name} has submitted "
                f"'{work.title}' for approval."
            ),
            work=work,
        )

    messages.success(
        request,
        "Completion submitted for owner approval.",
    )

    return redirect(
        "marketplace:work_detail",
        work_id=work.pk,
    )



@login_required
@require_POST
def approve_work_completion(request, work_id):

    with transaction.atomic():

        # Get and lock work request
        work = get_object_or_404(
            WorkRequest.objects.select_for_update(),
            pk=work_id,
        )

        # Only work-posting business Owner / Manager
        # can approve completion
        if not can_manage_business_work(
            request.user,
            work.business,
        ):
            messages.error(
                request,
                "You do not have permission to approve this completion.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Completion request must be pending
        if work.status != "completion_pending":
            messages.error(
                request,
                "No completion request is pending.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Get accepted supplier offers
        accepted_offers = list(
            WorkOffer.objects
            .select_related("business")
            .filter(
                work_request=work,
                status="accepted",
            )
        )

        if not accepted_offers:
            messages.error(
                request,
                "No accepted supplier found for this work.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Mark work as completed
        work.status = "completed"
        work.save(update_fields=["status"])

        # Notify accepted suppliers
        for offer in accepted_offers:
            notify_business_members(
                business=offer.business,
                notification_type="work_completed",
                title="Work completion approved",
                message=(
                    f"'{work.title}' has been approved as completed."
                ),
                work=work,
            )

    messages.success(
        request,
        "Work marked as completed successfully.",
    )

    return redirect(
        "marketplace:work_detail",
        work_id=work.pk,
    )


@login_required
@require_POST
def reject_work_completion(request, work_id):

    with transaction.atomic():

        # Get and lock work request
        work = get_object_or_404(
            WorkRequest.objects.select_for_update(),
            pk=work_id,
        )

        # Only work-posting business Owner / Manager
        # can reject completion
        if not can_manage_business_work(
            request.user,
            work.business,
        ):
            messages.error(
                request,
                "You do not have permission to reject this completion.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Completion request must be pending
        if work.status != "completion_pending":
            messages.error(
                request,
                "No completion request is pending.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Get accepted supplier offers
        accepted_offers = list(
            WorkOffer.objects
            .select_related("business")
            .filter(
                work_request=work,
                status="accepted",
            )
        )

        if not accepted_offers:
            messages.error(
                request,
                "No accepted supplier found for this work.",
            )
            return redirect(
                "marketplace:work_detail",
                work_id=work.pk,
            )

        # Return work to assigned status
        work.status = "assigned"
        work.save(update_fields=["status"])

        # Notify accepted suppliers
        for offer in accepted_offers:
            notify_business_members(
                business=offer.business,
                notification_type="completion_rejected",
                title="Completion request rejected",
                message=(
                    f"'{work.title}' needs further work before approval."
                ),
                work=work,
            )

    messages.success(
        request,
        "Completion request rejected. Work remains assigned.",
    )

    return redirect(
        "marketplace:work_detail",
        work_id=work.pk,
    )

@login_required
@require_http_methods(["GET", "POST"])
def submit_business_review(request, work_id):

    work = get_object_or_404(
        WorkRequest.objects.select_related("business"),
        pk=work_id,
        status="completed",
    )

    accepted_offer = (
        WorkOffer.objects
        .select_related("business")
        .filter(
            work_request=work,
            status="accepted",
        )
        .first()
    )

    if not accepted_offer:
        messages.error(
            request,
            "This work has no accepted supplier.",
        )
        return redirect(
            "marketplace:work_detail",
            work_id=work.pk,
        )

    # Only the work owner reviews the accepted supplier
    reviewer_business = work.business
    reviewed_business = accepted_offer.business

    can_review = (
        BusinessMembership.objects.filter(
            user=request.user,
            business=reviewer_business,
            role__in=["owner", "manager"],
        ).exists()
    )

    if not can_review:
        messages.error(
            request,
            "You are not authorized to review this work.",
        )
        return redirect(
            "marketplace:work_detail",
            work_id=work.pk,
        )

    if reviewer_business.pk == reviewed_business.pk:
        messages.error(
            request,
            "A business cannot review itself.",
        )
        return redirect(
            "marketplace:work_detail",
            work_id=work.pk,
        )

    if BusinessReview.objects.filter(
        work_request=work,
        reviewer_business=reviewer_business,
    ).exists():

        messages.info(
            request,
            "You have already reviewed this work.",
        )

        return redirect(
            "marketplace:work_detail",
            work_id=work.pk,
        )

    form = BusinessReviewForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        with transaction.atomic():

            # Lock work to reduce concurrent duplicate submissions
            locked_work = WorkRequest.objects.select_for_update().get(
                pk=work.pk
            )

            if locked_work.status != "completed":
                messages.error(
                    request,
                    "Only completed work can be reviewed.",
                )
                return redirect(
                    "marketplace:work_detail",
                    work_id=work.pk,
                )

            if BusinessReview.objects.filter(
                work_request=work,
                reviewer_business=reviewer_business,
            ).exists():
                messages.error(
                    request,
                    "This work has already been reviewed.",
                )
                return redirect(
                    "marketplace:work_detail",
                    work_id=work.pk,
                )

            review = form.save(commit=False)
            review.work_request = work
            review.reviewer_business = reviewer_business
            review.reviewed_business = reviewed_business
            review.reviewed_by = request.user
            review.save()

        messages.success(
            request,
            "Review submitted successfully.",
        )

        return redirect(
            "accounts:supplier_profile",
            business_id=reviewed_business.pk,
        )

    return render(
        request,
        "marketplace/submit_review.html",
        {
            "form": form,
            "work": work,
            "reviewed_business": reviewed_business,
        },
    )
