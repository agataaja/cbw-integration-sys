"""Arena API transport for cross-system integration.

This module owns the authenticated HTTP access to the Arena API.
The arena app keeps only the inbound boundary and legacy wrappers.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from apps.live.models import ArenaClient, Tunnel

_token_cache: dict[str, dict[str, Any]] = {}


def get_db_credentials_by_pk(pk: int) -> dict[str, str]:
    credential = ArenaClient.objects.get(pk=pk)
    host = Tunnel.objects.get(pk=pk)
    return {
        "api_key": credential.api_key,
        "client_id": credential.client_id,
        "client_secret": credential.client_secret,
        "host": host.public_url,
        "grant_type": credential.grant_type,
    }


def get_token(host: str, client_id: str, client_secret: str, api_key: str, grant_type: str) -> tuple[str, float]:

    if host == "localhost":
        host = "host.docker.internal"
    
    url = f"{host}/oauth/v2/token"
    params = {
        "grant_type": grant_type,
        "client_id": client_id,
        "client_secret": client_secret,
        "api_key": api_key,
    }
    response = requests.post(url, json=params)
    response.raise_for_status()
    data = response.json()

    access_token = data["access_token"]
    expires_in = data.get("expires_in", 3600)
    expires_at = time.time() + expires_in - 60
    return access_token, expires_at


def get_api_base_url(pk: int ) -> str:
    credentials = get_db_credentials_by_pk(pk)
    if credentials["host"] == "localhost":
        host = "host.docker.internal"
    else:
        host = credentials["host"]

    return f"{host}/api/json"


def get_headers(pk: int) -> dict[str, str]:
    credentials = get_db_credentials_by_pk(pk)
    cache_key = str(pk)
    token_data = _token_cache.get(cache_key)

    if token_data is None or time.time() >= token_data["expires_at"]:
        access_token, expires_at = get_token(
            credentials["host"],
            credentials["client_id"],
            credentials["client_secret"],
            credentials["api_key"],
            credentials["grant_type"],
        )
        token_data = {
            "access_token": access_token,
            "expires_at": expires_at,
        }
        _token_cache[cache_key] = token_data

    return {"Authorization": f"Bearer {token_data['access_token']}"}


def get_endpoint_response(headers: dict[str, str], endpoint: str, pk: int) -> dict[str, Any]:
    url = f"{get_api_base_url(pk)}/{endpoint}"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def get_custom_id(person_id: Any, pk: int) -> Any:
    headers = get_headers(pk)
    custom = get_endpoint_response(headers, f"person/get/{person_id}", pk=pk)
    return custom["person"]["customId"]


def get_fighter_custom_id(fighter_id: Any, pk: int) -> Any:
    headers = get_headers(pk)
    custom = get_endpoint_response(headers, f"fighter/get/{fighter_id}", pk=pk)
    return get_custom_id(custom["fighter"]["personId"], pk=pk)


def get_weight_categories_by_sport_event_id(sport_event_id: Any, pk: int) -> dict[Any, str]:
    weight_categories = get_endpoint_response(get_headers(pk), f"weight-category/{sport_event_id}", pk=pk)["weightCategories"]
    categorias: dict[Any, str] = {}
    for category in weight_categories:
        categorias[category["id"]] = category["shortName"]
    return categorias


def get_fight(fight_id: Any, pk: int) -> dict[str, Any]:
    url = f"{get_api_base_url(pk)}/fight/get/{fight_id}"
    response = requests.get(url, headers=get_headers(pk), timeout=30)
    response.raise_for_status()
    return response.json().get("fight", {})


def get_all_fights_by_event_id(event_id: Any, pk: int) -> list[dict[str, Any]]:
    url = f"{get_api_base_url(pk)}/fight/{event_id}"
    response = requests.get(url, headers=get_headers(pk), timeout=30)
    response.raise_for_status()
    return response.json().get("fights", [])


def get_bracket_by_category_id(event_id: Any, sport_event_weight_category_id: Any, pk: int) -> dict[str, Any]:
    url = f"{get_api_base_url(pk)}/weight-category/get/{sport_event_weight_category_id}/bracket/live"
    response = requests.get(url, headers=get_headers(pk), timeout=30)
    response.raise_for_status()
    return response.json()


def get_all_sport_events_info(pk: int) -> dict[str, Any]:
    return get_endpoint_response(get_headers(pk), "sport-event/", pk=pk)


def get_weight_category_info_by_its_id(sport_event_weight_category_id: Any, pk: int) -> dict[str, Any]:
    return get_endpoint_response(get_headers(pk), f"weight-category/get/{sport_event_weight_category_id}", pk=pk)
