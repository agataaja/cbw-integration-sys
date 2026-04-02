from ..models import Luta
from ..integrations.api_arena import *
from ..integrations.sge_rest_api import sync_luta_with_remote
from ..utils.id_request import get_customId_by_fighterId_or_return_0, get_customId_by_personId_or_return_0
from ..services.arena_handler import get_evento_sge_from_fight
from datetime import datetime


def handle_webhook(data):

    entity = data.get("entity")

    if entity == "SportEventWeightCategory":
        process_category(data)

    elif entity == "Fight":
        process_fight(data)

    elif entity == "SportEvent":
        process_event(data)


def process_category(data):
    categoria_id = data.get("id")
    if not categoria_id:
        return

    category_info = get_weight_category_info_by_its_id(categoria_id)
    sport_event_id = category_info.get("weightCategory", {}).get("sportEventId")
    fights = get_all_fights_by_event_id(sport_event_id)

    if fights:
        # Já há lutas oficiais, salva normalmente
        for fight in fights:
            evento_id = get_evento_sge_from_fight(fight)
            if not evento_id:
                print("[WARN] luta ignorada — sem evento SGE correspondente")
                continue
            luta_obj = save_luta(fight, evento_id)
            sync_luta_with_remote(luta_obj)
    else:
        # Não há lutas oficiais → pegar dados do bracket (pré-ID)
        bracket = get_bracket_by_category_id(sport_event_id, categoria_id)
        hierarchy = bracket.get("hierarchy", [])
        for luta_data in hierarchy:
            evento_id = get_evento_sge_from_fight(luta_data, sport_event_id=sport_event_id)
            if not evento_id:
                print("[WARN] luta ignorada — sem evento SGE correspondente")
                continue

            save_luta_from_wcategory(luta_data, evento_id)


def process_fight(data):
    fight = get_fight(data.get("id"))
    evento_id = get_evento_sge_from_fight(fight)
    if not evento_id:
        print(f"[WARN] luta ignorada — sem evento SGE correspondente")
        return

    # verifica se existe luta temporária correspondente
    existing_temp = Luta.objects.filter(
        id_evento=evento_id,
        id_categoria_arena=fight.get("SportEventWeightCategoryId"),
        numero=fight.get("fightNumber"),
        is_temporary=True
    ).first()

    if existing_temp:
        print(f"[INFO] Atualizando luta temporária → {existing_temp.id}")
        existing_temp.id = f"{fight['id']}-{evento_id}"
        existing_temp.id_arena = fight["id"]
        existing_temp.is_temporary = False
        existing_temp.save()
        luta_obj = existing_temp
        sync_luta_with_remote(luta_obj)

    else:
        luta_obj = save_luta(fight, evento_id)
        sync_luta_with_remote(luta_obj)


def process_event(data):
    print(">>> Iniciando process_event")

    start = time.perf_counter()

    sport_event_id = data.get("id")
    fights = get_all_fights_by_event_id(sport_event_id)

    for fight in fights:
        evento_id = get_evento_sge_from_fight(fight)
        if not evento_id:
            print(f"[WARN] luta ignorada — sem evento SGE correspondente")
            continue
        luta_obj = save_luta(fight, evento_id=evento_id)
        sync_luta_with_remote(luta_obj)

    end = time.perf_counter()
    elapsed = end - start

    print(f">>> Finalizou process_event, total de lutas do evento: {len(fights)}")
    print(f">>> Tempo de execução: {elapsed:.2f} segundos")


def save_luta(luta_data, evento_id):

    id_arena = luta_data.get("id")
    id_categoria_arena = luta_data.get("SportEventWeightCategoryId")
    fight_number = luta_data.get("fightNumber")

    completa = int(bool(luta_data.get("isCompleted", 0)))

    if completa:

        id_winner = get_customId_by_fighterId_or_return_0(luta_data.get("winnerFighter"))

    is_temp = not bool(id_arena)

    # id único previsível
    if is_temp:
        id_luta = f"temp-{evento_id}-{id_categoria_arena}-{fight_number}"
    else:
        id_luta = f"{id_arena}-{evento_id}"

    luta_obj, _ = Luta.objects.update_or_create(
        id=id_luta,
        defaults={
            'id_categoria_arena': luta_data.get("SportEventWeightCategoryId"),
            "id_evento": evento_id,
            "flag_finalizado": int(bool(luta_data.get("isCompleted", 0))),
            "round": luta_data.get("round", ""),
            "id_atleta_ganhador": get_customId_by_fighterId_or_return_0(luta_data.get("winnerFighter")),
            "sportAlternateName": luta_data.get("sportAlternateName", ""),
            "weightCategoryName": luta_data.get("weightCategoryName", ""),
            "audienceName": luta_data.get("audienceName", ""),

            "id_atleta1": get_customId_by_personId_or_return_0(luta_data.get("fighter1PersonId")),
            "atleta1_flag_injured": int(bool(luta_data.get("fighter1IsInjured", 0))),
            "atleta1_flag_seeded": int(bool(luta_data.get("fighter1IsSeeded", 0))),
            "atleta1_draw_rank": luta_data.get("fighter1DrawRank", ""),
            "atleta1_RobinRank": luta_data.get("fighter1RobinRank", ""),
            "atleta1_ranking_point": luta_data.get("fighter1RankingPoint", 0),

            "id_atleta2": get_customId_by_personId_or_return_0(luta_data.get("fighter2PersonId")),
            "atleta2_flag_injured": int(bool(luta_data.get("fighter2IsInjured", 0))),
            "atleta2_flag_seeded": int(bool(luta_data.get("fighter2IsSeeded", 0))),
            "atleta2_draw_rank": luta_data.get("fighter2DrawRank", ""),
            "atleta2_RobinRank": luta_data.get("fighter2RobinRank", ""),
            "atleta2_ranking_point": luta_data.get("fighter2RankingPoint", 0),
            "resultado": luta_data.get("result", ""),
            "tipo_vitoria": luta_data.get("victoryType", ""),
            "numero": luta_data.get("fightNumber", 0),
            "tapete": luta_data.get("matName", ""),
            "data_inicio": luta_data.get("expectedStartDate", datetime.now()),
            "data_fim": luta_data.get("completedDate", datetime.now()),
        },
    )
    return luta_obj

