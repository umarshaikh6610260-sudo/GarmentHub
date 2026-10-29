from django.contrib import admin

from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views

from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("marketplace/", include("marketplace.urls")),
    path("", include("home.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path(
    "messages/",
    include("messaging.urls"),
),

# Password Reset
path(
    "password-reset/",
    auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
        success_url=reverse_lazy("password_reset_done"),
    ),
    name="password_reset",
),

path(
    "password-reset/done/",
    auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html",
    ),
    name="password_reset_done",
),

path(
    "password-reset/<uidb64>/<token>/",
    auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete"),
    ),
    name="password_reset_confirm",
),

path(
    "password-reset/complete/",
    auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html",
    ),
    name="password_reset_complete",
),

]
