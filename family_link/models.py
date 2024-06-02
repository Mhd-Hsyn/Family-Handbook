from api.models import Auth, BaseModel
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Chat_Room(BaseModel):
    participants = models.ManyToManyField("api.Auth", related_name="chat_room")
    last_message = models.TextField(blank=True,null=True)
    updated_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
 

class Message(BaseModel):
    room = models.ForeignKey(Chat_Room, on_delete=models.CASCADE, related_name="room_messages")
    sender = models.ForeignKey("api.Auth", on_delete=models.CASCADE, related_name="%(class)s_sent_messages")
    message = models.TextField(blank=True, null=True)
    audio_bytes = models.TextField(blank=True, null=True)
    message_type = models.CharField(
        choices=(
            ("text", "text"),
            ("audio", "audio"),
            ("image", "image"),
            ("docs", "docs")
        ),
        max_length=5,
        default="text",
    )
    file = models.FileField(upload_to='chat_images/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)


@receiver(post_save, sender=Message)
def update_last_message(sender, instance, **kwargs):
    chat = instance.room
    chat.last_message = instance.message
    chat.save()

    