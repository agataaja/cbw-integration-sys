
from apps.sge.models import GestaoAtletas, GestaoAtletasDocumentos, ResultadoSGE, GestaoEventos, InscricoesEventosSGE, RankingSGE



def _generate_event_context(event_id):

    try: 
        event = GestaoEventos.objects.get(id=event_id)

    except GestaoEventos.DoesNotExist:
        return None

    return {
        "id": event.id,
        "nome": event.descricao,
        "data_inicio": event.data_inicio,
        "data_fim": event.data_fim,
        "local": event.local,
        "escopo": event.escopo,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


def _generate_athlete_context(athlete):

    return {
        "id": athlete.id,
        "id_atleta": athlete.id_atleta,
        "nome": athlete.nome,
        "cpf": athlete.cpf,
        "data_nascimento": athlete.data_nascimento,
        "sexo": athlete.sexo,
        "nacionalidade": athlete.nacionalidade,
        "created_at": athlete.created_at,
        "updated_at": athlete.updated_at,
    }


def generate_resultado_sge_context(resultado_sge):

    return {
        "id": resultado_sge.id,
        "id_evento": resultado_sge.id_evento,
        "id_evento_arena": resultado_sge.id_evento_arena,
        "sportalternatename": resultado_sge.sportalternatename,
        "sportname": resultado_sge.sportname,
        "name": resultado_sge.name,
        "sportid": resultado_sge.sportid,
        "audiencename": resultado_sge.audiencename,
        "countfighters": resultado_sge.countfighters,
        "countfights": resultado_sge.countfights,
        "weightcategoryfullname": resultado_sge.weightcategoryfullname,
        "customid": resultado_sge.customid,
        "fullname": resultado_sge.fullname,
        "rank": resultado_sge.rank,
        "id_estabelecimento": resultado_sge.id_estabelecimento,
        "id_classe_peso": resultado_sge.id_classe_peso,
        "created_by": resultado_sge.created_by,
        "updated_by": resultado_sge.updated_by,
        "created_at": resultado_sge.created_at,
        "updated_at": resultado_sge.updated_at
    }

def generate_ranking_sge_context(ranking_sge):

    return {
        "id": ranking_sge.id,
        "id_evento": ranking_sge.id_evento,
        "id_evento_arena": ranking_sge.id_evento_arena,
        "sportalternatename": ranking_sge.sportalternatename,
        "sportname": ranking_sge.sportname,
        "name": ranking_sge.name,
        "sportid": ranking_sge.sportid,
        "audiencename": ranking_sge.audiencename,
        "countfighters": ranking_sge.countfighters,
        "countfights": ranking_sge.countfights,
        "weightcategoryfullname": ranking_sge.weightcategoryfullname,
        "customid": ranking_sge.customid,
        "fullname": ranking_sge.fullname,
        "rank": ranking_sge.rank,
        "id_estabelecimento": ranking_sge.id_estabelecimento,
        "id_classe_peso": ranking_sge.id_classe_peso,
        "created_by": ranking_sge.created_by,
        "updated_by": ranking_sge.updated_by,
        "created_at": ranking_sge.created_at,
        "updated_at": ranking_sge.updated_at
    }


def _query_athlete_by_cpf(cpf):
    """
    Find an athlete by CPF in the SGE database.
    Returns the athlete object if found, otherwise returns None.
    """
    cpf = cpf.replace(".", "").replace("-", "")

    try:
        return GestaoAtletasDocumentos.objects.get(numero=cpf)
    except GestaoAtletasDocumentos.DoesNotExist:
        return None