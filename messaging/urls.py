from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "messaging"

urlpatterns = [
    path(
        "",
        views.inbox,
        name="inbox",
    ),

    path(
        "conversation/",
        RedirectView.as_view(
            pattern_name="messaging:inbox",
            permanent=False,
        ),
    ),

    path(
        "conversation/<int:conversation_id>/",
        views.conversation_detail,
        name="conversation",
    ),

    path(
        "inquiry/<int:business_id>/",
        views.start_inquiry,
        name="start_inquiry",
    ),

    path(
        "conversation/<int:conversation_id>/send/",
        views.send_message,
        name="send_message",
    ),

    path(
        "conversation/<int:conversation_id>/read/",
        views.mark_conversation_read,
        name="mark_read",
    ),
]