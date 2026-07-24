from django.db import models
from apps.arena.models import ArenaClient
    

class Tunnel(models.Model):

    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        ERROR = "error", "Error"

    class Provider(models.TextChoices):
        NGROK = "ngrok", "Ngrok"
        CLOUDFLARE = "cloudflare", "Cloudflare"
        OTHER = "other", "Other"

    arena_client = models.ForeignKey(ArenaClient, on_delete=models.CASCADE, related_name="tunnels")
    provider = models.CharField(max_length=50, choices=Provider.choices, default=Provider.NGROK)
    instance = models.CharField(max_length=255, unique=True)
    public_url = models.URLField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFLINE)

    last_seen = models.DateTimeField( null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider} tunnel ({self.instance})"