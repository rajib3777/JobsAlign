from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class ChatsBasicTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(email='a@example.com', password='pass')
        self.u2 = User.objects.create_user(email='b@example.com', password='pass')
        self.client.login(email='a@example.com', password='pass')

    def test_create_conversation_and_send_message(self):
        resp = self.client.post(reverse('conversation-create'), data={'participant_ids': [str(self.u2.id)]}, content_type='application/json')
        self.assertIn(resp.status_code, (200,201))
        conv_id = resp.data.get('id')
        self.assertIsNotNone(conv_id)
        # send message
        resp2 = self.client.post(reverse('message-create'), data={'conversation': conv_id, 'content': 'hello'}, content_type='application/json')
        self.assertIn(resp2.status_code, (200,201))
        msgs = Message.objects.filter(conversation_id=conv_id)
        self.assertTrue(msgs.exists())
