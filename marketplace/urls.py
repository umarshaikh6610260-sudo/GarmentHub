from django.urls import path
from . import views

app_name = "marketplace"

urlpatterns = [
    path("", views.marketplace_home, name="home"),
    path("work/create/", views.create_work, name="create_work"),
    path("work/<int:work_id>/", views.work_detail, name="work_detail"),
    path("work/<int:work_id>/offer/", views.submit_offer, name="submit_offer"),
    path("offer/<int:offer_id>/accept/", views.accept_offer, name="accept_offer"),
    path("workspace/", views.workspace, name="workspace"),
    path(
    "work/<int:work_id>/status/",
    views.update_work_status,
    name="update_work_status",
),
path(
    "notifications/",
    views.notifications_page,
    name="notifications",
),
path(
    "notifications/<int:notification_id>/read/",
    views.mark_notification_read,
    name="mark_notification_read",
),
path(
    "notifications/read-all/",
    views.mark_all_notifications_read,
    name="mark_all_notifications_read",
),
path("how-it-works/", views.how_it_works, name="how_it_works"),

path(
    "offers/<int:offer_id>/accept/",
    views.accept_offer,
    name="accept_offer",
),
path(
    "offers/<int:offer_id>/reject/",
    views.reject_offer,
    name="reject_offer",
),
path(
    "work/<int:work_id>/submit-completion/",
    views.submit_work_completion,
    name="submit_work_completion",
),
path(
    "work/<int:work_id>/approve-completion/",
    views.approve_work_completion,
    name="approve_work_completion",
),
path(
    "work/<int:work_id>/reject-completion/",
    views.reject_work_completion,
    name="reject_work_completion",
),

path(
    "work/<int:work_id>/review/",
    views.submit_business_review,
    name="submit_business_review",
),

]