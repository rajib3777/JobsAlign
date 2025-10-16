from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'user_type', 'is_active', 'is_staff', 'is_verified')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_verified')
    search_fields = ('email', 'full_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email','password')}),
        (_('Personal info'), {'fields': ('full_name','user_type','profile_photo','tagline')}),
        (_('Contact / links'), {'fields': ('country','city','address','linkedin','github','website')}),
        (_('Permissions'), {'fields': ('is_active','is_staff','is_superuser','groups','user_permissions')}),
        (_('Important dates'), {'fields': ('last_login','date_joined','last_seen')}),
        (_('External links'), {'fields': ('google_auth','google_id','referral','wallet')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email','full_name','password1','password2'),
        }),
    )

