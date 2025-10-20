from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from .models import Notification, NotificationPreference
from .tasks import deliver_push_notification, send_email_notification
import json

channel_layer = get_channel_layer()

def _user_pref_allows(user, channel, verb=None):
    """Check user preferences for a given channel and (optionally) verb."""
    # default: allow
    if not NotificationPreference.objects.filter(user=user).exists():
        return True
    prefs = NotificationPreference.objects.filter(user=user)
    # specific preference for verb+channel
    if verb:
        if prefs.filter(channel=channel, notification_type=verb).exists():
            return prefs.get(channel=channel, notification_type=verb).enabled
    # any channel-level preference
    try:
        p = prefs.get(channel=channel, notification_type__isnull=True)
        return p.enabled
    except NotificationPreference.DoesNotExist:
        return True

@transaction.atomic
def create_notification(user, verb, title, message=None, actor=None, data=None, group_key=None, level='info', skip_channels=None, send_push=True, send_email=True):
    """
    Create notification object and schedule delivery based on user preferences.
    - group_key: when present, we attempt to find an existing recent notification with same key and update it (stacking)
    - skip_channels: list like ['email'] to skip immediate sending
    """
    skip_channels = skip_channels or []
    data = data or {}
    # Try stacking/deduplication if group_key provided (stack within last 10 minutes)
    notif = None
    if group_key:
        ten_min = timezone.now() - timezone.timedelta(minutes=10)
        existing = Notification.objects.filter(user=user, group_key=group_key, created_at__gte=ten_min).order_by('-created_at').first()
        if existing:
            # update existing: increment an aggregated counter in data
            existing.data = {**existing.data, **data}
            existing.message = message or existing.message
            existing.title = title or existing.title
            existing.updated_at = timezone.now()
            existing.save(update_fields=['data','message','title','updated_at'])
            notif = existing

    if not notif:
        notif = Notification.objects.create(
            user=user,
            actor=actor,
            verb=verb,
            title=title,
            message=message,
            level=level,
            data=data or {},
            group_key=group_key
        )

    # send in-app real-time via channels (if preference allows)
    try:
        if _user_pref_allows(user, 'inapp', verb=verb):
            payload = {
                'type':'notification.message',
                'data': {
                    'id': str(notif.id),
                    'verb': notif.verb,
                    'title': notif.title,
                    'message': notif.message,
                    'data': notif.data,
                    'created_at': notif.created_at.isoformat(),
                }
            }
            async_to_sync(channel_layer.group_send)(f'user_{user.id}', payload)
    except Exception:
        pass

    # schedule push if allowed
    if send_push and _user_pref_allows(user, 'push', verb=verb):
        try:
            # push delivery via celery (e.g. FCM or APNs)
            deliver_push_notification.delay(str(notif.id))
        except Exception:
            pass

    # schedule email if allowed
    if send_email and _user_pref_allows(user, 'email', verb=verb):
        try:
            send_email_notification.delay(str(notif.id))
        except Exception:
            pass

    return notif

def create_notification_via_api(requesting_user, user_id, verb, title, message=None, actor_id=None, data=None, group_key=None, level='info'):
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    target = User.objects.get(id=user_id)
    actor = None
    if actor_id:
        actor = User.objects.get(id=actor_id)
    return create_notification(target, verb, title, message=message, actor=actor, data=data, group_key=group_key, level=level)
