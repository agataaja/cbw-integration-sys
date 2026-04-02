from ..integrations.authorization_arena import *


def get_endpoint_response(headers, endpoint):
    url = f"http://localhost:8080/api/json/{endpoint}"
    response = requests.get(url, headers=headers)
    return response.json()


def get_custom_id(person_id):

    headers = get_headers()

    custom = get_endpoint_response(headers, f"person/get/{person_id}")

    return custom['person']['customId']


def get_fighter_custom_id(fighter_id):

    headers = get_headers()

    custom = get_endpoint_response(headers, f"fighter/get/{fighter_id}")

    return get_custom_id(custom['fighter']['personId'])


def get_weight_categories_by_sport_event_id(sport_event_id):

    weight_categories = get_endpoint_response(get_headers(), f"weight-category/{sport_event_id}")['weightCategories']
    categorias = {}

    for category in weight_categories:
        id_categoria = category['id']
        nome = category['shortName']
        categorias[id_categoria] = nome
    return categorias


def get_fight(fight_id):
    url = f"http://localhost:8080/api/json/fight/get/{fight_id}"
    r = requests.get(url, headers=get_headers())
    r.raise_for_status()
    return r.json().get("fight", {})


def get_all_fights_by_event_id(event_id):

    url = f"http://localhost:8080/api/json/fight/{event_id}"
    r = requests.get(url, headers=get_headers())
    r.raise_for_status()
    return r.json().get("fights", [])


def get_bracket_by_category_id(event_id, sport_event_weight_category_id):

    url = f'http://localhost:8080/api/json/fight/{event_id}/bracket/{sport_event_weight_category_id}'
    url2 = f'http://localhost:8080/api/json/weight-category/get/{sport_event_weight_category_id}/bracket/live'
    r = requests.get(url2, headers=get_headers())
    r.raise_for_status()
    #return r.json().get("fights", [])
    return r.json()


def get_all_sport_events_info(pk):

    response = get_endpoint_response(get_headers(pk), 'sport-event/')
    return response


def get_weight_category_info_by_its_id(sportEventWeightCategoryId):

    response = get_endpoint_response(get_headers(), f'weight-category/get/{sportEventWeightCategoryId}')

    return response
