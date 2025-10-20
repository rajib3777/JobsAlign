"""
ASGI config for jobsalign project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsalign.settings')

application = get_asgi_application()


#my add
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

import chats.routings
import notifications.routings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsalign.settings')
django.setup()

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,  # normal HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notifications.routing.websocket_urlpatterns +
            chats.routing.websocket_urlpatterns
        )
    ),
})

