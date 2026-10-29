from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Conversation(models.Model):

    business_one = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="conversations_as_one",
    )

    business_two = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="conversations_as_two",
    )

    subject = models.CharField(
        max_length=180,
        default="Business Inquiry",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="started_conversations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-updated_at", "-pk"]

        constraints = [
            models.CheckConstraint(
                condition=Q(
                    business_one_id__lt=F("business_two_id")
                ),
                name="conversation_ordered_business_ids",
            ),

            models.UniqueConstraint(
                fields=["business_one", "business_two"],
                name="unique_business_conversation",
            ),
        ]

    def __str__(self):
        return (
            f"{self.business_one.name} - "
            f"{self.business_two.name}"
        )

    def other_business(self, business):
        if business.pk == self.business_one_id:
            return self.business_two

        if business.pk == self.business_two_id:
            return self.business_one

        return None


class BusinessMessage(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender_business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="sent_business_messages",
    )

    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_garmenthub_messages",
    )

    body = models.TextField(
        max_length=3000,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"Message #{self.pk}"


class ConversationReadState(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="read_states",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_read_states",
    )

    last_read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_read_state",
            ),
        ]