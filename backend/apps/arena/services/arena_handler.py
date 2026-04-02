from ..models import EventosArena, CredentialsArena
from ..integrations.api_arena import get_all_sport_events_info
from ..utils.maps import map_audience_name_by_name
from django.db import transaction


def get_evento_sge_from_fight(fight_data, sport_event_id=None):
    """
    Retorna o id do evento SGE associado à luta recebida do webhook.
    """
    if not sport_event_id:
        sport_event_id = fight_data.get("sportEventId")

    audience_name = fight_data.get("audienceName")

    if not sport_event_id:
        return None

    try:
        evento_arena = EventosArena.objects.get(id_arena=sport_event_id)
    except EventosArena.DoesNotExist:
        print(f"[WARN] Evento Arena não encontrado para sport_event_id={sport_event_id}")
        return None

    # Filtrar entre os eventos SGE associados
    eventos_sge = evento_arena.eventos_sge.all()

    if not eventos_sge.exists():
        print(f"[WARN] Nenhum evento SGE associado ao evento Arena {evento_arena.nome_evento}")
        return None

    # Tentativa 1: casar pelo audienceName
    if audience_name:
        evento_sge = eventos_sge.filter(audienceName__iexact=audience_name).first()
        if evento_sge:
            return evento_sge.id_sge

    # Tentativa 2: fallback - se só há um evento associado, usa ele
    if eventos_sge.count() == 1:
        return eventos_sge.first().id_sge

    # Tentativa 3: não conseguiu determinar
    print(f"[WARN] Não foi possível determinar evento SGE para arena {evento_arena.id_arena} / audienceName={audience_name}")
    return None


def fetch_eventos_arena(pk):

    eventos_api = get_all_sport_events_info(pk)['events']['items']
    objetos = []

    for item in eventos_api:
        objetos.append({
            "id_arena": item['id'],
            "nome_evento": item['name'],
            "isTeamEvent": item['isTeamEvent'],
            "isBeachWrestlingTournament": item['isBeachWrestlingTournament'],
            "audienceName": map_audience_name_by_name(item['name'])
        })

    credencial_obj = CredentialsArena.objects.get(pk=pk)  # ou pegue pelo id correto

    with transaction.atomic():
        for obj in objetos:
            EventosArena.objects.update_or_create(
                id_arena=obj['id_arena'],
                defaults={
                    "nome_evento": obj['nome_evento'],
                    "isTeamEvent": obj['isTeamEvent'],
                    "isBeachWrestlingTournament": obj['isBeachWrestlingTournament'],
                    "audienceName": obj['audienceName'],
                    "credencial": credencial_obj  # <-- isso é obrigatório
                }
            )