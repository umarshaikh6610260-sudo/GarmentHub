from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateVerificationStorage(FileSystemStorage):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "location",
            settings.BASE_DIR / "private_verification_uploads",
        )
        super().__init__(*args, **kwargs)

    def url(self, name):
        raise ValueError(
            "Verification documents do not have public URLs."
        )