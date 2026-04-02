import requests
from ..utils.formatters import format_datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import logging
import os

API_URL = "https://restcbw.bigmidia.com/cbw/api/evento-luta"
API_HEADERS = {"Content-Type": "application/json"}


# === CONFIGURAÇÃO DE LOGGING ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

success_logger = logging.getLogger("success_logger")
error_logger = logging.getLogger("error_logger")

success_handler = logging.FileHandler(os.path.join(LOG_DIR, "success.log"))
error_handler = logging.FileHandler(os.path.join(LOG_DIR, "errors.log"))

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

success_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

success_logger.addHandler(success_handler)
error_logger.addHandler(error_handler)

success_logger.setLevel(logging.INFO)
error_logger.setLevel(logging.ERROR)


def log_success(method, url, status_code, payload=None, response_text=None):
    success_logger.info(
        f"[{method}] {url} | Status: {status_code} | Payload: {payload} | Response: {response_text}"
    )


def log_error(method, url, status_code=None, error=None, payload=None, response_text=None):
    error_logger.error(
        f"[{method}] {url} | Status: {status_code} | Error: {error} | Payload: {payload} | Response: {response_text}"
    )


def sync_luta_with_remote(luta_obj):

    payload = {
        "id": luta_obj.id,
        "id_evento": luta_obj.id_evento,
        "numero": luta_obj.numero,
        "tapete": luta_obj.tapete,
        "round": luta_obj.round,
        "sportAlternateName": luta_obj.sportAlternateName,
        "weightCategoryName": luta_obj.weightCategoryName,
        "audienceName": luta_obj.audienceName,
        "id_classe_peso": luta_obj.id_classe_peso,
        "flag_finalizado": luta_obj.flag_finalizado,
        "id_atleta_ganhador": luta_obj.id_atleta_ganhador,
        "resultado": luta_obj.resultado,
        "tipo_vitoria": luta_obj.tipo_vitoria,
        "id_atleta1": str(luta_obj.id_atleta1),
        "atleta1_flag_injured": luta_obj.atleta1_flag_injured,
        "atleta1_flag_seeded": luta_obj.atleta1_flag_seeded,
        "atleta1_draw_rank": luta_obj.atleta1_draw_rank,
        "atleta1_RobinRank": luta_obj.atleta1_RobinRank,
        "atleta1_ranking_point": luta_obj.atleta1_ranking_point,
        "id_atleta2": str(luta_obj.id_atleta2),
        "atleta2_flag_injured": luta_obj.atleta2_flag_injured,
        "atleta2_flag_seeded": luta_obj.atleta2_flag_seeded,
        "atleta2_draw_rank": str(luta_obj.atleta2_draw_rank),
        "atleta2_RobinRank": luta_obj.atleta2_RobinRank,
        "atleta2_ranking_point": luta_obj.atleta2_ranking_point,
        "data_inicio": format_datetime(
            luta_obj.data_inicio),
        "data_fim": format_datetime(
            luta_obj.data_fim)
    }

    try:
        r = requests.get(f"{API_URL}/{luta_obj.id}", headers=API_HEADERS)

        if r.status_code == 200:
            s = requests.put(f"{API_URL}/{luta_obj.id}", headers=API_HEADERS, json=payload)
            if 200 <= s.status_code < 300:
                log_success("PUT", f"{API_URL}/{luta_obj.id}", s.status_code, payload, s.text)
            else:
                log_error("PUT", f"{API_URL}/{luta_obj.id}", s.status_code, payload=payload, response_text=s.text)
        else:
            p = requests.post(API_URL, headers=API_HEADERS, json=payload)
            if 200 <= p.status_code < 300:
                log_success("POST", API_URL, p.status_code, payload, p.text)
            else:
                log_error("POST", API_URL, p.status_code, payload=payload, response_text=p.text)

    except Exception as e:
        log_error("SYNC", API_URL, error=str(e), payload=payload)


def fetch_data(base_url, querys, headers, page):

    response = requests.get(f"{base_url}?page={page}{querys}", headers=headers).json()['items']
    return pd.json_normalize(response)


def clean_all_records(query):

    page_count = requests.get(f"{API_URL}", headers=API_HEADERS).json()["_meta"]["pageCount"]
    querys = f"&{query}"

    print(page_count)

    with ThreadPoolExecutor() as executor:
        dfs = executor.map(lambda page: fetch_data(API_URL, querys, API_HEADERS, page), range(1, page_count + 1))

    final_df = pd.concat(dfs, ignore_index=True)

    for _, record in final_df.iterrows():

        id_luta = record['id']

        p = requests.delete(f'{API_URL}/{id_luta}')
        print(p.status_code, p.text)


def request_athlete_photo(id_atleta):

    url = f'https://restcbw.bigmidia.com/gestao/api/atleta/{id_atleta}'

    photo_id = requests.get(url, headers=API_HEADERS).json()['foto']

    photo_url = f'https://sge.cbw.org.br/_uploads/fotoAtleta/{photo_id}'

    return photo_url


def get_all_sge_eventos_info():

    base_url = "https://restcbw.bigmidia.com/gestao/api/evento"
    querys = f"&flag_del=0"

    page_count = requests.get(f"{base_url}", headers=API_HEADERS).json()["_meta"]["pageCount"]

    with ThreadPoolExecutor() as executor:

        dfs = executor.map(lambda page: fetch_data(base_url, querys, API_HEADERS, page), range(1, page_count+1))

    df = pd.concat(dfs, ignore_index=True)
    df["ano"] = pd.to_datetime(df["data_fim"]).dt.year
    df = df[df['flag_del'] == 0]
    return df
