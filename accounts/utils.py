from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse


def send_verification_email(request, user):
    """
    Sends an account verification email to the newly registered user.
    """

    # Generate unique verification token & encoded user ID
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # Construct verification link
    verification_link = request.build_absolute_uri(
        reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
    )

    # Email content
    subject = "Verify Your JobsAlign Account"
    message = f"""
    Hi {user.full_name},

    Welcome to JobsAlign! Please verify your email address by clicking the link below:

    {verification_link}

    If you didn't sign up for JobsAlign, you can ignore this email.

    Regards,
    JobsAlign Team
    """

    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.send(fail_silently=False)
