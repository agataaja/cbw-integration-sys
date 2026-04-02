from django.contrib import admin
from .models import Luta, WebhookPayload, CredentialsArena, EventosArena, EventosSge
import json


@admin.register(Luta)
class LutaAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'id_evento',
                    'numero',
                    'tapete',

                    # Atleta 1
                    'id_atleta1',
                    'atleta1_flag_injured',
                    'atleta1_flag_seeded',
                    'atleta1_draw_rank',
                    'atleta1_RobinRank',
                    'atleta1_ranking_point',

                    # Atleta 2
                    'id_atleta2',
                    'atleta2_flag_injured',
                    'atleta2_flag_seeded',
                    'atleta2_draw_rank',
                    'atleta2_RobinRank',
                    'atleta2_ranking_point',

                    # Resultado
                    'flag_finalizado',
                    'id_atleta_ganhador',
                    'resultado',
                    'tipo_vitoria',

                    # Categoria e estilo
                    'sportAlternateName',
                    'weightCategoryName',
                    'id_classe_peso',
                    'audienceName',
                    'round',

                    # Datas
                    'data_inicio',
                    'data_fim',
                    )
    list_filter = ('sportAlternateName', 'weightCategoryName', 'round', 'tapete', 'audienceName')
    search_fields = ('id_atleta1', 'id_atleta2', 'id_atleta_ganhador')


@admin.register(WebhookPayload)
class WebhookPayloadAdmin(admin.ModelAdmin):
    list_display = ('id', 'received_at', 'short_payload')
    list_filter = ('received_at',)
    search_fields = ('payload',)

    # Mostrar um resumo do JSON no admin
    def short_payload(self, obj):
        # Formata o JSON e mostra só as primeiras 100 chars
        return json.dumps(obj.payload, ensure_ascii=False)

    short_payload.short_description = 'Payload'


@admin.register(CredentialsArena)
class CredentialsArenaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome_maquina', 'client_id', 'client_secret', 'api_key')
    list_filter = ('nome_maquina',)
    search_fields = ('nome_maquina',)


@admin.register(EventosSge)
class EventoSgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_sge', 'local', 'data_inicio', 'data_fim', 'id_tipo', 'descricao', 'escopo', 'audienceName','ano')
    list_filter = ('local', 'id_tipo', 'escopo', 'audienceName', 'ano')
    search_fields = ('escopo', 'descricao')


@admin.register(EventosArena)
class EventoArenaAdmin(admin.ModelAdmin):
    list_display = ("id", "id_arena", "nome_evento", 'get_eventos_sge', "credencial", "isTeamEvent", "isBeachWrestlingTournament", "audienceName")
    list_filter = ("credencial", "isTeamEvent", "isBeachWrestlingTournament", "audienceName")
    search_fields = ("id_arena", "nome_evento")

    def get_eventos_sge(self, obj):
        return ", ".join([n.descricao for n in obj.eventos_sge.all()])


class EventosInline(admin.TabularInline):
    model = EventosArena
    extra = 0



