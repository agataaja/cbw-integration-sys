from ..models import EventosSge
from ..integrations.sge_rest_api import get_all_sge_eventos_info
from ..utils.maps import map_audience_name_by_name
from django.db import transaction


def process_eventos_sge():
    df = get_all_sge_eventos_info()

    objetos = []
    for _, row in df.iterrows():
        objetos.append(EventosSge(
            id_sge=row['id'],
            local=row['local'],
            data_inicio=row['data_inicio'],
            data_fim=row['data_fim'],
            id_tipo=row['id_tipo'],
            descricao=row['descricao'],
            escopo=row['escopo'],
            audienceName=map_audience_name_by_name(row['descricao']),
            ano =row['ano']

        ))

    # Use transaction.atomic para garantir integridade
    with transaction.atomic():
        for obj in objetos:
            # update_or_create por registro
            EventosSge.objects.update_or_create(
                id_sge=obj.id_sge,
                defaults={
                    "local": obj.local,
                    "data_inicio": obj.data_inicio,
                    "data_fim": obj.data_fim,
                    "id_tipo": obj.id_tipo,
                    "descricao": obj.descricao,
                    "escopo": obj.escopo,
                    "audienceName": obj.audienceName,
                    "ano": obj.ano
                }
            )
