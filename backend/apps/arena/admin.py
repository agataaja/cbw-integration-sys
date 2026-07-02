from django.contrib import admin
from .models import ArenaWebhookPayload
import json


@admin.register(ArenaWebhookPayload)
class ArenaWebhookPayloadAdmin(admin.ModelAdmin):
    list_display = ('id', 'received_at', 'short_payload')
    list_filter = ('received_at',)
    search_fields = ('payload',)

    # Mostrar um resumo do JSON no admin
    def short_payload(self, obj):
        # Formata o JSON e mostra só as primeiras 100 chars
        return json.dumps(obj.payload, ensure_ascii=False)

    short_payload.short_description = 'Payload'




