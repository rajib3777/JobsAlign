from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from decimal import Decimal
import uuid



# ======================================
# 🔹 Custom User Manager
# ======================================
class UserManager(BaseUserManager):
    def create_user(self, email, full_name=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, full_name, password, **extra_fields)


# ======================================
# 🔹 User Model (Google Auth Ready)
# ======================================
class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = [
        ("buyer", "Buyer"),
        ("freelancer", "Freelancer"),
        ("admin", "Admin"),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    # 🧩 Basic Info
    username = models.CharField(max_length=150, blank=True, null=True, default='user')
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default="buyer")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # 🧠 Google Authentication Support
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True, help_text="Google account ID")
    google_avatar = models.URLField(blank=True, null=True, help_text="Google profile picture URL")
    google_auth = models.BooleanField(default=False)

    # 🖼️ Profile & Media
    profile_photo = models.ImageField(
        upload_to="profiles/photos/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png"])],
        blank=True,
        null=True,
    )
    cover_photo = models.ImageField(
        upload_to="profiles/covers/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png"])],
        blank=True,
        null=True,
    )
    tagline = models.CharField(max_length=150, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True)

    # ✅ Account & Verification
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    # 🌍 Location & Social Links
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
     # 🪪 KYC / Identity Verification
    is_identity_verified = models.BooleanField(default=False)
    identity_document = models.FileField(
        upload_to="kyc/documents/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "pdf"])],
        blank=True,
        null=True,
        help_text="Government ID or Passport"
    )

    # 🏆 Professional Metrics (Levels / Scores)
    level = models.CharField(max_length=50, default="New", help_text="Freelancer level like Level 1, Level 2, Top Rated")
    trust_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    # 💼 Portfolio & Skills
    skills = models.JSONField(default=list, blank=True, help_text="List of key skills")
    portfolio_url = models.URLField(blank=True, null=True, help_text="External portfolio link")
    portfolio_description = models.TextField(blank=True, null=True)

    # 📊 Marketplace Analytics
    total_projects = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    # 👥 Social Metrics
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)

    # 🕵️ Login Tracking (for security and insights)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_device = models.CharField(max_length=255, blank=True, null=True)

    # 🔔 Notification Preferences
    allow_email_notifications = models.BooleanField(default=True)
    allow_system_notifications = models.BooleanField(default=True)

    # # 💰 External Relations (via other apps)
    # referral = models.OneToOneField(
    #     "referral.ReferralAccount",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="user_account",
    # )
    wallet = models.OneToOneField(
        "payments.Wallet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_account",
    )

    # ⭐ Rating System
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    total_reviews = models.PositiveIntegerField(default=0)

    # 🕓 Online Tracking
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    # ======================================
    # 🔹 Helper Methods
    # ======================================
    def update_rating(self, new_rating):
        total = self.total_reviews + 1
        self.rating = ((self.rating * self.total_reviews) + new_rating) / total
        self.total_reviews = total
        self.save(update_fields=["rating", "total_reviews"])

    @property
    def profile_completion(self):
        """Calculate profile completion percentage."""
        fields = [
            self.profile_photo,
            self.cover_photo,
            self.tagline,
            self.bio,
            self.country,
            self.city,
            self.linkedin,
            self.github,
            self.website,
        ]
        filled = sum(1 for f in fields if f)
        total = len(fields)
        return round((filled / total) * 100, 2)

    def mark_online(self):
        self.is_online = True
        self.last_seen = timezone.now()
        self.save(update_fields=["is_online", "last_seen"])

    def mark_offline(self):
        self.is_online = False
        self.last_seen = timezone.now()
        self.save(update_fields=["is_online", "last_seen"])

    def generate_google_auth_user(self, google_data):
        """
        Create or update user via Google OAuth.
        google_data = {
            'id': 'google_id',
            'email': 'user@gmail.com',
            'name': 'User Name',
            'picture': 'https://googleusercontent.com/...'
        }
        """
        self.google_id = google_data.get("id")
        self.google_auth = True
        self.is_verified = True
        self.google_avatar = google_data.get("picture")
        if not self.profile_photo:
            self.profile_photo = google_data.get("picture")
        self.save()


# # ======================================
# # 🔹 Signals for auto-referral & wallet link
# # ======================================
# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=User)
# def create_related_accounts(sender, instance, created, **kwargs):
#     """
#     Auto-create referral & wallet when a new user is registered.
#     """
#     if created:
#         # from referral.models import ReferralAccount
#         # from payments.models import Wallet

#         if not instance.referral:
#             referral_acc = ReferralAccount.objects.create(user=instance)
#             instance.referral = referral_acc

#         if not instance.wallet:
#             wallet_acc = Wallet.objects.create(user=instance)
#             instance.wallet = wallet_acc

#         instance.save()


