import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "site1.site1.settings")  # ajuste o nome do seu projeto
django.setup()

from polls.integrations.sge_rest_api import sync_luta_with_remote, clean_all_records
from polls.models import Luta
from polls.integrations.api_arena import get_weight_category_info_by_its_id, get_all_sport_events_info


def test_sending_data_sge():

    lutas = Luta.objects.all()

    for luta in lutas:
        sync_luta_with_remote(luta)


def cleaning_all_sge_records(query):

    clean_all_records(query)


if __name__ == '__main__':

    cleaning_all_sge_records("id_evento=179")
