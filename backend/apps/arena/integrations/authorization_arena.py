import requests
import time
from ..models import CredentialsArena


# Variáveis globais de cache
_cached_token = None
_token_expires_at = 0  # timestamp


def get_db_credentials_by_pk(pk):

    credencial_pk = CredentialsArena.objects.get(pk=pk)

    api_key = credencial_pk.api_key
    client_id = credencial_pk.client_id
    client_secret = credencial_pk.client_secret

    return api_key, client_id, client_secret


def get_headers(pk=4):

    credentials = get_db_credentials_by_pk(pk)

    api_key = credentials[0]
    client_id = credentials[1]
    client_secret = credentials[2]
    ip = 'localhost'

    global _cached_token, _token_expires_at

    # Verifica se o token ainda está válido
    if _cached_token is None or time.time() >= _token_expires_at:
        _cached_token, _token_expires_at = get_token(ip, client_id, client_secret, api_key)
        print('new token')

    headers = {'Authorization': f'Bearer {_cached_token}'}

    return headers


def get_token(ip, client_id, client_secret, api_key):

    url = f'http://{ip}:8080/oauth/v2/token'
    params = {
        'grant_type': 'https://arena.uww.io/grants/api_key',
        'client_id': client_id,
        'client_secret': client_secret,
        'api_key': api_key
    }
    response = requests.post(url, params=params)
    data = response.json()

    access_token = data["access_token"]
    expires_in = data.get("expires_in", 3600)  # segundos
    expires_at = time.time() + expires_in - 60  # margem de 1 min

    return access_token, expires_at

