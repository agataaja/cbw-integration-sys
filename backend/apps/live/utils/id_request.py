from ..integrations.api_arena import get_fighter_custom_id, get_custom_id


def get_customId_by_fighterId_or_return_0(fighterId):
    try:
        return_id = get_fighter_custom_id(fighterId)
        return return_id
    except(Exception):
        return


def get_customId_by_personId_or_return_0(personId):
    try:
        return_id = get_custom_id(personId)
        return int(return_id)
    except(Exception):
        return

