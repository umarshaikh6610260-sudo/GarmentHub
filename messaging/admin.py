from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import (
    Conversation,
    BusinessMessage,
    ConversationReadState,
)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "business_one",
        "business_two",
        "subject",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "business_one__name",
        "business_two__name",
        "subject",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]


@admin.register(BusinessMessage)
class BusinessMessageAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "conversation",
        "sender_business",
        "sender_user",
        "created_at",
    ]

    list_filter = [
        "created_at",
    ]

    search_fields = [
        "sender_business__name",
        "body",
    ]

    readonly_fields = [
        "created_at",
    ]


@admin.register(ConversationReadState)
class ConversationReadStateAdmin(admin.ModelAdmin):

    list_display = [
        "conversation",
        "user",
        "last_read_at",
    ]