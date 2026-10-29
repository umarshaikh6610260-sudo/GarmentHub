from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import (
    Count,
    Max,
    OuterRef,
    Q,
    Subquery,
)
from django.db.models.functions import Coalesce
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Business, BusinessMembership

from .forms import BusinessMessageForm, StartInquiryForm
from .models import (
    BusinessMessage,
    Conversation,
    ConversationReadState,
)


# -----------------------------------------
# Permission helpers
# -----------------------------------------

def member_businesses(user):
    return Business.objects.filter(
        memberships__user=user,
    ).distinct()


def manageable_businesses(user):
    return Business.objects.filter(
        memberships__user=user,
        memberships__role__in=["owner", "manager"],
    ).distinct()


def can_send_as(user, business):
    return BusinessMembership.objects.filter(
        user=user,
        business=business,
        role__in=["owner", "manager"],
    ).exists()


def conversation_for_user(user, conversation_id):

    return get_object_or_404(
        Conversation.objects
        .select_related("business_one", "business_two")
        .filter(
            Q(business_one__memberships__user=user)
            | Q(business_two__memberships__user=user)
        )
        .distinct(),
        pk=conversation_id,
    )


# -----------------------------------------
# Inbox
# -----------------------------------------

@login_required
def inbox(request):

    businesses = list(
        member_businesses(request.user).order_by("name")
    )

    business_ids = [business.pk for business in businesses]

    conversations = (
        Conversation.objects
        .filter(
            Q(business_one_id__in=business_ids)
            | Q(business_two_id__in=business_ids)
        )
        .select_related("business_one", "business_two")
        .order_by("-updated_at", "-pk")
    )

    page_obj = Paginator(conversations, 15).get_page(
        request.GET.get("page")
    )

    rows = []

    for conversation in page_obj.object_list:

        last_message = (
            conversation.messages
            .select_related("sender_business")
            .order_by("-created_at", "-pk")
            .first()
        )

        read_state = ConversationReadState.objects.filter(
            conversation=conversation,
            user=request.user,
        ).first()

        unread_messages = conversation.messages.exclude(
            sender_business_id__in=business_ids
        )

        if read_state and read_state.last_read_at:
            unread_messages = unread_messages.filter(
                created_at__gt=read_state.last_read_at
            )

        rows.append({
            "conversation": conversation,
            "last_message": last_message,
            "unread_count": unread_messages.count(),
        })

    return render(
        request,
        "messaging/inbox.html",
        {
            "rows": rows,
            "page_obj": page_obj,
            "businesses": businesses,
        },
    )


# -----------------------------------------
# Start inquiry
# -----------------------------------------

@login_required
def start_inquiry(request, business_id):

    receiver = get_object_or_404(
        Business,
        pk=business_id,
    )

    # Only Owner / Manager can send an inquiry
    sender_businesses = list(
        manageable_businesses(request.user)
        .exclude(pk=receiver.pk)
        .order_by("name")
    )

    # Do not allow contacting a business
    # where the user is already a member.
    if BusinessMembership.objects.filter(
        user=request.user,
        business=receiver,
    ).exists():

        messages.error(
            request,
            "You cannot send an inquiry to your own business.",
        )

        return redirect(
            "accounts:supplier_profile",
            business_id=receiver.pk,
        )

    if not sender_businesses:
        messages.error(
            request,
            "You need an Owner or Manager business to send inquiries.",
        )

        return redirect(
            "accounts:supplier_profile",
            business_id=receiver.pk,
        )

    form = StartInquiryForm(
        request.POST or None,
        businesses=sender_businesses,
    )

    if request.method == "POST" and form.is_valid():

        sender_id = int(
            form.cleaned_data["sender_business"]
        )

        sender = get_object_or_404(
            manageable_businesses(request.user),
            pk=sender_id,
        )

        first_id, second_id = sorted([
            sender.pk,
            receiver.pk,
        ])

        with transaction.atomic():

            conversation, created = (
                Conversation.objects.get_or_create(
                    business_one_id=first_id,
                    business_two_id=second_id,
                    defaults={
                        "subject": (
                            form.cleaned_data["subject"]
                            or "Business Inquiry"
                        ),
                        "created_by": request.user,
                    },
                )
            )

            BusinessMessage.objects.create(
                conversation=conversation,
                sender_business=sender,
                sender_user=request.user,
                body=form.cleaned_data["message"],
            )

            Conversation.objects.filter(
                pk=conversation.pk,
            ).update(
                updated_at=timezone.now()
            )

        messages.success(
            request,
            "Your inquiry has been sent successfully.",
        )

        return redirect(
            "messaging:conversation",
            conversation_id=conversation.pk,
        )

    return render(
        request,
        "messaging/start_inquiry.html",
        {
            "receiver": receiver,
            "form": form,
        },
    )


# -----------------------------------------
# Conversation detail
# -----------------------------------------

@login_required
def conversation_detail(request, conversation_id):

    conversation = conversation_for_user(
        request.user,
        conversation_id,
    )

    user_businesses = list(
        member_businesses(request.user)
        .filter(
            pk__in=[
                conversation.business_one_id,
                conversation.business_two_id,
            ]
        )
    )

    sender_businesses = list(
        manageable_businesses(request.user)
        .filter(
            pk__in=[
                conversation.business_one_id,
                conversation.business_two_id,
            ]
        )
    )

    messages_qs = (
        conversation.messages
        .select_related("sender_business", "sender_user")
        .order_by("created_at", "pk")
    )

    page_obj = Paginator(messages_qs, 30).get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "messaging/conversation.html",
        {
            "conversation": conversation,
            "chat_messages": page_obj.object_list,
            "page_obj": page_obj,
            "sender_businesses": sender_businesses,
            "user_businesses": user_businesses,
            "message_form": BusinessMessageForm(),
        },
    )


# -----------------------------------------
# Send message
# -----------------------------------------

@login_required
@require_POST
def send_message(request, conversation_id):

    conversation = conversation_for_user(
        request.user,
        conversation_id,
    )

    sender_id = request.POST.get("sender_business")

    sender = get_object_or_404(
        manageable_businesses(request.user),
        pk=sender_id,
    )

    if sender.pk not in [
        conversation.business_one_id,
        conversation.business_two_id,
    ]:
        messages.error(
            request,
            "This business is not part of the conversation.",
        )
        return redirect(
            "messaging:conversation",
            conversation_id=conversation.pk,
        )

    form = BusinessMessageForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "Please enter a valid message (maximum 3000 characters).",
        )
        return redirect(
            "messaging:conversation",
            conversation_id=conversation.pk,
        )

    with transaction.atomic():

        message = form.save(commit=False)
        message.conversation = conversation
        message.sender_business = sender
        message.sender_user = request.user
        message.save()

        Conversation.objects.filter(
            pk=conversation.pk,
        ).update(
            updated_at=timezone.now()
        )

    messages.success(
        request,
        "Message sent successfully.",
    )

    return redirect(
        "messaging:conversation",
        conversation_id=conversation.pk,
    )


# -----------------------------------------
# Mark conversation as read
# -----------------------------------------

@login_required
@require_POST
def mark_conversation_read(request, conversation_id):

    conversation = conversation_for_user(
        request.user,
        conversation_id,
    )

    ConversationReadState.objects.update_or_create(
        conversation=conversation,
        user=request.user,
        defaults={
            "last_read_at": timezone.now(),
        },
    )

    return redirect(
        "messaging:conversation",
        conversation_id=conversation.pk,
    )