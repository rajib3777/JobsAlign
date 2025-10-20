from channels.generic.websocket import AsyncJsonWebsocketConsumer

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer that subscribes to user's notification group: user_<id>
    Sends `notification.message` events as they are group-sent by utils.create_notification.
    """
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        self.group_name = f'user_{user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event):
        # Event created in utils: type 'notification.message'
        await self.send_json({
            'type': 'notification',
            'data': event.get('data')
        })
