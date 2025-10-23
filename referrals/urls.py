from django.urls import path
from . import api_views

urlpatterns = [
    path("me/code/", api_views.MyReferralCodeView.as_view(), name="referral-my-code"),
    path("me/referrals/", api_views.MyReferralsView.as_view(), name="referral-my-referrals"),
    path("apply/<str:code>/", api_views.ApplyReferralView.as_view(), name="referral-apply"),
    path("me/commissions/", api_views.MyCommissionsView.as_view(), name="referral-my-commissions"),
]
