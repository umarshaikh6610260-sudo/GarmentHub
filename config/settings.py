# from pathlib import Path

# import os

# # SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# DEBUG = os.environ.get(
#     "DJANGO_DEBUG", "False"
# ).lower() == "true"

# ALLOWED_HOSTS = [
#     host.strip()
#     for host in os.environ.get(
#         "DJANGO_ALLOWED_HOSTS", ""
#     ).split(",")
#     if host.strip()
# ]

# CSRF_TRUSTED_ORIGINS = [
#     origin.strip()
#     for origin in os.environ.get(
#         "DJANGO_CSRF_TRUSTED_ORIGINS", ""
#     ).split(",")
#     if origin.strip()
# ]

# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = "replace-this-key-before-deployment"
# DEBUG = True
# ALLOWED_HOSTS = []

# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "home",
#     "accounts",
#     "marketplace",
#     "messaging",
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.locale.LocaleMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# ROOT_URLCONF = "config.urls"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [BASE_DIR / "templates"],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#                 "marketplace.context_processors.notification_count",
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = "config.wsgi.application"

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# AUTH_PASSWORD_VALIDATORS = [
#     {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
#     {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
#     {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
#     {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
# ]

# LANGUAGE_CODE = "en-in"
# TIME_ZONE = "Asia/Kolkata"
# USE_I18N = True
# USE_TZ = True

# LANGUAGES = [
#     ("en", "English"),
#     ("hi", "हिन्दी"),
#     ("gu", "ગુજરાતી"),
# ]

# LOCALE_PATHS = [
#     BASE_DIR / "locale",
# ]

# STATIC_URL = "static/"
# STATICFILES_DIRS = [BASE_DIR / "static"]
# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# LOGIN_REDIRECT_URL = "accounts:dashboard"
# LOGOUT_REDIRECT_URL = "accounts:login"



from pathlib import Path


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================
# BASIC SETTINGS
# ==========================================

SECRET_KEY = "django-insecure-garmenthub-local-development-key"

DEBUG = True

ALLOWED_HOSTS = []


# ==========================================
# INSTALLED APPLICATIONS
# ==========================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # GarmentHub Applications
    "home",
    "accounts",
    "marketplace",
    "messaging",
]


# ==========================================
# MIDDLEWARE
# ==========================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================================
# URL CONFIGURATION
# ==========================================

ROOT_URLCONF = "config.urls"


# ==========================================
# TEMPLATES
# ==========================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "marketplace.context_processors.notification_count",
            ],
        },
    },
]


# ==========================================
# WSGI
# ==========================================

WSGI_APPLICATION = "config.wsgi.application"


# ==========================================
# DATABASE
# ==========================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ==========================================
# PASSWORD VALIDATION
# ==========================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]


# ==========================================
# LANGUAGE AND TIMEZONE
# ==========================================

LANGUAGE_CODE = "en-in"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


LANGUAGES = [
    ("en", "English"),
    ("hi", "हिन्दी"),
    ("gu", "ગુજરાતી"),
]


LOCALE_PATHS = [
    BASE_DIR / "locale",
]


# ==========================================
# STATIC FILES
# ==========================================

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# ==========================================
# DEFAULT PRIMARY KEY
# ==========================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==========================================
# LOGIN / LOGOUT
# ==========================================

LOGIN_REDIRECT_URL = "accounts:dashboard"

LOGOUT_REDIRECT_URL = "accounts:login"


# ==========================================
# LOCAL DEVELOPMENT SECURITY
# ==========================================

SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = False

CSRF_COOKIE_SECURE = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"