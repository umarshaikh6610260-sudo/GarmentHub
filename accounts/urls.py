
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "business/create/",
        views.create_business,
        name="create_business",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "business/<int:business_id>/",
        views.business_detail,
        name="business_detail",
    ),

    path(
    "business/<int:business_id>/edit/",
    views.edit_business,
    name="edit_business",
),
path(
    "business/<int:business_id>/members/add/",
    views.add_business_member,
    name="add_business_member",
),
path(
    "business/<int:business_id>/members/<int:membership_id>/role/",
    views.change_member_role,
    name="change_member_role",
),
path(
    "business/<int:business_id>/members/<int:membership_id>/remove/",
    views.remove_business_member,
    name="remove_business_member",
),
path(
    "suppliers/",
    views.supplier_directory,
    name="supplier_directory",
),

path(
    "suppliers/<int:business_id>/",
    views.supplier_profile,
    name="supplier_profile",
),

path(
    "business/<int:business_id>/verification/request/",
    views.request_business_verification,
    name="request_business_verification",
),

path(
    "business/<int:business_id>/verification/status/",
    views.verification_status,
    name="verification_status",
),

path(
    "verification/<int:verification_id>/document/",
    views.download_verification_document,
    name="download_verification_document",
),

]
