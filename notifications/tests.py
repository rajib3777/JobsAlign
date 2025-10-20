from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Notification
from . import utils

User = get_user_model()

class NotificationBasicTest(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(email='a@example.com', password='pass')
        self.u2 = User.objects.create_user(email='b@example.com', password='pass')

    def test_create_notification_inapp(self):
        notif = utils.create_notification(user=self.u1, verb='test', title='Hello', message='World', actor=self.u2)
        self.assertTrue(Notification.objects.filter(id=notif.id).exists())
        self.assertEqual(notif.title, 'Hello')
