import requests


def get_token(api_key, client_id, client_secret, ip):
    url = f'http://{ip}:8080/oauth/v2/token'
    params = {
        'grant_type': 'https://arena.uww.io/grants/api_key',
        'client_id': client_id,
        'client_secret': client_secret,
        'api_key': api_key
    }
    response = requests.post(url, params=params)
    return response.json()["access_token"]


def get_endpoint_response(headers, endpoint):
    url = f"http://localhost:8080/api/json/{endpoint}"
    response = requests.get(url, headers=headers)
    return response.json()


def post_endpoint(headers, endpoint, data):

    url = f"http://localhost:8080/api/json/{endpoint}"
    response = requests.post(url, headers=headers, json=data)

    return print(response.status_code)


def patch_endpoint(headers, endpoint, data):

    url = f"http://localhost:8080/api/json/{endpoint}"
    response = requests.put(url, headers=headers, json=data)

    return print(response.status_code)


def delete_endpoint(headers, endpoint, data):

    url = f"http://localhost:8080/api/json/{endpoint}"
    response = requests.delete(url, headers=headers, json=data)

    return print(response.status_code)


def get_custom_id(headers, person_id):

    custom = get_endpoint_response(headers, f"person/get/{person_id}")
    return custom['person']['customId']



